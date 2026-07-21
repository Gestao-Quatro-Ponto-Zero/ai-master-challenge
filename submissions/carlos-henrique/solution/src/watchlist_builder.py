"""Graph evidence integration and governed watchlist assembly."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd

from graph_schema import stable_key
from watchlist_explanations import build_evidence_packet, stable_json
from watchlist_priority import assign_priority
from watchlist_rules import apply_rules


def load_graph_evidence(instance_path: Path, analytical_path: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Project only promoted, non-HIGH, non-small, ROBUST/SENSITIVE graph evidence."""
    analytical = nx.read_graphml(analytical_path)
    eligible: dict[str, dict[str, Any]] = {}
    finding_map: dict[str, list[str]] = defaultdict(list)
    for node, data in analytical.nodes(data=True):
        if data.get("label") == "Pattern" and data.get("stability_status") in {"ROBUST", "SENSITIVE"} and data.get("same_day_dependency") != "HIGH" and not bool(data.get("small_sample")) and bool(data.get("is_promotable")):
            eligible[node] = data
    for source, target, data in analytical.edges(data=True):
        if data.get("relationship") == "SUPPORTED_BY" and source in eligible:
            finding = analytical.nodes[target]
            finding_map[source].append(str(finding.get("finding_id", target)))

    instance = nx.read_graphml(instance_path)
    journey_accounts: dict[str, str] = {}
    for source, target, data in instance.edges(data=True):
        if data.get("relationship") == "HAS_JOURNEY": journey_accounts[target] = source
    account_patterns: dict[str, set[str]] = defaultdict(set)
    for source, target, data in instance.edges(data=True):
        if data.get("relationship") == "MATCHES_PATTERN" and target in eligible and source in journey_accounts:
            account_patterns[journey_accounts[source]].add(target)

    rows = []
    for account_key in sorted(node for node, data in instance.nodes(data=True) if data.get("label") == "Account"):
        patterns = sorted(account_patterns.get(account_key, set()))
        findings = sorted({item for pattern in patterns for item in finding_map.get(pattern, [])})
        churn_paths = [p for p in patterns if "CHURN" in str(eligible[p].get("pattern", ""))]
        support_churn = [p for p in churn_paths if "SUPPORT" in str(eligible[p].get("pattern", ""))]
        paths = [f"{account_key}->journey->${pattern}".replace("$", "") for pattern in patterns[:20]]
        top = eligible[patterns[0]] if patterns else {}
        rows.append({
            "account_key": account_key,
            "matched_pattern_keys": stable_json(patterns),
            "matched_graph_finding_ids": stable_json(findings),
            "matched_graph_paths": stable_json(paths),
            "graph_pattern_count": len(patterns),
            "has_promotable_churn_path": bool(churn_paths),
            "has_promotable_support_churn_path": bool(support_churn),
            "graph_evidence_stability": "ROBUST" if patterns and all(eligible[p].get("stability_status") == "ROBUST" for p in patterns) else ("SENSITIVE" if patterns else "NO_GRAPH_EVIDENCE"),
            "graph_evidence_limitation": "STRUCTURAL_NOT_CAUSAL" if patterns else "NO_ELIGIBLE_PATTERN_MATCH",
            "graph_pattern": str(top.get("pattern", "")),
            "graph_path": paths[0] if paths else "",
            "graph_scope": str(top.get("journey_scope", "")),
            "pattern_support": int(top.get("account_support", 0) or 0),
            "pattern_denominator": int(top.get("denominator_accounts", 0) or 0),
            "pattern_stability": str(top.get("stability_status", "")),
            "pattern_quality_profile": f"{top.get('quality_population','')}_{top.get('stability_status','')}",
            "associated_outcome": str(top.get("outcome_context", "")),
            "graph_limitation": "OBSERVED_IN_GROUP_NOT_ACCOUNT_OUTCOME;STRUCTURAL_NOT_CAUSAL" if patterns else "NO_ELIGIBLE_PATTERN_MATCH",
        })
    metrics = {
        "eligible_promoted_patterns": len(eligible), "accounts_with_eligible_patterns": sum(bool(v) for v in account_patterns.values()),
        "finding_links": sum(len(v) for v in finding_map.values()), "unstable_or_high_or_small_promoted": 0,
    }
    return pd.DataFrame(rows), metrics


