"""Tests for the portable Neo4j package."""

import sys
from pathlib import Path

import networkx as nx

SRC = Path(__file__).parents[1] / "src"
sys.path.insert(0, str(SRC))

from neo4j_export import NODE_FILES, RELATIONSHIP_FILES, export_neo4j  # noqa: E402


def _graphs() -> tuple[nx.MultiDiGraph, nx.MultiDiGraph]:
    instance = nx.MultiDiGraph(name="instance", graph_mode="INSTANCE")
    nodes = {
        "acct_x": "Account", "journey_x": "Journey", "event_x": "EventInstance",
        "eventtype_feature": "EventType", "taxonomy_t1": "Taxonomy",
        "outcome_single_churn": "Outcome", "quality_q1": "QualityProfile",
    }
    for key, label in nodes.items():
        props = {"label": label}
        if label == "Account": props.update(account_key=key, is_anonymized=True)
        if label == "Journey": props.update(journey_key=key)
        if label == "EventInstance": props.update(event_instance_key=key)
        if label == "QualityProfile": props.update(quality_profile_key=key)
        instance.add_node(key, **props)
    instance.add_edge("acct_x", "journey_x", key="r1", relationship="HAS_JOURNEY")
    instance.add_edge("journey_x", "event_x", key="r2", relationship="HAS_EVENT")
    instance.add_edge("event_x", "eventtype_feature", key="r3", relationship="OF_TYPE")
    analytical = nx.MultiDiGraph(name="analytical", graph_mode="ANALYTICAL")
    analytical.add_node("pattern_x", label="Pattern", pattern_key="pattern_x")
    analytical.add_node("finding_f1", label="Finding", finding_id="F1")
    analytical.add_node("investigation_review", label="Investigation", investigation_type="REVIEW_DATA_QUALITY")
    analytical.add_edge("pattern_x", "finding_f1", key="r4", relationship="SUPPORTED_BY")
    analytical.add_edge("finding_f1", "investigation_review", key="r5", relationship="RECOMMENDS_INVESTIGATION")
    return instance, analytical


def test_export_has_exact_node_relationship_and_cypher_contract(tmp_path: Path) -> None:
    instance, analytical = _graphs()
    manifest = export_neo4j(instance, analytical, tmp_path, event_journey_sample_size=1)
    expected = set(NODE_FILES.values()) | set(RELATIONSHIP_FILES.values()) | {
        "constraints.cypher", "indexes.cypher", "import.cypher", "example_queries.cypher",
    }
    assert {path.name for path in tmp_path.iterdir()} == expected
    assert manifest["privacy"] == {"raw_account_id_exported": False, "source_event_id_exported": False, "pii_exported": False}
    assert manifest["nodes"]["EventInstance"]["rows"] == 1
    assert manifest["relationships"]["HAS_EVENT"]["rows"] == 1
    assert "IS UNIQUE" in (tmp_path / "constraints.cypher").read_text(encoding="utf-8")
    assert "neo4j-admin database import" in (tmp_path / "import.cypher").read_text(encoding="utf-8")
    assert "raw-account" not in "".join(path.read_text(encoding="utf-8") for path in tmp_path.iterdir())
