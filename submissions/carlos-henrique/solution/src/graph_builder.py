"""Build governed JourneyGraph instance and analytical NetworkX graphs."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable

import networkx as nx
import numpy as np
import pandas as pd

from graph_schema import EVENT_TYPES, INVESTIGATIONS, OUTCOMES, simple_value, stable_key


REDUCED_EVENT_MAP = {
    "ACCOUNT_CREATED": "ACCOUNT", "SUBSCRIPTION_STARTED": "SUBSCRIPTION_START",
    "SUBSCRIPTION_ENDED": "SUBSCRIPTION_END", "FEATURE_USED": "FEATURE",
    "SUPPORT_TICKET_OPENED": "SUPPORT_OPEN", "SUPPORT_TICKET_CLOSED": "SUPPORT_CLOSE",
    "CHURN_RECORDED": "CHURN", "REACTIVATION_RECORDED": "REACTIVATION",
}


@dataclass(frozen=True)
class GraphBuild:
    graph: nx.MultiDiGraph
    accounting: dict[str, Any]


def _add_node(graph: nx.MultiDiGraph, key: str, label: str, **properties: Any) -> None:
    graph.add_node(key, label=label, **{name: simple_value(value) for name, value in properties.items()})


def _add_edge(graph: nx.MultiDiGraph, source: str, target: str, relationship: str, **properties: Any) -> None:
    logical = json.dumps([source, target, relationship, properties], ensure_ascii=False, sort_keys=True, default=str)
    edge_key = stable_key("rel", logical)
    if graph.has_edge(source, target, edge_key):
        raise ValueError(f"Duplicate logical edge: {relationship} {source} {target}")
    graph.add_edge(source, target, key=edge_key, relationship=relationship, **{name: simple_value(value) for name, value in properties.items()})


def _coverage_band(value: float | None) -> str:
    if value is None or pd.isna(value): return "UNKNOWN"
    if value >= .90: return "HIGH_GE_90PCT"
    if value >= .70: return "MEDIUM_70_89PCT"
    return "LOW_LT_70PCT"


def _warning_band(value: float | None) -> str:
    if value is None or pd.isna(value): return "UNKNOWN"
    if value <= .10: return "LOW_LE_10PCT"
    if value <= .30: return "MEDIUM_11_30PCT"
    return "HIGH_GT_30PCT"


def _mrr_band(value: float) -> str:
    if value <= 0: return "ZERO"
    if value < 500: return "LOW_LT_500"
    if value < 2000: return "MID_500_1999"
    return "HIGH_GE_2000"


def _quality_profile(
    graph: nx.MultiDiGraph, *, population: str, stability: str,
    same_day: str, small_sample: bool, warning_ratio: float | None,
    coverage: float | None, confidence: str,
) -> str:
    warning_band = _warning_band(warning_ratio)
    coverage_band = _coverage_band(coverage)
    key = stable_key("quality", population, stability, same_day, small_sample, warning_band, coverage_band, confidence)
    if key not in graph:
        _add_node(
            graph, key, "QualityProfile", quality_profile_key=key, population=population,
            stability_status=stability, same_day_dependency=same_day, small_sample=small_sample,
            warning_dependency_ratio_band=warning_band, coverage_band=coverage_band,
            confidence_level=confidence, limitations_count=int(stability != "ROBUST") + int(same_day != "NONE") + int(small_sample),
        )
    return key


def _contains_contiguous(tokens: list[str], pattern: list[str]) -> bool:
    return any(tokens[index:index + len(pattern)] == pattern for index in range(max(len(tokens) - len(pattern) + 1, 0)))


def _contains_subsequence(tokens: list[str], pattern: list[str]) -> bool:
    iterator = iter(tokens)
    return all(any(token == expected for token in iterator) for expected in pattern)


def pattern_matches(tokens: list[str], pattern: list[str], pattern_type: str) -> bool:
    if pattern_type.startswith("PRE_CHURN_SUFFIX"):
        return len(tokens) >= len(pattern) and tokens[-len(pattern):] == pattern
    if pattern_type.startswith("SEQUENTIAL"):
        return _contains_subsequence(tokens, pattern)
    return _contains_contiguous(tokens, pattern)


def promoted_patterns(
    sequential_artifact: dict[str, Any], ngram_artifact: dict[str, Any],
    pre_churn_artifact: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Normalize and promote only governed Phase 5 pattern candidates."""
    output: list[dict[str, Any]] = []
    rejected = defaultdict(int)

    def eligible(row: dict[str, Any], minimum: int) -> bool:
        if row.get("stability_status") not in {"ROBUST", "SENSITIVE"}:
            rejected["UNSTABLE"] += 1; return False
        if row.get("same_day_dependency", "NONE") == "HIGH":
            rejected["HIGH_ORDER_DEPENDENCY"] += 1; return False
        if bool(row.get("small_sample", False)):
            rejected["SMALL_SAMPLE"] += 1; return False
        if int(row.get("account_support", row.get("churn_support", 0))) < minimum:
            rejected["INSUFFICIENT_SUPPORT"] += 1; return False
        denominator = int(row.get("denominator_accounts", row.get("churn_denominator", 0)))
        if denominator <= 0:
            rejected["INVALID_DENOMINATOR"] += 1; return False
        return True

    for row in sequential_artifact["patterns"]:
        candidate = dict(row)
        candidate["small_sample"] = int(row["denominator_accounts"]) < 20
        if row.get("is_generic"):
            rejected["GENERIC_PATTERN"] += 1; continue
        if not eligible(candidate, 15): continue
        output.append({
            **candidate, "pattern_type": "SEQUENTIAL_CLOSED", "journey_scope": "FULL_OBSERVED_JOURNEY",
            "outcome_context": "ALL_OUTCOMES", "quality_population": "MAIN",
            "exposure_control": "ACCOUNT_SUPPORT_MAX_GAP_5_EVENTS_90_DAYS",
            "source_artifact": "sequential_patterns.json",
        })
    for row in ngram_artifact["patterns"]:
        if not row.get("passes_primary_filter", False):
            rejected["NGRAM_PRIMARY_FILTER"] += 1; continue
        if not eligible(row, 10): continue
        output.append({
            **row, "pattern_type": f"NGRAM_{row['n']}_{row['representation']}",
            "outcome_context": row["outcome"], "exposure_control": "ACCOUNT_SUPPORT_SCOPE_AND_OUTCOME",
            "source_artifact": "ngram_patterns.json",
        })
    for row in pre_churn_artifact["patterns"]:
        candidate = {
            **row, "account_support": row["churn_support"], "denominator_accounts": row["churn_denominator"],
            "relative_support": row["churn_rate"], "small_sample": min(row["churn_denominator"], row["non_churn_denominator"]) < 20,
        }
        if not eligible(candidate, 10): continue
        output.append({
            **candidate, "pattern_type": f"PRE_CHURN_SUFFIX_{row['window_days']}D_L{row['suffix_length']}", "journey_scope": "PRE_FIRST_CHURN",
            "outcome_context": "CHURN_OBSERVED", "quality_population": "MAIN",
            "confidence": row["churn_rate"], "coverage": row["churn_rate"], "lift": row["discriminative_ratio"],
            "leverage": row["absolute_difference"], "discriminative_ratio": row["discriminative_ratio"],
            "principal_support": row["principal_support"], "strict_support": row["strict_support"],
            "exposure_control": row["exposure_control"], "source_artifact": "pre_churn_patterns.json",
        })
    output.sort(key=lambda row: (row["pattern_type"], row["journey_scope"], row["outcome_context"], row["pattern_label"]))
    return output, dict(sorted(rejected.items()))


