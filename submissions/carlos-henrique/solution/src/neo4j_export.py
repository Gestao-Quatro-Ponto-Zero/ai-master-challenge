"""Portable Neo4j CSV and Cypher export without server dependency."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Any, Iterable

import networkx as nx


NODE_FILES = {
    "Account": "nodes_account.csv", "Journey": "nodes_journey.csv",
    "EventInstance": "nodes_event_instance.csv", "EventType": "nodes_event_type.csv",
    "Pattern": "nodes_pattern.csv", "Outcome": "nodes_outcome.csv",
    "Taxonomy": "nodes_taxonomy.csv", "QualityProfile": "nodes_quality_profile.csv",
    "Finding": "nodes_finding.csv", "Investigation": "nodes_investigation.csv",
}

RELATIONSHIP_FILES = {
    "HAS_JOURNEY": "relationships_has_journey.csv", "HAS_EVENT": "relationships_has_event.csv",
    "OF_TYPE": "relationships_of_type.csv", "NEXT_EVENT": "relationships_next_event.csv",
    "CLASSIFIED_AS": "relationships_classified_as.csv", "ASSOCIATED_WITH_OUTCOME": "relationships_associated_with_outcome.csv",
    "HAS_QUALITY_PROFILE": "relationships_has_quality_profile.csv", "MATCHES_PATTERN": "relationships_matches_pattern.csv",
    "CONTAINS_EVENT_TYPE": "relationships_contains_event_type.csv", "TRANSITIONS_TO": "relationships_transitions_to.csv",
    "SUPPORTED_BY": "relationships_supported_by.csv", "RECOMMENDS_INVESTIGATION": "relationships_recommends_investigation.csv",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(path: Path, rows: list[dict[str, Any]], required: list[str]) -> None:
    extra = sorted({key for row in rows for key in row if key not in required})
    columns = required + extra
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def _node_inventory(instance: nx.MultiDiGraph, analytical: nx.MultiDiGraph) -> dict[str, dict[str, dict[str, Any]]]:
    inventory = {label: {} for label in NODE_FILES}
    for graph in (instance, analytical):
        for node, data in graph.nodes(data=True):
            label = data["label"]
            if label in inventory:
                inventory[label][node] = {":ID": node, ":LABEL": label, **{key: value for key, value in data.items() if key != "label"}}
    return inventory


def export_neo4j(
    instance: nx.MultiDiGraph, analytical: nx.MultiDiGraph, output_dir: Path,
    *, event_journey_sample_size: int = 250,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    inventory = _node_inventory(instance, analytical)
    journey_keys = sorted(inventory["Journey"])
    sampled_journeys = set(journey_keys[:event_journey_sample_size])
    sampled_events = {
        target for source, target, data in instance.edges(data=True)
        if data["relationship"] == "HAS_EVENT" and source in sampled_journeys
    }
    inventory["EventInstance"] = {key: row for key, row in inventory["EventInstance"].items() if key in sampled_events}

    manifest: dict[str, Any] = {
        "export_mode": "PORTABLE_CSV_NO_SERVER", "event_instance_export": "DETERMINISTIC_JOURNEY_SAMPLE",
        "event_journey_sample_size": min(event_journey_sample_size, len(journey_keys)),
        "full_instance_graph_preserved_in_graphml": True, "nodes": {}, "relationships": {},
        "privacy": {"raw_account_id_exported": False, "source_event_id_exported": False, "pii_exported": False},
    }
    for label, filename in NODE_FILES.items():
        rows = [inventory[label][key] for key in sorted(inventory[label])]
        _write_csv(output_dir / filename, rows, [":ID", ":LABEL"])
        manifest["nodes"][label] = {"file": filename, "rows": len(rows)}

    relationship_rows: dict[str, list[dict[str, Any]]] = {relationship: [] for relationship in RELATIONSHIP_FILES}
    for graph in (instance, analytical):
        for source, target, key, data in graph.edges(data=True, keys=True):
            relationship = data["relationship"]
            if relationship not in relationship_rows: continue
            if relationship in {"HAS_EVENT", "OF_TYPE", "NEXT_EVENT"}:
                if relationship == "HAS_EVENT" and (source not in sampled_journeys or target not in sampled_events): continue
                if relationship == "OF_TYPE" and source not in sampled_events: continue
                if relationship == "NEXT_EVENT" and (source not in sampled_events or target not in sampled_events): continue
            row = {":START_ID": source, ":END_ID": target, ":TYPE": relationship, "relationship_key": key}
            row.update({name: value for name, value in data.items() if name != "relationship"})
            relationship_rows[relationship].append(row)
    for relationship, filename in RELATIONSHIP_FILES.items():
        unique = {row["relationship_key"]: row for row in relationship_rows[relationship]}
        rows = [unique[key] for key in sorted(unique)]
        _write_csv(output_dir / filename, rows, [":START_ID", ":END_ID", ":TYPE"])
        manifest["relationships"][relationship] = {"file": filename, "rows": len(rows)}

    cypher = _cypher_files()
    for filename, content in cypher.items():
        (output_dir / filename).write_text(content, encoding="utf-8", newline="\n")
    manifest["cypher_files"] = sorted(cypher)
    files = sorted(path for path in output_dir.iterdir() if path.is_file())
    manifest["file_hashes"] = {path.name: {"sha256": _sha256(path), "bytes": path.stat().st_size} for path in files}
    manifest["limitations"] = [
        "EVENT_INSTANCE_CSV_IS_A_DETERMINISTIC_SAMPLE", "GRAPHML_RETAINS_FULL_INSTANCE_GRAPH",
        "IMPORT_NOT_EXECUTED_AGAINST_EXTERNAL_NEO4J", "ALL_IDENTIFIERS_ARE_PUBLIC_ANONYMOUS_KEYS",
    ]
    return manifest


def _cypher_files() -> dict[str, str]:
    constraints = """// JourneyGraph constraints — run before import
