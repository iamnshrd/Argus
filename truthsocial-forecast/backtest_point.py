#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import random
import statistics
import sys
from collections import Counter
from datetime import date, datetime, time, timedelta
from pathlib import Path

from regime import classify_regime, extreme_outlier_risk, regime_settings
from topic_mix import classify_row, load_topics
from truthsocial_forecast import (
    APP_DIR,
    ET,
    WEEK_SECONDS,
    fallback_bins,
    bin_probabilities,
    forecast_totals_from_posts,
    load_post_history,
    percentile,
    post_history_weeks,
)


DEFAULT_CALENDAR = APP_DIR / "data" / "election_calendar_2026.csv"
DEFAULT_TAXONOMY = APP_DIR / "topic_taxonomy.json"

WEEKDAYS = {
    "sunday": 0,
    "monday": 1,
    "tuesday": 2,
    "wednesday": 3,
    "thursday": 4,
    "friday": 5,
    "saturday": 6,
}


def row_offset(row) -> float:
    posted_at = row.post.posted_at.astimezone(ET)
    start_dt = datetime.combine(row.source_week_start, time.min, ET)
    return (posted_at - start_dt).total_seconds()


def latest_history_file() -> Path | None:
    files = sorted((APP_DIR / "data").glob("truthsocial_posts_*.jsonl"))
    return files[-1] if files else None


def parse_week(value: str, weeks: list[date]) -> date:
    ordered = sorted(weeks)
    if value == "first":
        return ordered[0]
    if value == "latest":
        return ordered[-1]
    parsed = date.fromisoformat(value)
    if parsed not in weeks:
        raise ValueError(f"week {parsed} not found in post history")
    return parsed


def cutoff_seconds(weekday: str, clock: str) -> int:
    day = WEEKDAYS[weekday.lower()]
    hour, minute = [int(part) for part in clock.split(":", 1)]
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise ValueError("--time must be HH:MM")
    return day * 24 * 60 * 60 + hour * 60 * 60 + minute * 60


