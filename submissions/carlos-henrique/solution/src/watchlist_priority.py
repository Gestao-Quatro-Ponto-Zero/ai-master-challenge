"""Transparent discrete components and P1-P4 decision matrix."""

from __future__ import annotations

from typing import Any, Mapping


LEVEL = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
BEHAVIORAL_QUEUES = {
    "HIGH_MRR_LOW_ENGAGEMENT_REVIEW", "RECENT_CHURN_REVIEW",
    "RECURRING_CHURN_REVIEW", "REACTIVATION_REVIEW",
    "SUPPORT_JOURNEY_REVIEW", "ADOPTION_REVIEW",
}


def evidence_strength(row: Mapping[str, Any]) -> str:
    stability = str(row.get("stability_status", "SENSITIVE"))
    coverage = float(row.get("quality_coverage_ratio", 0) or 0)
    group = int(row.get("rule_group_size", 0) or 0)
    if stability == "ROBUST" and coverage >= .50 and group >= 20 and bool(row.get("strict_supported", False)):
        return "HIGH"
    if stability in {"ROBUST", "SENSITIVE"} and coverage >= .30 and group >= 10:
        return "MEDIUM"
    return "LOW"


def temporal_urgency(row: Mapping[str, Any]) -> str:
    rule_id = str(row["watchlist_rule_id"])
    queue = str(row["queue"])
    if queue == "DATA_QUALITY_REVIEW":
        return "HIGH" if bool(row.get("requires_data_review", False)) else "MEDIUM"
    if rule_id in {"W001"}:
        return "HIGH"
    if rule_id in {"W002"}:
        return "LOW"
    if rule_id in {"W003", "W016"}:
        return "HIGH" if float(row.get("usage_count_30d", 0) or 0) == 0 else "MEDIUM"
    if queue in {"RECENT_CHURN_REVIEW", "RECURRING_CHURN_REVIEW"} or rule_id == "W008":
        days = row.get("days_since_last_churn")
        if days is None or days != days: return "LOW"
        if float(days) <= 30: return "HIGH"
        if float(days) <= 90: return "MEDIUM"
        return "LOW"
    if queue == "REACTIVATION_REVIEW":
        days = row.get("days_since_last_reactivation")
        if days is None or days != days: return "LOW"
        if float(days) <= 30: return "HIGH"
        if float(days) <= 90: return "MEDIUM"
        return "LOW"
    if queue == "SUPPORT_JOURNEY_REVIEW":
        days = row.get("days_support_before_churn") if rule_id == "W009" else row.get("days_since_last_support")
        if days is None or days != days: return "LOW"
        if float(days) <= 7: return "HIGH"
        if float(days) <= 30: return "MEDIUM"
        return "LOW"
    return "LOW"


def materiality(row: Mapping[str, Any]) -> str:
    band = str(row.get("mrr_band", "LOW"))
    if band == "VERY_HIGH": return "HIGH"
    if band == "HIGH": return "MEDIUM"
    return "LOW"


def data_confidence(row: Mapping[str, Any]) -> str:
    coverage = float(row.get("quality_coverage_ratio", 0) or 0)
    divergence = float(row.get("main_strict_divergence", 1) or 0)
    order = str(row.get("same_day_order_dependency", "NONE"))
    if (
        coverage >= .60 and divergence <= .20 and not bool(row.get("has_subscription_overlap", False))
        and not bool(row.get("timeline_inconsistent", False)) and row.get("stability_status") == "ROBUST"
        and order == "NONE" and bool(row.get("strict_supported", False))
    ):
        return "HIGH"
    if coverage >= .40 and divergence <= .60 and not bool(row.get("timeline_inconsistent", False)) and str(row.get("stability_status")) in {"ROBUST", "SENSITIVE"}:
        return "MEDIUM"
    return "LOW"


def priority_matrix(evidence: str, urgency: str, material: str, confidence: str, queue: str) -> tuple[str, str, str]:
    """Return priority, explicit reason, and named matrix cell without averaging."""
    e, u, m, c = LEVEL[evidence], LEVEL[urgency], LEVEL[material], LEVEL[confidence]
    if queue == "DATA_QUALITY_REVIEW" and u == 3 and m >= 2 and e >= 2:
        return "P1", "High analytical-risk urgency with material associated MRR; human data review required.", "DQ_HIGH_URGENCY_MATERIAL"
    if e == 3 and u == 3 and m >= 2 and c >= 2:
        return "P1", "High evidence and urgency with material context and sufficient data confidence.", "E3_U3_M2PLUS_C2PLUS"
    if e >= 2 and u >= 2 and m >= 2 and c >= 2:
        return "P2", "Medium-or-higher evidence, urgency, materiality, and confidence.", "E2PLUS_U2PLUS_M2PLUS_C2PLUS"
    if e >= 2 or c == 1 or u == 2:
        return "P3", "Review is useful, but evidence, timing, or data confidence limits escalation.", "REVIEW_WITH_LIMITATION"
    return "P4", "Informational item with low immediate urgency or materiality.", "INFORMATIONAL"


def assign_priority(row: Mapping[str, Any]) -> dict[str, str]:
    evidence = evidence_strength(row)
    urgency = temporal_urgency(row)
    material = materiality(row)
    confidence = data_confidence(row)
    priority, reason, cell = priority_matrix(evidence, urgency, material, confidence, str(row["queue"]))
    blocked = False
    if str(row["queue"]) in BEHAVIORAL_QUEUES and confidence == "LOW" and priority == "P1":
        priority, reason, cell, blocked = "P3", "Behavioral P1 blocked because data confidence is LOW; data review precedes interpretation.", "LOW_CONFIDENCE_P1_BLOCK", True
    return {
        "evidence_strength": evidence, "temporal_urgency": urgency,
        "materiality": material, "data_confidence": confidence,
        "priority": priority, "priority_reason": reason,
        "priority_matrix_cell": cell, "behavioral_p1_blocked": blocked,
    }
