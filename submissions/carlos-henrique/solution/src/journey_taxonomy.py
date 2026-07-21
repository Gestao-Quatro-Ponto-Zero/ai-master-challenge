"""Deterministic, descriptive journey taxonomy (never predictive or causal)."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd


TAXONOMY: tuple[dict[str, Any], ...] = (
    {"taxonomy_id": "J01", "name": "ADOPTION_JOURNEY", "definition": "High 30-day use and multiple active days after subscription start.", "required_conditions": ["feature_event_count_30d >= population Q67", "active_days_30d >= 2"], "exclusion_conditions": [], "temporal_window": "30D", "business_interpretation": "Observed product adoption path.", "limitations": ["DESCRIPTIVE_NOT_CAUSAL"]},
    {"taxonomy_id": "J02", "name": "LOW_ENGAGEMENT_JOURNEY", "definition": "Low activity in the fixed 30-day window.", "required_conditions": ["feature_event_count_30d <= population Q33"], "exclusion_conditions": [], "temporal_window": "30D", "business_interpretation": "Observed low-engagement path.", "limitations": ["ABSENCE_OF_EVENT_IS_NOT_INTERVENTION"]},
    {"taxonomy_id": "J03", "name": "SUPPORT_HEAVY_JOURNEY", "definition": "At least three support openings in the observed journey.", "required_conditions": ["support_open_count >= 3"], "exclusion_conditions": [], "temporal_window": "FULL", "business_interpretation": "Support-intensive observed path.", "limitations": ["TICKET_CONTENT_NOT_USED"]},
    {"taxonomy_id": "J04", "name": "CHURN_PATH", "definition": "Observed journey includes one churn and no later recovery class.", "required_conditions": ["churn_count = 1"], "exclusion_conditions": ["RECURRING_CHURN_PATH"], "temporal_window": "FULL", "business_interpretation": "First-churn descriptive path.", "limitations": ["NO_CAUSAL_ATTRIBUTION"]},
    {"taxonomy_id": "J05", "name": "RECURRING_CHURN_PATH", "definition": "Observed journey contains at least two churn events.", "required_conditions": ["churn_count >= 2"], "exclusion_conditions": [], "temporal_window": "FULL", "business_interpretation": "Repeated churn path.", "limitations": ["DESCRIPTIVE_NOT_PREDICTIVE"]},
    {"taxonomy_id": "J06", "name": "REACTIVATION_PATH", "definition": "Churn is followed by an observed reactivation.", "required_conditions": ["reactivation_count >= 1"], "exclusion_conditions": [], "temporal_window": "POST_CHURN", "business_interpretation": "Observed reactivation path.", "limitations": ["CUSTOMER_SUCCESS_ACTION_NOT_INFERRED"]},
    {"taxonomy_id": "J07", "name": "RECOVERY_JOURNEY", "definition": "Reactivation is followed by feature use or subscription start.", "required_conditions": ["post_reactivation_activity = true"], "exclusion_conditions": [], "temporal_window": "POST_REACTIVATION", "business_interpretation": "Observed activity recovery.", "limitations": ["ACTIVITY_DOES_NOT_IMPLY_CAUSATION"]},
    {"taxonomy_id": "J08", "name": "DORMANT_JOURNEY", "definition": "At least 90 days between adjacent usable events.", "required_conditions": ["maximum_event_gap_days >= 90"], "exclusion_conditions": [], "temporal_window": "FULL", "business_interpretation": "Long observed inactivity interval.", "limitations": ["OUTSIDE_SYSTEM_ACTIVITY_UNOBSERVED"]},
    {"taxonomy_id": "J09", "name": "HIGH_VALUE_LOW_USAGE", "definition": "High MRR and low activity in a fixed window.", "required_conditions": ["max_mrr >= 2000", "feature_event_count_30d <= population Q33"], "exclusion_conditions": [], "temporal_window": "30D", "business_interpretation": "High-value low-use observed path.", "limitations": ["VALUE_BAND_IS_DESCRIPTIVE"]},
    {"taxonomy_id": "J10", "name": "DATA_QUALITY_CONSTRAINED", "definition": "Warnings or limited quality coverage constrain classification.", "required_conditions": ["quality_coverage_ratio < 0.80 or warning-dependent"], "exclusion_conditions": [], "temporal_window": "FULL", "business_interpretation": "Journey interpretation requires quality caution.", "limitations": ["QUALITY_STATUS_NOT_CUSTOMER_BEHAVIOR"]},
)


def _metrics(record: dict[str, Any], feature: pd.Series, low: float, high: float) -> dict[str, Any]:
    tokens, dates = record["_tokens"], record["_dates"]
    reactivation = next((i for i, token in enumerate(tokens) if token == "REACTIVATION"), None)
    after = [] if reactivation is None else tokens[reactivation + 1:]
    gaps = [(pd.Timestamp(right) - pd.Timestamp(left)).days for left, right in zip(dates, dates[1:])]
    feature_30 = float(feature.get("feature_event_count_30d", 0) or 0)
    return {
        "churn_count": tokens.count("CHURN"), "reactivation_count": tokens.count("REACTIVATION"),
        "support_open_count": tokens.count("SUPPORT_OPEN"), "feature_event_count_30d": feature_30,
        "active_days_30d": float(feature.get("active_days_30d", 0) or 0),
        "max_mrr_band": "HIGH_GE_2000" if float(feature.get("max_mrr", 0) or 0) >= 2000 else "BELOW_2000",
        "maximum_event_gap_days": max(gaps, default=0),
        "post_reactivation_activity": any(token in {"FEATURE", "SUBSCRIPTION_START"} for token in after),
        "low_usage_threshold": low, "high_usage_threshold": high,
        "quality_coverage_ratio": float(feature.get("quality_coverage_ratio", 0) or 0),
    }


def _classes(metrics: dict[str, Any], population: str) -> tuple[str, list[str], str]:
    matches: list[str] = []
    if metrics["feature_event_count_30d"] >= metrics["high_usage_threshold"] and metrics["active_days_30d"] >= 2:
        matches.append("ADOPTION_JOURNEY")
    if metrics["feature_event_count_30d"] <= metrics["low_usage_threshold"]:
        matches.append("LOW_ENGAGEMENT_JOURNEY")
    if metrics["support_open_count"] >= 3: matches.append("SUPPORT_HEAVY_JOURNEY")
    if metrics["churn_count"] >= 2: matches.append("RECURRING_CHURN_PATH")
    elif metrics["churn_count"] == 1: matches.append("CHURN_PATH")
    if metrics["reactivation_count"] >= 1: matches.append("REACTIVATION_PATH")
    if metrics["post_reactivation_activity"]: matches.append("RECOVERY_JOURNEY")
    if metrics["maximum_event_gap_days"] >= 90: matches.append("DORMANT_JOURNEY")
    if metrics["max_mrr_band"] == "HIGH_GE_2000" and metrics["feature_event_count_30d"] <= metrics["low_usage_threshold"]: matches.append("HIGH_VALUE_LOW_USAGE")
    if metrics["quality_coverage_ratio"] < 0.80 or population == "MAIN": matches.append("DATA_QUALITY_CONSTRAINED")
    priority = ("RECURRING_CHURN_PATH", "RECOVERY_JOURNEY", "REACTIVATION_PATH", "CHURN_PATH", "HIGH_VALUE_LOW_USAGE", "SUPPORT_HEAVY_JOURNEY", "DORMANT_JOURNEY", "ADOPTION_JOURNEY", "LOW_ENGAGEMENT_JOURNEY", "DATA_QUALITY_CONSTRAINED")
    primary = next((name for name in priority if name in matches), "LOW_ENGAGEMENT_JOURNEY")
    rule = f"PRIORITY[{primary}] from deterministic Phase 5 thresholds"
    return primary, [name for name in matches if name != primary], rule


def classify_journeys(records: list[dict[str, Any]], account_features: pd.DataFrame) -> pd.DataFrame:
    """Classify full journeys in MAIN and STRICT and reconcile labels."""
    features = account_features.copy()
    features["account_id"] = features["account_id"].astype(str)
    features = features.set_index("account_id")
    low, high = features["feature_event_count_30d"].quantile([1 / 3, 2 / 3]).tolist()
    rows = []
    for record in records:
        if record["journey_scope"] != "FULL_OBSERVED_JOURNEY":
            continue
        account_id = str(record["account_id"])
        metric = _metrics(record, features.loc[account_id], float(low), float(high))
        primary, secondary, rule = _classes(metric, record["quality_population"])
        quality = metric["quality_coverage_ratio"]
        confidence = "HIGH" if quality >= 0.90 else ("MEDIUM" if quality >= 0.70 else "LOW")
        rows.append({
            "account_id": account_id, "journey_scope": "FULL_OBSERVED_JOURNEY",
            "primary_journey_class": primary,
            "secondary_journey_classes": json.dumps(secondary, separators=(",", ":")),
            "classification_rule": rule,
            "supporting_metrics": json.dumps(metric, separators=(",", ":"), sort_keys=True),
            "quality_population": record["quality_population"], "confidence_level": confidence,
            "stability_status": "PENDING", "limitations": json.dumps(["DESCRIPTIVE_NOT_CAUSAL", "NOT_AN_INDIVIDUAL_SCORE"], separators=(",", ":")),
        })
    result = pd.DataFrame(rows)
    main = result.loc[result["quality_population"].eq("MAIN")].set_index("account_id")["primary_journey_class"]
    strict = result.loc[result["quality_population"].eq("STRICT")].set_index("account_id")["primary_journey_class"]
    for index, row in result.iterrows():
        account_id = row["account_id"]
        status = "ROBUST" if account_id in strict and account_id in main and strict[account_id] == main[account_id] else ("SENSITIVE" if account_id in strict else "UNSTABLE")
        result.at[index, "stability_status"] = status
    if result.duplicated(["account_id", "journey_scope", "quality_population"]).any():
        raise AssertionError("Taxonomy grain is not unique.")
    return result.sort_values(["account_id", "quality_population"]).reset_index(drop=True)
