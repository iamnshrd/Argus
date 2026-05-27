#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

from backtest_point import feature_weight, simulate_from_features, week_features
from live_features import largest_burst
from regime import classify_regime, extreme_outlier_risk
from rollcall_client import RollCallClient
from topic_mix import classify_row, load_topics
from truthsocial_forecast import (
    APP_DIR,
    ET,
    PostHistoryRow,
    bin_probabilities,
    current_week,
    default_event_ticker,
    elapsed_week_fraction,
    fallback_bins,
    fetch_bins,
    load_post_history,
    percentile,
)


DEFAULT_HISTORY = APP_DIR / "data" / "truthsocial_posts_2026-01-04_2026-05-23.jsonl"
DEFAULT_OUTPUT = APP_DIR / "pages" / "data" / "forecast.json"
DEFAULT_TAXONOMY = APP_DIR / "topic_taxonomy.json"
DEFAULT_CALENDAR = APP_DIR / "data" / "election_calendar_2026.csv"


def parse_now(value: str | None) -> datetime:
    if not value:
        return datetime.now(ET)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=ET)
    return parsed.astimezone(ET)


def request_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": "Argus TruthSocialPages/0.1"})
    with urlopen(request, timeout=25) as response:
        return json.load(response)


def cents(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value * 100, 1)


def orderbook_quote(ticker: str) -> dict:
    try:
        data = request_json(f"https://api.elections.kalshi.com/trade-api/v2/markets/{ticker}/orderbook")
    except OSError:
        return {}
    book = data.get("orderbook_fp", {})
    yes_levels = [(float(price) * 100, float(quantity)) for price, quantity in book.get("yes_dollars", [])]
    no_levels = [(float(price) * 100, float(quantity)) for price, quantity in book.get("no_dollars", [])]
    yes_bid = max(yes_levels, default=(None, 0), key=lambda item: item[0])
    no_bid = max(no_levels, default=(None, 0), key=lambda item: item[0])
    return {
        "yesBid": yes_bid[0],
        "yesBidQuantity": yes_bid[1],
        "yesAsk": 100 - no_bid[0] if no_bid[0] is not None else None,
        "yesAskQuantity": no_bid[1],
        "noBid": no_bid[0],
        "noBidQuantity": no_bid[1],
        "noAsk": 100 - yes_bid[0] if yes_bid[0] is not None else None,
        "noAskQuantity": yes_bid[1],
    }