def enrich_patterns_with_mrr(
    patterns: list[dict[str, Any]], journeys: pd.DataFrame, account_features: pd.DataFrame,
) -> list[dict[str, Any]]:
    main = journeys.loc[journeys["quality_population"].eq("MAIN")].copy()
    main["tokens"] = main["collapsed_sequence"].map(json.loads)
    mrr = account_features.set_index(account_features["account_id"].astype(str))["max_mrr"].fillna(0).astype(float).to_dict()
    enriched = []
    grouped = {scope: frame for scope, frame in main.groupby("journey_scope", sort=False)}
    for row in patterns:
        frame = grouped.get(row["journey_scope"], main.iloc[0:0])
        if row["outcome_context"] not in {"ALL_OUTCOMES", "CHURN_OBSERVED"}:
            frame = frame.loc[frame["outcome"].eq(row["outcome_context"])]
        matched = frame.loc[frame["tokens"].map(lambda tokens: pattern_matches(tokens, row["pattern"], row["pattern_type"]))]
        values = [float(mrr.get(str(account_id), 0.0)) for account_id in matched["account_id"].astype(str).unique()]
        item = dict(row)
        item.update({
            "associated_mrr": float(sum(values)), "median_mrr": float(np.median(values)) if values else None,
            "mean_mrr": float(np.mean(values)) if values else None, "mrr_account_count": len(values),
        })
        enriched.append(item)
    return enriched