CREATE CONSTRAINT account_key IF NOT EXISTS FOR (n:Account) REQUIRE n.account_key IS UNIQUE;
CREATE CONSTRAINT journey_key IF NOT EXISTS FOR (n:Journey) REQUIRE n.journey_key IS UNIQUE;
CREATE CONSTRAINT event_instance_key IF NOT EXISTS FOR (n:EventInstance) REQUIRE n.event_instance_key IS UNIQUE;
CREATE CONSTRAINT pattern_key IF NOT EXISTS FOR (n:Pattern) REQUIRE n.pattern_key IS UNIQUE;
CREATE CONSTRAINT quality_profile_key IF NOT EXISTS FOR (n:QualityProfile) REQUIRE n.quality_profile_key IS UNIQUE;
CREATE CONSTRAINT finding_id IF NOT EXISTS FOR (n:Finding) REQUIRE n.finding_id IS UNIQUE;
"""
    indexes = """// JourneyGraph analytical indexes
CREATE INDEX event_type_name IF NOT EXISTS FOR (n:EventType) ON (n.event_type);
CREATE INDEX pattern_stability IF NOT EXISTS FOR (n:Pattern) ON (n.stability_status);
CREATE INDEX pattern_scope IF NOT EXISTS FOR (n:Pattern) ON (n.journey_scope);
CREATE INDEX journey_scope IF NOT EXISTS FOR (n:Journey) ON (n.journey_scope);
CREATE INDEX taxonomy_name IF NOT EXISTS FOR (n:Taxonomy) ON (n.name);
"""
    imports = """// Offline import example. Adjust paths for the Neo4j import directory.
