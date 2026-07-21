"""Run the deterministic governed Phase 6 JourneyGraph pipeline."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd


SOLUTION_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = SOLUTION_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from graph_analysis import (  # noqa: E402
    build_subgraphs, centrality_metrics, execute_queries, graph_findings,
    path_analysis, structural_metrics,
)
from graph_builder import (  # noqa: E402
    build_analytical_graph, build_instance_graph, enrich_patterns_with_mrr,
    promoted_patterns,
)
from graph_reporting import generate_figures, render_reports, write_json  # noqa: E402
from graph_schema import graph_schema_artifact  # noqa: E402
from graph_validation import validate_all  # noqa: E402
from neo4j_export import export_neo4j  # noqa: E402


PROCESSED = SOLUTION_ROOT / "data" / "processed"
ARTIFACTS = SOLUTION_ROOT / "artifacts"
REPORTS = SOLUTION_ROOT / "reports"
FIGURES = REPORTS / "figures"
NEO4J = SOLUTION_ROOT / "graph" / "neo4j"
EXPECTED_BASE_COMMIT = "990c6fd6778d8a7b329e5ab70ccad841d0fd3327"
EXPECTED_HASHES = {
    "data/processed/account_journeys.parquet": "1d9dc6795a92f2389f315503a38263f24713290d2c74eb4e8823e0eb283faeed",
    "data/processed/account_journey_taxonomy.parquet": "87f5d43bc4503e313084790fb25947c44b9f9362b556a2bf1fb9793edc0f348e",
    "artifacts/sequential_patterns.json": "ac86a7dfa999061b7f06ff0da97292d7558c1df665057e45e17190dcba180390",
    "artifacts/transition_matrix.json": "64d941d3b20a4532977043c90e69ff9de70ba22e86555881a612fd023ef346ce",
    "artifacts/journey_findings.json": "58f31818ec28049c334190c10c9405a82b7062d34b4cf0185de90b1ed2c02008",
}
ARTIFACT_NAMES = (
    "graph_summary.json", "graph_schema.json", "graph_reconciliation.json",
    "graph_metrics.json", "graph_centrality.json", "graph_paths.json",
    "graph_queries.json", "graph_quality.json", "graph_findings.json",
    "neo4j_export_manifest.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(name: str) -> dict[str, Any]:
    return json.loads((ARTIFACTS / name).read_text(encoding="utf-8"))


def validate_inputs() -> dict[str, Any]:
    verified = {}
    for relative, expected in EXPECTED_HASHES.items():
        path = SOLUTION_ROOT / relative
        verified[relative] = path.is_file() and sha256(path) == expected
    event_manifest = load_json("event_log_manifest.json")
    event_path = PROCESSED / "event_log.parquet"
    verified["data/processed/event_log.parquet"] = event_path.is_file() and sha256(event_path) == event_manifest["output_hashes"]["data/processed/event_log.parquet"]["sha256"]
    required = (
        PROCESSED / "account_diagnostic_features.parquet", ARTIFACTS / "ngram_patterns.json",
        ARTIFACTS / "pre_churn_patterns.json", ARTIFACTS / "journey_taxonomy.json",
        ARTIFACTS / "journey_stability.json", ARTIFACTS / "sensitivity_analysis.json",
        ARTIFACTS / "survival_sensitivity.json",
    )
    for path in required:
        verified[str(path.relative_to(SOLUTION_ROOT)).replace("\\", "/")] = path.is_file()
    if not all(verified.values()):
        raise RuntimeError(f"Phase 6 input gate failed: {[key for key, value in verified.items() if not value]}")
    return {
        "expected_base_commit": EXPECTED_BASE_COMMIT, "verified_inputs": len(verified),
        "all_hashes_match": True, "reconciliation_unexplained_difference_phase2": event_manifest["reconciliation_unexplained_difference"],
        "input_hashes": {relative: sha256(SOLUTION_ROOT / relative) for relative in EXPECTED_HASHES},
    }


def _transition_rows(graph: nx.MultiDiGraph) -> list[dict[str, Any]]:
    rows = []
    for source, target, data in graph.edges(data=True):
        if data["relationship"] != "TRANSITIONS_TO": continue
        rows.append({
            "source_event": graph.nodes[source]["event_type"], "target_event": graph.nodes[target]["event_type"],
            **{key: value for key, value in data.items() if key != "relationship"},
        })
    return sorted(rows, key=lambda row: (-int(row["account_support"]), row["source_event"], row["target_event"], row["journey_scope"]))


def _quality_artifact(
    analytical: nx.MultiDiGraph, pattern_rejections: dict[str, int],
    transition_rejections: dict[str, int], candidate_counts: dict[str, int],
) -> dict[str, Any]:
    profiles = [data for _, data in analytical.nodes(data=True) if data["label"] == "QualityProfile"]
    pattern_stability = Counter(data["stability_status"] for _, data in analytical.nodes(data=True) if data["label"] == "Pattern")
    combined = Counter(pattern_rejections); combined.update(transition_rejections)
    return {
        "populations": ["MAIN", "STRICT", "MAIN_WITH_STRICT_SENSITIVITY"],
        "quality_profile_count": len(profiles), "quality_profiles": profiles,
        "promoted_pattern_stability": dict(sorted(pattern_stability.items())),
        "rejected_candidates": dict(sorted(combined.items())), "candidate_counts": candidate_counts,
        "promotion_policy": ["ROBUST_OR_SENSITIVE", "MINIMUM_SUPPORT", "VALID_DENOMINATOR", "NOT_SMALL_SAMPLE", "SAME_DAY_NOT_HIGH"],
        "limitations": ["WARNING_DEPENDENCY_PRESERVED", "STRICT_REACTIVATION_COVERAGE_LIMITED", "TECHNICAL_SAME_DAY_ORDER_NOT_CAUSAL"],
    }


def _validate_public_artifacts(payloads: dict[str, Any]) -> None:
    text = json.dumps(payloads, ensure_ascii=False).lower()
    for forbidden in (
        '"account_id":', '"account_name":', '"email":', '"feedback_text":',
        '"source_event_id":', '"revenue_lost":', '"revenue_saved":',
        '"preventable_revenue":',
    ):
        if forbidden in text:
            raise AssertionError(f"Forbidden public artifact content: {forbidden}")


def main() -> None:
    input_gate = validate_inputs()
    journeys = pd.read_parquet(PROCESSED / "account_journeys.parquet")
    taxonomy = pd.read_parquet(PROCESSED / "account_journey_taxonomy.parquet")
    events = pd.read_parquet(PROCESSED / "event_log.parquet")
    accounts = pd.read_parquet(PROCESSED / "account_diagnostic_features.parquet")
    sequential = load_json("sequential_patterns.json")
    ngrams = load_json("ngram_patterns.json")
    pre_churn = load_json("pre_churn_patterns.json")
    transitions = load_json("transition_matrix.json")["transitions"]
    phase5_findings = load_json("journey_findings.json")["findings"]
    taxonomy_artifact = load_json("journey_taxonomy.json")

    patterns, pattern_rejections = promoted_patterns(sequential, ngrams, pre_churn)
    patterns = enrich_patterns_with_mrr(patterns, journeys, accounts)
    instance_build = build_instance_graph(journeys, events, taxonomy, accounts, patterns, taxonomy_artifact["definitions"])
    analytical_build = build_analytical_graph(patterns, transitions, phase5_findings, taxonomy_artifact["definitions"], journeys, accounts)
    instance, analytical = instance_build.graph, analytical_build.graph

    validation = validate_all(
        instance, analytical, accounts["account_id"].astype(str), journeys, taxonomy, accounts,
        len(patterns), analytical_build.accounting["promoted_transitions"], len(phase5_findings),
    )
    instance_metrics = structural_metrics(instance)
    analytical_metrics = structural_metrics(analytical)
    centrality = centrality_metrics(analytical)
    paths = path_analysis(analytical)
    subgraphs = build_subgraphs(analytical)
    all_pattern_candidates = list(sequential["patterns"]) + list(ngrams["patterns"]) + list(pre_churn["patterns"])
    queries = execute_queries(analytical, instance, centrality, paths, transitions, all_pattern_candidates, taxonomy)
    findings = graph_findings(queries, centrality, paths)

    PROCESSED.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(instance, PROCESSED / "journey_instance_graph.graphml", named_key_ids=True)
    nx.write_graphml(analytical, PROCESSED / "journey_analytical_graph.graphml", named_key_ids=True)
    neo4j_manifest = export_neo4j(instance, analytical, NEO4J, event_journey_sample_size=250)

    metrics = {
        "instance_graph": instance_metrics, "analytical_graph": analytical_metrics,
        "subgraphs": {name: {"nodes": graph.number_of_nodes(), "edges": graph.number_of_edges()} for name, graph in subgraphs.items()},
    }
    quality = _quality_artifact(
        analytical, pattern_rejections, analytical_build.accounting["rejected_transitions"],
        {"sequential": len(sequential["patterns"]), "ngram": len(ngrams["patterns"]), "pre_churn": len(pre_churn["patterns"]), "transition": len(transitions)},
    )
    schema = graph_schema_artifact()
    observation_end = pd.Timestamp(events["event_time"].max()).isoformat()
    summary = {
        "schema_version": "6.0.0", "generation_timestamp": observation_end,
        "generation_timestamp_basis": "event_log_observation_end", "gate_result": "PASS_WITH_WARNINGS",
        "implementation": "NETWORKX_REFERENCE_WITH_OPTIONAL_NEO4J_EXPORT",
        "instance_graph": instance_build.accounting, "analytical_graph": analytical_build.accounting,
        "graphml": {
            "journey_instance_graph.graphml": {"sha256": sha256(PROCESSED / "journey_instance_graph.graphml"), "bytes": (PROCESSED / "journey_instance_graph.graphml").stat().st_size},
            "journey_analytical_graph.graphml": {"sha256": sha256(PROCESSED / "journey_analytical_graph.graphml"), "bytes": (PROCESSED / "journey_analytical_graph.graphml").stat().st_size},
        },
        "dependencies": {name: importlib.metadata.version(name) for name in ("pandas", "numpy", "networkx", "matplotlib", "pyarrow", "pytest")},
        "input_validation": input_gate, "difference_unexplained": 0,
        "limitations": ["SOURCE_WARNINGS_PERSIST", "CENTRALITY_STRUCTURAL_NOT_CAUSAL", "EVENT_INSTANCE_CSV_SAMPLED", "NEO4J_NOT_EXECUTED_EXTERNALLY"],
    }
    payloads = {
        "graph_summary.json": summary, "graph_schema.json": schema,
        "graph_reconciliation.json": validation["reconciliation"], "graph_metrics.json": metrics,
        "graph_centrality.json": centrality, "graph_paths.json": paths,
        "graph_queries.json": {"query_count": len(queries), "networkx_queries": queries, "cypher_equivalent_file": "graph/neo4j/example_queries.cypher"},
        "graph_quality.json": quality, "graph_findings.json": {"maximum_findings": 7, "finding_count": len(findings), "findings": findings},
        "neo4j_export_manifest.json": neo4j_manifest,
    }
    _validate_public_artifacts(payloads)
    for name in ARTIFACT_NAMES:
        write_json(ARTIFACTS / name, payloads[name])

    transition_rows = _transition_rows(analytical)
    taxonomy_counts = taxonomy.loc[taxonomy["quality_population"].eq("MAIN"), "primary_journey_class"].value_counts().sort_index().to_dict()
    context = {
        "summary": summary, "metrics": metrics, "validation": validation, "paths": paths,
        "findings": findings, "queries": queries, "neo4j": neo4j_manifest, "schema": schema,
        "top_transitions": transition_rows, "quality_counts": quality["promoted_pattern_stability"],
        "rejected_counts": quality["rejected_candidates"], "taxonomy_counts": taxonomy_counts,
    }
    render_reports(REPORTS, context)
    generate_figures(FIGURES, context)
    print(json.dumps({
        "gate": summary["gate_result"], "instance_nodes": instance.number_of_nodes(),
        "instance_edges": instance.number_of_edges(), "analytical_nodes": analytical.number_of_nodes(),
        "analytical_edges": analytical.number_of_edges(), "patterns": len(patterns),
        "transitions": analytical_build.accounting["promoted_transitions"], "findings": len(findings),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
