"""Deterministic, evidence-based explanations for human reviewers."""

from __future__ import annotations

import json
from typing import Any, Mapping


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True, default=str)


def build_explanation(row: Mapping[str, Any]) -> dict[str, str]:
    """Create bounded language; never infer causality, intent, or an action outcome."""
    metrics = {
        "associated_mrr": round(float(row.get("associated_mrr", 0) or 0), 2),
        "usage_count_30d": round(float(row.get("usage_count_30d", 0) or 0), 2),
        "support_count_90d": int(row.get("support_count_90d", 0) or 0),
        "churn_count": int(row.get("churn_count", 0) or 0),
        "reactivation_count": int(row.get("reactivation_count", 0) or 0),
        "quality_coverage_ratio": round(float(row.get("quality_coverage_ratio", 0) or 0), 4),
    }
    patterns = json.loads(str(row.get("matched_pattern_keys", "[]")))
    findings = json.loads(str(row.get("matched_graph_finding_ids", "[]")))
    observed = f"Rule {row['watchlist_rule_id']} matched cutoff-safe account evidence in {row['queue']}."
    why = f"The configured deterministic conditions were met for a group of {int(row.get('rule_group_size', 0))} accounts."
    graph = (
        f"{len(patterns)} promoted JourneyGraph patterns and {len(findings)} linked findings provide descriptive context."
        if patterns else "No eligible promoted JourneyGraph pattern was attached; tabular evidence remains sufficient for review."
    )
    quality_flags = [
        name for name, active in {
            "LOW_STRICT_COVERAGE": float(row.get("quality_coverage_ratio", 0) or 0) < .4,
            "MAIN_STRICT_DIVERGENCE": float(row.get("main_strict_divergence", 0) or 0) > .3,
            "SUBSCRIPTION_OVERLAP": bool(row.get("has_subscription_overlap", False)),
            "TIMELINE_INCONSISTENCY": bool(row.get("timeline_inconsistent", False)),
            "SAME_DAY_ORDER_DEPENDENCY": str(row.get("same_day_order_dependency", "NONE")) != "NONE",
        }.items() if active
    ]
    limitations = ["DESCRIPTIVE_NOT_PREDICTIVE", "ASSOCIATION_NOT_CAUSATION"]
    if quality_flags: limitations.append("QUALITY_LIMITATIONS_REQUIRE_REVIEW")
    if str(row.get("stability_status")) == "SENSITIVE": limitations.append("SENSITIVE_TO_QUALITY_POPULATION")
    return {
        "what_was_observed": observed,
        "why_it_was_flagged": why,
        "supporting_evidence": stable_json(metrics),
        "temporal_context": f"Evidence is restricted to timestamps at or before {row['reference_date']} with a {int(row.get('reference_window_days') or 0)}-day rule window.",
        "graph_context": graph,
        "quality_context": f"Data confidence is {row['data_confidence']}; explicit flags: {', '.join(quality_flags) if quality_flags else 'none'}.",
        "limitations": stable_json(limitations),
        "authorized_next_step": str(row["authorized_investigation"]),
        "prohibited_interpretation": "Do not treat this item as a prediction, causal claim, automated decision, or authorization for outreach.",
    }


def build_evidence_packet(row: Mapping[str, Any]) -> dict[str, Any]:
    explanation = build_explanation(row)
    patterns = json.loads(str(row.get("matched_pattern_keys", "[]")))
    findings = json.loads(str(row.get("matched_graph_finding_ids", "[]")))
    paths = json.loads(str(row.get("matched_graph_paths", "[]")))
    sources = ["PHASE_3_DIAGNOSTIC", "PHASE_4_SURVIVAL", "PHASE_5_JOURNEY", "DATA_QUALITY"]
    if patterns: sources.append("PHASE_6_GRAPH")
    provenance = []
    evidence_specs = [
        ("PHASE_3_DIAGNOSTIC", "data/processed/account_diagnostic_features.parquet", "associated_mrr", row.get("associated_mrr"), row.get("mrr_band")),
        ("PHASE_4_SURVIVAL", "data/processed/account_survival_dataset.parquet", "primary_outcome", row.get("primary_outcome"), "observed at cutoff"),
        ("PHASE_5_JOURNEY", "data/processed/account_journey_taxonomy.parquet", "taxonomy_class", row.get("taxonomy_class"), "configured rule condition"),
        ("DATA_QUALITY", "data/processed/event_log.parquet", "quality_coverage_ratio", row.get("quality_coverage_ratio"), "minimum rule coverage"),
    ]
    if patterns:
        evidence_specs.append(("PHASE_6_GRAPH", "data/processed/journey_instance_graph.graphml", "promoted_pattern_count", len(patterns), "is_promotable=true"))
    for source, artifact, metric, observed, comparison in evidence_specs:
        provenance.append({
            "source": source, "source_artifact": artifact, "metric_name": metric,
            "rule_condition": row["watchlist_rule_id"], "observed_value": observed,
            "comparison_value": comparison, "population": "MAIN_WITH_STRICT_SENSITIVITY",
            "cutoff": str(row["reference_date"]), "window": int(row.get("reference_window_days") or 0),
            "stability": row["stability_status"],
            "quality_status": "REVIEW_REQUIRED" if row.get("requires_data_review") else "USABLE_WITH_GOVERNANCE",
        })
    return {
        "watchlist_item_key": row["watchlist_item_key"],
        "account_key": row["account_key"],
        "rule_id": row["watchlist_rule_id"],
        "queue": row["queue"],
        "reference_date": row["reference_date"],
        "evidence_sources": stable_json(sources),
        "observed_metrics": explanation["supporting_evidence"],
        "matched_patterns": stable_json(patterns),
        "matched_graph_paths": stable_json(paths),
        "matched_findings": stable_json(findings),
        "population": "MAIN_WITH_STRICT_SENSITIVITY",
        "denominators": stable_json({"accounts": int(row.get("population_denominator", 0)), "rule_group": int(row.get("rule_group_size", 0))}),
        "windows": stable_json({"rule_window_days": int(row.get("reference_window_days") or 0), "cutoff": str(row["reference_date"])}),
        "quality_flags": stable_json(json.loads(explanation["limitations"])),
        "stability": row["stability_status"],
        "provenance": stable_json(provenance),
        **explanation,
    }


def validate_explanation_language(frame: Any) -> dict[str, int]:
    columns = ["what_was_observed", "why_it_was_flagged", "graph_context", "authorized_next_step"]
    forbidden = ("guarantees", "will churn", "caused by", "must contact", "automatic discount", "revenue lost")
    violations = 0
    for column in columns:
        violations += int(frame[column].fillna("").str.lower().apply(lambda text: any(term in text for term in forbidden)).sum())
    if violations:
        raise AssertionError("Unsafe or causal explanation language detected.")
    return {"unsafe_language_violations": violations}
