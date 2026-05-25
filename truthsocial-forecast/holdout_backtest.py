#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
from datetime import datetime, time, timedelta
from pathlib import Path

from backtest_point import (
    DEFAULT_CALENDAR,
    DEFAULT_TAXONOMY,
    bin_probabilities,
    feature_weight,
    load_calendar,
    percentile,
    simulate_from_features,
    value_bin,
    week_features,
)
from grid_backtest import actual_bin_probability, cutoff_seconds, rank_probability
from remaining_model import late_remaining_totals
from regime import classify_regime, extreme_outlier_risk
from topic_mix import load_topics
from truthsocial_forecast import APP_DIR, ET, fallback_bins, load_post_history, post_history_weeks


DEFAULT_TRAIN_HISTORY = APP_DIR / "data" / "truthsocial_posts_2026-01-04_2026-05-23.jsonl"
DEFAULT_TEST_HISTORY = APP_DIR / "data" / "sample" / "truthsocial_posts_2025-09-01_2025-10-31.jsonl"
DEFAULT_OUTPUT = APP_DIR / "data" / "sample" / "holdout_backtest_2025-09-01_2025-10-31_vs_2026.csv"
DEFAULT_CLOCKS = ("09:00", "12:00", "15:00", "18:00")


def source_week_ends(path: Path) -> dict:
    ends = {}
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            item = json.loads(line)
            start = item.get("source_week_start")
            end = item.get("source_week_end")
            if start and end:
                ends[start] = end
    return ends


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build_row(week, cutoff, target, totals, regime, reasons, remaining_regime=None) -> dict:
    actual = target["actual"]
    cutoff_dt = datetime.combine(week, time.min, ET) + timedelta(seconds=cutoff)
    p10 = percentile(totals, 0.10)
    p50 = percentile(totals, 0.50)
    p90 = percentile(totals, 0.90)
    outlier_risk, outlier_reasons = extreme_outlier_risk(target)
    return {
        "week": week.isoformat(),
        "cutoff": cutoff_dt.isoformat(),
        "source_day": int(cutoff // (24 * 60 * 60)) + 1,
        "observed": target["observed"],
        "last24": target["last24"],
        "burst6": target["burst6"],
        "future_events": target["future_event_count"],
        "regime": regime,
        "regime_reasons": "; ".join(reasons),
        "remaining_regime": remaining_regime.name if remaining_regime else "",
        "remaining_regime_reasons": "; ".join(remaining_regime.reasons) if remaining_regime else "",
        "extreme_outlier_risk": outlier_risk,
        "extreme_outlier_reasons": "; ".join(outlier_reasons),
        "actual": actual,
        "p10": p10,
        "p50": p50,
        "p90": p90,
        "mean": round(statistics.mean(totals), 2),
        "abs_error_p50": abs(p50 - actual),
        "covered_p10_p90": p10 <= actual <= p90,
        "actual_percentile": round(rank_probability(totals, actual), 4),
        "actual_bin": value_bin(actual),
        "actual_bin_probability": round(actual_bin_probability(totals, actual), 4),
    }


def parse_days(value: str) -> list[int]:
    days = [int(part.strip()) for part in value.split(",") if part.strip()]
    invalid = [day for day in days if day < 1 or day > 7]
    if invalid:
        raise argparse.ArgumentTypeError("--days must contain numbers from 1 to 7")
    return days


def parse_clocks(value: str) -> list[str]:
    clocks = [part.strip() for part in value.split(",") if part.strip()]
    for clock in clocks:
        hour, minute = [int(part) for part in clock.split(":", 1)]
        if not 0 <= hour <= 23 or not 0 <= minute <= 59:
            raise argparse.ArgumentTypeError("--clocks must contain HH:MM values")
    return clocks


def summarize(rows: list[dict], skipped: list[str]) -> None:
    print(f"cuts: {len(rows)}")
    if skipped:
        print(f"skipped incomplete source windows: {', '.join(skipped)}")
    print(f"median abs error p50: {statistics.median(row['abs_error_p50'] for row in rows):.1f}")
    print(f"mean abs error p50: {statistics.mean(row['abs_error_p50'] for row in rows):.1f}")
    print(f"p10-p90 coverage: {sum(row['covered_p10_p90'] for row in rows)}/{len(rows)}")
    print(f"mean actual-bin probability: {statistics.mean(row['actual_bin_probability'] for row in rows) * 100:.1f}%")
    print()
    print("By source day")
    for day in sorted({row["source_day"] for row in rows}):
        group = [row for row in rows if row["source_day"] == day]
        print(
            f"day {day}: n={len(group)}, "
            f"median_abs_error={statistics.median(row['abs_error_p50'] for row in group):.1f}, "
            f"mean_abs_error={statistics.mean(row['abs_error_p50'] for row in group):.1f}, "
            f"coverage={sum(row['covered_p10_p90'] for row in group)}/{len(group)}, "
            f"mean_bin_p={statistics.mean(row['actual_bin_probability'] for row in group) * 100:.1f}%"
        )
    print()
    if any(row["remaining_regime"] for row in rows):
        print("By remaining regime")
        for regime in sorted({row["remaining_regime"] for row in rows if row["remaining_regime"]}):
            group = [row for row in rows if row["remaining_regime"] == regime]
            print(
                f"{regime}: n={len(group)}, "
                f"median_abs_error={statistics.median(row['abs_error_p50'] for row in group):.1f}, "
                f"mean_abs_error={statistics.mean(row['abs_error_p50'] for row in group):.1f}, "
                f"coverage={sum(row['covered_p10_p90'] for row in group)}/{len(group)}, "
                f"mean_bin_p={statistics.mean(row['actual_bin_probability'] for row in group) * 100:.1f}%"
            )
        print()
    print("By regime")
    for regime in sorted({row["regime"] for row in rows}):
        group = [row for row in rows if row["regime"] == regime]
        print(
            f"{regime}: n={len(group)}, "
            f"median_abs_error={statistics.median(row['abs_error_p50'] for row in group):.1f}, "
            f"mean_abs_error={statistics.mean(row['abs_error_p50'] for row in group):.1f}, "
            f"coverage={sum(row['covered_p10_p90'] for row in group)}/{len(group)}, "
            f"mean_bin_p={statistics.mean(row['actual_bin_probability'] for row in group) * 100:.1f}%"
        )
    print()
    print("By extreme outlier risk")
    for risk in ("normal", "elevated", "high"):
        group = [row for row in rows if row["extreme_outlier_risk"] == risk]
        if not group:
            continue
        print(
            f"{risk}: n={len(group)}, "
            f"median_abs_error={statistics.median(row['abs_error_p50'] for row in group):.1f}, "
            f"mean_abs_error={statistics.mean(row['abs_error_p50'] for row in group):.1f}, "
            f"coverage={sum(row['covered_p10_p90'] for row in group)}/{len(group)}, "
            f"mean_bin_p={statistics.mean(row['actual_bin_probability'] for row in group) * 100:.1f}%"
        )
    print()
    print("Worst misses")
    for row in sorted(rows, key=lambda item: item["abs_error_p50"], reverse=True)[:8]:
        print(
            f"{row['week']} day={row['source_day']} obs={row['observed']} "
            f"actual={row['actual']} p50={row['p50']} p90={row['p90']} "
            f"err={row['abs_error_p50']} regime={row['regime']} outlier={row['extreme_outlier_risk']}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 2026-trained model on a separate holdout post-history file.")
    parser.add_argument("--train-history", type=Path, default=DEFAULT_TRAIN_HISTORY)
    parser.add_argument("--test-history", type=Path, default=DEFAULT_TEST_HISTORY)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument("--election-calendar", type=Path, default=DEFAULT_CALENDAR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--samples", type=int, default=12000)
    parser.add_argument("--seed", type=int, default=29)
    parser.add_argument("--post-noise-sigma", type=float, default=0.12)
    parser.add_argument("--calendar-lookahead-days", type=int, default=14)
    parser.add_argument("--days", type=parse_days, default=parse_days("2,3,4,5"))
    parser.add_argument("--clocks", type=parse_clocks, default=list(DEFAULT_CLOCKS))
    parser.add_argument("--no-remaining-model", action="store_true")
    parser.add_argument("--include-incomplete", action="store_true")
    args = parser.parse_args()

    random.seed(args.seed)
    train_rows = load_post_history(args.train_history)
    test_rows = load_post_history(args.test_history)
    topics = load_topics(args.taxonomy)
    calendar = load_calendar(args.election_calendar)

    train_by_week = {}
    for row in train_rows:
        train_by_week.setdefault(row.source_week_start, []).append(row)
    test_by_week = {}
    for row in test_rows:
        test_by_week.setdefault(row.source_week_start, []).append(row)

    train_weeks = [week for week, _ in post_history_weeks(train_rows)]
    test_weeks = [week for week, _ in post_history_weeks(test_rows)]
    ends = source_week_ends(args.test_history)
    skipped = []
    if not args.include_incomplete:
        complete_weeks = []
        for week in test_weeks:
            end = ends.get(week.isoformat())
            if end == (week + timedelta(days=6)).isoformat():
                complete_weeks.append(week)
            else:
                skipped.append(week.isoformat())
        test_weeks = complete_weeks

    cutoffs = [cutoff_seconds(day, clock) for day in args.days for clock in args.clocks]
    train_feature_cache = {
        (week, cutoff): week_features(week, train_by_week[week], cutoff, topics, calendar, args.calendar_lookahead_days)
        for cutoff in cutoffs
        for week in train_weeks
    }

    rows = []
    for week in test_weeks:
        for cutoff in cutoffs:
            target = week_features(week, test_by_week[week], cutoff, topics, calendar, args.calendar_lookahead_days)
            training = [train_feature_cache[(train_week, cutoff)] for train_week in train_weeks]
            weights = [feature_weight(candidate, target) for candidate in training]
            totals = simulate_from_features(target, training, weights, args.samples, args.post_noise_sigma, tail_overlay=True)
            remaining_regime = None
            if not args.no_remaining_model:
                remaining_result = late_remaining_totals(target, training, cutoff)
                if remaining_result:
                    totals, remaining_regime = remaining_result
            regime, reasons = classify_regime(target)
            rows.append(build_row(week, cutoff, target, totals, regime, reasons, remaining_regime))

    if not rows:
        parser.error("no test rows after filtering incomplete source windows")

    write_csv(args.output, rows)
    print("Truth Social holdout backtest")
    print(f"Train history: {args.train_history}")
    print(f"Test history: {args.test_history}")
    print(f"Output: {args.output}")
    print("Training policy: fixed train-history only; no leave-one-out from test file")
    summarize(rows, skipped)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
