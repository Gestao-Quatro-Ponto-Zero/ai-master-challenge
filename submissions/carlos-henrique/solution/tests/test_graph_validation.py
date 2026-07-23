"""Tests for graph privacy, semantics, schema, and temporal gates."""

import sys
from pathlib import Path

import networkx as nx
import pytest

SRC = Path(__file__).parents[1] / "src"
sys.path.insert(0, str(SRC))

from graph_validation import (  # noqa: E402
    validate_graphml_types, validate_non_causal, validate_privacy,
    validate_promotion, validate_schema, validate_temporal,
)


def _instance() -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph(name="fixture", graph_mode="INSTANCE")
    graph.add_node("acct_hash", label="Account", account_key="acct_hash", is_anonymized=True)
    graph.add_node("journey_hash", label="Journey", journey_start="2024-01-01T00:00:00", journey_end="2024-01-03T00:00:00")
    graph.add_node("event_1", label="EventInstance", event_time="2024-01-01T00:00:00")
    graph.add_node("event_2", label="EventInstance", event_time="2024-01-03T00:00:00")
    graph.add_edge("acct_hash", "journey_hash", key="r1", relationship="HAS_JOURNEY")
    graph.add_edge("journey_hash", "event_1", key="r2", relationship="HAS_EVENT", event_position=1)
    graph.add_edge("journey_hash", "event_2", key="r3", relationship="HAS_EVENT", event_position=2)
    graph.add_edge("event_1", "event_2", key="r4", relationship="NEXT_EVENT")
    return graph


def test_valid_graph_passes_schema_privacy_temporal_and_graphml_gates() -> None:
    graph = _instance()
    assert validate_schema(graph)["duplicate_relationships"] == 0
    assert validate_privacy(graph, ["raw-account-1"])["raw_account_ids_exposed"] == 0
    assert validate_temporal(graph)["temporal_violations"] == 0
    assert validate_non_causal(graph)["violations"] == 0
    assert validate_graphml_types(graph)["invalid_property_types"] == 0


def test_causal_text_and_pii_are_rejected() -> None:
    graph = _instance()
    graph.nodes["journey_hash"]["statement"] = "FEATURE DRIVES churn"
    with pytest.raises(AssertionError, match="Causal semantics"):
        validate_non_causal(graph)
    graph.nodes["journey_hash"].pop("statement")
    graph.nodes["acct_hash"]["email"] = "private@example.test"
    with pytest.raises(AssertionError, match="Privacy violation"):
        validate_privacy(graph, ["raw-account-1"])


def test_temporal_reversal_and_nonpromotable_patterns_are_rejected() -> None:
    graph = _instance()
    graph.nodes["event_2"]["event_time"] = "2023-12-31T00:00:00"
    with pytest.raises(AssertionError, match="temporal order"):
        validate_temporal(graph)
    analytical = nx.MultiDiGraph(name="fixture", graph_mode="ANALYTICAL")
    analytical.add_node(
        "p", label="Pattern", stability_status="UNSTABLE",
        same_day_dependency="NONE", small_sample=False, is_promotable=True,
    )
    with pytest.raises(AssertionError, match="Non-promotable"):
        validate_promotion(analytical)
