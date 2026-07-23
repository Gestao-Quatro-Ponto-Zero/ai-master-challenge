"""Deterministic aggregate artifacts, reports, and non-causal figures."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd


def _clean(value: Any) -> Any:
    if isinstance(value, dict): return {str(key): _clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)): return [_clean(item) for item in value]
    if isinstance(value, (np.integer,)): return int(value)
    if isinstance(value, (np.floating,)): return None if np.isnan(value) else float(value)
    if isinstance(value, (pd.Timestamp,)): return value.isoformat()
    if value is pd.NA or (isinstance(value, float) and np.isnan(value)): return None
    return value


def write_json(path: Path, payload: Mapping[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_clean(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _top(items: list[dict[str, Any]], key: str = "account_support", limit: int = 10) -> list[dict[str, Any]]:
    return sorted(items, key=lambda row: (-float(row.get(key) or 0), str(row.get("pattern_label", ""))))[:limit]


def render_reports(report_dir: Path, context: Mapping[str, Any]) -> None:
    summary = context["summary"]
    findings = context["findings"]
    top_transitions = _top(context["transitions"], limit=8)
    top_patterns = _top(context["sequential_patterns"], limit=8)
    finding_lines = "\n".join(f"- **{row['title']}** — {row['statement']}" for row in findings) or "- Nenhum finding atingiu todos os gates de promoção."
    transition_lines = "\n".join(f"- {r['source_event']} → {r['target_event']}: {r['account_support']}/{r['denominator_accounts']} contas; {r['stability_status']}." for r in top_transitions)
    pattern_lines = "\n".join(f"- {r['pattern_label']}: {r['account_support']}/{r['denominator_accounts']} contas; {r['stability_status']}." for r in top_patterns)
    mining = f"""# Journey mining — diagnóstico descritivo

## Executive Summary

Foram construídas {summary['journey_rows']:,} jornadas governadas para {summary['accounts']} contas, sem quarentena. Padrões representam recorrência observada, não causa, previsão ou recomendação individual. O gate é **{summary['gate_result']}** porque warnings e ordenação intradiária ainda limitam parte da evidência.

## 1. Objetivo

Descrever sequências recorrentes de uso, suporte, churn e reativação de forma auditável.

## 2. População

Principal: VALID + VALID_WITH_WARNING. Estrita: VALID. Contas: {summary['accounts']}.

## 3. Construção das sequências

Unidade conta; cada escopo tem limite temporal explícito e chave única por população.

## 4. Ordenação

`account_id`, `event_time`, `event_order_on_same_day`, `event_id`. O desempate técnico não é causal.

## 5. Normalização

Representações raw, colapsada e bucket diário estruturado; bandas {summary['length_bands']}.

## 6. Transições

{transition_lines}

## 7. N-grams

Bigrams a 5-grams colapsados e bigram raw de sensibilidade, com suporte por conta.

## 8. Padrões sequenciais

{pattern_lines}

## 9. Pré-churn

Sufixos de 2, 3 e 5 eventos foram comparados em janelas fixas de 7/30/60/90 dias; observation_end é o pseudo-cutoff não churn.

## 10. Churn recorrente

Intervalos são descritivos e preservam reativação, retorno de uso, suporte e duração.

## 11. Reativação

Somente eventos explícitos sustentam reativação; ausência de evento não foi tratada como intervenção.

## 12. Taxonomia

Dez classes determinísticas, uma principal e classes secundárias, sem score ou previsão.

## 13. Estabilidade

ROBUST, SENSITIVE e UNSTABLE reconciliam principal e estrita; HIGH nunca é finding.

## 14. Exposição

Janelas fixas, landmarks, suporte por conta e bandas de comprimento limitam viés de jornadas longas.

## 15. Findings

{finding_lines}

## 16. Limitações

Associação não implica causalidade; sistema não observa ações externas; warnings e grupos pequenos limitam interpretação.

## 17. Preparação para o grafo

Somente padrões ROBUST/SENSITIVE, com denominadores, exposição e direção preservados, poderão alimentar a próxima fase. Nenhum grafo foi construído.
"""
    methodology = f"""# Metodologia de journey mining

## Contrato

Fonte: event log ativo da Fase 2; unidade: conta; quarentena excluída. Foram usadas {summary['event_rows']} linhas ativas.

## Medidas

- `support`: contas distintas contendo o padrão.
- `relative_support`: suporte dividido pelo denominador de contas.
- `confidence`: frequência condicional dentro do grupo definido.
- `lift`: frequência do grupo dividida pela referência, somente com denominador não zero.
- `coverage`: contas cobertas pelo padrão / contas do grupo.
- `leverage`: diferença entre frequência observada e produto das marginais, quando aplicável.
- `discriminative_ratio`: razão de frequências entre desfechos, com zero protegido.

## Mineração

Implementação própria testada; parâmetros: suporte ≥ 15 contas, comprimento ≤ 5, gap ≤ 5 eventos, gap ≤ 90 dias, apenas padrões fechados. Antes/depois do pruning: {summary['patterns_before_pruning']}/{summary['patterns_after_pruning']}.

