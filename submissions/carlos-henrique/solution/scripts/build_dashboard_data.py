"""Build deterministic, privacy-safe JSON data for the Phase 9 demo dashboard."""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import networkx as nx
import pandas as pd


SOLUTION = Path(__file__).resolve().parents[1]
SRC = SOLUTION / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from graph_schema import stable_key  # noqa: E402


OUTPUT_DIR = SOLUTION / "app" / "public" / "data"
CUTOFF = "2024-12-31T19:00:00"
SOURCE_COMMIT = "3e96b07e9f113c15ec2a9635324054c3e7b27b00"
OUTPUT_NAMES = (
    "overview.json",
    "quality.json",
    "journey_samples.json",
    "journey_index.json",
    "graph_nodes.json",
    "graph_edges.json",
    "graph_findings.json",
    "watchlist_summary.json",
    "watchlist_items_demo.json",
    "watchlist_rules.json",
    "experiment_registry.json",
    "experiment_details.json",
    "governance.json",
    "demo_story.json",
    "metadata.json",
)

EXPECTED_INPUT_HASHES = {
    "artifacts/diagnostic_summary.json": "b83795407a369fd5253c3f984ef2e1e12d0a7b5a4abe1bc77cf5db99142815a0",
    "artifacts/temporal_quality_summary.json": "4ae7be9a8616f98410607efb8e919df2876c73445673fe1ff303eec813393bed",
    "artifacts/journey_summary.json": "e97de7722678e42e863b487265468a63ee29d8fd239dd96e145f1a4f84e7116e",
    "artifacts/journey_findings.json": "58f31818ec28049c334190c10c9405a82b7062d34b4cf0185de90b1ed2c02008",
    "artifacts/graph_summary.json": "7b3f4327d0cb304b53c5d132792f3ea79d839ff8071c523c9be661394af8795b",
    "artifacts/graph_findings.json": "ecb52c72df6b5a498feb0b5269c67c3d0bdfd945c0b83c3eac15c36556a7d360",
    "artifacts/watchlist_summary.json": "7da712d65739513bc93c43fe98f08356bc3f286c940b0a07e4392ff23c921721",
    "artifacts/watchlist_rules.json": "fe29b1939ff670510d5cb3ef92e3da67abb55b5bc28aec2cc56459a241dc6e4d",
    "artifacts/watchlist_findings.json": "fbe4aa080104f81847efbd4ad5e015026b3857f656d53f308d4ccbdbc3807e21",
    "artifacts/experiment_lab_summary.json": "f0bb61d09b26f9b70f9428c428b3be79347f79df2980be365f28dfb29419d801",
    "artifacts/experiment_hypotheses.json": "28c76f0ab2409b55fe943a3557045feafe9d2aea2e9b5527ff1f0ac70053dbea",
    "artifacts/experiment_findings.json": "03fe69d64dc442a35221062c25dd4543145f5a0e5b07202c8584c1dc73aed8db",
    "artifacts/experiment_sample_size.json": "3688b105dd6f2b049258bbd997f7e643c2d06aa47a9ad4320cdd72a5a29527d4",
    "artifacts/experiment_guardrails.json": "f6b88dbf5e95acbb0ad2284ad1f53018f3fa5d6175f6b5628dedea5be85833e5",
    "artifacts/experiment_ethics.json": "1853f1adc22d8ddad35818db1ee859a737d0a9b72b97b3d05c3f87e4d67d24c6",
    "artifacts/experiment_balance.json": "d82047c5cfac85419608a3c256e3f15b87329a82372797f8a5f60360d7177688",
    "artifacts/experiment_feasibility.json": "def622141615f84f9b7efdc942b9219de2cd75290bfb9e9f3532c6cc7943217d",
    "data/processed/account_journeys.parquet": "1d9dc6795a92f2389f315503a38263f24713290d2c74eb4e8823e0eb283faeed",
    "data/processed/account_journey_taxonomy.parquet": "87f5d43bc4503e313084790fb25947c44b9f9362b556a2bf1fb9793edc0f348e",
    "data/processed/account_watchlist_summary.parquet": "89f927b65c73db78febcd890be7aec3e65e9f2d288af25e280bcb8cdcc503c2d",
    "data/processed/intervention_watchlist.parquet": "17636089c4ff4ff6a62280a04fb39575cdb27d7b35496ab5c337149cac806361",
    "data/processed/watchlist_evidence.parquet": "c841ce99d7f29a0113ee07f12f9fd127f6ba7ffebaaecf6c8589774e4b502f10",
    "data/processed/experiment_registry.parquet": "87e9900939fcf3e22af2889798b050a70052a7827d8361ea661a6ec9a3b85385",
    "data/processed/experiment_specifications.parquet": "8b04d9c3c845f65a4b553d4b2083ef1bc698549064923301a7fc1943d5230600",
    "data/processed/journey_analytical_graph.graphml": "84e20c30dd2e8674257b1dc737b37f88bccd17c80425bec4b7e58a3c3cbb6775",
}

FORBIDDEN_KEYS = {
    "account_id",
    "account_name",
    "customer_id",
    "email",
    "feedback",
    "source_record_id",
    "subscription_id",
}
FORBIDDEN_PHRASES = {
    "at-risk revenue",
    "saved revenue",
    "guaranteed retention",
    "best action",
    "recommended discount",
    "ai decides",
    "causal driver",
}
RAW_ID_PATTERN = re.compile(r"\b(?:A|S|U)-[0-9a-f]{6,}\b", re.IGNORECASE)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(relative: str) -> dict[str, Any]:
    return json.loads((SOLUTION / relative).read_text(encoding="utf-8"))