def _taxonomy_maps(taxonomy: pd.DataFrame) -> tuple[dict[tuple[str, str], str], dict[tuple[str, str], str]]:
    primary, stability = {}, {}
    for row in taxonomy.itertuples(index=False):
        key = (str(row.account_id), str(row.quality_population))
        primary[key] = str(row.primary_journey_class)
        stability[key] = str(row.stability_status)
    return primary, stability


def build_instance_graph(
    journeys: pd.DataFrame, events: pd.DataFrame, taxonomy: pd.DataFrame,
    account_features: pd.DataFrame, patterns: list[dict[str, Any]], taxonomy_definitions: list[dict[str, Any]],
) -> GraphBuild:
    """Build the full traceability graph without operational identifiers."""
    graph = nx.MultiDiGraph(name="JOURNEY_INSTANCE_GRAPH", graph_mode="INSTANCE", schema_version="6.0.0")
    for event_type in EVENT_TYPES:
        _add_node(graph, f"eventtype_{event_type.lower()}", "EventType", event_type=event_type)
    for outcome in OUTCOMES:
        _add_node(graph, f"outcome_{outcome.lower()}", "Outcome", outcome=outcome, associated_mrr=0.0, median_mrr=0.0, mean_mrr=0.0, mrr_account_count=0)
    for definition in taxonomy_definitions:
        _add_node(graph, f"taxonomy_{definition['taxonomy_id'].lower()}", "Taxonomy", taxonomy_id=definition["taxonomy_id"], name=definition["name"], definition=definition["definition"], associated_mrr=0.0, median_mrr=0.0, mean_mrr=0.0, mrr_account_count=0)

    primary_taxonomy, taxonomy_stability = _taxonomy_maps(taxonomy)
    feature_work = account_features.copy()
    feature_work["account_id"] = feature_work["account_id"].astype(str)
    feature_map = feature_work.set_index("account_id").to_dict("index")
    journey_counts = journeys.groupby(journeys["account_id"].astype(str)).size().to_dict()
    event_counts = events.groupby(events["account_id"].astype(str)).size().to_dict()
    strict_accounts = set(journeys.loc[journeys["quality_population"].eq("STRICT"), "account_id"].astype(str))

    for account_id in sorted(journeys["account_id"].astype(str).unique()):
        feature = feature_map[account_id]
        mrr = float(feature.get("max_mrr", 0) or 0)
        account_key = stable_key("acct", account_id)
        _add_node(
            graph, account_key, "Account", account_key=account_key,
            primary_outcome=str(feature["primary_outcome"]), mrr_band=_mrr_band(mrr), associated_mrr=mrr,
            quality_population="MAIN_AND_STRICT" if account_id in strict_accounts else "MAIN_ONLY",
            quality_coverage_ratio=float(feature.get("quality_coverage_ratio", 0) or 0),
            journey_count=int(journey_counts.get(account_id, 0)), event_count=int(event_counts.get(account_id, 0)),
            taxonomy_class=primary_taxonomy.get((account_id, "MAIN"), "UNCLASSIFIED"), is_anonymized=True,
        )

    pattern_by_scope: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in patterns:
        family = stable_key("patternfamily", row["pattern_label"], row["pattern_type"])
        key = stable_key("pattern", row["pattern_label"], row["pattern_type"], row["journey_scope"], row["outcome_context"], row["quality_population"])
        item = dict(row); item["pattern_key"] = key; item["pattern_family_key"] = family
        pattern_by_scope[row["journey_scope"]].append(item)
        _add_node(graph, key, "Pattern", **_pattern_properties(item))

    events_work = events.copy()
    events_work["account_id"] = events_work["account_id"].astype(str)
    events_work["event_time"] = pd.to_datetime(events_work["event_time"])
    for column in ("event_id", "event_type", "quality_status", "source_table"):
        events_work[column] = events_work[column].astype("object")
    event_groups = {key: frame for key, frame in events_work.groupby("account_id", sort=False)}
    journey_rows = journeys.sort_values(["account_id", "quality_population", "journey_scope"])
    total_instances = 0
    match_edges = 0
    for journey in journey_rows.itertuples(index=False):
        account_id = str(journey.account_id)
        account_key = stable_key("acct", account_id)
        journey_key = stable_key("journey", account_id, journey.journey_scope, journey.quality_population)
        stability = taxonomy_stability.get((account_id, str(journey.quality_population)), "SENSITIVE" if journey.quality_population == "MAIN" else "ROBUST")
        _add_node(
            graph, journey_key, "Journey", journey_key=journey_key, journey_scope=journey.journey_scope,
            quality_population=journey.quality_population, journey_start=pd.Timestamp(journey.journey_start).isoformat(),
            journey_end=pd.Timestamp(journey.journey_end).isoformat(), raw_length=int(journey.raw_length),
            collapsed_length=int(journey.collapsed_length), distinct_event_types=int(journey.distinct_event_types),
            observed_days=int(journey.observed_days), same_day_order_dependency=journey.same_day_order_dependency,
            contains_churn=bool(journey.contains_churn), contains_reactivation=bool(journey.contains_reactivation),
            quality_coverage_ratio=float(journey.quality_coverage_ratio or 0), stability_status=stability,
            journey_length_band=journey.journey_length_band,
        )
        _add_edge(graph, account_key, journey_key, "HAS_JOURNEY", quality_population=journey.quality_population, journey_scope=journey.journey_scope)
        quality_key = _quality_profile(
            graph, population=journey.quality_population, stability=stability,
            same_day=journey.same_day_order_dependency, small_sample=False,
            warning_ratio=0.0 if journey.quality_population == "STRICT" else 1.0 - float(journey.quality_coverage_ratio or 0),
            coverage=float(journey.quality_coverage_ratio or 0), confidence="HIGH" if float(journey.quality_coverage_ratio or 0) >= .9 else "MEDIUM",
        )
        _add_edge(graph, journey_key, quality_key, "HAS_QUALITY_PROFILE")
        tax_name = primary_taxonomy.get((account_id, str(journey.quality_population)))
        if tax_name:
            definition = next(item for item in taxonomy_definitions if item["name"] == tax_name)
            _add_edge(graph, journey_key, f"taxonomy_{definition['taxonomy_id'].lower()}", "CLASSIFIED_AS", classification_source="ACCOUNT_TAXONOMY_PHASE5")
        outcome = str(journey.outcome)
        if outcome in OUTCOMES:
            _add_edge(graph, journey_key, f"outcome_{outcome.lower()}", "ASSOCIATED_WITH_OUTCOME", association="OBSERVED_DESCRIPTIVE")

        frame = event_groups[account_id]
        allowed = {"VALID"} if journey.quality_population == "STRICT" else {"VALID", "VALID_WITH_WARNING"}
        selected = frame.loc[
            frame["quality_status"].isin(allowed)
            & ~frame["is_quarantined"].astype(bool)
            & frame["event_time"].between(pd.Timestamp(journey.journey_start), pd.Timestamp(journey.journey_end), inclusive="both")
        ].sort_values(["event_time", "event_order_on_same_day", "event_id"])
        if len(selected) != int(journey.raw_length):
            raise AssertionError(f"Journey/event reconciliation failed for {journey_key}: {len(selected)} != {journey.raw_length}")
        previous_key: str | None = None
        previous_time: pd.Timestamp | None = None
        for position, event in enumerate(selected.itertuples(index=False), 1):
            event_key = stable_key("event", journey_key, event.event_id)
            reduced = REDUCED_EVENT_MAP[str(event.event_type)]
            endpoint = position in {1, len(selected)} or reduced in {"CHURN", "REACTIVATION"}
            _add_node(
                graph, event_key, "EventInstance", event_instance_key=event_key, event_type=reduced,
                event_time=pd.Timestamp(event.event_time).isoformat(), event_position=position,
                same_day_order=int(event.event_order_on_same_day), quality_status=event.quality_status,
                source_table=event.source_table, journey_scope=journey.journey_scope,
                is_warning=event.quality_status == "VALID_WITH_WARNING", is_endpoint_event=endpoint,
            )
            _add_edge(graph, journey_key, event_key, "HAS_EVENT", event_position=position)
            _add_edge(graph, event_key, f"eventtype_{reduced.lower()}", "OF_TYPE")
            if previous_key is not None and previous_time is not None:
                elapsed = (pd.Timestamp(event.event_time) - previous_time).total_seconds() / 86400
                _add_edge(graph, previous_key, event_key, "NEXT_EVENT", event_position=position - 1, elapsed_days=float(elapsed), same_day=elapsed < 1, journey_scope=journey.journey_scope)
            previous_key, previous_time = event_key, pd.Timestamp(event.event_time)
            total_instances += 1

        tokens = json.loads(journey.collapsed_sequence)
        for pattern in pattern_by_scope.get(str(journey.journey_scope), []):
            if pattern["quality_population"] != journey.quality_population: continue
            if pattern["outcome_context"] not in {"ALL_OUTCOMES", "CHURN_OBSERVED", outcome}: continue
            if pattern_matches(tokens, pattern["pattern"], pattern["pattern_type"]):
                _add_edge(graph, journey_key, pattern["pattern_key"], "MATCHES_PATTERN", match_mode=pattern["pattern_type"], is_promotable=True)
                match_edges += 1
    return GraphBuild(graph, {
        "accounts": sum(data["label"] == "Account" for _, data in graph.nodes(data=True)),
        "journeys": len(journeys), "event_instances": total_instances, "pattern_matches": match_edges,
        "quarantined_events_used": 0, "raw_operational_ids_exposed": 0,
    })


