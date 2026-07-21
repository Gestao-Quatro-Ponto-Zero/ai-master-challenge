"""Tests for the governed JourneyGraph schema."""

import json
import sys
from pathlib import Path

SRC = Path(__file__).parents[1] / "src"
sys.path.insert(0, str(SRC))

from graph_schema import (  # noqa: E402
    FORBIDDEN_CAUSAL_TERMS, NODE_LABELS, PUBLIC_NAMESPACE_SALT,
    RELATIONSHIP_TYPES, graph_schema_artifact, simple_value, stable_key,
)


def test_identifiers_are_deterministic_anonymous_and_namespaced() -> None:
    first = stable_key("acct", "raw-account-1")
    assert first == stable_key("acct", "raw-account-1")
    assert first.startswith("acct_")
    assert "raw-account-1" not in first
    assert first != stable_key("journey", "raw-account-1")
    assert graph_schema_artifact()["identifier_policy"]["salt"] == PUBLIC_NAMESPACE_SALT


def test_schema_declares_all_governed_types_without_causal_edges() -> None:
    required_nodes = {"Account", "Journey", "EventInstance", "EventType", "Pattern", "Outcome", "Taxonomy", "QualityProfile", "Finding", "Investigation"}
    required_edges = {"HAS_JOURNEY", "HAS_EVENT", "OF_TYPE", "NEXT_EVENT", "CLASSIFIED_AS", "ASSOCIATED_WITH_OUTCOME", "HAS_QUALITY_PROFILE", "MATCHES_PATTERN", "CONTAINS_EVENT_TYPE", "OBSERVED_BEFORE", "ASSOCIATED_WITH", "SUPPORTED_BY", "RECOMMENDS_INVESTIGATION", "TRANSITIONS_TO"}
    assert required_nodes == set(NODE_LABELS)
    assert required_edges <= set(RELATIONSHIP_TYPES)
    assert set(RELATIONSHIP_TYPES).isdisjoint(FORBIDDEN_CAUSAL_TERMS)


def test_graphml_values_are_simple_and_lists_use_stable_json() -> None:
    encoded = simple_value(["B", "A"])
    assert json.loads(encoded) == ["B", "A"]
    assert isinstance(simple_value(True), bool)
    assert isinstance(simple_value(None), str)
