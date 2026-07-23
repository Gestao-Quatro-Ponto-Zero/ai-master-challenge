"""JourneyGraph schema, temporal, privacy, semantic, and reconciliation checks."""

from __future__ import annotations

import json
from collections import Counter
from typing import Any, Iterable

import networkx as nx
import pandas as pd

from graph_schema import FORBIDDEN_CAUSAL_TERMS, FORBIDDEN_PII_PROPERTIES, NODE_LABELS, RELATIONSHIP_TYPES


def validate_schema(graph: nx.MultiDiGraph) -> dict[str, Any]:
    invalid_labels = sorted({data.get("label") for _, data in graph.nodes(data=True)} - set(NODE_LABELS))
    invalid_relationships = sorted({data.get("relationship") for *_, data in graph.edges(data=True, keys=True)} - set(RELATIONSHIP_TYPES))
    if invalid_labels or invalid_relationships:
        raise AssertionError(f"Schema violation: labels={invalid_labels}, relationships={invalid_relationships}")
    if graph.number_of_nodes() != len(set(graph.nodes)):
        raise AssertionError("Duplicate node keys detected.")
    edge_keys = [key for _, _, key in graph.edges(keys=True)]
    if len(edge_keys) != len(set(edge_keys)):
        raise AssertionError("Duplicate logical edge keys detected.")
    return {"valid_labels": len(NODE_LABELS), "valid_relationship_types": len(RELATIONSHIP_TYPES), "duplicate_nodes": 0, "duplicate_relationships": 0}


def validate_non_causal(graph: nx.MultiDiGraph) -> dict[str, Any]:
    violations = []
    for node, data in graph.nodes(data=True):
        text = " ".join(str(value).upper() for value in data.values())
        for term in FORBIDDEN_CAUSAL_TERMS:
            if term in text:
                violations.append({"node": node, "term": term})

    for source, target, key, data in graph.edges(data=True, keys=True):
        relationship = str(data.get("relationship", "")).upper()
        if relationship in FORBIDDEN_CAUSAL_TERMS:
            violations.append({"source": source, "target": target, "key": key, "term": relationship})
        text = " ".join(str(value).upper() for value in data.values())
        for term in FORBIDDEN_CAUSAL_TERMS:
            if term in text:
                violations.append({"source": source, "target": target, "key": key, "term": term})
    if violations:
        raise AssertionError(f"Causal semantics detected: {violations[:3]}")
    return {"forbidden_terms_checked": len(FORBIDDEN_CAUSAL_TERMS), "violations": 0}


def validate_privacy(graph: nx.MultiDiGraph, raw_account_ids: Iterable[str]) -> dict[str, Any]:
    property_names = set()
    public_values = set()
    for _, data in graph.nodes(data=True):
        property_names.update(data)
        public_values.update(str(value) for value in data.values())
    for *_, data in graph.edges(data=True, keys=True):
        property_names.update(data)
        public_values.update(str(value) for value in data.values())
    forbidden_properties = sorted(property_names & set(FORBIDDEN_PII_PROPERTIES))
    leaked_ids = sorted(set(str(value) for value in raw_account_ids) & public_values)
    if forbidden_properties or leaked_ids:
        raise AssertionError(f"Privacy violation: properties={forbidden_properties}, ids={len(leaked_ids)}")
    account_nodes = [data for _, data in graph.nodes(data=True) if data["label"] == "Account"]
    if any(not bool(data["is_anonymized"]) for data in account_nodes):
        raise AssertionError("An account node is not marked anonymized.")
    return {"forbidden_properties": forbidden_properties, "raw_account_ids_exposed": len(leaked_ids), "anonymized_account_nodes": len(account_nodes)}


def validate_temporal(instance_graph: nx.MultiDiGraph) -> dict[str, Any]:
    event_times = {
        node: pd.Timestamp(data["event_time"])
        for node, data in instance_graph.nodes(data=True) if data["label"] == "EventInstance"
    }
    next_edges = 0
    out_next = Counter()
    for source, target, data in instance_graph.edges(data=True):
        if data["relationship"] != "NEXT_EVENT": continue
        next_edges += 1; out_next[source] += 1
        if event_times[target] < event_times[source]:
            raise AssertionError("NEXT_EVENT violates temporal order.")
    if any(count > 1 for count in out_next.values()):
        raise AssertionError("An EventInstance has multiple NEXT_EVENT successors.")
    journey_events: dict[str, list[tuple[int, str]]] = {}
    for source, target, data in instance_graph.edges(data=True):
        if data["relationship"] == "HAS_EVENT":
            journey_events.setdefault(source, []).append((int(data["event_position"]), target))
    for journey, positioned in journey_events.items():
        positions = sorted(position for position, _ in positioned)
        if positions != list(range(1, len(positions) + 1)):
            raise AssertionError(f"Non-contiguous event positions in {journey}")
        start = pd.Timestamp(instance_graph.nodes[journey]["journey_start"])
        end = pd.Timestamp(instance_graph.nodes[journey]["journey_end"])
        times = [event_times[node] for _, node in positioned]
        if min(times) < start or max(times) > end:
            raise AssertionError(f"Event outside journey boundary in {journey}")
    return {"journeys_checked": len(journey_events), "next_event_edges": next_edges, "temporal_violations": 0, "duplicate_next_successors": 0}