def _pattern_properties(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "pattern_key": row["pattern_key"], "pattern_family_key": row["pattern_family_key"],
        "pattern": row["pattern"], "pattern_type": row["pattern_type"], "pattern_length": len(row["pattern"]),
        "journey_scope": row["journey_scope"], "outcome_context": row["outcome_context"],
        "quality_population": row["quality_population"], "account_support": int(row["account_support"]),
        "denominator_accounts": int(row["denominator_accounts"]), "relative_support": float(row.get("relative_support") or 0),
        "confidence": float(row.get("confidence") or 0), "lift": float(row.get("lift") or 0),
        "coverage": float(row.get("coverage") or 0), "leverage": float(row.get("leverage") or 0),
        "discriminative_ratio": float(row.get("discriminative_ratio") or 0),
        "principal_support": int(row.get("principal_support", row["account_support"])),
        "strict_support": int(row.get("strict_support", 0)), "stability_status": row["stability_status"],
        "same_day_dependency": row.get("same_day_dependency", "NONE"), "small_sample": bool(row.get("small_sample", False)),
        "exposure_control": row.get("exposure_control", "ACCOUNT_SUPPORT"), "is_promotable": True,
        "associated_mrr": float(row.get("associated_mrr", 0)), "median_mrr": float(row.get("median_mrr") or 0),
        "mean_mrr": float(row.get("mean_mrr") or 0), "mrr_account_count": int(row.get("mrr_account_count", 0)),
    }


