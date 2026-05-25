from __future__ import annotations

from dataclasses import dataclass

from truthsocial_forecast import percentile


SECONDS_PER_DAY = 24 * 60 * 60


@dataclass(frozen=True)
class RemainingRegime:
    name: str
    quantile: float
    reasons: list[str]


def source_day(cutoff_seconds: int) -> int:
    return int(cutoff_seconds // SECONDS_PER_DAY) + 1


def mechanical_share(features: dict) -> float:
    topic = features["topic_shares"]
    return (
        topic.get("reposts", 0)
        + topic.get("image_only", 0)
        + topic.get("video_only", 0)
        + topic.get("quote_truths", 0)
    )


def classify_remaining_regime(target: dict, cutoff_seconds: int) -> RemainingRegime | None:
    day = source_day(cutoff_seconds)
    if day < 6:
        return None

    observed = target["observed"]
    last24 = target["last24"]
    burst6 = target["burst6"]
    mechanics = mechanical_share(target)

    if observed >= 105 and (last24 >= 15 or burst6 >= 20):
        return RemainingRegime(
            name="burst_exhaustion",
            quantile=0.25,
            reasons=["high count already banked", "late burst likely partly exhausted"],
        )

    if burst6 >= 25 and mechanics >= 0.40:
        return RemainingRegime(
            name="burst_exhaustion",
            quantile=0.25,
            reasons=["large prior burst", "media/repost mechanics likely exhausted"],
        )

    if observed < 75 and last24 <= 8:
        return RemainingRegime(
            name="quiet_taper",
            quantile=0.25,
            reasons=["low observed count", "weak last-24h continuation"],
        )

    if observed < 90 and last24 >= 15 and 0.30 <= mechanics < 0.38 and burst6 < 25:
        return RemainingRegime(
            name="late_continuation",
            quantile=0.85,
            reasons=["moderate count", "live last-24h", "media/repost mechanics"],
        )

    if observed < 110 and last24 >= 25 and mechanics >= 0.35:
        return RemainingRegime(
            name="active_taper",
            quantile=0.75,
            reasons=["active last-24h", "media/repost mechanics"],
        )

    return RemainingRegime(
        name="normal_taper",
        quantile=0.50,
        reasons=["standard late-week remaining profile"],
    )


def late_remaining_totals(target: dict, training: list[dict], cutoff_seconds: int) -> tuple[list[int], RemainingRegime] | None:
    regime = classify_remaining_regime(target, cutoff_seconds)
    if regime is None:
        return None

    remaining = sorted(len(candidate["remaining"]) for candidate in training)
    if not remaining:
        return None

    median_remaining = percentile(remaining, 0.50)
    target_remaining = percentile(remaining, regime.quantile)
    adjustment = target_remaining - median_remaining
    totals = [
        target["observed"] + max(0, int(round(value + adjustment)))
        for value in remaining
    ]
    return totals, regime
