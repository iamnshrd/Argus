#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import statistics
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from truthsocial_forecast import APP_DIR, load_post_history, post_history_weeks


ENDORSEMENT_RE = re.compile(
    r"\b("
    r"endorse|endorsed|endorsement|"
    r"complete and total|total endorsement|strong endorsement|"
    r"vote for|has my complete"
    r")\b",
    re.IGNORECASE,
)

ELECTION_RE = re.compile(
    r"\b("
    r"election|primary|runoff|vote|voting|ballot|candidate|"
    r"congress|senate|governor|mayor|district|nominee|"
    r"republican primary|maga"
    r")\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class WeekFeature:
    week_start: date
    total: int
    endorsement_posts: int
    election_posts: int
    is_election_week: bool


def latest_history_file() -> Path | None:
    files = sorted((APP_DIR / "data").glob("truthsocial_posts_*.jsonl"))
    return files[-1] if files else None


def sunday_for(day: date) -> date:
    return day - timedelta(days=(day.weekday() + 1) % 7)


def calendar_weeks(path: Path) -> set[date]:
    weeks = set()
    with path.open("r", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            weeks.add(sunday_for(date.fromisoformat(row["date"])))
    return weeks


def correlation(xs: list[int], ys: list[int]) -> float:
    if len(xs) < 2 or len(ys) < 2:
        return float("nan")
    mean_x = statistics.mean(xs)
    mean_y = statistics.mean(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denom_x = sum((x - mean_x) ** 2 for x in xs) ** 0.5
    denom_y = sum((y - mean_y) ** 2 for y in ys) ** 0.5
    if not denom_x or not denom_y:
        return float("nan")
    return numerator / (denom_x * denom_y)


def mean(values: list[int]) -> float:
    return statistics.mean(values) if values else float("nan")


def build_features(post_history: Path, election_weeks: set[date]) -> list[WeekFeature]:
    rows = load_post_history(post_history)
    totals = {week: len(offsets) for week, offsets in post_history_weeks(rows)}
    endorsement_counts = {week: 0 for week in totals}
    election_counts = {week: 0 for week in totals}

    for row in rows:
        text = row.post.text
        if ENDORSEMENT_RE.search(text):
            endorsement_counts[row.source_week_start] = endorsement_counts.get(row.source_week_start, 0) + 1
        if ELECTION_RE.search(text):
            election_counts[row.source_week_start] = election_counts.get(row.source_week_start, 0) + 1

    return [
        WeekFeature(
            week_start=week,
            total=totals[week],
            endorsement_posts=endorsement_counts.get(week, 0),
            election_posts=election_counts.get(week, 0),
            is_election_week=week in election_weeks,
        )
        for week in sorted(totals)
    ]


def print_group(label: str, rows: list[WeekFeature]) -> None:
    totals = [row.total for row in rows]
    print(f"{label}: n={len(rows)}, mean_total={mean(totals):.1f}, totals={totals}")


def main() -> int:
    default_history = latest_history_file()
    default_calendar = APP_DIR / "data" / "election_calendar_2026.csv"
    parser = argparse.ArgumentParser(description="Test endorsement/election-week count hypotheses.")
    parser.add_argument("--post-history", type=Path, default=default_history)
    parser.add_argument("--election-calendar", type=Path, default=default_calendar)
    parser.add_argument(
        "--election-week",
        action="append",
        default=[],
        help="Sunday source-week start to tag as an actual election week, YYYY-MM-DD.",
    )
    args = parser.parse_args()

    if not args.post_history:
        parser.error("no post history file found; run download_truths.py first")

    election_weeks = set()
    if args.election_calendar and args.election_calendar.exists():
        election_weeks |= calendar_weeks(args.election_calendar)
    election_weeks |= {date.fromisoformat(value) for value in args.election_week}
    rows = build_features(args.post_history, election_weeks)
    totals = [row.total for row in rows]
    endorsements = [row.endorsement_posts for row in rows]
    elections = [row.election_posts for row in rows]

    print("Truth Social endorsement/election hypothesis check")
    print(f"Post history: {args.post_history}")
    print()
    print("Weekly features")
    print(f"{'week':>10} {'total':>5} {'endorse':>8} {'election_terms':>14} {'actual_election':>16}")
    for row in rows:
        marker = "yes" if row.is_election_week else ""
        print(
            f"{row.week_start} "
            f"{row.total:>5} "
            f"{row.endorsement_posts:>8} "
            f"{row.election_posts:>14} "
            f"{marker:>16}"
        )

    print()
    print(f"corr(total, endorsement_posts): {correlation(totals, endorsements):.2f}")
    print(f"corr(total, election_term_posts): {correlation(totals, elections):.2f}")
    print()
    for threshold in (5, 10, 20, 30):
        print_group(
            f"endorsement_posts >= {threshold}",
            [row for row in rows if row.endorsement_posts >= threshold],
        )
        print_group(
            f"endorsement_posts <  {threshold}",
            [row for row in rows if row.endorsement_posts < threshold],
        )
        print()

    if election_weeks:
        print_group("actual election weeks", [row for row in rows if row.is_election_week])
        print_group("non-election weeks", [row for row in rows if not row.is_election_week])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