## Exposição e ordenação

Janelas fixas, landmarks, bandas quantílicas e suporte por conta. Ordem intradiária é técnica; dependência HIGH bloqueia promoção.

## Privacidade e uso

Artefatos contêm somente agregados. A taxonomia é descritiva, não causal, preditiva ou interventiva.
"""
    taxonomy_counts = context["taxonomy_counts"]
    taxonomy = "# Taxonomia de jornadas\n\n" + "\n".join(
        f"## {row['name']} ({row['taxonomy_id']})\n\n{row['definition']} Janela: {row['temporal_window']}. Limitações: {', '.join(row['limitations'])}.\n"
        for row in context["taxonomy_definitions"]
    ) + "\n## Distribuição principal\n\n" + "\n".join(f"- {name}: {count}" for name, count in taxonomy_counts.items()) + "\n"
    stability_counts = context["stability_counts"]
    stability = f"""# Estabilidade de padrões e jornadas

## Resultado

- ROBUST: {stability_counts.get('ROBUST', 0)}
- SENSITIVE: {stability_counts.get('SENSITIVE', 0)}
- UNSTABLE: {stability_counts.get('UNSTABLE', 0)}

## Regra

ROBUST preserva presença, direção e magnitude material entre principal e estrita e não depende de ordem HIGH. SENSITIVE preserva presença/direção com variação relevante. UNSTABLE desaparece, muda direção, depende de amostra pequena ou ordenação HIGH.

## Limitações

Warnings afetam suporte; a estabilidade não converte associação em causalidade. Padrões instáveis foram excluídos dos findings.
"""
    for name, text in (("journey-mining.md", mining), ("journey-methodology.md", methodology), ("journey-taxonomy.md", taxonomy), ("journey-stability.md", stability)):
        (report_dir / name).write_text(text, encoding="utf-8")


def generate_figures(figure_dir: Path, context: Mapping[str, Any]) -> None:
    figure_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(figure_dir / ".mpl-cache"))
    import matplotlib.pyplot as plt
    plt.rcParams.update({"figure.dpi": 120, "axes.titleweight": "bold", "font.size": 9})
    palette = {"main": "#31688e", "strict": "#35b779", "accent": "#e07a5f"}

    def label(value: str, limit: int = 56) -> str:
        return value if len(value) <= limit else f"{value[:26]} ? {value[-26:]}"

    def save(name: str) -> None:
        plt.tight_layout(); plt.savefig(figure_dir / name, dpi=160, bbox_inches="tight"); plt.close()

    transitions = _top(context["transitions"], limit=10)[::-1]
    plt.figure(figsize=(9, 5)); plt.barh([f"{r['source_event']} → {r['target_event']}" for r in transitions], [r["relative_support"] for r in transitions], color=palette["main"])
    plt.xlabel("Suporte relativo por conta"); plt.title("Transições mais prevalentes — principal (agregado)"); save("top-transitions.png")

    pre = _top(context["pre_churn"], key="absolute_difference", limit=10)[::-1]
    plt.figure(figsize=(9, 5)); plt.barh([label(f"{r['window_days']}d | {r['pattern_label']}") for r in pre], [r["absolute_difference"] or 0 for r in pre], color=palette["accent"])
    plt.xlabel("Diferença absoluta churn − não churn"); plt.title("Padrões pré-churn com pseudo-cutoff comparável"); save("pre-churn-patterns.png")

    react = context["reactivation_summary"].get("top_sequences", [])[:10][::-1]
    plt.figure(figsize=(9, 5)); plt.barh([label(r["pattern_label"]) for r in react], [r["account_support"] for r in react], color=palette["strict"])
    plt.xlabel("Contas"); plt.title("Sequências entre churn e reativação (agregado)"); save("reactivation-patterns.png")

    seq = context["sequential_patterns"]
    colors = [{"ROBUST": palette["strict"], "SENSITIVE": "#f4a261", "UNSTABLE": "#a8a8a8"}[r["stability_status"]] for r in seq]
    plt.figure(figsize=(6, 6)); plt.scatter([r["principal_support"] for r in seq], [r["strict_support"] for r in seq], c=colors, alpha=.7)
    limit = max([r["principal_support"] for r in seq] + [1]); plt.plot([0, limit], [0, limit], "--", color="#555555"); plt.xlabel("Suporte principal"); plt.ylabel("Suporte estrito"); plt.title("Estabilidade de padrões fechados"); save("pattern-stability.png")

    counts = context["taxonomy_counts"]
    plt.figure(figsize=(9, 5)); plt.barh(list(counts.keys())[::-1], list(counts.values())[::-1], color=palette["main"]); plt.xlabel("Contas"); plt.title("Taxonomia principal de jornadas"); save("journey-taxonomy-distribution.png")

    lengths = context["journey_lengths"]
    plt.figure(figsize=(8, 5)); plt.hist(lengths, bins=20, color=palette["main"], edgecolor="white"); plt.xlabel("Eventos por jornada completa"); plt.ylabel("Contas"); plt.title("Distribuição do comprimento das jornadas — principal"); save("journey-length-distribution.png")