def parse_json(value: Any, fallback: Any) -> Any:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return fallback
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value))
    except (json.JSONDecodeError, TypeError):
        return fallback


def clean(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [clean(item) for item in value]
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(clean(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def validate_inputs() -> dict[str, str]:
    observed: dict[str, str] = {}
    for relative, expected in EXPECTED_INPUT_HASHES.items():
        path = SOLUTION / relative
        if not path.is_file():
            raise FileNotFoundError(f"Required Phase 3-8 artifact missing: {relative}")
        actual = sha256(path)
        if actual != expected:
            raise AssertionError(f"Input hash mismatch for {relative}: {actual}")
        observed[relative] = actual
    return observed


def build_overview() -> dict[str, Any]:
    diagnostic = read_json("artifacts/diagnostic_summary.json")
    graph = read_json("artifacts/graph_summary.json")
    watchlist = read_json("artifacts/watchlist_summary.json")
    experiments = read_json("artifacts/experiment_lab_summary.json")
    health = diagnostic["data_health"]
    return {
        "headline": "From fragmented customer events to governed retention intelligence.",
        "cutoff": CUTOFF,
        "metrics": [
            {"label": "Accounts", "value": 500, "context": "Anonymous analytical population"},
            {"label": "Events processed", "value": health["eligible_generated_events"], "context": "Before quality gates"},
            {"label": "Usable events", "value": health["valid_events"] + health["warning_events"], "context": "MAIN population"},
            {"label": "Journeys", "value": graph["instance_graph"]["journeys"], "context": "Across governed scopes"},
            {"label": "Promotable patterns", "value": graph["analytical_graph"]["promoted_patterns"], "context": "ROBUST or SENSITIVE"},
            {"label": "Promotable transitions", "value": graph["analytical_graph"]["promoted_transitions"], "context": "No HIGH dependency"},
            {"label": "Review queues", "value": watchlist["queues"], "context": "Human investigation only"},
            {"label": "Experiment designs", "value": experiments["experiment_count"], "context": "All hypotheses untested"},
            {"label": "Tests approved", "value": 119, "context": "Phase 8 baseline"},
            {"label": "PII exposed", "value": 0, "context": "Dashboard contract"},
            {"label": "Future leakage", "value": 0, "context": "Cutoff-enforced"},
            {"label": "Causal claims", "value": 0, "context": "Descriptive evidence only"},
        ],
        "pipeline": ["Raw Data", "Audited Events", "Customer Journeys", "JourneyGraph", "Human Review", "Experiment Design"],
        "cards": [
            {"title": "Data Quality", "metric": "13,927 usable events", "summary": "Warnings remain visible; quarantined events are excluded from behavioral evidence."},
            {"title": "Journey Intelligence", "metric": "4,221 governed journeys", "summary": "Repeated paths are counted by account and tested across MAIN and STRICT populations."},
            {"title": "Explainable Watchlist", "metric": "7 human-review queues", "summary": "Deterministic rules prioritize investigation without a predictive score."},
            {"title": "Experiment Readiness", "metric": "1 ready for review", "summary": "Seven designs remain pilot-only, underpowered, or not feasible."},
        ],
    }


def build_quality() -> dict[str, Any]:
    diagnostic = read_json("artifacts/diagnostic_summary.json")
    temporal = read_json("artifacts/temporal_quality_summary.json")
    health = diagnostic["data_health"]
    flags = temporal.get("quality_flag_counts", {})
    if isinstance(flags, list):
        anomalies = sorted(flags, key=lambda item: item.get("count", 0), reverse=True)[:8]
    else:
        anomalies = [
            {"flag": key, "count": value}
            for key, value in sorted(flags.items(), key=lambda item: item[1], reverse=True)[:8]
        ]
    return {
        "cutoff": CUTOFF,
        "distribution": [
            {"status": "VALID", "events": health["valid_events"], "behavioral_use": True},
            {"status": "VALID_WITH_WARNING", "events": health["warning_events"], "behavioral_use": True},
            {"status": "QUARANTINED", "events": health["quarantined_events"], "behavioral_use": False},
        ],
        "coverage": {
            "main": round(health["analytical_coverage_ratio"], 6),
            "strict": round(health["strict_coverage_ratio"], 6),
            "warning_share_of_usable": round(health["warning_ratio_among_usable"], 6),
            "quarantine_share": round(health["quarantine_ratio"], 6),
        },
        "quality_backlog": {
            "accounts": 467,
            "label": "467 accounts require one or more data-quality reviews before unrestricted behavioral interpretation.",
        },
        "anomalies": anomalies,
        "subscription_overlap": {
            "episodes": health["episodes"],
            "overlapping_episode_ratio": health["overlapping_episode_ratio"],
            "subscriptions_with_warning": health["subscriptions_with_warning"],
        },
        "reconciliation": {"unexplained_difference": 0},
        "privacy": {"pii_exposed": 0, "future_leakage": 0},
        "tooltips": [
            "A warning can affect one event without invalidating the full journey.",
            "Quarantined events never generate behavioral signals.",
            "STRICT is a sensitivity population using VALID events only.",
            "Low data confidence blocks strong behavioral interpretation.",
        ],
        "limitations": diagnostic["limitations"],
    }


def _account_key_frame(frame: pd.DataFrame) -> pd.DataFrame:
    copy = frame.copy()
    copy["account_key"] = copy["account_id"].astype(str).map(lambda value: stable_key("acct", value))
    return copy


def _timeline(sequence: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for bucket in parse_json(sequence, []):
        for event in bucket.get("events", []):
            rows.append({"date": bucket.get("date"), "event": event.get("event"), "count": int(event.get("count", 1))})
    return rows[:60]


def build_journeys() -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    journeys = _account_key_frame(pd.read_parquet(SOLUTION / "data/processed/account_journeys.parquet"))
    taxonomy = _account_key_frame(pd.read_parquet(SOLUTION / "data/processed/account_journey_taxonomy.parquet"))
    watch = pd.read_parquet(SOLUTION / "data/processed/intervention_watchlist.parquet")
    main = journeys.loc[
        journeys["journey_scope"].eq("FULL_OBSERVED_JOURNEY") & journeys["quality_population"].eq("MAIN")
    ].copy()
    tax = taxonomy.loc[
        taxonomy["journey_scope"].eq("FULL_OBSERVED_JOURNEY") & taxonomy["quality_population"].eq("MAIN"),
        ["account_key", "primary_journey_class", "confidence_level", "stability_status", "limitations"],
    ].copy()
    account_watch = watch.groupby("account_key", sort=True).agg(
        graph_patterns=("graph_pattern_count", "max"),
        data_confidence=("data_confidence", "first"),
        has_overlap=("has_subscription_overlap", "max"),
        rule_group_size=("rule_group_size", "max"),
        usage_30d=("usage_count_30d", "max"),
        pattern_keys=("matched_pattern_keys", "first"),
    ).reset_index()
    candidates = main.merge(tax, on="account_key", how="left", validate="one_to_one").merge(
        account_watch, on="account_key", how="left", validate="one_to_one"
    )
    candidates["graph_patterns"] = candidates["graph_patterns"].fillna(0)
    candidates["rule_group_size"] = candidates["rule_group_size"].fillna(0)

    profiles = {
        "DEMO_A": candidates[
            candidates["outcome"].eq("NO_CHURN_OBSERVED")
            & candidates["primary_journey_class"].eq("HIGH_VALUE_LOW_USAGE")
            & candidates["graph_patterns"].gt(0)
            & candidates["rule_group_size"].ge(10)
        ],
        "DEMO_B": candidates[
            candidates["outcome"].eq("RECURRING_CHURN")
            & candidates["graph_patterns"].gt(0)
            & candidates["rule_group_size"].ge(10)
        ],
        "DEMO_C": candidates[
            candidates["outcome"].eq("REACTIVATED")
            & candidates["graph_patterns"].gt(0)
            & candidates["rule_group_size"].ge(10)
            & candidates["usage_30d"].gt(0)
        ],
    }
    selected: list[tuple[str, pd.Series]] = []
    for profile, group in profiles.items():
        if group.empty:
            raise AssertionError(f"No valid account for {profile}")
        ranked = group.assign(no_overlap=(~group["has_overlap"].fillna(True)).astype(int)).sort_values(
            ["no_overlap", "quality_coverage_ratio", "source_event_count", "account_key"],
            ascending=[False, False, False, True],
        )
        selected.append((profile, ranked.iloc[0]))

    rationales = {
        "DEMO_A": "Low engagement with no observed churn; promoted pattern context is available. Dataset-wide subscription overlap remains visible as a limitation.",
        "DEMO_B": "Recurring churn with sufficient coverage, promoted pattern context, and no subscription-overlap flag.",
        "DEMO_C": "Observed reactivation followed by usage, promoted pattern context, and no subscription-overlap flag.",
    }
    samples: list[dict[str, Any]] = []
    for profile, row in selected:
        pattern_keys = parse_json(row.get("pattern_keys"), [])[:5]
        limits = parse_json(row.get("limitations"), [])
        if bool(row.get("has_overlap")):
            limits.append("SUBSCRIPTION_OVERLAP_REQUIRES_DATA_REVIEW")
        samples.append({
            "profile": profile,
            "account_key": row["account_key"],
            "selection_rationale": rationales[profile],
            "journey_scope": row["journey_scope"],
            "period": {"start": row["journey_start"], "end": row["journey_end"]},
            "outcome": row["outcome"],
            "taxonomy": row["primary_journey_class"],
            "quality": {
                "population": row["quality_population"],
                "coverage": round(float(row["quality_coverage_ratio"]), 4),
                "confidence": row.get("data_confidence") or row.get("confidence_level"),
                "stability": row.get("stability_status"),
                "requires_data_review": bool(row.get("has_overlap")),
            },
            "event_count": int(row["source_event_count"]),
            "distinct_event_types": int(row["distinct_event_types"]),
            "timeline": _timeline(row["time_bucketed_sequence"]),
            "pattern_keys": pattern_keys,
            "pattern_count": int(row["graph_patterns"]),
            "limitations": sorted(set(limits + ["DESCRIPTIVE_EVIDENCE_ONLY", "NO_CAUSAL_CLAIM"])),
            "explanation": {
                "what_was_observed": f"A {row['primary_journey_class']} journey ending in {row['outcome']} was observed before the cutoff.",
                "why_it_appears_here": "This deterministic demo profile satisfies coverage, group-size, and promoted-pattern checks.",
                "evidence": f"{int(row['source_event_count'])} usable events and {int(row['graph_patterns'])} linked promotable patterns.",
                "population": "MAIN with STRICT sensitivity available",
                "denominator": "One selected anonymous account within a 500-account observational population",
                "quality": f"Coverage {float(row['quality_coverage_ratio']):.1%}; data confidence {row.get('data_confidence')}",
                "stability": row.get("stability_status"),
                "limitations": sorted(set(limits + ["DESCRIPTIVE_EVIDENCE_ONLY"])),
                "authorized_next_step": "Human review of the linked journey evidence.",
                "prohibited_interpretation": "Do not infer prediction, causality, or authorization for outreach.",
            },
        })

    outcome_counts = main["outcome"].value_counts().sort_index()
    taxonomy_counts = tax["primary_journey_class"].value_counts().sort_values(ascending=False)
    scope_counts = journeys.groupby(["journey_scope", "quality_population"]).size().reset_index(name="journeys")
    index = {
        "cutoff": CUTOFF,
        "accounts": int(main["account_key"].nunique()),
        "journeys": int(len(journeys)),
        "outcome_distribution": [{"outcome": key, "accounts": int(value)} for key, value in outcome_counts.items()],
        "taxonomy_distribution": [{"taxonomy": key, "accounts": int(value)} for key, value in taxonomy_counts.items()],
        "scope_distribution": scope_counts.to_dict("records"),
        "filters": {
            "outcomes": sorted(main["outcome"].dropna().unique().tolist()),
            "taxonomies": sorted(tax["primary_journey_class"].dropna().unique().tolist()),
            "qualities": sorted(journeys["quality_population"].dropna().unique().tolist()),
            "scopes": sorted(journeys["journey_scope"].dropna().unique().tolist()),
        },
        "limitations": ["Account samples are intentionally bounded.", "Quarantined events are excluded.", "No operational identifier is exported."],
    }
    return {"cutoff": CUTOFF, "samples": samples}, index, [row["account_key"] for _, row in selected]


def _node_record(node_id: str, attrs: dict[str, Any]) -> dict[str, Any]:
    label = str(attrs.get("label", "Unknown"))
    display = attrs.get("event_type") or attrs.get("outcome") or attrs.get("finding_id") or attrs.get("investigation_type")
    if label == "Pattern":
        display = " → ".join(parse_json(attrs.get("pattern"), []))
    if label == "QualityProfile":
        display = f"{attrs.get('stability_status')} · {attrs.get('coverage_band')}"
    return {
        "id": node_id,
        "type": label,
        "label": display or node_id,
        "properties": {key: clean(value) for key, value in attrs.items() if key not in {"label", "account_key"}},
    }


def _edge_record(source: str, target: str, key: Any, attrs: dict[str, Any]) -> dict[str, Any]:
    digest = hashlib.sha256(f"{source}|{target}|{key}|{attrs.get('relationship')}".encode()).hexdigest()[:14]
    return {
        "id": f"edge_{digest}",
        "source": source,
        "target": target,
        "type": attrs.get("relationship", "RELATED_TO"),
        "properties": {key_: clean(value) for key_, value in attrs.items() if key_ != "account_key"},
    }


def _induced_edges(graph: nx.Graph, nodes: set[str], allowed: set[str], limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    edges = graph.edges(keys=True, data=True) if graph.is_multigraph() else ((s, t, 0, d) for s, t, d in graph.edges(data=True))
    for source, target, key, attrs in edges:
        if source in nodes and target in nodes and attrs.get("relationship") in allowed:
            rows.append(_edge_record(source, target, key, attrs))
    rows.sort(key=lambda item: (item["type"], item["source"], item["target"], item["id"]))
    return rows[:limit]


def build_graph() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    graph = nx.read_graphml(SOLUTION / "data/processed/journey_analytical_graph.graphml")
    promoted_patterns = [
        (node, attrs) for node, attrs in graph.nodes(data=True)
        if attrs.get("label") == "Pattern"
        and bool(attrs.get("is_promotable"))
        and not bool(attrs.get("small_sample"))
        and attrs.get("stability_status") in {"ROBUST", "SENSITIVE"}
        and attrs.get("same_day_dependency") != "HIGH"
    ]
    promoted_patterns.sort(key=lambda item: (-int(item[1].get("account_support", 0)), item[0]))
    event_nodes = {node for node, attrs in graph.nodes(data=True) if attrs.get("label") == "EventType"}

    transition_edges: list[dict[str, Any]] = []
    raw_edges = graph.edges(keys=True, data=True) if graph.is_multigraph() else ((s, t, 0, d) for s, t, d in graph.edges(data=True))
    for source, target, key, attrs in raw_edges:
        if attrs.get("relationship") != "TRANSITIONS_TO":
            continue
        if not bool(attrs.get("is_promotable")) or bool(attrs.get("small_sample")):
            continue
        if attrs.get("stability_status") not in {"ROBUST", "SENSITIVE"} or attrs.get("same_day_dependency") == "HIGH":
            continue
        transition_edges.append(_edge_record(source, target, key, attrs))
    transition_edges.sort(key=lambda item: (-int(item["properties"].get("account_support", 0)), item["id"]))
    transition_edges = transition_edges[:35]

    pattern_ids = {node for node, _ in promoted_patterns[:15]}
    pattern_neighbors = set(pattern_ids)
    for node in pattern_ids:
        pattern_neighbors.update(graph.successors(node))
        pattern_neighbors.update(graph.predecessors(node))
    pattern_allowed = {node for node in pattern_neighbors if graph.nodes[node].get("label") in {"Pattern", "EventType", "Outcome"}}
    pattern_allowed = set(sorted(pattern_allowed, key=lambda node: (graph.nodes[node].get("label", ""), node))[:35])

    governance_pattern_ids = {node for node, _ in promoted_patterns[:10]}
    governance_nodes = set(governance_pattern_ids)
    frontier = set(governance_pattern_ids)
    for _ in range(2):
        next_frontier: set[str] = set()
        for node in frontier:
            next_frontier.update(graph.successors(node))
            next_frontier.update(graph.predecessors(node))
        next_frontier = {
            node for node in next_frontier
            if graph.nodes[node].get("label") in {"Pattern", "QualityProfile", "Finding", "Investigation"}
        }
        governance_nodes.update(next_frontier)
        frontier = next_frontier
    governance_nodes = set(sorted(governance_nodes, key=lambda node: (graph.nodes[node].get("label", ""), node))[:35])

    modes = {
        "event-flow": event_nodes,
        "pattern-explorer": pattern_allowed,
        "governance-view": governance_nodes,
    }
    node_payload: dict[str, Any] = {"cutoff": CUTOFF, "modes": {}}
    edge_payload: dict[str, Any] = {"cutoff": CUTOFF, "modes": {}}
    for mode, node_ids in modes.items():
        nodes = [_node_record(node, graph.nodes[node]) for node in sorted(node_ids)]
        if mode == "event-flow":
            edges = [edge for edge in transition_edges if edge["source"] in node_ids and edge["target"] in node_ids]
        elif mode == "pattern-explorer":
            edges = _induced_edges(graph, node_ids, {"CONTAINS_EVENT_TYPE", "ASSOCIATED_WITH", "OBSERVED_BEFORE"}, 80)
        else:
            edges = _induced_edges(graph, node_ids, {"HAS_QUALITY_PROFILE", "SUPPORTED_BY", "RECOMMENDS_INVESTIGATION"}, 80)
        if len(nodes) > 35 or len(edges) > 80:
            raise AssertionError(f"Graph view limit exceeded for {mode}")
        node_payload["modes"][mode] = {"nodes": nodes, "node_count": len(nodes), "truncated": True}
        edge_payload["modes"][mode] = {"edges": edges, "edge_count": len(edges), "truncated": True}

    source_findings = read_json("artifacts/graph_findings.json")["findings"]
    findings = []
    for finding in source_findings:
        findings.append({
            "finding_id": finding.get("finding_id"),
            "source_phase": "PHASE_6_GRAPH",
            "title": finding.get("title"),
            "population": finding.get("population", "MAIN_WITH_STRICT_SENSITIVITY"),
            "denominator": finding.get("denominator") or finding.get("population_denominator"),
            "confidence": finding.get("confidence_level"),
            "stability": finding.get("stability_status"),
            "limitations": finding.get("limitations", ["DESCRIPTIVE_NOT_CAUSAL"]),
            "display_summary": "Existing governed graph finding; inspect support, population, stability, and limitations together.",
        })
    return node_payload, edge_payload, {"cutoff": CUTOFF, "findings": findings}


def _level_rank(value: str) -> int:
    return {"HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(str(value), 0)


def _safe_prohibited_actions(value: Any) -> list[str]:
    labels = {
        "AUTOMATIC_CONTACT": "AUTOMATED_OUTREACH",
        "AUTOMATIC_PLAN_CHANGE": "AUTOMATED_PLAN_CHANGE",
        "AUTOMATIC_DISCOUNT": "AUTOMATED_COMMERCIAL_OFFER",
        "AUTOMATIC_WIN_BACK": "AUTOMATED_REACTIVATION_OUTREACH",
        "CHURN_PREDICTION": "PREDICTIVE_INFERENCE",
        "CAUSAL_ATTRIBUTION": "CAUSAL_ATTRIBUTION",
        "REVENUE_LOSS_INTERPRETATION": "REVENUE_LOSS_ATTRIBUTION",
        "BEHAVIORAL_INTERPRETATION": "UNRESTRICTED_BEHAVIORAL_INTERPRETATION",
    }
    return [labels.get(action, "UNAUTHORIZED_OPERATION") for action in parse_json(value, [])]


def build_watchlist(demo_accounts: list[str]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    summary = pd.read_parquet(SOLUTION / "data/processed/account_watchlist_summary.parquet")



    items = pd.read_parquet(SOLUTION / "data/processed/intervention_watchlist.parquet")
    evidence = pd.read_parquet(SOLUTION / "data/processed/watchlist_evidence.parquet")
    behavior_queues = sorted(queue for queue in items["queue"].unique() if queue != "DATA_QUALITY_REVIEW")
    queues: list[dict[str, Any]] = []
    for queue in sorted(items["queue"].unique()):
        group = items[items["queue"].eq(queue)]
        dedup = group.sort_values(["account_key", "priority"]).drop_duplicates("account_key")
        queues.append({
            "queue": queue,
            "category": "DATA_QUALITY_BACKLOG" if queue == "DATA_QUALITY_REVIEW" else "BEHAVIORAL_INVESTIGATION",
            "items": int(len(group)),
            "unique_accounts": int(group["account_key"].nunique()),
            "associated_mrr": float(dedup["associated_mrr"].sum()),
            "priorities": {key: int(value) for key, value in group["priority"].value_counts().sort_index().items()},
        })
    priority_accounts = summary.groupby("highest_priority")["account_key"].nunique().sort_index()

    evidence_fields = [
        "watchlist_item_key", "what_was_observed", "why_it_was_flagged", "supporting_evidence",
        "temporal_context", "graph_context", "quality_context", "limitations",
        "authorized_next_step", "prohibited_interpretation", "provenance",
    ]
    merged = items.merge(evidence[evidence_fields], on="watchlist_item_key", how="left", validate="one_to_one")
    merged["_priority_rank"] = merged["priority"].map({"P1": 1, "P2": 2, "P3": 3, "P4": 4}).fillna(9)
    merged["_confidence_rank"] = merged["data_confidence"].map(_level_rank)
    required = merged[merged["account_key"].isin(demo_accounts)]
    behavior = merged[merged["queue"].isin(behavior_queues)].sort_values(
        ["_priority_rank", "_confidence_rank", "account_key"], ascending=[True, False, True]
    ).drop_duplicates(["account_key", "queue"]).head(36)
    quality = merged[merged["queue"].eq("DATA_QUALITY_REVIEW")].sort_values(
        ["_priority_rank", "_confidence_rank", "account_key"], ascending=[True, False, True]
    ).drop_duplicates("account_key").head(18)
    demo = pd.concat([required, behavior, quality], ignore_index=True).drop_duplicates("watchlist_item_key").head(60)

    exported: list[dict[str, Any]] = []
    for row in demo.to_dict("records"):
        exported.append({
            "watchlist_item_key": row["watchlist_item_key"],
            "account_key": row["account_key"],
            "queue": row["queue"],
            "category": "DATA_QUALITY_BACKLOG" if row["queue"] == "DATA_QUALITY_REVIEW" else "BEHAVIORAL_INVESTIGATION",
            "priority": row["priority"],
            "evidence_strength": row["evidence_strength"],
            "temporal_urgency": row["temporal_urgency"],
            "materiality": row["materiality"],
            "data_confidence": row["data_confidence"],
            "taxonomy": row["taxonomy_class"],
            "associated_mrr_band": row["mrr_band"],
            "requires_data_review": bool(row["requires_data_review"]),
            "requires_human_review": True,
            "rule": {"id": row["watchlist_rule_id"], "name": row["rule_name"], "version": row["rule_version"]},
            "quality_coverage": round(float(row["quality_coverage_ratio"]), 4),
            "limitation_count": int(row["limitation_count"]),
            "human_owner": row["human_owner"],
            "authorized_investigation": row["authorized_investigation"],
            "prohibited_actions": _safe_prohibited_actions(row["prohibited_actions"]),
            "explanation": {
                "what_was_observed": row.get("what_was_observed"),
                "why_it_appears_here": row.get("why_it_was_flagged"),
                "evidence": parse_json(row.get("supporting_evidence"), {}),
                "population": row["quality_population"],
                "denominator": int(row["rule_group_size"]),
                "quality": row.get("quality_context"),
                "stability": row["stability_status"],
                "limitations": parse_json(row.get("limitations"), []),
                "authorized_next_step": row.get("authorized_next_step"),
                "prohibited_interpretation": row.get("prohibited_interpretation"),
                "provenance": parse_json(row.get("provenance"), []),
            },
        })
    source_rules = read_json("artifacts/watchlist_rules.json")
    return (
        {
            "cutoff": CUTOFF,
            "unique_accounts": int(summary["account_key"].nunique()),
            "items": int(len(items)),
            "queues": queues,
            "priority_by_unique_accounts": [{"priority": key, "accounts": int(value)} for key, value in priority_accounts.items()],
            "data_quality_backlog_accounts": 467,
            "associated_mrr_note": "Associated MRR is not revenue at risk.",
            "human_review_required": True,
        },
        {"cutoff": CUTOFF, "items": exported, "row_count": len(exported), "account_level_data": "BOUNDED_ANONYMOUS_DEMO_SAMPLE"},
        {"cutoff": CUTOFF, "metadata": source_rules["metadata"], "rules": source_rules["rule_executions"]},
    )


def _spec_by_experiment() -> dict[str, dict[str, Any]]:
    frame = pd.read_parquet(SOLUTION / "data/processed/experiment_specifications.parquet")
    output: dict[str, dict[str, Any]] = {}
    for row in frame.to_dict("records"):
        value = parse_json(row["specification_value"], row["specification_value"])
        output.setdefault(row["experiment_id"], {}).setdefault(row["section"], {})[row["specification_key"]] = value
    return output


def build_experiments() -> tuple[dict[str, Any], dict[str, Any]]:
    registry = pd.read_parquet(SOLUTION / "data/processed/experiment_registry.parquet")
    hypotheses = {item["experiment_id"]: item for item in read_json("artifacts/experiment_hypotheses.json")["hypotheses"]}
    samples = read_json("artifacts/experiment_sample_size.json")["scenarios"]
    guardrails = read_json("artifacts/experiment_guardrails.json")["guardrails"]
    ethics = {item["experiment_id"]: item for item in read_json("artifacts/experiment_ethics.json")["assessments"]}
    balance = read_json("artifacts/experiment_balance.json")["checks"]
    feasibility = {item["experiment_id"]: item for item in read_json("artifacts/experiment_feasibility.json")["experiments"]}
    specifications = _spec_by_experiment()
    public_registry: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []
    for row in registry.sort_values("experiment_id").to_dict("records"):
        experiment_id = row["experiment_id"]
        hypothesis = hypotheses[experiment_id]
        public = {
            "experiment_id": experiment_id,
            "name": row["experiment_name"],
            "queue": row["queue"],
            "design": row["design_type"],
            "status": row["status"],
            "eligible_accounts": int(row["eligible_accounts"]),
            "required_sample": int(row["adjusted_required_sample"]),
            "primary_metric": row["primary_metric"],
            "mde": row["minimum_detectable_effect"],
            "power": row["power"],
            "follow_up_days": int(row["follow_up_days"]),
            "contamination_risk": row["contamination_risk"],
            "ethical_risk": row["ethical_risk"],
            "causal_status": "UNTESTED",
        }
        public_registry.append(public)
        scenarios = [item for item in samples if item["experiment_id"] == experiment_id]
        guards = [item for item in guardrails if item["experiment_id"] == experiment_id]
        checks = [item for item in balance if item["experiment_id"] == experiment_id]
        specs = specifications.get(experiment_id, {})
        details.append({
            **public,
            "observation": hypothesis["observation"],
            "hypothesis": hypothesis["mechanism_hypothesis"],
            "candidate_intervention": row["intervention_id"],
            "unit_of_randomization": row["unit_of_randomization"],
            "baseline": row["baseline_value"],
            "sample_gap": max(0, int(row["adjusted_required_sample"]) - int(row["eligible_accounts"])),
            "attrition_scenarios": [item for item in scenarios if item["minimum_detectable_effect"] == row["minimum_detectable_effect"]],
            "simulated_assignment": True,
            "balance_warnings": sum(item["balance_status"] != "PASS" for item in checks),
            "sap": specs.get("SAP", {}),
            "guardrails": guards,
            "stopping_rules": specs.get("STOPPING_RULES", {}).get("items", []),
            "ethics": ethics[experiment_id],
            "governance_gates": feasibility[experiment_id]["gates"],
            "limitations": parse_json(row["limitations"], []),
            "status_message": (
                "Ready for methodological and operational review, not for automatic execution."
                if experiment_id == "EXP006"
                else "Pilot only due to limited historical reactivation sample."
                if experiment_id == "EXP005"
                else "Design constraints remain visible; no experiment has been executed."
            ),
        })
    return {"cutoff": CUTOFF, "experiments": public_registry}, {"cutoff": CUTOFF, "experiments": details}


def build_governance() -> dict[str, Any]:
    groups = [
        {"category": "Data", "range": "D001–D020", "count": 20},
        {"category": "Temporal", "range": "D021–D041", "count": 21},
        {"category": "Survival", "range": "D042–D051", "count": 10},
        {"category": "Journey", "range": "D052–D063", "count": 12},
        {"category": "Graph", "range": "D064–D074", "count": 11},
        {"category": "Watchlist", "range": "D075–D085", "count": 11},
        {"category": "Experimentation", "range": "D086–D097", "count": 12},
    ]
    checks = [
        ("No PII", True), ("No future leakage", True), ("No causal claims", True),
        ("No predictive score", True), ("No automated intervention", True),
        ("Deterministic rules", True), ("Human review", True), ("Reconciled outputs", True),
        ("Versioned rules", True), ("Reproducible pipeline", True),
        ("MAIN / STRICT sensitivity", True), ("Explicit limitations", True),
    ]
    return {
        "cutoff": CUTOFF,
        "checks": [{"label": label, "passed": passed} for label, passed in checks],
        "assumptions": ["Historical observational data only.", "Daily source timestamps can limit within-day ordering.", "Associated MRR is context, not loss or exposure."],
        "warnings": ["Source warnings persist.", "Reactivation evidence is limited.", "Most experiment designs are not yet feasible."],
        "prohibited_operations": ["Customer contact", "Automatic plan change", "Automatic cancellation", "Live experiment execution", "External account-level data transfer"],
        "human_decision_points": ["Resolve data-quality review", "Inspect journey evidence", "Approve experiment design", "Authorize any future operational workflow"],
        "decision_groups": groups,
        "decision_count": 97,
        "limitations": ["Demo is a fixed local snapshot.", "No production observability or authentication.", "No external database or LLM."],
    }


def build_story(demo_accounts: list[str]) -> dict[str, Any]:
    steps = [
        ("The problem", "/", "Fragmented events obscure the customer journey.", "35,586 events processed", "Raw sources require governance before interpretation.", "Historical snapshot only."),
        ("Data quality before prediction", "/quality", "Quality is controlled, not hidden.", "13,927 usable events", "Warnings remain visible and quarantine stays excluded.", "MAIN includes warning-bearing events."),
        ("Reconstruct the journey", "/journeys", "Events become bounded, explainable timelines.", "4,221 journeys", "Anonymous demo accounts show different observed outcomes.", "Account examples are not representative estimates."),
        ("Find recurring paths", "/journeys", "Repeated sequences are counted by account.", "435 promotable patterns", "Support and denominator travel together.", "Same-day ordering is not causal evidence."),
        ("Organize evidence in a graph", "/graph", "A reduced graph connects events, patterns, findings, and reviews.", "43 promotable transitions", "Only governed analytical relationships are rendered.", "Graph relationships are descriptive."),
        ("Build a human-review watchlist", "/watchlist", "Rules prioritize investigation without an individual score.", "7 review queues", "Behavior and data quality remain visually separate.", "Automatic intervention is not allowed."),
        ("Convert observations into testable hypotheses", "/experiments", "The Experiment Lab separates observation from causal testing.", "8 untested designs", "Sample feasibility is shown before promotion.", "No experiment has been executed."),
        ("Preserve governance", "/governance", "Every layer exposes constraints and authorized human decisions.", "97 recorded decisions", "Reproducibility and privacy are product features.", "Demo mode is not a production control plane."),
    ]
    return {
        "duration_minutes": "2–4",
        "demo_accounts": demo_accounts,
        "steps": [
            {"step": index, "title": title, "route": route, "sentence": sentence, "metric": metric, "insight": insight, "limitation": limitation}
            for index, (title, route, sentence, metric, insight, limitation) in enumerate(steps, start=1)
        ],
    }


def validate_payloads(payloads: dict[str, Any]) -> dict[str, Any]:
    if set(payloads) != set(OUTPUT_NAMES):
        raise AssertionError("Dashboard output inventory mismatch")
    serialized = json.dumps(clean(payloads), ensure_ascii=False, sort_keys=True, allow_nan=False)
    lowered = serialized.lower()
    if RAW_ID_PATTERN.search(serialized):
        raise AssertionError("Raw operational identifier found in dashboard data")
    for key in FORBIDDEN_KEYS:
        if f'"{key}"' in lowered:
            raise AssertionError(f"Forbidden key found: {key}")
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lowered:
            raise AssertionError(f"Prohibited language found: {phrase}")
    if "unstable" in json.dumps(payloads["graph_nodes.json"], ensure_ascii=False).lower():
        raise AssertionError("UNSTABLE graph node exported")
    graph_nodes = payloads["graph_nodes.json"]["modes"]
    graph_edges = payloads["graph_edges.json"]["modes"]
    if any(view["node_count"] > 35 for view in graph_nodes.values()):
        raise AssertionError("Graph node limit exceeded")
    if any(view["edge_count"] > 80 for view in graph_edges.values()):
        raise AssertionError("Graph edge limit exceeded")
    if any(item["causal_status"] != "UNTESTED" for item in payloads["experiment_registry.json"]["experiments"]):
        raise AssertionError("Invalid experiment causal status")
    priorities = {item["priority"] for item in payloads["watchlist_items_demo.json"]["items"]}
    if not priorities.issubset({"P1", "P2", "P3", "P4"}):
        raise AssertionError("Invalid watchlist priority")
    return {
        "output_count": len(payloads),
        "pii_fields": 0,
        "raw_operational_ids": 0,
        "prohibited_language": 0,
        "non_finite_values": 0,
        "graph_limits_passed": True,
        "experiment_status_passed": True,
        "watchlist_priority_passed": True,
    }


def build_payloads() -> dict[str, Any]:
    input_hashes = validate_inputs()
    journey_samples, journey_index, demo_accounts = build_journeys()
    graph_nodes, graph_edges, graph_findings = build_graph()
    watchlist_summary, watchlist_items, watchlist_rules = build_watchlist(demo_accounts)
    experiment_registry, experiment_details = build_experiments()
    payloads: dict[str, Any] = {
        "overview.json": build_overview(),
        "quality.json": build_quality(),
        "journey_samples.json": journey_samples,
        "journey_index.json": journey_index,
        "graph_nodes.json": graph_nodes,
        "graph_edges.json": graph_edges,
        "graph_findings.json": graph_findings,
        "watchlist_summary.json": watchlist_summary,
        "watchlist_items_demo.json": watchlist_items,
        "watchlist_rules.json": watchlist_rules,
        "experiment_registry.json": experiment_registry,
        "experiment_details.json": experiment_details,
        "governance.json": build_governance(),
        "demo_story.json": build_story(demo_accounts),
    }
    metadata = {
        "project_name": "JourneyGraph Retention Intelligence",
        "dashboard_version": "9.0.0",
        "data_cutoff": CUTOFF,
        "build_timestamp_policy": "FIXED_TO_DATA_CUTOFF",
        "source_commit": SOURCE_COMMIT,
        "pipeline_phases": list(range(0, 9)),
        "test_count": 119,
        "artifact_hashes": input_hashes,
        "populations": {"accounts": 500, "usable_events": 13927, "journeys": 4221},
        "limitations": ["HISTORICAL_OBSERVATIONAL_DATA", "LOCAL_DEMO_SNAPSHOT", "NO_LIVE_BACKEND", "NO_CAUSAL_CLAIM"],
        "demo_mode": True,
        "external_dependencies": [],
        "pii_status": "NONE_EXPOSED",
        "causal_status": "NO_CAUSAL_CLAIM",
    }
    payloads["metadata.json"] = metadata
    validation = validate_payloads(payloads)
    payloads["metadata.json"]["validation"] = validation
    return clean(payloads)


def run(output_dir: Path = OUTPUT_DIR) -> dict[str, Any]:
    payloads = build_payloads()
    for name in OUTPUT_NAMES:
        write_json(output_dir / name, payloads[name])
    hashes = {name: sha256(output_dir / name) for name in OUTPUT_NAMES}
    return {
        "cutoff": CUTOFF,
        "demo_accounts": payloads["demo_story.json"]["demo_accounts"],
        "output_count": len(hashes),
        "output_hashes": hashes,
        "validation": payloads["metadata.json"]["validation"],
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
