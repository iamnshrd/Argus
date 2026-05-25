#!/usr/bin/env python3
"""
Forecast Kalshi's weekly Trump Truth Social post-count bins.

The target is the Roll Call / Factba.se count used by Kalshi, not a native
Truth Social scrape. This keeps the model aligned with resolution mechanics.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from rollcall_client import JsonCountCache, RollCallClient, RollCallCount, RollCallError, RollCallPost

KALSHI_EVENT_URL = "https://api.elections.kalshi.com/trade-api/v2/events/{ticker}"
ET = ZoneInfo("America/New_York")
WEEK_SECONDS = 7 * 24 * 60 * 60
APP_DIR = Path(__file__).resolve().parent
DEFAULT_CACHE_FILE = APP_DIR / ".cache" / "rollcall_counts.json"


@dataclass(frozen=True)
class Bin:
    label: str
    ticker: str
    strike_type: str
    floor: int | None
    cap: int | None
    yes_bid: float | None
    yes_ask: float | None

    def contains(self, value: int) -> bool:
        if self.strike_type == "less":
            return self.cap is not None and value < self.cap
        if self.strike_type == "greater":
            return self.floor is not None and value > self.floor
        if self.strike_type == "between":
            return (
                self.floor is not None
                and self.cap is not None
                and self.floor <= value <= self.cap
            )
        return False


@dataclass(frozen=True)
class PostHistoryRow:
    post: RollCallPost
    source_week_start: date


def request_json(url: str, timeout: int = 25) -> dict:
    request = Request(url, headers={"User-Agent": "Argus TruthSocialForecast/0.1"})
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def sunday_for(day: date) -> date:
    return day - timedelta(days=(day.weekday() + 1) % 7)


def current_week(now_et: datetime) -> tuple[date, date]:
    start = sunday_for(now_et.date())
    return start, start + timedelta(days=6)


def kalshi_suffix(day: date) -> str:
    return day.strftime("%y%b%d").upper()


def default_event_ticker(week_end: date) -> str:
    return f"KXTRUTHSOCIAL-{kalshi_suffix(week_end)}"


def parse_bins(event: dict) -> list[Bin]:
    bins: list[Bin] = []
    for market in event.get("markets", []):
        bins.append(
            Bin(
                label=market.get("yes_sub_title") or market.get("title") or market["ticker"],
                ticker=market["ticker"],
                strike_type=market["strike_type"],
                floor=market.get("floor_strike"),
                cap=market.get("cap_strike"),
                yes_bid=parse_price(market.get("yes_bid_dollars")),
                yes_ask=parse_price(market.get("yes_ask_dollars")),
            )
        )
    return sorted(bins, key=bin_sort_key)


def parse_price(value: object) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def bin_sort_key(item: Bin) -> tuple[int, int]:
    lower = item.floor if item.floor is not None else -10**9
    upper = item.cap if item.cap is not None else 10**9
    return lower, upper


def fallback_bins() -> list[Bin]:
    ranges = [
        ("<80", "less", None, 80),
        ("80-99", "between", 80, 99),
        ("100-119", "between", 100, 119),
        ("120-139", "between", 120, 139),
        ("140-159", "between", 140, 159),
        ("160-179", "between", 160, 179),
        ("180-199", "between", 180, 199),
        ("200-220", "between", 200, 220),
        (">220", "greater", 220, None),
    ]
    return [
        Bin(label=label, ticker="", strike_type=strike_type, floor=floor, cap=cap, yes_bid=None, yes_ask=None)
        for label, strike_type, floor, cap in ranges
    ]


def fetch_bins(event_ticker: str) -> tuple[list[Bin], str | None]:
    try:
        event = request_json(KALSHI_EVENT_URL.format(ticker=event_ticker))
    except (HTTPError, URLError, TimeoutError) as exc:
        return fallback_bins(), f"Kalshi event fetch failed: {exc}. Using fallback bins."

    bins = parse_bins(event)
    if not bins:
        return fallback_bins(), "Kalshi event had no markets. Using fallback bins."
    return bins, None


def recency_weights(history: list[RollCallCount], half_life_weeks: float) -> list[float]:
    # history[0] is the most recent completed week.
    return [0.5 ** (index / half_life_weeks) for index, _ in enumerate(history)]


def weighted_choice(items: list[RollCallCount], weights: list[float]) -> RollCallCount:
    return random.choices(items, weights=weights, k=1)[0]


def elapsed_week_fraction(now_et: datetime, week_start: date) -> float:
    start_dt = datetime.combine(week_start, time.min, ET)
    elapsed = max(0.0, (now_et - start_dt).total_seconds())
    return min(1.0, elapsed / WEEK_SECONDS)


def forecast_totals(
    history: list[RollCallCount],
    observed_so_far: int,
    phase_fraction: float,
    samples: int,
    half_life_weeks: float,
    live_prior_hours: float,
) -> list[int]:
    if not history:
        raise ValueError("Need at least one historical week.")

    weights = recency_weights(history, half_life_weeks)
    weighted_mean = sum(w * item.count for item, w in zip(history, weights)) / sum(weights)
    expected_so_far = max(1.0, weighted_mean * phase_fraction)

    elapsed_hours = phase_fraction * 7 * 24
    live_weight = elapsed_hours / (elapsed_hours + live_prior_hours)
    live_ratio = observed_so_far / expected_so_far
    live_scale = max(0.35, min(2.75, 1 + live_weight * (live_ratio - 1)))

    counts = [item.count for item in history]
    spread = statistics.pstdev(counts) if len(counts) > 1 else max(20.0, counts[0] * 0.2)
    noise_sigma = min(0.35, max(0.08, spread / max(1.0, statistics.mean(counts)) * 0.35))

    totals: list[int] = []
    for _ in range(samples):
        base = weighted_choice(history, weights).count
        noise = random.lognormvariate(mu=-(noise_sigma**2) / 2, sigma=noise_sigma)
        total = int(round(base * live_scale * noise))
        totals.append(max(observed_so_far, total))
    return totals


def load_post_history(path: Path) -> list[PostHistoryRow]:
    posts: list[PostHistoryRow] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                item = json.loads(line)
                post = RollCallPost.from_json(item)
                source_week = item.get("source_week_start")
                source_week_start = (
                    date.fromisoformat(source_week)
                    if source_week
                    else sunday_for(post.posted_at.astimezone(ET).date())
                )
                posts.append(PostHistoryRow(post=post, source_week_start=source_week_start))
    return posts


def post_history_weeks(posts: list[PostHistoryRow]) -> list[tuple[date, list[float]]]:
    grouped: dict[date, list[float]] = {}
    for row in posts:
        posted_at = row.post.posted_at.astimezone(ET)
        week_start = row.source_week_start
        start_dt = datetime.combine(week_start, time.min, ET)
        offset = (posted_at - start_dt).total_seconds()
        grouped.setdefault(week_start, []).append(offset)

    return [(start, sorted(offsets)) for start, offsets in sorted(grouped.items(), reverse=True)]


def forecast_totals_from_posts(
    posts: list[PostHistoryRow],
    observed_so_far: int,
    phase_fraction: float,
    samples: int,
    half_life_weeks: float,
    noise_sigma: float,
) -> list[int]:
    weeks = post_history_weeks(posts)
    if not weeks:
        raise ValueError("Post history has no complete Sunday-Saturday weeks.")

    weights = [0.5 ** (index / half_life_weeks) for index, _ in enumerate(weeks)]
    cutoff = phase_fraction * WEEK_SECONDS
    totals: list[int] = []
    for _ in range(samples):
        _, offsets = random.choices(weeks, weights=weights, k=1)[0]
        remaining = sum(1 for offset in offsets if offset > cutoff)
        if noise_sigma > 0 and remaining > 0:
            noise = random.lognormvariate(mu=-(noise_sigma**2) / 2, sigma=noise_sigma)
            remaining = max(0, int(round(remaining * noise)))
        totals.append(observed_so_far + remaining)
    return totals


def bin_probabilities(totals: Iterable[int], bins: list[Bin]) -> list[tuple[Bin, float]]:
    totals = list(totals)
    if not totals:
        return [(item, 0.0) for item in bins]

    rows = []
    for item in bins:
        hits = sum(1 for total in totals if item.contains(total))
        rows.append((item, hits / len(totals)))
    return rows


def percentile(values: list[int], pct: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = round((len(ordered) - 1) * pct)
    return ordered[index]


def print_report(
    *,
    now_et: datetime,
    week_start: date,
    week_end: date,
    event_ticker: str,
    observed: int,
    history: list[RollCallCount],
    post_history_path: Path | None,
    totals: list[int],
    bins: list[Bin],
    warning: str | None,
) -> None:
    counts = [item.count for item in history]
    print("Truth Social weekly post-count forecast")
    print(f"Target: {event_ticker} ({week_start} to {week_end}, ET)")
    print(f"Now ET: {now_et:%Y-%m-%d %H:%M:%S %Z}")
    print(f"Observed Roll Call count so far: {observed}")
    if warning:
        print(f"Warning: {warning}")
    print()
    print(
        "History: "
        f"n={len(counts)}, mean={statistics.mean(counts):.1f}, "
        f"median={statistics.median(counts):.0f}, "
        f"stdev={statistics.pstdev(counts):.1f}, min={min(counts)}, max={max(counts)}"
    )
    print(
        "Forecast total: "
        f"p10={percentile(totals, 0.10)}, "
        f"p25={percentile(totals, 0.25)}, "
        f"p50={percentile(totals, 0.50)}, "
        f"p75={percentile(totals, 0.75)}, "
        f"p90={percentile(totals, 0.90)}"
    )
    if post_history_path:
        print(f"Simulation source: post history ({post_history_path})")
    else:
        print("Simulation source: weekly count baseline")
    print()
    print("Bins")
    print(f"{'bin':>10} {'prob':>8} {'fair':>8} {'yes bid':>8} {'yes ask':>8}  ticker")
    for item, probability in bin_probabilities(totals, bins):
        bid = price_text(item.yes_bid)
        ask = price_text(item.yes_ask)
        print(
            f"{item.label:>10} "
            f"{probability:>7.1%} "
            f"{probability * 100:>7.1f}c "
            f"{bid:>8} "
            f"{ask:>8}  "
            f"{item.ticker}"
        )
    print()
    print("Recent completed weeks")
    for item in history[:8]:
        print(f"{item.start}..{item.end}: {item.count}")


def price_text(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value * 100:.0f}c"


def parse_now(value: str | None) -> datetime:
    if not value:
        return datetime.now(ET)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=ET)
    return parsed.astimezone(ET)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--now", help="Current ET timestamp, e.g. 2026-05-24T10:00:00")
    parser.add_argument("--event-ticker", help="Kalshi event ticker. Defaults to the current week.")
    parser.add_argument("--lookback-weeks", type=int, default=26)
    parser.add_argument("--samples", type=int, default=30000)
    parser.add_argument("--half-life-weeks", type=float, default=8.0)
    parser.add_argument("--live-prior-hours", type=float, default=36.0)
    parser.add_argument("--post-history", type=Path, help="JSONL post history from download_truths.py.")
    parser.add_argument("--post-noise-sigma", type=float, default=0.12)
    parser.add_argument("--cache-file", type=Path, default=DEFAULT_CACHE_FILE)
    parser.add_argument("--cache-ttl-hours", type=float, default=12.0)
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args(argv)

    if args.lookback_weeks < 4:
        parser.error("--lookback-weeks must be at least 4")
    if args.samples < 1000:
        parser.error("--samples must be at least 1000")

    random.seed(args.seed)
    now_et = parse_now(args.now)
    week_start, week_end = current_week(now_et)
    event_ticker = args.event_ticker or default_event_ticker(week_end)
    cache = None if args.no_cache else JsonCountCache(args.cache_file, args.cache_ttl_hours)
    rollcall = RollCallClient(cache=cache)

    try:
        observed = rollcall.count_truth_social_posts(week_start, now_et.date(), use_cache=False)
        history = rollcall.count_completed_weeks(week_start, args.lookback_weeks)
        bins, warning = fetch_bins(event_ticker)
        if args.post_history:
            totals = forecast_totals_from_posts(
                posts=load_post_history(args.post_history),
                observed_so_far=observed,
                phase_fraction=elapsed_week_fraction(now_et, week_start),
                samples=args.samples,
                half_life_weeks=args.half_life_weeks,
                noise_sigma=args.post_noise_sigma,
            )
        else:
            totals = forecast_totals(
                history=history,
                observed_so_far=observed,
                phase_fraction=elapsed_week_fraction(now_et, week_start),
                samples=args.samples,
                half_life_weeks=args.half_life_weeks,
                live_prior_hours=args.live_prior_hours,
            )
    except (HTTPError, URLError, TimeoutError, KeyError, ValueError, RollCallError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        if cache:
            cache.save()

    print_report(
        now_et=now_et,
        week_start=week_start,
        week_end=week_end,
        event_ticker=event_ticker,
        observed=observed,
        history=history,
        post_history_path=args.post_history,
        totals=totals,
        bins=bins,
        warning=warning,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