def _investigation_for_finding(finding: dict[str, Any]) -> str:
    text = " ".join(str(finding.get(key, "")) for key in ("title", "business_relevance", "recommended_investigation")).upper()
    if "QUALIDADE" in text or "QUALITY" in text: return "REVIEW_DATA_QUALITY"
    if "SUPPORT" in text or "SUPORTE" in text: return "REVIEW_SUPPORT_JOURNEY"
    if "REATIVA" in text: return "VALIDATE_REACTIVATION_PATH"
    if "MRR" in text: return "REVIEW_HIGH_MRR_LOW_USAGE"
    if "ADOPTION" in text or "USO" in text: return "INVESTIGATE_PRODUCT_ADOPTION"
    return "VALIDATE_PATTERN_IN_NEW_COHORT"


def _transition_mrr(
    row: dict[str, Any], journeys: pd.DataFrame, account_features: pd.DataFrame,
) -> dict[str, Any]:
    frame = journeys.loc[
        journeys["quality_population"].eq("MAIN") & journeys["journey_scope"].eq(row["journey_scope"])
        & journeys["outcome"].eq(row["outcome"])
    ].copy()
    frame["tokens"] = frame["collapsed_sequence"].map(json.loads)
    matched = frame.loc[frame["tokens"].map(lambda tokens: _contains_contiguous(tokens, [row["source_event"], row["target_event"]]))]
    mrr_map = account_features.set_index(account_features["account_id"].astype(str))["max_mrr"].fillna(0).astype(float).to_dict()
    values = [mrr_map[str(account)] for account in matched["account_id"].astype(str).unique()]
    return {"associated_mrr": float(sum(values)), "median_mrr": float(np.median(values)) if values else 0.0, "mean_mrr": float(np.mean(values)) if values else 0.0, "mrr_account_count": len(values)}