def load_calendar(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
        return [{**row, "date": date.fromisoformat(row["date"])} for row in csv.DictReader(file)]


def future_events(calendar: list[dict], now_et: datetime, days: int = 14) -> list[dict]:
    end = now_et.date() + timedelta(days=days)
    return [event for event in calendar if now_et.date() <= event["date"] <= end]


def row_offset(row: PostHistoryRow) -> int:
    posted = row.post.posted_at.astimezone(ET)
    start = datetime.combine(row.source_week_start, datetime.min.time(), ET)
    return int((posted - start).total_seconds())


def daily_profile(rows: list[PostHistoryRow]) -> list[dict]:
    names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    counts = defaultdict(int)
    weeks = {row.source_week_start for row in rows}
    for row in rows:
        day_index = (row.post.posted_at.astimezone(ET).date() - row.source_week_start).days
        if 0 <= day_index <= 6:
            counts[(row.source_week_start, day_index)] += 1
    profile = []
    for day_index, name in enumerate(names):
        values = [counts[(week, day_index)] for week in weeks]
        profile.append(
            {
                "day": name,
                "mean": round(statistics.mean(values), 1),
                "median": round(statistics.median(values), 1),
                "min": min(values),
                "max": max(values),
            }
        )
    return profile


def topic_summary(rows: list[PostHistoryRow], taxonomy: Path, limit: int = 8) -> list[dict]:
    topics = load_topics(taxonomy)
    counts = Counter(classify_row(row, topics) for row in rows)
    total = len(rows)
    return [
        {
            "topic": topic,
            "count": count,
            "share": round(count / total, 4) if total else 0,
        }
        for topic, count in counts.most_common(limit)
    ]


def grouped_by_week(rows: list[PostHistoryRow]) -> dict[date, list[PostHistoryRow]]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[row.source_week_start].append(row)
    return grouped


def page_forecast_totals(
    *,
    current_week_start: date,
    current_posts: list[PostHistoryRow],
    history_rows: list[PostHistoryRow],
    cutoff_seconds: int,
    topics: list[dict],
    calendar: list[dict],
    samples: int,
) -> tuple[list[int], dict, list[dict], list[float]]:
    target = week_features(current_week_start, current_posts, cutoff_seconds, topics, calendar, 14)
    training = [
        week_features(source_week, rows, cutoff_seconds, topics, calendar, 14)
        for source_week, rows in grouped_by_week(history_rows).items()
    ]
    weights = [feature_weight(candidate, target) for candidate in training]
    totals = simulate_from_features(
        target,
        training,
        weights,
        samples,
        noise_sigma=0.12,
        tail_overlay=False,
    )
    return totals, target, training, weights


def nearest_weeks(training: list[dict], weights: list[float], limit: int = 6) -> list[dict]:
    return [
        {
            "week": candidate["week"].isoformat(),
            "weight": round(weight, 4),
            "observed": candidate["observed"],
            "last24": candidate["last24"],
            "burst6": candidate["burst6"],
            "actual": candidate["actual"],
            "remaining": len(candidate["remaining"]),
        }
        for candidate, weight in sorted(
            zip(training, weights),
            key=lambda item: item[1],
            reverse=True,
        )[:limit]
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build static GitHub Pages data for Truth Social forecast.")
    parser.add_argument("--now")
    parser.add_argument("--event-ticker")
    parser.add_argument("--post-history", type=Path, default=DEFAULT_HISTORY)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument("--calendar", type=Path, default=DEFAULT_CALENDAR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--samples", type=int, default=50000)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    random.seed(args.seed)
    now_et = parse_now(args.now)
    week_start, week_end = current_week(now_et)
    event_ticker = args.event_ticker or default_event_ticker(week_end)
    calendar = load_calendar(args.calendar)
    topics = load_topics(args.taxonomy)
    rollcall = RollCallClient()
    current_posts = [
        PostHistoryRow(post=post, source_week_start=week_start)
        for post in rollcall.truth_social_posts(week_start, now_et.date())
        if post.posted_at.astimezone(ET) <= now_et
    ]
    observed = len(current_posts)
    history_rows = load_post_history(args.post_history)
    cutoff_seconds = int(elapsed_week_fraction(now_et, week_start) * 7 * 24 * 60 * 60)
    totals, target, training, weights = page_forecast_totals(
        current_week_start=week_start,
        current_posts=current_posts,
        history_rows=history_rows,
        cutoff_seconds=cutoff_seconds,
        topics=topics,
        calendar=calendar,
        samples=args.samples,
    )
    bins, warning = fetch_bins(event_ticker)
    if not bins:
        bins = fallback_bins()

    market_rows = []
    for item, probability in bin_probabilities(totals, bins):
        yes_fair = round(probability * 100, 1)
        no_fair = round(100 - yes_fair, 1)
        quote = orderbook_quote(item.ticker) if item.ticker else {}
        yes_bid = quote.get("yesBid", cents(item.yes_bid))
        yes_ask = quote.get("yesAsk", cents(item.yes_ask))
        no_bid = quote.get("noBid", 100 - yes_ask if yes_ask is not None else None)
        no_ask = quote.get("noAsk", 100 - yes_bid if yes_bid is not None else None)
        market_rows.append(
            {
                "label": item.label,
                "ticker": item.ticker,
                "yesFair": yes_fair,
                "noFair": no_fair,
                "yesBid": yes_bid,
                "yesAsk": yes_ask,
                "noBid": no_bid,
                "noAsk": no_ask,
                "noAskQuantity": quote.get("noAskQuantity"),
                "yesEdgeAtAsk": round(yes_fair - yes_ask, 1) if yes_ask is not None else None,
                "noEdgeAtAsk": round(no_fair - no_ask, 1) if no_ask is not None else None,
            }
        )

    events = future_events(calendar, now_et)
    last6 = sum(1 for row in current_posts if now_et - row.post.posted_at.astimezone(ET) <= timedelta(hours=6))
    last24 = sum(1 for row in current_posts if now_et - row.post.posted_at.astimezone(ET) <= timedelta(hours=24))
    regime, regime_reasons = classify_regime(target)
    outlier_risk, outlier_reasons = extreme_outlier_risk(target)

    data = {
        "generatedAt": datetime.now(ET).isoformat(),
        "nowEt": now_et.isoformat(),
        "eventTicker": event_ticker,
        "marketUrl": f"https://kalshi.com/markets/kxtruthsocial/number-of-trump-truth-social-posts-this-week/{event_ticker.lower()}",
        "week": {"start": week_start.isoformat(), "end": week_end.isoformat()},
        "observed": observed,
        "forecast": {
            "mean": round(statistics.mean(totals), 1),
            "p10": percentile(totals, 0.10),
            "p25": percentile(totals, 0.25),
            "p50": percentile(totals, 0.50),
            "p75": percentile(totals, 0.75),
            "p90": percentile(totals, 0.90),
        },
        "live": {
            "last6h": last6,
            "last24h": last24,
            "largest1hBurst": largest_burst(current_posts, 1),
            "largest6hBurst": largest_burst(current_posts, 6),
            "topics": topic_summary(current_posts, args.taxonomy),
            "futureEvents": [
                {"date": event["date"].isoformat(), "type": event["type"], "name": event["name"]}
                for event in events[:8]
            ],
        },
        "model": {
            "name": "similarity-weighted live state",
            "regime": regime,
            "regimeReasons": regime_reasons,
            "extremeOutlierRisk": outlier_risk,
            "extremeOutlierReasons": outlier_reasons,
            "nearestWeeks": nearest_weeks(training, weights),
        },
        "dailyProfile": daily_profile(history_rows),
        "markets": market_rows,
        "warning": warning,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, sort_keys=True)
        file.write("\n")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
