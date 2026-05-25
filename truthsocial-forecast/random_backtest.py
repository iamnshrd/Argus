#!/usr/bin/env python3
from __future__ import annotations

import argparse
import random
import statistics
from datetime import datetime, time, timedelta
from pathlib import Path

from backtest_point import (
    DEFAULT_CALENDAR,
    DEFAULT_TAXONOMY,
    bin_probabilities,
    campaign_tail_probability,
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
DAY_CHOICES = {
    2: "Monday",
    3: "Tuesday",
    4: "Wednesday",
    5: "Thursday",
}


def cutoff_seconds(day_number: int, clock: str) -> int:
    hour, minute = [int(part) for part in clock.split(":", 1)]
    return (day_number - 1) * 24 * 60 * 60 + hour * 60 * 60 + minute * 60


def actual_bin_probability(totals: list[int], actual: int) -> float:
    actual_bin = value_bin(actual)
    return dict((item.label, prob) for item, prob in bin_probabilities(totals, fallback_bins())).get(actual_bin, 0.0)


def rank_probability(values: list[int], actual: int) -> float:
    return sum(1 for value in values if value <= actual) / len(values)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run random point backtests across historical weeks.")
    parser.add_argument("--post-history", type=Path, default=DEFAULT_HISTORY)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument("--election-calendar", type=Path, default=DEFAULT_CALENDAR)
    parser.add_argument("--samples", type=int, default=30000)
    parser.add_argument("--n", type=int, default=10)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--post-noise-sigma", type=float, default=0.12)
    parser.add_argument("--calendar-lookahead-days", type=int, default=14)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    random.seed(args.seed)
    rows = load_post_history(args.post_history)
    topics = load_topics(args.taxonomy)
    calendar = load_calendar(args.election_calendar)
    rows_by_week = {}
    for row in rows:
        rows_by_week.setdefault(row.source_week_start, []).append(row)

    weeks = [week for week, _ in post_history_weeks(rows)]
    chosen_weeks = rng.sample(weeks, k=min(args.n, len(weeks)))
    clocks = ["09:00", "12:00", "15:00", "18:00"]

    results = []
    for week in chosen_weeks:
        day_number = rng.choice(list(DAY_CHOICES))
        clock = rng.choice(clocks)
        cutoff = cutoff_seconds(day_number, clock)
        target = week_features(week, rows_by_week[week], cutoff, topics, calendar, args.calendar_lookahead_days)
        training = [
            week_features(other_week, week_rows, cutoff, topics, calendar, args.calendar_lookahead_days)
            for other_week, week_rows in rows_by_week.items()
            if other_week != week
        ]
        weights = [feature_weight(candidate, target) for candidate in training]
        totals = simulate_from_features(
            target,
            training,
            weights,
            args.samples,
            args.post_noise_sigma,
            tail_overlay=True,
        )
        cutoff_dt = datetime.combine(week, time.min, ET) + timedelta(seconds=cutoff)
        p10 = percentile(totals, 0.10)
        p50 = percentile(totals, 0.50)
        p90 = percentile(totals, 0.90)
        actual = target["actual"]
        regime, reasons = classify_regime(target)
        outlier_risk, outlier_reasons = extreme_outlier_risk(target)
        results.append(
            {
                "week": week,
                "cutoff": cutoff_dt,
                "observed": target["observed"],
                "actual": actual,
                "mean": statistics.mean(totals),
                "p10": p10,
                "p50": p50,
                "p90": p90,
                "actual_pctile": rank_probability(totals, actual),
                "actual_bin": value_bin(actual),
                "actual_bin_prob": actual_bin_probability(totals, actual),
                "covered": p10 <= actual <= p90,
                "tail_overlay": campaign_tail_probability(target),
                "future_events": target["future_event_count"],
                "regime": regime,
                "regime_reasons": reasons,
                "extreme_outlier_risk": outlier_risk,
                "extreme_outlier_reasons": outlier_reasons,
            }
        )

    print("Random Truth Social point backtest")
    print(f"Post history: {args.post_history}")
    print(f"Seed: {args.seed}")
    print("Cutoff days: 2-5 where Sunday=1, so Monday-Thursday")
    print()
    print(
        f"{'week':>10} {'cutoff':>16} {'obs':>4} {'actual':>6} "
        f"{'p10':>4} {'p50':>4} {'p90':>4} {'pctile':>7} {'bin_p':>6} {'cover':>5} {'events':>6}  regime / outlier"
    )
    for row in results:
        print(
            f"{row['week']} "
            f"{row['cutoff']:%a %H:%M} "
            f"{row['observed']:>4} "
            f"{row['actual']:>6} "
            f"{row['p10']:>4} "
            f"{row['p50']:>4} "
            f"{row['p90']:>4} "
            f"{row['actual_pctile'] * 100:>6.1f}% "
            f"{row['actual_bin_prob'] * 100:>5.1f}% "
            f"{'yes' if row['covered'] else 'no':>5} "
            f"{row['future_events']:>6}  "
            f"{row['regime']} / {row['extreme_outlier_risk']}"
        )

    errors = [abs(row["p50"] - row["actual"]) for row in results]
    covered = sum(1 for row in results if row["covered"])
    print()
    print(f"Median absolute error vs p50: {statistics.median(errors):.1f}")
    print(f"Mean absolute error vs p50: {statistics.mean(errors):.1f}")
    print(f"p10-p90 coverage: {covered}/{len(results)}")
    print(f"Mean actual-bin probability: {statistics.mean(row['actual_bin_prob'] for row in results) * 100:.1f}%")
    print()
    print("By regime")
    for regime in sorted({row["regime"] for row in results}):
        group = [row for row in results if row["regime"] == regime]
        group_errors = [abs(row["p50"] - row["actual"]) for row in group]
        group_covered = sum(1 for row in group if row["covered"])
        print(
            f"{regime}: n={len(group)}, "
            f"median_abs_error={statistics.median(group_errors):.1f}, "
            f"coverage={group_covered}/{len(group)}, "
            f"mean_bin_p={statistics.mean(row['actual_bin_prob'] for row in group) * 100:.1f}%"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
