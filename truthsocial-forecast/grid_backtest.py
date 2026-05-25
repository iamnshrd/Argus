#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
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
from regime import classify_regime, extreme_outlier_risk
from topic_mix import load_topics
from truthsocial_forecast import APP_DIR, ET, fallback_bins, load_post_history, post_history_weeks


DEFAULT_HISTORY = APP_DIR / "data" / "truthsocial_posts_2026-01-04_2026-05-23.jsonl"
DEFAULT_OUTPUT = APP_DIR / "data" / "grid_backtest_2026-01-04_2026-05-23.csv"


def cutoff_seconds(day_number: int, clock: str) -> int:
    hour, minute = [int(part) for part in clock.split(":", 1)]
    return (day_number - 1) * 24 * 60 * 60 + hour * 60 * 60 + minute * 60


def rank_probability(values: list[int], actual: int) -> float:
    return sum(1 for value in values if value <= actual) / len(values)


def actual_bin_probability(totals: list[int], actual: int) -> float:
    actual_bin = value_bin(actual)
    probs = dict((item.label, prob) for item, prob in bin_probabilities(totals, fallback_bins()))
    return probs.get(actual_bin, 0.0)


def build_row(week, cutoff, target, totals, regime, reasons) -> dict:
    actual = target["actual"]
    cutoff_dt = datetime.combine(week, time.min, ET) + timedelta(seconds=cutoff)
    p10 = percentile(totals, 0.10)
    p50 = percentile(totals, 0.50)
    p90 = percentile(totals, 0.90)
    outlier_risk, outlier_reasons = extreme_outlier_risk(target)
    return {
        "week": week.isoformat(),
        "cutoff": cutoff_dt.isoformat(),
        "observed": target["observed"],
        "last24": target["last24"],
        "burst6": target["burst6"],
        "future_events": target["future_event_count"],
        "regime": regime,
        "regime_reasons": "; ".join(reasons),
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


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict]) -> None:
    print(f"cuts: {len(rows)}")
    print(f"median abs error p50: {statistics.median(row['abs_error_p50'] for row in rows):.1f}")
    print(f"mean abs error p50: {statistics.mean(row['abs_error_p50'] for row in rows):.1f}")
    print(f"p10-p90 coverage: {sum(row['covered_p10_p90'] for row in rows)}/{len(rows)}")
    print(f"mean actual-bin probability: {statistics.mean(row['actual_bin_probability'] for row in rows) * 100:.1f}%")
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Run grid backtest across all weeks and cutoff points.")
    parser.add_argument("--post-history", type=Path, default=DEFAULT_HISTORY)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument("--election-calendar", type=Path, default=DEFAULT_CALENDAR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--samples", type=int, default=12000)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--post-noise-sigma", type=float, default=0.12)
    parser.add_argument("--calendar-lookahead-days", type=int, default=14)
    args = parser.parse_args()

    random.seed(args.seed)
    history = load_post_history(args.post_history)
    topics = load_topics(args.taxonomy)
    calendar = load_calendar(args.election_calendar)
    rows_by_week = {}
    for row in history:
        rows_by_week.setdefault(row.source_week_start, []).append(row)

    weeks = [week for week, _ in post_history_weeks(history)]
    cutoffs = [cutoff_seconds(day, clock) for day in (2, 3, 4, 5) for clock in ("09:00", "12:00", "15:00", "18:00")]
    feature_cache = {
        (week, cutoff): week_features(week, rows_by_week[week], cutoff, topics, calendar, args.calendar_lookahead_days)
        for cutoff in cutoffs
        for week in weeks
    }

    rows = []
    for week in weeks:
        for cutoff in cutoffs:
            target = feature_cache[(week, cutoff)]
            training = [
                feature_cache[(other_week, cutoff)]
                for other_week in weeks
                if other_week != week
            ]
            weights = [feature_weight(candidate, target) for candidate in training]
            totals = simulate_from_features(target, training, weights, args.samples, args.post_noise_sigma, tail_overlay=True)
            regime, reasons = classify_regime(target)
            rows.append(build_row(week, cutoff, target, totals, regime, reasons))

    write_csv(args.output, rows)
    print("Truth Social grid backtest")
    print(f"Post history: {args.post_history}")
    print(f"Output: {args.output}")
    summarize(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
