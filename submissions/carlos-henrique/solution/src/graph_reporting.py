"""JourneyGraph deterministic artifacts, reports, and aggregate figures."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

import networkx as nx
import numpy as np


def _clean(value: Any) -> Any:
    if isinstance(value, dict): return {str(key): _clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)): return [_clean(item) for item in value]
    if isinstance(value, (np.integer,)): return int(value)
    if isinstance(value, (np.floating,)): return None if np.isnan(value) else float(value)
    return value


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_clean(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_reports(report_dir: Path, context: Mapping[str, Any]) -> None:
    summary = context["summary"]
    metrics = context["metrics"]
    validation = context["validation"]
    paths = context["paths"]
    findings = context["findings"]
    queries = context["queries"]
    neo4j = context["neo4j"]
    schema = context["schema"]
    node_counts = metrics["instance_graph"]["nodes_by_type"]
    edge_counts = metrics["instance_graph"]["edges_by_type"]
    analytical_nodes = metrics["analytical_graph"]["nodes_by_type"]
    finding_lines = "\n".join(f"- **{row['title']}** — {row['statement']}" for row in findings) or "- Nenhum finding atingiu o gate."
    journeygraph = f"""# JourneyGraph governado

## 1. Executive Summary

- **O grafo está reconciliado para uso analítico com ressalvas.** O instance graph conecta {node_counts.get('Account', 0):,} contas anônimas, {node_counts.get('Journey', 0):,} jornadas e {node_counts.get('EventInstance', 0):,} ocorrências, enquanto o analytical graph promove somente evidências ROBUST/SENSITIVE.
- **A camada analítica preserva o gate da Fase 5.** Há {analytical_nodes.get('Pattern', 0):,} padrões promovidos e {metrics['analytical_graph']['edges_by_type'].get('TRANSITIONS_TO', 0):,} transições; UNSTABLE, HIGH e grupos pequenos permanecem fora.
- **Neo4j é uma opção de portabilidade, não uma dependência.** Dois GraphML completos sustentam o gate local; CSVs e Cypher derivados permitem demonstração externa sem servidor obrigatório.
- **O uso continua não causal e não operacional.** Centralidade descreve estrutura; MRR é associado; investigações exigem revisão humana.

## 2. Motivação

O JourneyGraph organiza estrutura, temporalidade, evidência e governança em uma camada de conhecimento rastreável. Ele não converte associação em causalidade nem cria ranking individual.

## 3. Modelo conceitual

Dez tipos de nó separam conta, jornada, ocorrência, vocabulário, padrão, outcome, taxonomia, qualidade, finding e investigação humana.

![Arquitetura conceitual](figures/journeygraph-overview.png)

## 4. Modelo lógico

Relações tipadas preservam direção temporal e contexto. `TRANSITIONS_TO` carrega escopo, outcome, suporte, denominador, estabilidade, qualidade e MRR associado.

## 5. Instance graph

O grafo de rastreabilidade possui {metrics['instance_graph']['node_count']:,} nós e {metrics['instance_graph']['edge_count']:,} relações. EventInstance inclui `journey_key`, impedindo reutilização silenciosa da mesma ocorrência em escopos distintos.

## 6. Analytical graph

O grafo promovido possui {metrics['analytical_graph']['node_count']:,} nós e {metrics['analytical_graph']['edge_count']:,} relações. Candidatos UNSTABLE podem ser contabilizados, mas não entram na projeção promovível.

## 7. Nós

Contagens por tipo no instance graph: {json.dumps(node_counts, ensure_ascii=False, sort_keys=True)}. As chaves públicas são SHA-256 truncadas com namespace local documentado; nenhum mapeamento reversível é versionado.

## 8. Relações

Contagens por tipo no instance graph: {json.dumps(edge_counts, ensure_ascii=False, sort_keys=True)}. Nenhuma relação usa semântica causal.

## 9. Temporalidade

`NEXT_EVENT` é único por posição, não retrocede no tempo e permanece dentro dos limites da jornada. A ordenação intradiária é técnica e explicitamente qualificada.

## 10. Padrões

Padrões textualmente iguais em escopos diferentes conservam nós distintos e compartilham apenas `pattern_family_key`. A promoção exige suporte, denominador, estabilidade e ordem não HIGH.

## 11. Outcomes

Seis outcomes controlados recebem associações descritivas. `OBSERVED_BEFORE` e `ASSOCIATED_WITH` não significam efeito ou determinação.

