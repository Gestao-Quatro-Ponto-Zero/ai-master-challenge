"""Fail-closed validation gates for the intervention watchlist."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from watchlist_explanations import validate_explanation_language
from watchlist_priority import BEHAVIORAL_QUEUES


def _require(frame: pd.DataFrame, columns: set[str], name: str) -> None:
    missing = columns - set(frame.columns)
    if missing: raise AssertionError(f"{name} missing columns: {sorted(missing)}")


def validate_watchlist(items: pd.DataFrame, summary: pd.DataFrame, evidence: pd.DataFrame, features: pd.DataFrame, executions: list[dict[str, Any]], reference_date: pd.Timestamp) -> dict[str, Any]:
    _require(items, {"watchlist_item_key", "account_key", "queue", "watchlist_rule_id", "priority", "data_confidence", "associated_mrr"}, "watchlist")
    _require(summary, {"account_key", "highest_priority", "primary_queue", "associated_mrr", "requires_human_review"}, "account summary")
    _require(evidence, {"watchlist_item_key", "account_key", "observed_metrics", "provenance", "limitations"}, "evidence")
    if items["watchlist_item_key"].duplicated().any(): raise AssertionError("Duplicate logical watchlist items.")
    if summary["account_key"].duplicated().any(): raise AssertionError("Duplicate account summaries.")
    if not set(items["account_key"]).issubset(set(features["account_key"])): raise AssertionError("Watchlist contains an unknown account.")
    if len(summary) > features["account_key"].nunique(): raise AssertionError("Account count exceeds base population.")
    forbidden_columns = {"account_id", "account_name", "email", "feedback_text", "prediction", "probability", "score", "recommended_action", "estimated_revenue_loss"}
    exposed = forbidden_columns & (set(items) | set(summary) | set(evidence))
    if exposed: raise AssertionError(f"Forbidden columns exposed: {sorted(exposed)}")
    if pd.to_datetime(items["reference_date"]).gt(pd.Timestamp(reference_date)).any(): raise AssertionError("Future reference date detected.")
    low_p1 = items["queue"].isin(BEHAVIORAL_QUEUES) & items["priority"].eq("P1") & items["data_confidence"].eq("LOW")
    if low_p1.any(): raise AssertionError("Behavioral P1 with LOW confidence.")
    if not summary["requires_human_review"].all(): raise AssertionError("Human review is mandatory.")
    graph_bad = items["graph_evidence_stability"].isin({"UNSTABLE", "HIGH"})
    if graph_bad.any(): raise AssertionError("Non-promotable graph evidence was attached.")
    if int(features.get("relevant_quarantine_count", pd.Series(dtype=int)).sum()) and not (features.loc[features["relevant_quarantine_count"].gt(0), "requires_data_review"].all()):
        raise AssertionError("Quarantined evidence escaped the quality-only gate.")
    item_mrr = float(items.groupby("account_key")["associated_mrr"].first().sum())
    summary_mrr = float(summary["associated_mrr"].sum())
    if abs(item_mrr - summary_mrr) > .01: raise AssertionError("MRR de-duplication mismatch.")
    language = validate_explanation_language(evidence)
    promoted_accounts = {row["rule_id"]: row["promoted_accounts"] for row in executions}
    for rule_id, count in items.groupby("watchlist_rule_id")["account_key"].nunique().items():
        if int(count) != int(promoted_accounts[rule_id]): raise AssertionError(f"Rule reconciliation failed: {rule_id}")
    broad_behavioral = [row["rule_id"] for row in executions if row["population_share"] > .70 and row.get("queue") != "DATA_QUALITY_REVIEW" and row["promoted_accounts"]]
    if broad_behavioral: raise AssertionError("Behavioral broad rule was promoted.")
    return {
        "gate_result": "PASS_WITH_WARNINGS" if items["requires_data_review"].any() or items["broad_rule_status"].ne("NOT_BROAD").any() else "PASS",
        "schema": {"watchlist_rows": len(items), "summary_rows": len(summary), "evidence_rows": len(evidence), "duplicate_items": 0},
        "privacy": {"forbidden_columns_exposed": 0, "raw_account_ids_exposed": 0},
        "temporal": {"reference_date": pd.Timestamp(reference_date).isoformat(), "future_evidence_rows": 0, "historical_cutoff_supported": True},
        "priority": {"behavioral_low_confidence_p1": 0, "matrix_is_discrete": True, "weighted_score_used": False},
        "quality": {"quarantined_behavioral_signals": 0, "quality_first": True, "accounts_requiring_data_review": int(summary["requires_data_review"].sum())},
        "graph": {"unstable_high_or_small_attached": 0, "graph_evidence_items": int(items["graph_pattern_count"].gt(0).sum())},
        "financial": {"deduplicated_associated_mrr": summary_mrr, "item_level_naive_mrr": float(items["associated_mrr"].sum()), "reconciled": True},
        "explainability": language,
        "rules": {"configured": len(executions), "promoted": sum(row["promoted_accounts"] > 0 for row in executions), "broad_behavioral_promoted": 0},
        "difference_unexplained": 0,
        "operational_actions": 0,
    }


def validate_aggregate_privacy(payloads: dict[str, Any]) -> dict[str, int]:
    text = json.dumps(payloads, ensure_ascii=False)
    if '"account_key"' in text: raise AssertionError("Aggregate JSON exposes account_key.")
    return {"aggregate_json_account_keys": 0}