def load_calendar(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
        return [
            {
                **row,
                "date": date.fromisoformat(row["date"]),
            }
            for row in csv.DictReader(file)
        ]


def future_events(calendar: list[dict], cutoff_dt: datetime, lookahead_days: int) -> list[dict]:
    start = cutoff_dt.date()
    end = start + timedelta(days=lookahead_days)
    return [event for event in calendar if start <= event["date"] <= end]


def largest_burst(rows: list, hours: int) -> int:
    times = sorted(row.post.posted_at.astimezone(ET) for row in rows)
    if not times:
        return 0
    best = 0
    left = 0
    window = timedelta(hours=hours)
    for right, current in enumerate(times):
        while current - times[left] > window:
            left += 1
        best = max(best, right - left + 1)
    return best


def week_features(week: date, week_rows: list, cutoff: int, topics: list, calendar: list[dict], lookahead_days: int) -> dict:
    so_far = [row for row in week_rows if row_offset(row) <= cutoff]
    remaining = [row for row in week_rows if row_offset(row) > cutoff]
    topic_counts = Counter(classify_row(row, topics) for row in so_far)
    remaining_topic_counts = Counter(classify_row(row, topics) for row in remaining)
    topic_total = len(so_far)
    cutoff_dt = datetime.combine(week, time.min, ET) + timedelta(seconds=cutoff)
    events = future_events(calendar, cutoff_dt, lookahead_days)
    event_types = Counter(event["type"] for event in events)
    return {
        "week": week,
        "so_far": so_far,
        "remaining": remaining,
        "observed": len(so_far),
        "actual": len(week_rows),
        "topic_counts": topic_counts,
        "distinct_topic_count": len(topic_counts),
        "remaining_topic_counts": remaining_topic_counts,
        "topic_shares": {topic: count / topic_total for topic, count in topic_counts.items()} if topic_total else {},
        "last24": sum(1 for row in so_far if cutoff - 24 * 60 * 60 < row_offset(row) <= cutoff),
        "burst1": largest_burst(so_far, 1),
        "burst6": largest_burst(so_far, 6),
        "future_events": events,
        "future_event_count": len(events),
        "future_special_count": sum(1 for event in events if event["type"].startswith("special")),
        "future_primary_count": sum(1 for event in events if "primary" in event["type"]),
        "future_runoff_count": sum(1 for event in events if "runoff" in event["type"]),
        "future_event_types": event_types,
    }


def l1_distance(left: dict, right: dict) -> float:
    keys = set(left) | set(right)
    return sum(abs(left.get(key, 0) - right.get(key, 0)) for key in keys)


def feature_weight(candidate: dict, target: dict) -> float:
    return (
        math.exp(-abs(candidate["observed"] - target["observed"]) / 18)
        * math.exp(-l1_distance(candidate["topic_shares"], target["topic_shares"]) / 0.85)
        * math.exp(-abs(candidate["burst6"] - target["burst6"]) / 8)
        * math.exp(-abs(candidate["last24"] - target["last24"]) / 12)
        * math.exp(-abs(candidate["future_event_count"] - target["future_event_count"]) / 3)
        * math.exp(-abs(candidate["future_primary_count"] - target["future_primary_count"]) / 2)
        * math.exp(-abs(candidate["future_special_count"] - target["future_special_count"]) / 1.5)
    )


def simulate_from_features(
    target: dict,
    training: list[dict],
    weights: list[float] | None,
    samples: int,
    noise_sigma: float,
    tail_overlay: bool,
) -> list[int]:
    totals = []
    remaining_counts = sorted(len(candidate["remaining"]) for candidate in training)
    regime, _ = classify_regime(target)
    settings = regime_settings(regime)
    high_remaining_cutoff = remaining_counts[round((len(remaining_counts) - 1) * settings["tail_quantile"])] if remaining_counts else 0
    tail_candidates = [candidate for candidate in training if len(candidate["remaining"]) >= high_remaining_cutoff]
    if tail_overlay:
        tail_probability = min(
            0.6,
            max(settings["tail_floor"], campaign_tail_probability(target) * settings["tail_multiplier"]),
        )
    else:
        tail_probability = 0.0
    for _ in range(samples):
        if tail_candidates and random.random() < tail_probability:
            candidate = random.choice(tail_candidates)
        else:
            candidate = random.choices(training, weights=weights, k=1)[0] if weights else random.choice(training)
        remaining = len(candidate["remaining"])
        adjusted_sigma = noise_sigma * settings["noise_multiplier"]
        if adjusted_sigma > 0 and remaining > 0:
            noise = random.lognormvariate(mu=-(adjusted_sigma**2) / 2, sigma=adjusted_sigma)
            remaining = max(0, int(round(remaining * noise)))
        total = target["observed"] + remaining
        if settings["max_total"] is not None:
            total = min(total, settings["max_total"])
        totals.append(total)
    return totals


def campaign_tail_probability(target: dict) -> float:
    pressure = (
        0.045 * target["future_primary_count"]
        + 0.06 * target["future_special_count"]
        + 0.02 * target["future_runoff_count"]
    )
    if target["observed"] < 45 and target["future_event_count"] >= 3:
        pressure += 0.08
    return min(0.4, pressure)


def rank_probability(values: list[int], actual: int) -> float:
    return sum(1 for value in values if value <= actual) / len(values)


def value_bin(value: int) -> str:
    for item in fallback_bins():
        if item.contains(value):
            return item.label
    return "unknown"


def main(argv: list[str] | None = None) -> int:
    default_history = latest_history_file()
    parser = argparse.ArgumentParser(description="Backtest one historical cut of a weekly Truth Social forecast.")
    parser.add_argument("--post-history", type=Path, default=default_history)
    parser.add_argument("--week", default="first", help="'first', 'latest', or YYYY-MM-DD source week start.")
    parser.add_argument("--weekday", default="wednesday", choices=sorted(WEEKDAYS))
    parser.add_argument("--time", default="12:00", help="ET cutoff time, HH:MM.")
    parser.add_argument("--samples", type=int, default=30000)
    parser.add_argument("--half-life-weeks", type=float, default=8.0)
    parser.add_argument("--post-noise-sigma", type=float, default=0.12)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument("--election-calendar", type=Path, default=DEFAULT_CALENDAR)
    parser.add_argument("--calendar-lookahead-days", type=int, default=14)
    parser.add_argument("--simple", action="store_true", help="Use the old unweighted post-history simulation.")
    parser.add_argument("--no-tail-overlay", action="store_true", help="Disable forward calendar tail-risk overlay.")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args(argv)

    if not args.post_history:
        print("error: no post history file found; run download_truths.py first", file=sys.stderr)
        return 1
    if args.samples < 1000:
        parser.error("--samples must be at least 1000")

    random.seed(args.seed)
    rows = load_post_history(args.post_history)
    weeks = post_history_weeks(rows)
    week_starts = [start for start, _ in weeks]
    topics = load_topics(args.taxonomy)
    calendar = load_calendar(args.election_calendar)

    try:
        target_week = parse_week(args.week, week_starts)
        cutoff = cutoff_seconds(args.weekday, args.time)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    rows_by_week = {}
    for row in rows:
        rows_by_week.setdefault(row.source_week_start, []).append(row)
    target = week_features(
        target_week,
        rows_by_week[target_week],
        cutoff,
        topics,
        calendar,
        args.calendar_lookahead_days,
    )
    training = [
        week_features(week, week_rows, cutoff, topics, calendar, args.calendar_lookahead_days)
        for week, week_rows in rows_by_week.items()
        if week != target_week
    ]
    observed = target["observed"]
    actual = target["actual"]

    if args.simple:
        training_rows = [row for row in rows if row.source_week_start != target_week]
        totals = forecast_totals_from_posts(
            posts=training_rows,
            observed_so_far=observed,
            phase_fraction=cutoff / WEEK_SECONDS,
            samples=args.samples,
            half_life_weeks=args.half_life_weeks,
            noise_sigma=args.post_noise_sigma,
        )
        model_name = "unweighted post-history"
        weights = None
    else:
        weights = [feature_weight(candidate, target) for candidate in training]
        totals = simulate_from_features(
            target,
            training,
            weights,
            args.samples,
            args.post_noise_sigma,
            tail_overlay=not args.no_tail_overlay,
        )
        model_name = "similarity-weighted live + calendar"

    cutoff_dt = datetime.combine(target_week, time.min, ET) + timedelta(seconds=cutoff)
    actual_probability_rank = rank_probability(totals, actual)
    actual_bin = value_bin(actual)
    bin_probs = dict((item.label, prob) for item, prob in bin_probabilities(totals, fallback_bins()))

    print("Truth Social point backtest")
    print(f"Post history: {args.post_history}")
    print(f"Target week: {target_week}..{target_week + timedelta(days=6)}")
    print(f"Cutoff: {cutoff_dt:%A %Y-%m-%d %H:%M %Z}")
    print("Training: all other source weeks (leave-one-week-out)")
    print(f"Model: {model_name}")
    print()
    print(f"Observed at cutoff: {observed}")
    print(f"Last 24h at cutoff: {target['last24']}")
    print(f"Largest 1h / 6h burst: {target['burst1']} / {target['burst6']}")
    regime, reasons = classify_regime(target)
    print(f"Regime: {regime} ({'; '.join(reasons)})")
    outlier_risk, outlier_reasons = extreme_outlier_risk(target)
    print(f"Extreme outlier risk: {outlier_risk} ({'; '.join(outlier_reasons) or 'no special signal'})")
    print(f"Future calendar events in {args.calendar_lookahead_days}d: {target['future_event_count']}")
    if not args.simple:
        tail_text = "disabled" if args.no_tail_overlay else f"{campaign_tail_probability(target) * 100:.1f}%"
        print(f"Calendar tail overlay probability: {tail_text}")
    for event in target["future_events"][:8]:
        print(f"  {event['date']} {event['type']}: {event['name']}")
    print("Topics at cutoff:")
    for topic, count in target["topic_counts"].most_common(8):
        pct = 100 * count / observed if observed else 0
        print(f"  {topic:<28} {pct:>5.1f}% n={count}")
    if weights:
        print("Nearest historical weeks:")
        for candidate, weight in sorted(zip(training, weights), key=lambda item: item[1], reverse=True)[:6]:
            print(
                f"  {candidate['week']} weight={weight:.3f} "
                f"observed={candidate['observed']} actual={candidate['actual']} "
                f"remaining={len(candidate['remaining'])} future_events={candidate['future_event_count']}"
            )
    print()
    print(f"Actual final count: {actual}")
    print(f"Actual bin: {actual_bin} ({bin_probs.get(actual_bin, 0) * 100:.1f}% forecast probability)")
    print(f"Actual percentile in forecast distribution: {actual_probability_rank * 100:.1f}%")
    print(f"Forecast mean: {statistics.mean(totals):.1f}")
    print(
        "Forecast total: "
        f"p10={percentile(totals, 0.10)}, "
        f"p25={percentile(totals, 0.25)}, "
        f"p50={percentile(totals, 0.50)}, "
        f"p75={percentile(totals, 0.75)}, "
        f"p90={percentile(totals, 0.90)}"
    )
    print()
    print("Bins")
    for item, probability in bin_probabilities(totals, fallback_bins()):
        marker = " <- actual" if item.label == actual_bin else ""
        print(f"{item.label:>10}: {probability:>6.1%}{marker}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