## 12. Taxonomia

As dez classes da Fase 5 são nós de conhecimento; classificações permanecem determinísticas e descritivas.

![Taxonomia agregada](figures/journeygraph-taxonomy.png)

## 13. Qualidade

QualityProfile materializa população, estabilidade, dependência intradiária, amostra, warnings, cobertura e confiança. Relações rejeitadas continuam auditáveis nos artefatos de qualidade.

![Camada de qualidade](figures/journeygraph-quality-layer.png)

## 14. Métricas estruturais

Densidade, grau, componentes, PageRank e betweenness são propriedades estruturais. Nenhuma centralidade foi calculada para Account e nenhum ranking individual foi produzido.

![Transições de eventos](figures/journeygraph-event-transitions.png)

## 15. Caminhos

Foram limitados a seis eventos e suporte mínimo explícito. O grafo separa caminhos de churn, recorrência e reativação sem linguagem causal.

![Caminhos de churn](figures/journeygraph-churn-paths.png)

![Caminhos de reativação](figures/journeygraph-reactivation-paths.png)

## 16. Consultas

Dez consultas NetworkX possuem equivalentes Cypher, filtros, denominadores, interpretação e limitação. Elas cobrem suporte, sensibilidade, reativação, qualidade, centralidade, taxonomia e MRR associado.

## 17. MRR associado

MRR é agregado por contas que correspondem a padrões ou transições. Os termos perda, economia e receita evitável são proibidos.

## 18. Findings

{finding_lines}

## 19. Limitações

Warnings reduzem estabilidade; a população estrita é limitada para reativação; ordem no mesmo dia não é causal; o CSV de EventInstance é uma amostra determinística; Neo4j não foi executado externamente.

## 20. Preparação para a Fase 7

Somente PROMOTABLE_GRAPH e subgrafos governados podem alimentar uma watchlist futura. Score, previsão, recomendação automática, contato e intervenção permanecem proibidos.
"""
    methodology = f"""# Metodologia do JourneyGraph

## Escopo

NetworkX 3.x é a implementação de referência local. O instance graph privilegia explicabilidade; o analytical graph privilegia padrões agregados promovíveis.

## Identificadores

SHA-256 truncado em 16 caracteres com salt público de namespacing. O account_id bruto participa somente do cálculo local e nunca é persistido em propriedade pública ou mapeamento reversível.

## Promoção

Somente ROBUST/SENSITIVE, suporte mínimo, denominador positivo, `small_sample=false` e dependência diferente de HIGH. Rejeições são contabilizadas em `graph_quality.json`.

## Centralidade

PageRank, grau ponderado e betweenness foram calculados apenas em EventType, com sensibilidade a account_support, relative_support e transition_count. Pattern recebe ranking somente por suporte/MRR agregado. Account nunca recebe centralidade.

## Caminhos e MRR

Caminhos têm no máximo seis eventos e suporte mínimo de dez contas. MRR é soma/mediana/média associada às contas correspondentes, sem interpretação de perda ou economia.

## Reconciliação

Contas, jornadas, taxonomia, padrões, transições, findings, outcomes e MRR foram reconciliados. Diferença inexplicada: {validation['reconciliation']['difference_unexplained']}.
"""
    schema_report = "# Schema do JourneyGraph\n\n" + "\n".join(
        f"## {label}\n\nPropriedades permitidas: `{', '.join(properties)}`.\n"
        for label, properties in schema["node_schemas"].items()
    ) + "\n## Relações\n\n" + "\n".join(f"- `{relationship}`" for relationship in schema["relationship_types"]) + "\n\n## Semântica proibida\n\n" + ", ".join(f"`{term}`" for term in schema["forbidden_causal_terms"]) + ".\n"
    validation_report = f"""# Validação do JourneyGraph

## Avaliação geral: Share with caveats

O grafo está reconciliado e metodologicamente utilizável, com ressalvas herdadas de warnings, cobertura e ordem intradiária.

## Metodologia

Foram validados schema, duplicação, privacidade, temporalidade, promoção, propriedades GraphML e semântica não causal nos dois grafos.

## Evidência

- diferença inexplicada: {validation['reconciliation']['difference_unexplained']};
- IDs operacionais expostos: {validation['instance_privacy']['raw_account_ids_exposed']};
- violações temporais: {validation['temporal']['temporal_violations']};
- padrões UNSTABLE promovidos: {validation['promotion']['unstable_promoted']};
- relações causais: {validation['analytical_non_causal']['violations']}.

