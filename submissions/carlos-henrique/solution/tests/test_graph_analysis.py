"""Tests for structural, path, and subgraph analysis."""

import json
import sys
from pathlib import Path

import networkx as nx

SRC = Path(__file__).parents[1] / "src"
sys.path.insert(0, str(SRC))

from graph_analysis import build_subgraphs, centrality_metrics, path_analysis, structural_metrics  # noqa: E402


def _analytical() -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph(name="fixture", graph_mode="ANALYTICAL")
    for event in ("FEATURE", "CHURN", "REACTIVATION"):
        graph.add_node(f"eventtype_{event.lower()}", label="EventType", event_type=event)
    for index, (tokens, stability, mrr) in enumerate((
        (["FEATURE", "CHURN"], "ROBUST", 900.0),
        (["CHURN", "REACTIVATION"], "SENSITIVE", 700.0),
        (["FEATURE"] * 7, "ROBUST", 100.0),
    )):
        graph.add_node(
            f"pattern_{index}", label="Pattern", pattern=json.dumps(tokens),
            pattern_label=" -> ".join(tokens), pattern_type="SEQUENTIAL_CLOSED",
            journey_scope="FULL_OBSERVED_JOURNEY", outcome_context="SINGLE_CHURN",
            account_support=20, denominator_accounts=40, relative_support=.5,
            associated_mrr=mrr, mrr_account_count=20, stability_status=stability,
            same_day_dependency="NONE", small_sample=False, is_promotable=True,
        )
    for index, (left, right, support) in enumerate((("FEATURE", "CHURN", 20), ("CHURN", "REACTIVATION", 15))):
        graph.add_edge(
            f"eventtype_{left.lower()}", f"eventtype_{right.lower()}", key=f"r{index}",
            relationship="TRANSITIONS_TO", account_support=support,
            relative_support=support / 40, transition_count=support + 2,
            stability_status="ROBUST", same_day_dependency="NONE", small_sample=False,
            is_promotable=True,
        )
    return graph


def test_structural_metrics_and_centrality_are_event_type_only() -> None:
    graph = _analytical()
    metrics = structural_metrics(graph)
    centrality = centrality_metrics(graph)
    assert metrics["node_count"] == 6
    assert set(centrality["event_type_by_weight"]) == {"account_support", "relative_support", "transition_count"}
    assert {row["event_type"] for row in centrality["event_type_by_weight"]["account_support"]} == {"FEATURE", "CHURN", "REACTIVATION"}
    assert "NO_ACCOUNT_CENTRALITY_COMPUTED" in centrality["limitations"]


def test_paths_honor_length_support_and_subgraph_policy() -> None:
    graph = _analytical()
    paths = path_analysis(graph, minimum_support=10, maximum_length=6)
    assert paths["ending_in_churn"][0]["pattern"] == ["FEATURE", "CHURN"]
    assert all(len(row["pattern"]) <= 6 for group in paths.values() if isinstance(group, list) for row in group if isinstance(row, dict))
    subgraphs = build_subgraphs(graph)
    assert set(subgraphs) == {"ROBUST_GRAPH", "PROMOTABLE_GRAPH", "CHURN_GRAPH", "REACTIVATION_GRAPH", "QUALITY_REVIEW_GRAPH", "HIGH_MRR_GRAPH"}
    assert subgraphs["PROMOTABLE_GRAPH"].number_of_nodes() == graph.number_of_nodes()
