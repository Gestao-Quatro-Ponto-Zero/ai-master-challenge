"""Contract tests for the deterministic Phase 9 dashboard data layer."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest


SOLUTION = Path(__file__).resolve().parents[1]
SCRIPT = SOLUTION / "scripts" / "build_dashboard_data.py"
SPEC = importlib.util.spec_from_file_location("build_dashboard_data", SCRIPT)
assert SPEC and SPEC.loader
dashboard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dashboard)


@pytest.fixture(scope="module")
def payloads() -> dict[str, object]:
    return dashboard.build_payloads()


def test_input_hash_gate_matches_phase_artifacts() -> None:
    observed = dashboard.validate_inputs()
    assert observed == dashboard.EXPECTED_INPUT_HASHES


def test_output_inventory_is_exact(payloads: dict[str, object]) -> None:
    assert set(payloads) == set(dashboard.OUTPUT_NAMES)
    assert len(payloads) == 15


def test_overview_reconciles_headline_metrics(payloads: dict[str, object]) -> None:
    metrics = {item["label"]: item["value"] for item in payloads["overview.json"]["metrics"]}
    assert metrics["Accounts"] == 500
    assert metrics["Events processed"] == 35_586
    assert metrics["Usable events"] == 13_927
    assert metrics["Journeys"] == 4_221
    assert metrics["Promotable patterns"] == 435
    assert metrics["Promotable transitions"] == 43


def test_demo_accounts_are_real_bounded_and_distinct(payloads: dict[str, object]) -> None:
    samples = payloads["journey_samples.json"]["samples"]
    assert [item["profile"] for item in samples] == ["DEMO_A", "DEMO_B", "DEMO_C"]
    assert len({item["account_key"] for item in samples}) == 3
    assert all(item["account_key"].startswith("acct_") for item in samples)
    assert all(item["pattern_count"] > 0 for item in samples)
    assert all(item["event_count"] > 0 for item in samples)


def test_graph_views_enforce_promotion_and_volume_limits(payloads: dict[str, object]) -> None:
    nodes = payloads["graph_nodes.json"]["modes"]
    edges = payloads["graph_edges.json"]["modes"]
    assert set(nodes) == {"event-flow", "pattern-explorer", "governance-view"}
    assert all(view["node_count"] <= 35 for view in nodes.values())
    assert all(view["edge_count"] <= 80 for view in edges.values())
    graph_text = json.dumps({"nodes": nodes, "edges": edges}).upper()
    assert '"STABILITY_STATUS": "UNSTABLE"' not in graph_text
    assert '"SAME_DAY_DEPENDENCY": "HIGH"' not in graph_text
    assert '"SMALL_SAMPLE": TRUE' not in graph_text


def test_watchlist_keeps_quality_and_behavior_separate(payloads: dict[str, object]) -> None:
    summary = payloads["watchlist_summary.json"]
    categories = {item["category"] for item in summary["queues"]}
    assert categories == {"DATA_QUALITY_BACKLOG", "BEHAVIORAL_INVESTIGATION"}
    assert summary["data_quality_backlog_accounts"] == 467
    items = payloads["watchlist_items_demo.json"]["items"]
    assert {item["priority"] for item in items}.issubset({"P1", "P2", "P3", "P4"})
    assert all(item["requires_human_review"] for item in items)


def test_experiments_remain_unexecuted_and_untested(payloads: dict[str, object]) -> None:
    registry = payloads["experiment_registry.json"]["experiments"]
    assert len(registry) == 8
    assert {item["causal_status"] for item in registry} == {"UNTESTED"}
    assert {item["status"] for item in registry} == {
        "READY_FOR_REVIEW", "PILOT_ONLY", "UNDERPOWERED", "NOT_FEASIBLE"
    }
    details = payloads["experiment_details.json"]["experiments"]
    assert all(item["simulated_assignment"] is True for item in details)


def test_metadata_has_fixed_timestamp_policy(payloads: dict[str, object]) -> None:
    metadata = payloads["metadata.json"]
    assert metadata["build_timestamp_policy"] == "FIXED_TO_DATA_CUTOFF"
    assert metadata["data_cutoff"] == dashboard.CUTOFF
    assert metadata["source_commit"] == dashboard.SOURCE_COMMIT
    assert metadata["demo_mode"] is True
    assert metadata["external_dependencies"] == []


def test_payloads_have_no_pii_raw_ids_or_non_finite_values(payloads: dict[str, object]) -> None:
    text = json.dumps(payloads, ensure_ascii=False, allow_nan=False)
    lowered = text.lower()
    assert not dashboard.RAW_ID_PATTERN.search(text)
    for key in dashboard.FORBIDDEN_KEYS:
        assert f'"{key}"' not in lowered
    assert not re.search(r"\b(?:nan|infinity)\b", lowered)


def test_prohibited_product_language_is_absent(payloads: dict[str, object]) -> None:
    text = json.dumps(payloads, ensure_ascii=False).lower()
    assert all(phrase not in text for phrase in dashboard.FORBIDDEN_PHRASES)
    assert "automatic intervention: not allowed" not in text  # rendered UI owns this fixed label


def test_run_is_idempotent(tmp_path: Path) -> None:
    first = dashboard.run(tmp_path)
    second = dashboard.run(tmp_path)
    assert first["output_hashes"] == second["output_hashes"]
    assert sorted(path.name for path in tmp_path.glob("*.json")) == sorted(dashboard.OUTPUT_NAMES)