def assemble_watchlist(features: pd.DataFrame, config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[dict[str, Any]]]:
    triggers, executions = apply_rules(features, config)
    if triggers.empty:
        raise AssertionError("No watchlist rules were promoted.")
    prioritized = pd.DataFrame([assign_priority(row) for row in triggers.to_dict("records")])
    items = pd.concat([triggers.reset_index(drop=True), prioritized], axis=1)
    items["watchlist_item_key"] = items.apply(lambda row: stable_key("watchitem", row["account_key"], str(row["reference_date"]), row["watchlist_rule_id"]), axis=1)
    items["evidence_count"] = 5 + items["graph_pattern_count"].gt(0).astype(int)
    items["limitation_count"] = 2 + items["requires_data_review"].astype(int) + items["stability_status"].eq("SENSITIVE").astype(int)
    items["evidence_deduplication_count"] = items["evidence_count"]
    items["requires_human_review"] = True
    counts = items.groupby("account_key").agg(rule_trigger_count=("watchlist_rule_id", "nunique"), queue_trigger_count=("queue", "nunique")).reset_index()
    items = items.merge(counts, on="account_key", how="left")
    ordered = [
        "watchlist_item_key", "account_key", "reference_date", "queue", "watchlist_rule_id", "rule_name", "rule_version",
        "priority", "priority_reason", "priority_matrix_cell", "evidence_strength", "temporal_urgency", "materiality", "data_confidence",
        "associated_mrr", "mrr_band", "primary_outcome", "taxonomy_class", "stability_status", "quality_population", "quality_coverage_ratio",
        "human_owner", "authorized_investigation", "prohibited_actions", "reference_window_days", "rule_group_size", "rule_population_share",
        "broad_rule_status", "behavioral_p1_blocked", "rule_trigger_count", "queue_trigger_count", "matched_pattern_keys", "matched_graph_finding_ids",
        "matched_graph_paths", "graph_pattern_count", "has_promotable_churn_path", "has_promotable_support_churn_path", "graph_evidence_stability",
        "graph_evidence_limitation", "main_strict_divergence", "warning_dependency_ratio", "same_day_order_dependency", "requires_data_review",
        "days_since_last_usage", "usage_count_30d", "usage_count_90d", "distinct_features_90d", "support_count_30d", "support_count_90d",
        "mean_resolution_hours_90d", "satisfaction_available", "churn_count", "reactivation_count", "days_since_last_churn", "days_since_last_reactivation",
        "subscription_count", "has_subscription_overlap", "evidence_count", "limitation_count", "evidence_deduplication_count", "requires_human_review",
        "graph_pattern", "graph_path", "graph_scope", "pattern_support", "pattern_denominator", "pattern_stability",
        "pattern_quality_profile", "associated_outcome", "graph_limitation",
    ]
    items = items[ordered].sort_values(["priority", "queue", "account_key", "watchlist_rule_id"]).reset_index(drop=True)
    priority_rank = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}
    summary_rows = []
    for account_key, group in items.groupby("account_key", sort=True):
        best = group.assign(_rank=group["priority"].map(priority_rank)).sort_values(["_rank", "queue", "watchlist_rule_id"]).iloc[0]
        summary_rows.append({
            "account_key": account_key, "reference_date": best["reference_date"], "highest_priority": best["priority"],
            "primary_queue": best["queue"], "rule_ids": stable_json(sorted(group["watchlist_rule_id"].unique())),
            "queues": stable_json(sorted(group["queue"].unique())), "active_rule_count": int(group["watchlist_rule_id"].nunique()),
            "active_queue_count": int(group["queue"].nunique()), "associated_mrr": float(best["associated_mrr"]),
            "evidence_strength_max": max(group["evidence_strength"], key={"LOW":1,"MEDIUM":2,"HIGH":3}.get),
            "temporal_urgency_max": max(group["temporal_urgency"], key={"LOW":1,"MEDIUM":2,"HIGH":3}.get),
            "materiality_max": max(group["materiality"], key={"LOW":1,"MEDIUM":2,"HIGH":3}.get),
            "data_confidence_min": min(group["data_confidence"], key={"LOW":1,"MEDIUM":2,"HIGH":3}.get),
            "primary_outcome": best["primary_outcome"], "taxonomy_class": best["taxonomy_class"], "quality_population": best["quality_population"],
            "requires_data_review": bool(group["requires_data_review"].any()),
            "summary_explanation_key": stable_key("explanation", account_key, str(best["reference_date"])),
            "requires_human_review": True,
        })
    summary = pd.DataFrame(summary_rows)
    evidence = pd.DataFrame([build_evidence_packet(row) for row in items.to_dict("records")])
    return items, summary, evidence, executions
