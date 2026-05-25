#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from regime import classify_regime, extreme_outlier_risk
from rollcall_client import RollCallClient, RollCallError
from topic_mix import classify_row, load_topics
from truthsocial_forecast import APP_DIR, ET, WEEK_SECONDS, PostHistoryRow, current_week, load_post_history


DEFAULT_HISTORY = APP_DIR / "data" / "truthsocial_posts_2026-01-04_2026-05-23.jsonl"
DEFAULT_CALENDAR = APP_DIR / "data" / "election_calendar_2026.csv"


def parse_now(value: str | None) -> datetime:
    if not value:
        return datetime.now(ET)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=ET)
    return parsed.astimezone(ET)


def week_elapsed_seconds(now_et: datetime, week_start) -> float:
    start_dt = datetime.combine(week_start, time.min, ET)
    return max(0.0, min(WEEK_SECONDS, (now_et - start_dt).total_seconds()))


def topic_counts(rows: list[PostHistoryRow], taxonomy: Path) -> Counter:
    topics = load_topics(taxonomy)
    counts = Counter()
    for row in rows:
        counts[classify_row(row, topics)] += 1
    return counts


def load_calendar(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
        return [{**row, "date": date.fromisoformat(row["date"])} for row in csv.DictReader(file)]


def future_events(calendar: list[dict], now_et: datetime, lookahead_days: int) -> list[dict]:
    end = now_et.date() + timedelta(days=lookahead_days)
    return [event for event in calendar if now_et.date() <= event["date"] <= end]


def campaign_tail_probability(events: list[dict], observed: int) -> float:
    primary_count = sum(1 for event in events if "primary" in event["type"])
    special_count = sum(1 for event in events if event["type"].startswith("special"))
    runoff_count = sum(1 for event in events if "runoff" in event["type"])
    pressure = 0.045 * primary_count + 0.06 * special_count + 0.02 * runoff_count
    if observed < 45 and len(events) >= 3:
        pressure += 0.08
    return min(0.4, pressure)


def rows_before_cutoff(rows: list[PostHistoryRow], cutoff_seconds: float) -> list[PostHistoryRow]:
    selected = []
    for row in rows:
        posted_at = row.post.posted_at.astimezone(ET)
        start_dt = datetime.combine(row.source_week_start, time.min, ET)
        if (posted_at - start_dt).total_seconds() <= cutoff_seconds:
            selected.append(row)
    return selected


def historical_so_far(history: list[PostHistoryRow], cutoff_seconds: float) -> list[tuple]:
    by_week = {}
    for row in history:
        by_week.setdefault(row.source_week_start, []).append(row)
    rows = []
    for week, week_rows in sorted(by_week.items()):
        so_far = rows_before_cutoff(week_rows, cutoff_seconds)
        rows.append((week, len(so_far), len(week_rows), topic_counts(so_far, APP_DIR / "topic_taxonomy.json")))
    return rows


def largest_burst(rows: list[PostHistoryRow], hours: int) -> int:
    times = sorted(row.post.posted_at.astimezone(ET) for row in rows)
    best = 0
    left = 0
    window = timedelta(hours=hours)
    for right, current in enumerate(times):
        while current - times[left] > window:
            left += 1
        best = max(best, right - left + 1)
    return best


def print_topics(counts: Counter, total: int, limit: int) -> None:
    for topic, count in counts.most_common(limit):
        pct = 100 * count / total if total else 0
        print(f"  {topic:<28} {pct:>5.1f}%  n={count}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize live Truth Social weekly features.")
    parser.add_argument("--now", help="Current ET timestamp, e.g. 2026-05-24T10:00:00")
    parser.add_argument("--post-history", type=Path, default=DEFAULT_HISTORY)
    parser.add_argument("--taxonomy", type=Path, default=APP_DIR / "topic_taxonomy.json")
    parser.add_argument("--election-calendar", type=Path, default=DEFAULT_CALENDAR)
    parser.add_argument("--calendar-lookahead-days", type=int, default=14)
    parser.add_argument("--top", type=int, default=8)
    args = parser.parse_args()

    now_et = parse_now(args.now)
    week_start, week_end = current_week(now_et)
    cutoff_seconds = week_elapsed_seconds(now_et, week_start)

    try:
        current_posts = RollCallClient().truth_social_posts(week_start, now_et.date())
    except RollCallError as exc:
        parser.exit(1, f"error: {exc}\n")

    current_rows = [
        PostHistoryRow(post=post, source_week_start=week_start)
        for post in current_posts
        if post.posted_at.astimezone(ET) <= now_et
    ]
    history = load_post_history(args.post_history)
    history_points = historical_so_far(history, cutoff_seconds)
    so_far_counts = [count for _, count, _, _ in history_points]
    current_topics = topic_counts(current_rows, args.taxonomy)
    events = future_events(load_calendar(args.election_calendar), now_et, args.calendar_lookahead_days)
    total = len(current_rows)
    feature_snapshot = {
        "observed": total,
        "last24": sum(1 for row in current_rows if now_et - row.post.posted_at.astimezone(ET) <= timedelta(hours=24)),
        "burst6": largest_burst(current_rows, 6),
        "topic_shares": {topic: count / total for topic, count in current_topics.items()} if total else {},
        "distinct_topic_count": len(current_topics),
        "future_event_count": len(events),
        "future_primary_count": sum(1 for event in events if "primary" in event["type"]),
        "future_special_count": sum(1 for event in events if event["type"].startswith("special")),
    }
    regime, reasons = classify_regime(feature_snapshot)
    outlier_risk, outlier_reasons = extreme_outlier_risk(feature_snapshot)

    print("Truth Social live features")
    print(f"Now ET: {now_et:%Y-%m-%d %H:%M:%S %Z}")
    print(f"Week: {week_start}..{week_end}")
    print(f"Posts so far: {len(current_rows)}")
    if so_far_counts:
        rank = sum(1 for count in so_far_counts if count <= len(current_rows)) / len(so_far_counts)
        print(f"Historical so-far range: min={min(so_far_counts)}, median={sorted(so_far_counts)[len(so_far_counts)//2]}, max={max(so_far_counts)}")
        print(f"So-far percentile vs history: {rank * 100:.1f}%")
    print(f"Posts last 6h: {sum(1 for row in current_rows if now_et - row.post.posted_at.astimezone(ET) <= timedelta(hours=6))}")
    print(f"Posts last 24h: {sum(1 for row in current_rows if now_et - row.post.posted_at.astimezone(ET) <= timedelta(hours=24))}")
    print(f"Largest 1h burst: {largest_burst(current_rows, 1)}")
    print(f"Largest 6h burst: {largest_burst(current_rows, 6)}")
    print(f"Regime: {regime} ({'; '.join(reasons)})")
    print(f"Extreme outlier risk: {outlier_risk} ({'; '.join(outlier_reasons) or 'no special signal'})")
    print(f"Future calendar events in {args.calendar_lookahead_days}d: {len(events)}")
    print(f"Calendar tail overlay probability: {campaign_tail_probability(events, len(current_rows)) * 100:.1f}%")
    for event in events[:8]:
        print(f"  {event['date']} {event['type']}: {event['name']}")
    print()
    print("Topics so far")
    print_topics(current_topics, len(current_rows), args.top)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