// neo4j-admin database import full journeygraph --nodes=nodes_account.csv --nodes=nodes_journey.csv --nodes=nodes_event_instance.csv --nodes=nodes_event_type.csv --nodes=nodes_pattern.csv --nodes=nodes_outcome.csv --nodes=nodes_taxonomy.csv --nodes=nodes_quality_profile.csv --nodes=nodes_finding.csv --nodes=nodes_investigation.csv --relationships=relationships_has_journey.csv --relationships=relationships_has_event.csv --relationships=relationships_of_type.csv --relationships=relationships_next_event.csv --relationships=relationships_classified_as.csv --relationships=relationships_associated_with_outcome.csv --relationships=relationships_has_quality_profile.csv --relationships=relationships_matches_pattern.csv --relationships=relationships_contains_event_type.csv --relationships=relationships_transitions_to.csv --relationships=relationships_supported_by.csv --relationships=relationships_recommends_investigation.csv --overwrite-destination=true
"""
    queries = """// 1. ROBUST transitions by account support
MATCH (a:EventType)-[r:TRANSITIONS_TO]->(b:EventType)
WHERE r.stability_status = 'ROBUST' AND r.is_promotable = true
RETURN a.event_type, b.event_type, r.journey_scope, r.account_support, r.denominator_accounts
ORDER BY r.account_support DESC LIMIT 20;

// 2. SENSITIVE patterns in recurring churn context
MATCH (p:Pattern)-[:ASSOCIATED_WITH|OBSERVED_BEFORE]->(o:Outcome)
WHERE p.stability_status = 'SENSITIVE' AND (o.outcome = 'RECURRING_CHURN' OR p.pattern CONTAINS 'CHURN')
RETURN p.pattern, p.account_support, p.strict_support, p.journey_scope ORDER BY p.account_support DESC LIMIT 20;

// 3. Reactivation journeys with observed use
MATCH (j:Journey)-[:HAS_EVENT]->(e:EventInstance)-[:OF_TYPE]->(t:EventType)
WHERE j.journey_scope = 'BETWEEN_CHURN_AND_REACTIVATION' AND t.event_type = 'FEATURE'
RETURN count(DISTINCT j) AS journeys_with_use;

// 4. Warning-dependent patterns
MATCH (p:Pattern) RETURN p.pattern, p.principal_support, p.strict_support,
       p.principal_support - p.strict_support AS support_gap
ORDER BY support_gap DESC LIMIT 20;

// 5. Churn paths by associated MRR
MATCH (p:Pattern)-[:CONTAINS_EVENT_TYPE]->(t:EventType {event_type:'CHURN'})
RETURN p.pattern, p.associated_mrr, p.mrr_account_count, p.account_support
ORDER BY p.associated_mrr DESC LIMIT 20;

// 6. Taxonomy coverage profiles
MATCH (j:Journey)-[:CLASSIFIED_AS]->(t:Taxonomy)
MATCH (j)-[:HAS_QUALITY_PROFILE]->(q:QualityProfile)
RETURN t.name, q.coverage_band, count(*) AS journeys ORDER BY journeys DESC;

// 7. HIGH-order candidates are intentionally absent from the promoted graph
MATCH (p:Pattern) WHERE p.same_day_dependency = 'HIGH' RETURN count(p) AS must_be_zero;

// 8. Findings recommending data-quality review
MATCH (f:Finding)-[:RECOMMENDS_INVESTIGATION]->(i:Investigation)
WHERE i.investigation_type = 'REVIEW_DATA_QUALITY' RETURN f.finding_id, f.title;

// 9. EventType structural connectivity (not causal importance)
MATCH (a:EventType)-[r:TRANSITIONS_TO]->() RETURN a.event_type, sum(r.account_support) AS weighted_out_degree
ORDER BY weighted_out_degree DESC;

// 10. Pattern families across churn and reactivation contexts
MATCH (p:Pattern) WHERE p.outcome_context CONTAINS 'CHURN' OR p.outcome_context CONTAINS 'REACTIVATION'
RETURN p.pattern_family_key, collect(DISTINCT p.outcome_context) AS contexts, count(*) AS pattern_nodes
ORDER BY pattern_nodes DESC;
"""
    return {"constraints.cypher": constraints, "indexes.cypher": indexes, "import.cypher": imports, "example_queries.cypher": queries}