def build_analytical_graph(
    patterns: list[dict[str, Any]], transitions: list[dict[str, Any]], findings: list[dict[str, Any]],
    taxonomy_definitions: list[dict[str, Any]], journeys: pd.DataFrame, account_features: pd.DataFrame,
) -> GraphBuild:
    graph = nx.MultiDiGraph(name="JOURNEY_ANALYTICAL_GRAPH", graph_mode="ANALYTICAL", schema_version="6.0.0")
    for event_type in EVENT_TYPES:
        _add_node(graph, f"eventtype_{event_type.lower()}", "EventType", event_type=event_type)
    for outcome in OUTCOMES:
        accounts = account_features.loc[account_features["primary_outcome"].eq(outcome)]
        values = accounts["max_mrr"].fillna(0).astype(float)
        _add_node(graph, f"outcome_{outcome.lower()}", "Outcome", outcome=outcome, associated_mrr=float(values.sum()), median_mrr=float(values.median()) if len(values) else 0.0, mean_mrr=float(values.mean()) if len(values) else 0.0, mrr_account_count=len(values))
    main_taxonomy = journeys.loc[journeys["quality_population"].eq("MAIN"), ["account_id"]].drop_duplicates()
    for definition in taxonomy_definitions:
        _add_node(graph, f"taxonomy_{definition['taxonomy_id'].lower()}", "Taxonomy", taxonomy_id=definition["taxonomy_id"], name=definition["name"], definition=definition["definition"], associated_mrr=0.0, median_mrr=0.0, mean_mrr=0.0, mrr_account_count=0)
    for investigation in INVESTIGATIONS:
        _add_node(graph, f"investigation_{investigation.lower()}", "Investigation", investigation_type=investigation, is_automatic=False, requires_human_review=True)

    pattern_keys: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for row in patterns:
        family = stable_key("patternfamily", row["pattern_label"], row["pattern_type"])
        key = stable_key("pattern", row["pattern_label"], row["pattern_type"], row["journey_scope"], row["outcome_context"], row["quality_population"])
        item = {**row, "pattern_key": key, "pattern_family_key": family}
        _add_node(graph, key, "Pattern", **_pattern_properties(item))
        pattern_keys[tuple(row["pattern"])].append(key)
        for event_type in sorted(set(row["pattern"])):
            _add_edge(graph, key, f"eventtype_{event_type.lower()}", "CONTAINS_EVENT_TYPE", occurrences_in_pattern=row["pattern"].count(event_type))
        quality_key = _quality_profile(
            graph, population=row["quality_population"], stability=row["stability_status"],
            same_day=row.get("same_day_dependency", "NONE"), small_sample=bool(row.get("small_sample", False)),
            warning_ratio=row.get("warning_dependency_ratio"), coverage=row.get("relative_support"),
            confidence="HIGH" if row["stability_status"] == "ROBUST" else "MEDIUM",
        )
        _add_edge(graph, key, quality_key, "HAS_QUALITY_PROFILE")
        context = row["outcome_context"]
        if context in OUTCOMES:
            _add_edge(graph, key, f"outcome_{context.lower()}", "ASSOCIATED_WITH", association="OBSERVED_DESCRIPTIVE")
        elif context == "CHURN_OBSERVED":
            for outcome in ("SINGLE_CHURN", "RECURRING_CHURN", "REACTIVATED_THEN_CHURNED_AGAIN"):
                _add_edge(graph, key, f"outcome_{outcome.lower()}", "OBSERVED_BEFORE", association="FIXED_WINDOW_DESCRIPTIVE")

    promoted_transitions = 0
    rejected_transitions = defaultdict(int)
    for row in sorted(transitions, key=lambda item: (item["source_event"], item["target_event"], item["journey_scope"], item["outcome"])):
        if row["stability_status"] not in {"ROBUST", "SENSITIVE"}: rejected_transitions["UNSTABLE"] += 1; continue
        if row["same_day_dependency"] == "HIGH": rejected_transitions["HIGH_ORDER_DEPENDENCY"] += 1; continue
        if row["small_sample"]: rejected_transitions["SMALL_SAMPLE"] += 1; continue
        if int(row["account_support"]) < 10 or int(row["denominator_accounts"]) <= 0: rejected_transitions["SUPPORT_OR_DENOMINATOR"] += 1; continue
        mrr = _transition_mrr(row, journeys, account_features)
        _add_edge(
            graph, f"eventtype_{row['source_event'].lower()}", f"eventtype_{row['target_event'].lower()}", "TRANSITIONS_TO",
            journey_scope=row["journey_scope"], outcome=row["outcome"], account_support=int(row["account_support"]),
            transition_count=int(row["transition_count"]), denominator_accounts=int(row["denominator_accounts"]),
            relative_support=float(row["relative_support"]), source_conditional_probability=float(row["source_conditional_probability"]),
            lift=float(row["lift_vs_population"] or 0), principal_support=int(row["principal_support"]), strict_support=int(row["strict_support"]),
            stability_status=row["stability_status"], same_day_dependency=row["same_day_dependency"], small_sample=False,
            is_promotable=True, **mrr,
        )
        promoted_transitions += 1

    for finding in findings:
        finding_key = f"finding_{str(finding['finding_id']).lower()}"
        _add_node(
            graph, finding_key, "Finding", finding_id=finding["finding_id"], title=finding["title"],
            confidence_level=finding["confidence_level"], stability_status=finding["stability_status"],
            business_relevance=finding["business_relevance"], recommended_investigation=finding["recommended_investigation"], is_causal=False,
        )
        for pattern_key in pattern_keys.get(tuple(finding["pattern"]), []):
            _add_edge(graph, pattern_key, finding_key, "SUPPORTED_BY", support=int(finding["account_support"]), denominator=int(finding["sample_size"]))
        investigation = _investigation_for_finding(finding)
        _add_edge(graph, finding_key, f"investigation_{investigation.lower()}", "RECOMMENDS_INVESTIGATION", requires_human_review=True)
    return GraphBuild(graph, {
        "promoted_patterns": len(patterns), "promoted_transitions": promoted_transitions,
        "rejected_transitions": dict(sorted(rejected_transitions.items())), "findings": len(findings),
        "investigations": len(INVESTIGATIONS), "operational_actions": 0,
    })
