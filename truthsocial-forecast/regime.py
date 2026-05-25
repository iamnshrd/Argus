from __future__ import annotations


def classify_regime(features: dict) -> tuple[str, list[str]]:
    reasons = []
    observed = features["observed"]
    last24 = features["last24"]
    burst6 = features["burst6"]
    topic = features["topic_shares"]
    distinct_topics = features.get("distinct_topic_count", len(topic))
    future_events = features["future_event_count"]
    future_primary = features["future_primary_count"]
    future_special = features["future_special_count"]

    mechanical_share = (
        topic.get("reposts", 0)
        + topic.get("image_only", 0)
        + topic.get("video_only", 0)
        + topic.get("quote_truths", 0)
    )
    endorsement_share = topic.get("campaign_endorsements", 0)

    high_score = 0
    fade_score = 0

    if observed >= 80:
        high_score += 2
        reasons.append("high observed count")
    elif observed >= 55:
        high_score += 1
        reasons.append("above-average observed count")
    elif observed < 35:
        fade_score += 1
        reasons.append("low observed count")

    if last24 >= 25:
        high_score += 2
        reasons.append("strong last-24h activity")
    elif last24 <= 4:
        fade_score += 1
        reasons.append("weak last-24h activity")

    if burst6 >= 20:
        high_score += 1
        reasons.append("large 6h burst")
    elif burst6 <= 8:
        fade_score += 1
        reasons.append("small 6h burst")

    if mechanical_share >= 0.45:
        high_score += 1
        reasons.append("mechanical media/repost-heavy mix")

    if endorsement_share >= 0.15:
        high_score += 1
        reasons.append("endorsement-heavy mix")

    if observed < 45 and distinct_topics >= 7 and endorsement_share >= 0.08:
        reasons.append("broad early topic spark with endorsements")
    elif observed < 55 and distinct_topics >= 8:
        reasons.append("broad early topic spark")

    if future_events >= 4 or future_primary >= 3 or future_special >= 1:
        high_score += 1
        reasons.append("forward election/primary calendar risk")

    has_mechanical_spark = mechanical_share >= 0.35 or distinct_topics >= 7

    if observed < 35 and future_events == 0 and not has_mechanical_spark:
        return "fade_risk", reasons
    if observed < 40 and last24 <= 4 and future_events <= 1 and mechanical_share < 0.35:
        return "fade_risk", reasons
    if fade_score >= 2 and high_score <= 1 and not has_mechanical_spark:
        return "fade_risk", reasons
    if high_score >= 4 or (high_score >= 3 and observed >= 80):
        return "high_tail", reasons
    return "normal", reasons


def extreme_outlier_risk(features: dict) -> tuple[str, list[str]]:
    topic = features["topic_shares"]
    observed = features["observed"]
    distinct_topics = features.get("distinct_topic_count", len(topic))
    endorsement_share = topic.get("campaign_endorsements", 0)
    mechanical_share = (
        topic.get("reposts", 0)
        + topic.get("image_only", 0)
        + topic.get("video_only", 0)
        + topic.get("quote_truths", 0)
    )
    future_events = features["future_event_count"]
    future_special = features["future_special_count"]
    future_primary = features["future_primary_count"]

    reasons = []
    score = 0

    if observed < 45 and distinct_topics >= 7:
        score += 1
        reasons.append("broad early topic mix")
    if endorsement_share >= 0.08:
        score += 1
        reasons.append("endorsement signal")
    if mechanical_share >= 0.35:
        score += 1
        reasons.append("media/repost mechanics already visible")
    if future_events >= 4 or future_primary >= 3 or future_special >= 1:
        score += 1
        reasons.append("forward election calendar")
    if observed >= 80 or features["last24"] >= 35:
        score += 1
        reasons.append("already-high live pace")

    if score >= 4:
        return "high", reasons
    if score >= 2:
        return "elevated", reasons
    return "normal", reasons


def regime_settings(regime: str) -> dict:
    if regime == "high_tail":
        return {
            "tail_multiplier": 1.35,
            "tail_floor": 0.18,
            "tail_quantile": 0.6,
            "noise_multiplier": 1.35,
            "max_total": None,
        }
    if regime == "fade_risk":
        return {
            "tail_multiplier": 0.35,
            "tail_floor": 0.0,
            "tail_quantile": 0.85,
            "noise_multiplier": 0.85,
            "max_total": 180,
        }
    return {
        "tail_multiplier": 1.0,
        "tail_floor": 0.0,
        "tail_quantile": 0.7,
        "noise_multiplier": 1.0,
        "max_total": None,
    }
