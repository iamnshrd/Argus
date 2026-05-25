#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from rollcall_client import RollCallClient, RollCallError
from truthsocial_forecast import current_week


ET = ZoneInfo("America/New_York")
APP_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = APP_DIR / "data"


def parse_now(value: str | None) -> datetime:
    if not value:
        return datetime.now(ET)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=ET)
    return parsed.astimezone(ET)


def default_range(now_et: datetime, weeks: int) -> tuple:
    week_start, _ = current_week(now_et)
    end = week_start - timedelta(days=1)
    start = week_start - timedelta(days=7 * weeks)
    return start, end


def week_ranges(start: date, end: date) -> list[tuple[date, date]]:
    ranges = []
    cursor = start
    while cursor <= end:
        week_end = min(cursor + timedelta(days=6), end)
        ranges.append((cursor, week_end))
        cursor += timedelta(days=7)
    return ranges


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download Roll Call Truth Social posts to JSONL.")
    parser.add_argument("--now", help="Current ET timestamp, e.g. 2026-05-24T10:00:00")
    parser.add_argument("--weeks", type=int, default=13, help="Completed weeks to download before current week.")
    parser.add_argument("--start", type=lambda value: date.fromisoformat(value), help="Explicit start date, YYYY-MM-DD.")
    parser.add_argument("--end", type=lambda value: date.fromisoformat(value), help="Explicit end date, YYYY-MM-DD.")
    parser.add_argument("--output", type=Path, help="Output JSONL path.")
    args = parser.parse_args(argv)

    if args.weeks < 1:
        parser.error("--weeks must be at least 1")

    now_et = parse_now(args.now)
    if args.start or args.end:
        if not args.start or not args.end:
            parser.error("--start and --end must be provided together")
        start, end = args.start, args.end
        if start > end:
            parser.error("--start must be before --end")
    else:
        start, end = default_range(now_et, args.weeks)
    output = args.output or DEFAULT_DATA_DIR / f"truthsocial_posts_{start}_{end}.jsonl"

    client = RollCallClient()
    weeks = week_ranges(start, end)

    try:
        rows = []
        for week_start, week_end in weeks:
            for post in client.truth_social_posts(week_start, week_end):
                row = post.to_json()
                row["source_week_start"] = week_start.isoformat()
                row["source_week_end"] = week_end.isoformat()
                rows.append(row)
    except RollCallError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            file.write("\n")

    print(f"Downloaded {len(rows)} source-week rows")
    print(f"Range: {start}..{end} ET")
    print(f"Output: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