def validate_promotion(analytical_graph: nx.MultiDiGraph) -> dict[str, Any]:
    patterns = 0; transitions = 0
    for _, data in analytical_graph.nodes(data=True):
        if data["label"] != "Pattern": continue
        patterns += 1
        if data["stability_status"] not in {"ROBUST", "SENSITIVE"} or data["same_day_dependency"] == "HIGH" or bool(data["small_sample"]) or not bool(data["is_promotable"]):
            raise AssertionError("Non-promotable pattern entered analytical graph.")
    for *_, data in analytical_graph.edges(data=True, keys=True):
        if data["relationship"] != "TRANSITIONS_TO": continue
        transitions += 1
        if data["stability_status"] not in {"ROBUST", "SENSITIVE"} or data["same_day_dependency"] == "HIGH" or bool(data["small_sample"]) or not bool(data["is_promotable"]):
            raise AssertionError("Non-promotable transition entered analytical graph.")
    return {"promoted_patterns_checked": patterns, "promoted_transitions_checked": transitions, "unstable_promoted": 0, "high_dependency_promoted": 0, "small_sample_promoted": 0}


def validate_graphml_types(graph: nx.MultiDiGraph) -> dict[str, Any]:
    allowed = (str, int, float, bool)
    invalid = []
    for node, data in graph.nodes(data=True):
        invalid.extend((node, key, type(value).__name__) for key, value in data.items() if not isinstance(value, allowed))
    for source, target, data in graph.edges(data=True):
        invalid.extend((f"{source}->{target}", key, type(value).__name__) for key, value in data.items() if not isinstance(value, allowed))
    if invalid:
        raise AssertionError(f"GraphML-unsafe values: {invalid[:3]}")
    return {"invalid_property_types": 0, "allowed_types": ["string", "integer", "float", "boolean"]}


def reconcile_graphs(
    instance_graph: nx.MultiDiGraph, analytical_graph: nx.MultiDiGraph,
    journeys: pd.DataFrame, taxonomy: pd.DataFrame, account_features: pd.DataFrame,
    promoted_pattern_count: int, promoted_transition_count: int, finding_count: int,
) -> dict[str, Any]:
    instance_labels = Counter(data["label"] for _, data in instance_graph.nodes(data=True))
    analytical_labels = Counter(data["label"] for _, data in analytical_graph.nodes(data=True))
    analytical_relationships = Counter(data["relationship"] for *_, data in analytical_graph.edges(data=True, keys=True))
    account_mrr = sum(float(data["associated_mrr"]) for _, data in instance_graph.nodes(data=True) if data["label"] == "Account")
    expected_mrr = float(account_features["max_mrr"].fillna(0).sum())
    checks = {
        "accounts": {"graph": instance_labels["Account"], "tabular": int(account_features["account_id"].nunique())},
        "journeys": {"graph": instance_labels["Journey"], "tabular": len(journeys)},
        "taxonomy_classifications": {"graph": sum(data["relationship"] == "CLASSIFIED_AS" for *_, data in instance_graph.edges(data=True, keys=True)), "expected_journey_projection": len(journeys)},
        "promoted_patterns": {"graph": analytical_labels["Pattern"], "expected": promoted_pattern_count},
        "promoted_transitions": {"graph": analytical_relationships["TRANSITIONS_TO"], "expected": promoted_transition_count},
        "findings": {"graph": analytical_labels["Finding"], "expected": finding_count},
        "account_associated_mrr": {"graph": account_mrr, "tabular": expected_mrr},
        "primary_taxonomy_rows": {"tabular": len(taxonomy), "unique_grain": int(taxonomy.drop_duplicates(["account_id", "quality_population"]).shape[0])},
    }
    differences = []
    for name, values in checks.items():
        numeric = list(values.values())
        if len(numeric) >= 2 and abs(float(numeric[0]) - float(numeric[1])) > 1e-8:
            differences.append({"check": name, "values": values})
    if differences:
        raise AssertionError(f"Unexplained graph reconciliation differences: {differences}")
    explained = [
        {"reason": "EVENT_INSTANCE_DUPLICATED_BY_JOURNEY_SCOPE", "source": "account_journeys + event_log", "count": instance_labels["EventInstance"], "expected_behavior": "Each occurrence key includes journey_key for traceability."},
        {"reason": "PATTERN_PROMOTION_GATE", "source": "Phase 5 pattern artifacts", "count": promoted_pattern_count, "expected_behavior": "Only ROBUST/SENSITIVE, supported, non-HIGH and non-small patterns enter the promoted graph."},
        {"reason": "TRANSITION_PROMOTION_GATE", "source": "transition_matrix.json", "count": promoted_transition_count, "expected_behavior": "UNSTABLE, HIGH, small-sample, and insufficient-support transitions remain outside the graph."},
    ]
    return {"checks": checks, "explained_differences": explained, "difference_unexplained": 0, "status": "RECONCILED"}


def validate_all(
    instance_graph: nx.MultiDiGraph, analytical_graph: nx.MultiDiGraph,
    raw_account_ids: Iterable[str], journeys: pd.DataFrame, taxonomy: pd.DataFrame,
    account_features: pd.DataFrame, promoted_pattern_count: int,
    promoted_transition_count: int, finding_count: int,
) -> dict[str, Any]:
    return {
        "instance_schema": validate_schema(instance_graph), "analytical_schema": validate_schema(analytical_graph),
        "instance_privacy": validate_privacy(instance_graph, raw_account_ids), "analytical_privacy": validate_privacy(analytical_graph, raw_account_ids),
        "instance_non_causal": validate_non_causal(instance_graph), "analytical_non_causal": validate_non_causal(analytical_graph),
        "temporal": validate_temporal(instance_graph), "promotion": validate_promotion(analytical_graph),
        "instance_graphml_types": validate_graphml_types(instance_graph), "analytical_graphml_types": validate_graphml_types(analytical_graph),
        "reconciliation": reconcile_graphs(instance_graph, analytical_graph, journeys, taxonomy, account_features, promoted_pattern_count, promoted_transition_count, finding_count),
    }