## Ressalvas obrigatórias

- centralidade é estrutural;
- MRR é associado;
- EventInstance CSV é amostra, enquanto GraphML mantém o grafo completo;
- a execução externa do Neo4j não integra o gate.
"""
    neo4j_report = f"""# Guia Neo4j do JourneyGraph

## Pré-requisitos

Neo4j 5.x e acesso local ao diretório de import. O gate principal não exige Neo4j, Docker, credenciais ou rede.

## Constraints

Execute `constraints.cypher` antes da carga para garantir chaves únicas.

## Indexes

Execute `indexes.cypher` após constraints para acelerar escopo, estabilidade, taxonomia e evento.

## Import

Copie os CSVs derivados para o diretório de import e adapte o comando documentado em `import.cypher`. EventInstance usa amostra determinística de {neo4j['event_journey_sample_size']} jornadas; os GraphML preservam o grafo completo.

## Consultas

`example_queries.cypher` contém dez consultas equivalentes às investigações NetworkX.

## Limitações

Nenhum servidor externo foi iniciado. CSVs não contêm account_id bruto, source event id ou PII. Centralidade, padrões e MRR permanecem descritivos.

## Reprodução local

Execute `python solution/scripts/run_journey_graph.py`; valide hashes e, opcionalmente, importe os CSVs em uma base Neo4j descartável.
"""
    for name, text in (
        ("journeygraph.md", journeygraph), ("graph-methodology.md", methodology),
        ("graph-schema.md", schema_report), ("graph-validation.md", validation_report),
        ("neo4j-guide.md", neo4j_report),
    ):
        (report_dir / name).write_text(text, encoding="utf-8")


def _draw_graph(graph: nx.Graph, positions: dict[Any, Any], labels: dict[Any, str], sizes: list[float], colors: list[str], title: str, path: Path, edge_widths: list[float] | None = None) -> None:
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10, 6.2))
    nx.draw_networkx_nodes(graph, positions, node_size=sizes, node_color=colors, edgecolors="#233142", linewidths=1.2)
    nx.draw_networkx_edges(graph, positions, width=edge_widths or 1.2, edge_color="#7b8794", arrows=True, arrowsize=15, connectionstyle="arc3,rad=0.05")
    nx.draw_networkx_labels(graph, positions, labels=labels, font_size=8, font_weight="bold", font_color="#1f2933")
    plt.title(title, loc="left", fontsize=14, fontweight="bold", color="#1f2933")
    plt.axis("off"); plt.tight_layout(); plt.savefig(path, dpi=170, bbox_inches="tight", facecolor="white"); plt.close()


def generate_figures(figure_dir: Path, context: Mapping[str, Any]) -> None:
    figure_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(figure_dir / ".mpl-cache"))
    blue, gold, orange, olive, pink, neutral = "#31688e", "#d8a31a", "#d97732", "#6c8c3c", "#c45a78", "#c8d0d8"

    conceptual = nx.DiGraph()
    edges = [("Account", "Journey"), ("Journey", "EventInstance"), ("EventInstance", "EventType"), ("Journey", "Taxonomy"), ("Journey", "Outcome"), ("Journey", "QualityProfile"), ("Journey", "Pattern"), ("Pattern", "EventType"), ("Pattern", "Finding"), ("Finding", "Investigation")]
    conceptual.add_edges_from(edges)
    pos = nx.spring_layout(conceptual, seed=42, k=1.2)
    _draw_graph(conceptual, pos, {n: n for n in conceptual}, [1500] * len(conceptual), [blue, blue, gold, gold, orange, olive, olive, pink, pink, neutral], "Arquitetura conceitual do JourneyGraph", figure_dir / "journeygraph-overview.png")

    transitions = context["top_transitions"][:20]
    transition_graph = nx.DiGraph()
    for row in transitions:
        if transition_graph.has_edge(row["source_event"], row["target_event"]): transition_graph[row["source_event"]][row["target_event"]]["weight"] += row["account_support"]
        else: transition_graph.add_edge(row["source_event"], row["target_event"], weight=row["account_support"])
    pos = nx.circular_layout(transition_graph)
    weights = [transition_graph[u][v]["weight"] for u, v in transition_graph.edges]
    scale = max(weights or [1])
    _draw_graph(transition_graph, pos, {n: n.replace("SUBSCRIPTION_", "SUB_").replace("SUPPORT_", "SUP_") for n in transition_graph}, [1600] * len(transition_graph), [blue] * len(transition_graph), "Transições promovíveis entre tipos de evento", figure_dir / "journeygraph-event-transitions.png", [1 + 5 * value / scale for value in weights])

    def path_figure(rows: list[dict[str, Any]], name: str, title: str, color: str) -> None:
        graph = nx.DiGraph()
        for row in rows[:8]:
            for left, right in zip(row["pattern"], row["pattern"][1:]):
                if graph.has_edge(left, right): graph[left][right]["weight"] += row["account_support"]
                else: graph.add_edge(left, right, weight=row["account_support"])
        if not graph.nodes:
            import matplotlib.pyplot as plt
            plt.figure(figsize=(10, 6.2))
            plt.title(title, loc="left", fontsize=14, fontweight="bold", color="#1f2933")
            plt.text(
                .5, .52, "Nenhum caminho atingiu os gates de promo\u00e7\u00e3o",
                ha="center", va="center", fontsize=16, fontweight="bold", color="#4b5563",
            )
            plt.text(.5, .43, "Suporte, estabilidade, amostra e ordem intradi\u00e1ria preservados", ha="center", va="center", fontsize=11, color="#6b7280")
            plt.axis("off"); plt.tight_layout(); plt.savefig(figure_dir / name, dpi=170, bbox_inches="tight", facecolor="white"); plt.close()
            return
        pos = nx.spring_layout(graph, seed=42, k=1.4) if graph.nodes else {}
        weights = [graph[u][v]["weight"] for u, v in graph.edges]
        scale = max(weights or [1])
        _draw_graph(graph, pos, {n: n.replace("SUBSCRIPTION_", "SUB_").replace("SUPPORT_", "SUP_") for n in graph}, [1700] * len(graph), [color] * len(graph), title, figure_dir / name, [1 + 5 * value / scale for value in weights])
    path_figure(context["paths"]["ending_in_churn"], "journeygraph-churn-paths.png", "Caminhos promovíveis terminando em churn", orange)
    path_figure(context["paths"]["containing_reactivation"], "journeygraph-reactivation-paths.png", "Caminhos promovíveis contendo reativação", olive)

    quality = nx.DiGraph()
    quality.add_weighted_edges_from([("Promoted", "ROBUST", context["quality_counts"].get("ROBUST", 0)), ("Promoted", "SENSITIVE", context["quality_counts"].get("SENSITIVE", 0)), ("Candidates", "UNSTABLE rejected", context["rejected_counts"].get("UNSTABLE", 0)), ("Candidates", "HIGH rejected", context["rejected_counts"].get("HIGH_ORDER_DEPENDENCY", 0)), ("Candidates", "Small rejected", context["rejected_counts"].get("SMALL_SAMPLE", 0))])
    pos = {"Promoted": (-1, .5), "Candidates": (-1, -.5), "ROBUST": (1, 1), "SENSITIVE": (1, .5), "UNSTABLE rejected": (1, 0), "HIGH rejected": (1, -.5), "Small rejected": (1, -1)}
    widths = [1 + np.log1p(data["weight"]) / 2 for *_, data in quality.edges(data=True)]
    _draw_graph(quality, pos, {n: n for n in quality}, [1700, 1700, 1400, 1400, 1700, 1500, 1500], [blue, neutral, olive, gold, neutral, orange, pink], "Camada de qualidade e promoção", figure_dir / "journeygraph-quality-layer.png", widths)

    taxonomy = nx.DiGraph()
    for name, count in context["taxonomy_counts"].items(): taxonomy.add_edge("JOURNEYS", name.replace("_JOURNEY", ""), weight=count)
    pos = nx.spring_layout(taxonomy, seed=42, k=1.5)
    weights = [taxonomy[u][v]["weight"] for u, v in taxonomy.edges]
    scale = max(weights or [1])
    _draw_graph(taxonomy, pos, {n: n.replace("_", "\n") for n in taxonomy}, [1900 if n == "JOURNEYS" else 1200 for n in taxonomy], [blue if n == "JOURNEYS" else gold for n in taxonomy], "Classes taxonômicas e volume de jornadas", figure_dir / "journeygraph-taxonomy.png", [1 + 6 * value / scale for value in weights])
