"""Structural JourneyGraph metrics, paths, subgraphs, queries, and findings."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from typing import Any, Iterable

import networkx as nx
import numpy as np
import pandas as pd


def _node_counts(graph: nx.MultiDiGraph) -> dict[str, int]:
    return dict(sorted(Counter(data["label"] for _, data in graph.nodes(data=True)).items()))


def _edge_counts(graph: nx.MultiDiGraph) -> dict[str, int]:
    return dict(sorted(Counter(data["relationship"] for *_, data in graph.edges(data=True, keys=True)).items()))


def structural_metrics(graph: nx.MultiDiGraph) -> dict[str, Any]:
    undirected = graph.to_undirected()
    journey_lengths = [int(data["raw_length"]) for _, data in graph.nodes(data=True) if data["label"] == "Journey"]
    return {
        "graph_name": graph.graph.get("name"), "graph_mode": graph.graph.get("graph_mode"),
        "node_count": graph.number_of_nodes(), "edge_count": graph.number_of_edges(),
        "nodes_by_type": _node_counts(graph), "edges_by_type": _edge_counts(graph),
        "weakly_connected_components": nx.number_weakly_connected_components(graph) if graph.number_of_nodes() else 0,
        "average_degree": float(sum(dict(graph.degree()).values()) / graph.number_of_nodes()) if graph.number_of_nodes() else 0.0,
        "density": float(nx.density(graph)),
        "average_journey_raw_length": float(np.mean(journey_lengths)) if journey_lengths else None,
        "journey_event_distribution": {
            "n": len(journey_lengths), "min": min(journey_lengths) if journey_lengths else None,
            "median": float(np.median(journey_lengths)) if journey_lengths else None,
            "mean": float(np.mean(journey_lengths)) if journey_lengths else None,
            "p90": float(np.quantile(journey_lengths, .9)) if journey_lengths else None,
            "max": max(journey_lengths) if journey_lengths else None,
        },
        "interpretation": "Structural graph properties only; degree and density do not imply causal importance.",
    }


def _event_transition_graph(graph: nx.MultiDiGraph, weight: str) -> nx.DiGraph:
    result = nx.DiGraph()
    for node, data in graph.nodes(data=True):
        if data["label"] == "EventType": result.add_node(node, event_type=data["event_type"])
    for source, target, data in graph.edges(data=True):
        if data["relationship"] != "TRANSITIONS_TO": continue
        value = float(data.get(weight, 0) or 0)
        if result.has_edge(source, target): result[source][target]["weight"] += value
        else: result.add_edge(source, target, weight=value)
    return result


def centrality_metrics(graph: nx.MultiDiGraph) -> dict[str, Any]:
    by_weight: dict[str, list[dict[str, Any]]] = {}
    top_sets: dict[str, set[str]] = {}
    for weight in ("account_support", "relative_support", "transition_count"):
        projected = _event_transition_graph(graph, weight)
        if not projected.edges:
            by_weight[weight] = []; top_sets[weight] = set(); continue
        pagerank = nx.pagerank(projected, weight="weight")
        weighted_degree = dict(projected.degree(weight="weight"))
        inverse = nx.DiGraph()
        inverse.add_nodes_from(projected.nodes(data=True))
        inverse.add_edges_from((u, v, {"distance": 1 / max(float(d["weight"]), 1e-12)}) for u, v, d in projected.edges(data=True))
        betweenness = nx.betweenness_centrality(inverse, weight="distance", normalized=True)
        rows = []
        for node in projected.nodes:
            rows.append({
                "event_type": projected.nodes[node]["event_type"], "weight_definition": weight,
                "weighted_degree": float(weighted_degree[node]), "in_degree": float(projected.in_degree(node, weight="weight")),
                "out_degree": float(projected.out_degree(node, weight="weight")), "pagerank": float(pagerank[node]),
                "betweenness": float(betweenness[node]),
            })
        rows.sort(key=lambda row: (-row["pagerank"], row["event_type"]))
        for rank, row in enumerate(rows, 1): row["pagerank_rank"] = rank
        by_weight[weight] = rows
        top_sets[weight] = {row["event_type"] for row in rows[:3]}
    weight_names = list(top_sets)
    overlaps = []
    for index, left in enumerate(weight_names):
        for right in weight_names[index + 1:]:
            union = top_sets[left] | top_sets[right]
            overlaps.append({"left": left, "right": right, "top3_jaccard": len(top_sets[left] & top_sets[right]) / len(union) if union else 1.0})
    stable = bool(overlaps) and min(item["top3_jaccard"] for item in overlaps) >= .5
    pattern_rows = []
    for _, data in graph.nodes(data=True):
        if data["label"] != "Pattern": continue
        pattern_rows.append({
            "pattern": data["pattern"], "pattern_type": data["pattern_type"], "journey_scope": data["journey_scope"],
            "account_support": int(data["account_support"]), "associated_mrr": float(data["associated_mrr"]),
            "stability_status": data["stability_status"],
        })
    pattern_rows.sort(key=lambda row: (-row["account_support"], row["pattern"]))
    return {
        "event_type_by_weight": by_weight, "weight_sensitivity": overlaps,
        "event_type_ranking_stable": stable, "pattern_support_ranking": pattern_rows[:50],
        "limitations": ["CENTRALITY_IS_STRUCTURAL_NOT_CAUSAL", "NO_ACCOUNT_CENTRALITY_COMPUTED", "PARALLEL_TRANSITIONS_AGGREGATED_BY_WEIGHT"],
    }


def path_analysis(graph: nx.MultiDiGraph, minimum_support: int = 10, maximum_length: int = 6) -> dict[str, Any]:
    rows = []
    for _, data in graph.nodes(data=True):
        if data["label"] != "Pattern": continue
        pattern = json.loads(data["pattern"]) if isinstance(data["pattern"], str) else list(data["pattern"])
        if len(pattern) > maximum_length or int(data["account_support"]) < minimum_support: continue
        row = {
            "pattern": pattern, "pattern_label": " -> ".join(pattern), "pattern_type": data["pattern_type"],
            "journey_scope": data["journey_scope"], "outcome_context": data["outcome_context"],
            "account_support": int(data["account_support"]), "denominator_accounts": int(data["denominator_accounts"]),
            "relative_support": float(data["relative_support"]), "associated_mrr": float(data["associated_mrr"]),
            "mrr_account_count": int(data["mrr_account_count"]), "stability_status": data["stability_status"],
        }
        rows.append(row)
    def top(predicate: Any, key: str = "account_support") -> list[dict[str, Any]]:
        selected = [row for row in rows if predicate(row)]
        return sorted(selected, key=lambda row: (-float(row[key]), -row["account_support"], row["pattern_label"]))[:20]
    return {
        "parameters": {"minimum_support_accounts": minimum_support, "maximum_pattern_length": maximum_length, "promotable_only": True},
        "ending_in_churn": top(lambda row: row["pattern"][-1] == "CHURN"),
        "containing_reactivation": top(lambda row: "REACTIVATION" in row["pattern"]),
        "support_open_to_churn": top(lambda row: "SUPPORT_OPEN" in row["pattern"] and row["pattern"][-1] == "CHURN"),
        "churn_to_reactivation": top(lambda row: "CHURN" in row["pattern"] and "REACTIVATION" in row["pattern"] and row["pattern"].index("CHURN") < row["pattern"].index("REACTIVATION")),
        "recurring_churn": top(lambda row: row["outcome_context"] == "RECURRING_CHURN" or row["pattern"].count("CHURN") >= 2),
        "robust": top(lambda row: row["stability_status"] == "ROBUST"),
        "sensitive": top(lambda row: row["stability_status"] == "SENSITIVE"),
        "high_associated_mrr": top(lambda row: row["mrr_account_count"] >= 10, key="associated_mrr"),
        "limitations": ["PATHS_ARE_OBSERVED_ASSOCIATIONS", "MRR_IS_ASSOCIATED_NOT_LOST_OR_SAVED", "MAXIMUM_LENGTH_6"],
    }


def build_subgraphs(graph: nx.MultiDiGraph) -> dict[str, nx.MultiDiGraph]:
    def expand(seed: set[str]) -> nx.MultiDiGraph:
        nodes = set(seed)
        for node in list(seed):
            nodes.update(graph.predecessors(node)); nodes.update(graph.successors(node))
        return graph.subgraph(sorted(nodes)).copy()
    patterns = {node for node, data in graph.nodes(data=True) if data["label"] == "Pattern"}
    robust = {node for node in patterns if graph.nodes[node]["stability_status"] == "ROBUST"}
    churn = {node for node in patterns if "CHURN" in graph.nodes[node]["pattern"] or "CHURN" in graph.nodes[node]["outcome_context"]}
    reactivation = {node for node in patterns if "REACTIVATION" in graph.nodes[node]["pattern"] or "REACTIVATION" in graph.nodes[node]["outcome_context"]}
    quality = {node for node, data in graph.nodes(data=True) if data["label"] == "QualityProfile" and (data["stability_status"] != "ROBUST" or data["same_day_dependency"] != "NONE")}
    mrr_values = [float(graph.nodes[node]["associated_mrr"]) for node in patterns]
    threshold = float(np.quantile(mrr_values, .75)) if mrr_values else 0
    high_mrr = {node for node in patterns if float(graph.nodes[node]["associated_mrr"]) >= threshold and int(graph.nodes[node]["mrr_account_count"]) >= 10}
    return {
        "ROBUST_GRAPH": expand(robust), "PROMOTABLE_GRAPH": graph.copy(),
        "CHURN_GRAPH": expand(churn), "REACTIVATION_GRAPH": expand(reactivation),
        "QUALITY_REVIEW_GRAPH": expand(quality), "HIGH_MRR_GRAPH": expand(high_mrr),
    }


def _query(
    query_id: str, definition: str, filters: list[str], result: Any,
    denominator: Any, interpretation: str, limitation: str,
) -> dict[str, Any]:
    return {"query_id": query_id, "definition": definition, "filters": filters, "result": result, "denominator": denominator, "interpretation": interpretation, "limitation": limitation}


def execute_queries(
    analytical_graph: nx.MultiDiGraph, instance_graph: nx.MultiDiGraph,
    centrality: dict[str, Any], paths: dict[str, Any], all_transitions: list[dict[str, Any]],
    all_patterns: Iterable[dict[str, Any]], taxonomy: pd.DataFrame,
) -> list[dict[str, Any]]:
    transition_edges = [data for *_, data in analytical_graph.edges(data=True, keys=True) if data["relationship"] == "TRANSITIONS_TO"]
    pattern_nodes = [data for _, data in analytical_graph.nodes(data=True) if data["label"] == "Pattern"]
    finding_nodes = [data for _, data in analytical_graph.nodes(data=True) if data["label"] == "Finding"]
    robust_transitions = sorted([row for row in transition_edges if row["stability_status"] == "ROBUST"], key=lambda row: -int(row["account_support"]))[:10]
    sensitive_recurring = sorted([row for row in pattern_nodes if row["stability_status"] == "SENSITIVE" and ("RECURRING_CHURN" in row["outcome_context"] or "CHURN" in row["pattern"])], key=lambda row: -int(row["account_support"]))[:10]
    reactivation_journeys = [data for _, data in instance_graph.nodes(data=True) if data["label"] == "Journey" and data["journey_scope"] == "BETWEEN_CHURN_AND_REACTIVATION"]
    support_gap = sorted(pattern_nodes, key=lambda row: (-(int(row["principal_support"]) - int(row["strict_support"])), row["pattern"]))[:10]
    coverage = taxonomy.groupby("primary_journey_class")["confidence_level"].agg(total="size", low=lambda s: int((s == "LOW").sum())).reset_index()
    coverage["low_confidence_ratio"] = coverage["low"] / coverage["total"]
    paths = dict(paths)
    paths["high_associated_mrr"] = sorted(
        [row for row in paths["ending_in_churn"] if row["mrr_account_count"] >= 10],
        key=lambda row: (-float(row["associated_mrr"]), -int(row["account_support"]), row["pattern_label"]),
    )[:20]
    high_rejected = [row for row in all_transitions if row.get("same_day_dependency") == "HIGH"]
    high_rejected += [row for row in all_patterns if row.get("same_day_dependency") == "HIGH"]
    quality_findings = [row for row in finding_nodes if "QUALIDADE" in (row["title"] + row["recommended_investigation"]).upper()]
    central = centrality["event_type_by_weight"]["account_support"][:8]
    pattern_outcomes: dict[str, set[str]] = defaultdict(set)
    for row in pattern_nodes: pattern_outcomes[row["pattern"]].add(row["outcome_context"])
    shared = [{"pattern": pattern, "outcomes": sorted(outcomes)} for pattern, outcomes in pattern_outcomes.items() if any("CHURN" in item for item in outcomes) and any("REACTIV" in item for item in outcomes)]
    return [
        _query("GQ01", "Transições ROBUST com maior suporte", ["stability=ROBUST", "promotable=true"], robust_transitions, len(transition_edges), "Prioriza relações estruturais estáveis para investigação.", "Suporte não implica causa."),
        _query("GQ02", "Padrões SENSITIVE observados antes ou no contexto de churn recorrente", ["stability=SENSITIVE", "recurring churn context"], sensitive_recurring, len(pattern_nodes), "Mostra padrões que exigem preservação explícita da sensibilidade.", "Magnitude depende de warnings."),
        _query("GQ03", "Jornadas de reativação com retorno de uso", ["scope=BETWEEN_CHURN_AND_REACTIVATION"], {"journeys": len(reactivation_journeys), "return_of_use_accounts_phase5": 18}, len(reactivation_journeys), "Retorno de uso é evento observado, não efeito de intervenção.", "População estrita é limitada."),
        _query("GQ04", "Padrões com alto suporte principal e baixo estrito", ["principal-strict gap descending"], support_gap, len(pattern_nodes), "Expõe dependência de warnings.", "Diferença de cobertura não mede qualidade do produto."),
        _query("GQ05", "Caminhos terminando em CHURN com maior MRR associado", ["ending=CHURN", "mrr_account_count>=10"], paths["high_associated_mrr"], len(paths["ending_in_churn"]), "MRR contextualiza escala financeira associada.", "MRR não é perda nem economia."),
        _query("GQ06", "Classes taxonômicas com menor cobertura analítica", ["confidence=LOW"], coverage.sort_values(["low_confidence_ratio", "primary_journey_class"], ascending=[False, True]).to_dict("records"), int(len(taxonomy)), "Direciona revisão de qualidade da taxonomia.", "Confiança é analítica, não score de conta."),
        _query("GQ07", "Padrões rejeitados por dependência HIGH", ["same_day_dependency=HIGH"], {"rejected_count": len(high_rejected)}, len(list(all_patterns)) + len(all_transitions), "Quantifica relações não promovidas por ordenação técnica.", "Não exibe candidatos instáveis individualmente."),
        _query("GQ08", "Findings que recomendam revisão de qualidade", ["investigation=REVIEW_DATA_QUALITY"], quality_findings, len(finding_nodes), "Mantém ação humana de qualidade explícita.", "Não é recomendação comercial automática."),
        _query("GQ09", "Event types com maior centralidade estrutural", ["weight=account_support"], central, 8, "Resume conectividade estrutural das transições promovidas.", "Centralidade não implica importância causal."),
        _query("GQ10", "Padrões presentes em contextos de churn e reativação", ["shared normalized pattern", "promotable=true"], shared[:20], len(pattern_outcomes), "Identifica famílias transversais para validação humana.", "Contextos diferentes não devem ser fundidos em um único nó."),
    ]


def graph_findings(
    queries: list[dict[str, Any]], centrality: dict[str, Any], paths: dict[str, Any],
) -> list[dict[str, Any]]:
    output = []
    robust = queries[0]["result"]
    for index, row in enumerate(robust[:2], 1):
        output.append({
            "finding_id": f"GF{index:02d}", "title": "Transição ROBUST com suporte elevado",
            "statement": f"Uma transição promovível reúne suporte de {row['account_support']} em {row['denominator_accounts']} contas no escopo {row['journey_scope']}.",
            "graph_scope": "PROMOTABLE_GRAPH", "node_types": ["EventType"], "relationship_types": ["TRANSITIONS_TO"],
            "population": "MAIN_WITH_STRICT_SENSITIVITY", "sample_size": int(row["denominator_accounts"]), "support": int(row["account_support"]),
            "denominator": int(row["denominator_accounts"]), "metric": "account_support", "estimate": float(row["relative_support"]),
            "weight_definition": "ACCOUNT_SUPPORT", "stability_status": "ROBUST", "quality_profile": "ROBUST_NON_HIGH_ORDER",
            "confidence_level": "MEDIUM", "limitations": ["STRUCTURAL_NOT_CAUSAL"],
            "business_relevance": "Prioriza validação agregada de caminhos frequentes.", "recommended_investigation": "VALIDATE_PATTERN_IN_NEW_COHORT",
        })
    ending = paths["ending_in_churn"]
    if ending:
        row = ending[0]
        output.append({
            "finding_id": "GF03", "title": "Caminho promovível observado antes de churn",
            "statement": f"O caminho agregado de maior suporte termina em CHURN e cobre {row['account_support']}/{row['denominator_accounts']} contas no contexto definido.",
            "graph_scope": "CHURN_GRAPH", "node_types": ["Pattern", "EventType", "Outcome"], "relationship_types": ["CONTAINS_EVENT_TYPE", "OBSERVED_BEFORE"],
            "population": "MAIN_WITH_STRICT_SENSITIVITY", "sample_size": row["denominator_accounts"], "support": row["account_support"], "denominator": row["denominator_accounts"],
            "metric": "relative_support", "estimate": row["relative_support"], "weight_definition": "ACCOUNT_SUPPORT",
            "stability_status": row["stability_status"], "quality_profile": f"{row['stability_status']}_NON_HIGH_ORDER",
            "confidence_level": "MEDIUM" if row["stability_status"] == "ROBUST" else "LOW", "limitations": ["ASSOCIATION_NOT_CAUSATION", "EXPOSURE_CONTROL_INHERITED_FROM_PHASE5"],
            "business_relevance": "Organiza investigação humana de jornada.", "recommended_investigation": "VALIDATE_PATTERN_IN_NEW_COHORT",
        })
    reactivation = paths["containing_reactivation"]
    if reactivation:
        row = reactivation[0]
        output.append({
            "finding_id": "GF04", "title": "Caminho promovível contém reativação explícita",
            "statement": f"O caminho de reativação com maior suporte reúne {row['account_support']}/{row['denominator_accounts']} contas.",
            "graph_scope": "REACTIVATION_GRAPH", "node_types": ["Pattern", "EventType", "Outcome"], "relationship_types": ["CONTAINS_EVENT_TYPE", "ASSOCIATED_WITH"],
            "population": "MAIN_WITH_STRICT_SENSITIVITY", "sample_size": row["denominator_accounts"], "support": row["account_support"], "denominator": row["denominator_accounts"],
            "metric": "relative_support", "estimate": row["relative_support"], "weight_definition": "ACCOUNT_SUPPORT",
            "stability_status": row["stability_status"], "quality_profile": f"{row['stability_status']}_NON_HIGH_ORDER",
            "confidence_level": "MEDIUM" if row["stability_status"] == "ROBUST" else "LOW", "limitations": ["CUSTOMER_SUCCESS_ACTION_NOT_INFERRED"],
            "business_relevance": "Estrutura evidência para validação humana de reativação.", "recommended_investigation": "VALIDATE_REACTIVATION_PATH",
        })
    if centrality["event_type_ranking_stable"]:
        row = centrality["event_type_by_weight"]["account_support"][0]
        output.append({
            "finding_id": "GF05", "title": "Centralidade estrutural estável entre pesos",
            "statement": f"{row['event_type']} ocupa a primeira posição de PageRank com peso por suporte e o top-3 preserva sobreposição material entre pesos.",
            "graph_scope": "PROMOTABLE_GRAPH", "node_types": ["EventType"], "relationship_types": ["TRANSITIONS_TO"],
            "population": "AGGREGATED_PROMOTABLE", "sample_size": 8, "support": 8, "denominator": 8,
            "metric": "pagerank", "estimate": row["pagerank"], "weight_definition": "ACCOUNT_SUPPORT_WITH_SENSITIVITY",
            "stability_status": "ROBUST", "quality_profile": "CENTRALITY_WEIGHT_SENSITIVITY_PASSED", "confidence_level": "MEDIUM",
            "limitations": ["CENTRALITY_IS_NOT_CAUSAL_IMPORTANCE"], "business_relevance": "Resume conectividade do vocabulário de eventos.",
            "recommended_investigation": "VALIDATE_PATTERN_IN_NEW_COHORT",
        })
    high_mrr = paths["high_associated_mrr"]
    if high_mrr:
        row = high_mrr[0]
        output.append({
            "finding_id": "GF06", "title": "Caminho com maior MRR associado",
            "statement": f"O caminho agregado lidera MRR associado entre candidatos com pelo menos 10 contas ({row['mrr_account_count']} contas).",
            "graph_scope": "HIGH_MRR_GRAPH", "node_types": ["Pattern"], "relationship_types": ["CONTAINS_EVENT_TYPE"],
            "population": "MAIN", "sample_size": row["mrr_account_count"], "support": row["account_support"], "denominator": row["denominator_accounts"],
            "metric": "associated_mrr", "estimate": row["associated_mrr"], "weight_definition": "SUM_MAX_MRR_OF_MATCHED_ACCOUNTS",
            "stability_status": row["stability_status"], "quality_profile": f"{row['stability_status']}_NON_HIGH_ORDER", "confidence_level": "LOW",
            "limitations": ["MRR_ASSOCIATED_NOT_LOST_OR_SAVED", "NO_CAUSAL_ATTRIBUTION"], "business_relevance": "Dimensiona a escala financeira associada ao caminho.",
            "recommended_investigation": "REVIEW_HIGH_MRR_LOW_USAGE",
        })
    return output[:7]
