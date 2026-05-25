#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from truthsocial_forecast import APP_DIR, PostHistoryRow, load_post_history, post_history_weeks


@dataclass(frozen=True)
class Topic:
    label: str
    patterns: tuple[re.Pattern, ...]


def latest_history_file() -> Path | None:
    files = sorted((APP_DIR / "data").glob("truthsocial_posts_*.jsonl"))
    return files[-1] if files else None


def load_topics(path: Path) -> list[Topic]:
    with path.open("r", encoding="utf-8") as file:
        rows = json.load(file)
    topics = []
    for row in rows:
        topics.append(
            Topic(
                label=row["label"],
                patterns=tuple(keyword_pattern(keyword) for keyword in row["keywords"]),
            )
        )
    return topics


def keyword_pattern(keyword: str) -> re.Pattern:
    escaped = re.escape(keyword)
    return re.compile(rf"(?<!\w){escaped}(?!\w)", re.IGNORECASE)


def classify_row(row: PostHistoryRow, topics: list[Topic]) -> str:
    text = row.post.text.strip()
    if row.post.repost or text.startswith("RT:"):
        return "reposts"
    if row.post.quote:
        return "quote_truths"
    if text == "[Image]":
        return "image_only"
    if text == "[Video]":
        return "video_only"
    if row.post.media_type and row.post.media_type.lower() not in {"text", ""}:
        return f"media_{row.post.media_type.lower()}"
    return classify_text(text, topics)


def classify_text(text: str, topics: list[Topic]) -> str:
    best_label = "other"
    best_score = 0
    for topic in topics:
        score = sum(len(pattern.findall(text)) for pattern in topic.patterns)
        if score > best_score:
            best_label = topic.label
            best_score = score
    return best_label


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


def topic_mix(post_history: Path, taxonomy: Path) -> dict[date, Counter]:
    topics = load_topics(taxonomy)
    rows = load_post_history(post_history)
    valid_weeks = {week for week, _ in post_history_weeks(rows)}
    counts: dict[date, Counter] = defaultdict(Counter)
    for row in rows:
        if row.source_week_start not in valid_weeks:
            continue
        counts[row.source_week_start][classify_row(row, topics)] += 1
    return dict(counts)


def print_week(week: date, counts: Counter, top: int, min_percent: float) -> None:
    total = counts.total()
    print(f"{week} total={total}")
    shown = 0
    for topic, count in counts.most_common():
        percent = 100 * count / total if total else 0
        if percent < min_percent:
            continue
        print(f"  {topic:<28} {percent:>5.1f}%  n={count}")
        shown += 1
        if shown >= top:
            break


def export_csv(path: Path, mixes: dict[date, Counter], topics: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["week_start", "total"]
    for topic in topics:
        fields.extend([f"{topic}_count", f"{topic}_pct"])

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for week in sorted(mixes):
            counts = mixes[week]
            total = counts.total()
            row = {"week_start": week.isoformat(), "total": total}
            for topic in topics:
                count = counts.get(topic, 0)
                row[f"{topic}_count"] = count
                row[f"{topic}_pct"] = round(100 * count / total, 2) if total else 0
            writer.writerow(row)


def export_json(path: Path, mixes: dict[date, Counter], topics: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for week in sorted(mixes):
        counts = mixes[week]
        total = counts.total()
        rows.append(
            {
                "week_start": week.isoformat(),
                "total": total,
                "topics": {
                    topic: {
                        "count": counts.get(topic, 0),
                        "pct": round(100 * counts.get(topic, 0) / total, 2) if total else 0,
                    }
                    for topic in topics
                },
            }
        )
    with path.open("w", encoding="utf-8") as file:
        json.dump(rows, file, indent=2, ensure_ascii=False)
        file.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute weekly Truth Social topic mix from post history.")
    parser.add_argument("--post-history", type=Path, default=latest_history_file())
    parser.add_argument("--taxonomy", type=Path, default=APP_DIR / "topic_taxonomy.json")
    parser.add_argument("--week", help="'first', 'latest', YYYY-MM-DD, or omitted for all weeks.")
    parser.add_argument("--top", type=int, default=6)
    parser.add_argument("--min-percent", type=float, default=3.0)
    parser.add_argument("--export-csv", type=Path)
    parser.add_argument("--export-json", type=Path)
    args = parser.parse_args()

    if not args.post_history:
        parser.error("no post history file found; run download_truths.py first")
    if args.top < 1:
        parser.error("--top must be at least 1")

    taxonomy = load_topics(args.taxonomy)
    topics = [
        "reposts",
        "quote_truths",
        "image_only",
        "video_only",
    ] + [topic.label for topic in taxonomy] + ["other"]
    mixes = topic_mix(args.post_history, args.taxonomy)
    weeks = sorted(mixes)
    if args.week:
        weeks = [parse_week(args.week, weeks)]

    if args.export_csv:
        export_csv(args.export_csv, mixes, topics)
    if args.export_json:
        export_json(args.export_json, mixes, topics)

    print("Truth Social weekly topic mix")
    print(f"Post history: {args.post_history}")
    print(f"Taxonomy: {args.taxonomy}")
    print()
    for week in weeks:
        print_week(week, mixes[week], args.top, args.min_percent)
    if args.export_csv:
        print(f"\nCSV saved: {args.export_csv}")
    if args.export_json:
        print(f"JSON saved: {args.export_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
