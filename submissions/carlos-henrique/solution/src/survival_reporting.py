"""Deterministic aggregate artifacts, reports and static survival figures."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any, Mapping

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / ".venv" / ".matplotlib")
)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


BLUE = "#2563A6"
ORANGE = "#D97706"
OLIVE = "#6B7D32"
PINK = "#B64E73"
INK = "#27313D"
GRID = "#D9DEE5"
PALETTE = (BLUE, ORANGE, OLIVE, PINK, "#6B7280")


def clean_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): clean_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_json(item) for item in value]
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        return pd.Timestamp(value).isoformat()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return None if not math.isfinite(number) else number
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if value is pd.NA or value is pd.NaT:
        return None
    return value


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(clean_json(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _horizon_rows(analysis: Mapping[str, Any], estimator: str) -> str:
    key = "survival_probability" if estimator == "kaplan_meier" else "cumulative_hazard"
    lines = [
        "| Horizonte | Estimativa | IC 95% | Em risco | Eventos | Censurados | Suporte |",
        "|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in analysis[estimator]["horizons"]:
        value = row[key]
        estimate = "não estimado" if value is None else f"{value:.4f}"
        interval = (
            "não estimado"
            if row["confidence_interval_lower"] is None
            else f"[{row['confidence_interval_lower']:.4f}; {row['confidence_interval_upper']:.4f}]"
        )
        lines.append(
            f"| {row['horizon_days']}d | {estimate} | {interval} | {row['at_risk']} | "
            f"{row['events_observed']} | {row['censored']} | `{row['support_status']}` |"
        )
    return "\n".join(lines)


def _findings(findings: Mapping[str, Any]) -> str:
    lines: list[str] = []
    for item in findings["findings"]:
        lines.append(
            f"- **{item['finding_id']} — {item['title']}.** {item['statement']} "
            f"Sensibilidade `{item['sensitivity_status']}`; pressupostos `{item['assumption_status']}`; "
            f"confiança `{item['confidence_level']}`. Limitação: {item['limitations']}"
        )
    return "\n".join(lines) or "- Nenhum resultado superou o gate para finding principal."


def render_reports(payloads: Mapping[str, Mapping[str, Any]]) -> dict[str, str]:
    summary = payloads["survival_summary.json"]
    km = payloads["kaplan_meier_results.json"]
    na = payloads["nelson_aalen_results.json"]
    logrank = payloads["logrank_results.json"]
    landmarks = payloads["landmark_results.json"]
    sensitivity = payloads["survival_sensitivity.json"]
    assumptions = payloads["survival_assumptions.json"]
    findings = payloads["survival_findings.json"]
    main = km["populations"]["main"]
    strict = km["populations"]["strict"]
    main_na = na["populations"]["main"]
    sig = sum(
        item["multiplicity_status"] == "BH_SIGNIFICANT_0_05"
        for block in logrank["dimensions"]
        for item in block["comparisons"]
    )
    unstable = sum(item["classification"] == "UNSTABLE" for item in sensitivity["metric_comparisons"])
    landmark_lines = "\n".join(
        f"- **{item['landmark_days']} dias:** {item['accounting']['included']} contas; "
        f"{item['accounting']['churn_before_or_on_landmark']} churns anteriores/no landmark excluídos; "
        f"{item['analysis']['event_count']} eventos posteriores."
        for item in landmarks["landmarks"]
    )
    assumption_lines = "\n".join(
        f"- `{item['assumption']}` — **{item['status']}**: {item['evidence']}"
        for item in assumptions["assumptions"]
    )
    sensitivity_lines = "\n".join(
        f"- `{item['scenario_id']}`: n={item['sample_size']}, eventos={item['event_count']}, "
        f"censura={item['censoring_rate']:.2%}, mediana={item['median_survival_days']}."
        for item in sensitivity["scenarios"]
    )
    dependencies = ", ".join(f"{key} {value}" for key, value in summary["dependencies"].items())

    analysis_report = f"""# Análise de sobrevivência e risco temporal — RavenStack

> **Gate:** `{summary['gate']}`. Análise descritiva agregada; não é previsão individual, inferência causal ou taxa empresarial generalizável.

## 1. Objetivo

Estimar o tempo observado sem primeiro churn utilizável, explicitar censura administrativa e comparar curvas somente onde há suporte temporal e amostral.

## 2. População

A população principal usa `VALID + VALID_WITH_WARNING`; a estrita usa somente `VALID`; ambas excluem quarentena. Foram elegíveis {summary['population']['main_eligible']} de {summary['population']['source_accounts']} contas na origem principal; {summary['population']['main_excluded']} foram excluídas com motivo controlado.

## 3. Origem temporal

Origem principal: primeira `SUBSCRIPTION_STARTED` utilizável. `ACCOUNT_CREATED` é usada apenas na sensibilidade. Features comportamentais são reservadas a landmarks de janela fixa.

## 4. Endpoint

`FIRST_VALID_CHURN`: primeiro `CHURN_RECORDED` utilizável em ou após a exposição. Churn recorrente não substitui o primeiro endpoint; churn pré-exposição é ignorado e contabilizado.

## 5. Censura

Censura à direita em `{summary['censoring']['observation_end']}`. Na principal há {main['censored_count']} censurados ({main['censoring_rate']:.2%}) e {main['event_count']} eventos. Censura administrativa não prova retenção e a hipótese de censura não informativa permanece limitada.

## 6. Kaplan–Meier

{_horizon_rows(main, 'kaplan_meier')}

Mediana principal: `{main['median_survival_days']}` dias. População estrita: n={strict['sample_size']}, eventos={strict['event_count']}, censura={strict['censoring_rate']:.2%}, mediana=`{strict['median_survival_days']}`. Horizontes com menos de {summary['policy']['minimum_at_risk']} contas recebem `LOW_AT_RISK`; não há extrapolação além do suporte observado.

![Kaplan–Meier geral](figures/kaplan-meier-overall.png)

## 7. Nelson–Aalen

{_horizon_rows(main_na, 'nelson_aalen')}

O risco acumulado é complemento descritivo da Kaplan–Meier e não representa probabilidade futura individual.

![Risco acumulado](figures/cumulative-hazard-overall.png)

## 8. Comparações

Foram executadas {logrank['executed_comparisons']} comparações elegíveis, com Benjamini–Hochberg; {sig} permaneceram abaixo de 0,05 após correção. Tamanho, eventos, diferenças em 90/180/365 dias e RMST acompanham cada teste. P-value isolado não sustenta decisão.

![Curvas por qualidade](figures/kaplan-meier-quality-populations.png)

![Curvas por plano inicial](figures/kaplan-meier-selected-groups.png)

## 9. Landmarks

{landmark_lines}

Features foram calculadas somente entre exposição e landmark; contas com churn antes ou no marco foram excluídas. As curvas começam depois do marco e não reutilizam futuro.

![Comparação de landmarks](figures/landmark-survival-comparison.png)

## 10. RMST

RMST foi estimado em 90, 180 e 365 dias quando suportado. Diferenças significam tempo médio **observado** sem primeiro churn dentro do horizonte, nunca ganho causal.

![RMST](figures/rmst-comparison.png)

## 11. Cox

`{summary['cox']['status']}`. {summary['cox']['justification']} Nenhum coeficiente, hazard ratio ou score individual foi produzido.

## 12. Sensibilidade

{sensitivity_lines}

Há {unstable} comparações métricas classificadas como `UNSTABLE`; elas não foram promovidas a findings.

## 13. Pressupostos

{assumption_lines}

## 14. Findings

{_findings(findings)}

## 15. Limitações

- warnings alteram materialmente a cobertura de churn;
- timestamps diários não autorizam precedência intradiária ou causalidade;
- censura administrativa pode ser informativa e não foi resolvida;
- sobreposição em 99,84% dos episódios impede uma curva independente limpa por assinatura;
- comparações são exploratórias e não devem orientar intervenção automatizada.

## 16. Próximos passos

Preservar populações, censura, at-risk, landmarks e sensibilidade em eventual mineração de jornadas. Antes de qualquer uso operacional, validar cronologia upstream, semântica de assinaturas simultâneas e mecanismo de censura.
"""

    methodology = f"""# Metodologia de sobrevivência

## Definições

- **Unidade:** conta, uma linha por `account_id` no Parquet operacional local.
- **Origem principal:** primeira assinatura utilizável; **alternativa:** signup utilizável.
- **Endpoint:** primeiro churn utilizável em ou após a origem.
- **Censura:** direita, administrativa, em `{summary['censoring']['observation_end']}`.

## Fórmulas conceituais

Kaplan–Meier multiplica, em cada tempo de evento, `1 - dᵢ/nᵢ`; o intervalo de 95% usa variância de Greenwood e limites truncados em `[0,1]`. Nelson–Aalen soma `dᵢ/nᵢ`. RMST integra a função de sobrevivência até τ. O log-rank compara eventos observados e esperados sob igualdade das curvas; p-values pairwise recebem Benjamini–Hochberg.

## Origem temporal, exclusões e grupos

Duração negativa, origem ausente ou origem posterior ao fim administrativo são excluídas com código. Duração zero é preservada como `SAME_DAY_EVENT`. Grupos ordinários usam atributos de baseline (`first_plan`, MRR inicial, quantidade e sobreposição no baseline, qualidade). Uso e suporte são analisados apenas em janelas landmark fixas, evitando tempo imortal no agrupamento comum.

## Landmarks

Nos marcos de 30, 60 e 90 dias entram apenas contas elegíveis, observáveis até o marco e sem churn até ou no marco. Features consideram exclusivamente eventos entre exposição e marco; a duração posterior inicia no próprio marco. Exclusões e denominadores reconciliam exatamente.

## Log-rank, RMST e Cox

Log-rank exige pelo menos {summary['policy']['minimum_group_size']} contas e {summary['policy']['minimum_group_events']} eventos por grupo. RMST usa 90/180/365 dias e é diferença observada, não causal. Cox foi `{summary['cox']['status']}` porque {summary['cox']['justification'].lower()}

## Pressupostos

{assumption_lines}

## Contrato visual

As seis figuras são PNGs estáticos reproduzíveis. Perguntas: forma geral e incerteza; influência da qualidade; diferença por plano inicial; risco acumulado; sobrevivência condicional nos landmarks; RMST por horizonte. Linhas, tracejados e rótulos complementam uma paleta azul/laranja/oliva/rosa; nenhum ID ou PII aparece. QA final ocorre nos PNGs exportados.

## Uso permitido

Descrição agregada de tempo até primeiro churn, suporte temporal, censura, diferenças exploratórias e sensibilidade.

## Uso proibido

Probabilidade individual, score, ranking, causalidade, previsão, taxa empresarial generalizável, ação automatizada ou curva independente por assinatura.

## Ambiente reproduzível

{dependencies}.
"""

    assumptions_report = f"""# Pressupostos da análise de sobrevivência

## Classificação formal

{assumption_lines}

## Decisão sobre Cox

Status `{summary['cox']['status']}`. {summary['cox']['justification']} Riscos proporcionais permanecem `NOT_TESTED`, portanto não há modelo a promover.

## Decisão sobre assinaturas

Curvas por assinatura não foram executadas: 99,84% dos episódios se sobrepõem, término não equivale necessariamente a churn e episódios da mesma conta não são independentes.
"""

    sensitivity_report = f"""# Sensibilidade da sobrevivência

## Cenários

{sensitivity_lines}

## Comparações métricas

| Cenário | Métrica | Referência | Alternativa | Classe |
|---|---|---:|---:|---|
""" + "\n".join(
        f"| `{item['scenario_id']}` | `{item['metric']}` | {item['reference']} | {item['alternative']} | `{item['classification']}` |"
        for item in sensitivity["metric_comparisons"]
    ) + """

## Interpretação

`ROBUST` indica variação relativa de até 10%; `SENSITIVE`, até 30%; `UNSTABLE`, acima de 30%, mudança de direção ou ausência de suporte. Resultados instáveis não são findings principais. Comparações entre signup e assinatura avaliam a origem temporal, não a causalidade da assinatura.
"""
    return {
        "survival-analysis.md": analysis_report,
        "survival-methodology.md": methodology,
        "survival-assumptions.md": assumptions_report,
        "survival-sensitivity.md": sensitivity_report,
    }


def _style_axes(axis: plt.Axes, title: str, subtitle: str, ylabel: str) -> None:
    axis.set_title(title, loc="left", fontsize=15, fontweight="bold", color=INK, pad=24)
    axis.text(0, 1.02, subtitle, transform=axis.transAxes, fontsize=9, color="#59636E", va="bottom")
    axis.set_xlabel("Dias observados", color=INK)
    axis.set_ylabel(ylabel, color=INK)
    axis.grid(axis="both", color=GRID, linewidth=0.7, alpha=0.65)
    axis.spines[["top", "right"]].set_visible(False)
    axis.tick_params(colors=INK)


def _save(fig: plt.Figure, path: Path) -> None:
    fig.savefig(
        path,
        dpi=160,
        bbox_inches="tight",
        facecolor="white",
        metadata={"Software": "JourneyGraph Phase 4"},
    )
    plt.close(fig)


def _plot_km(axis: plt.Axes, analysis: Mapping[str, Any], label: str, color: str, linestyle: str = "-") -> None:
    curve = pd.DataFrame(analysis["kaplan_meier"]["curve"])
    axis.step(curve["time_days"], curve["survival_probability"], where="post", label=label, color=color, linewidth=2.2, linestyle=linestyle)
    axis.fill_between(
        curve["time_days"],
        curve["confidence_interval_lower"],
        curve["confidence_interval_upper"],
        step="post",
        color=color,
        alpha=0.10,
        linewidth=0,
    )


def generate_figures(
    figures_dir: Path,
    km_payload: Mapping[str, Any],
    na_payload: Mapping[str, Any],
    landmark_payload: Mapping[str, Any],
) -> list[Path]:
    figures_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    main = km_payload["populations"]["main"]
    strict = km_payload["populations"]["strict"]

    fig, axis = plt.subplots(figsize=(10, 6))
    _plot_km(axis, main, f"Principal (n={main['sample_size']})", BLUE)
    _plot_km(axis, strict, f"Estrita (n={strict['sample_size']})", ORANGE, "--")
    _style_axes(axis, "Kaplan–Meier — população geral", "Primeiro churn utilizável; áreas mostram IC 95% de Greenwood", "Probabilidade de sobrevivência observada")
    axis.set_ylim(0, 1.03)
    axis.legend(frameon=False, loc="lower left")
    risk = [next(row for row in main["kaplan_meier"]["horizons"] if row["horizon_days"] == h)["at_risk"] for h in (30, 90, 180, 365, 540)]
    axis.text(0.99, 0.98, "Principal em risco — 30/90/180/365/540d: " + "/".join(map(str, risk)), transform=axis.transAxes, ha="right", va="top", fontsize=8, color="#59636E")
    path = figures_dir / "kaplan-meier-overall.png"
    _save(fig, path); outputs.append(path)

    fig, axis = plt.subplots(figsize=(10, 6))
    quality_groups = km_payload["groups"]["main"]["quality_population"]
    for index, (label, analysis) in enumerate(sorted(quality_groups.items())):
        _plot_km(axis, analysis, f"{label} (n={analysis['sample_size']})", PALETTE[index], "-" if index == 0 else "--")
    _style_axes(axis, "Kaplan–Meier — populações de qualidade", "Atributo de qualidade até o endpoint; comparação descritiva e sensível a warnings", "Probabilidade de sobrevivência observada")
    axis.set_ylim(0, 1.03); axis.legend(frameon=False, loc="lower left")
    path = figures_dir / "kaplan-meier-quality-populations.png"
    _save(fig, path); outputs.append(path)

    fig, axis = plt.subplots(figsize=(10, 6))
    plan_groups = km_payload["groups"]["main"]["first_plan"]
    for index, (label, analysis) in enumerate(sorted(plan_groups.items())):
        _plot_km(axis, analysis, f"{label} (n={analysis['sample_size']})", PALETTE[index], ("-", "--", ":")[index % 3])
    _style_axes(axis, "Kaplan–Meier — plano inicial", "Plano disponível na primeira assinatura; comparação agregada não causal", "Probabilidade de sobrevivência observada")
    axis.set_ylim(0, 1.03); axis.legend(frameon=False, loc="lower left")
    path = figures_dir / "kaplan-meier-selected-groups.png"
    _save(fig, path); outputs.append(path)

    fig, axis = plt.subplots(figsize=(10, 6))
    for analysis, label, color, style in ((na_payload["populations"]["main"], "Principal", BLUE, "-"), (na_payload["populations"]["strict"], "Estrita", ORANGE, "--")):
        curve = pd.DataFrame(analysis["nelson_aalen"]["curve"])
        axis.step(curve["time_days"], curve["cumulative_hazard"], where="post", label=label, color=color, linewidth=2.2, linestyle=style)
        axis.fill_between(curve["time_days"], curve["confidence_interval_lower"], curve["confidence_interval_upper"], step="post", color=color, alpha=0.10, linewidth=0)
    _style_axes(axis, "Nelson–Aalen — risco acumulado", "Complemento descritivo; não é probabilidade individual", "Risco acumulado")
    axis.set_ylim(bottom=0); axis.legend(frameon=False, loc="upper left")
    path = figures_dir / "cumulative-hazard-overall.png"
    _save(fig, path); outputs.append(path)

    fig, axis = plt.subplots(figsize=(10, 6))
    for index, item in enumerate(landmark_payload["landmarks"]):
        analysis = item["analysis"]
        _plot_km(axis, analysis, f"{item['landmark_days']}d (n={analysis['sample_size']})", PALETTE[index], ("-", "--", ":")[index])
    _style_axes(axis, "Sobrevivência após landmarks", "Contas observáveis e sem churn até cada marco; tempo reiniciado no landmark", "Probabilidade de sobrevivência observada")
    axis.set_ylim(0, 1.03); axis.legend(frameon=False, loc="lower left")
    path = figures_dir / "landmark-survival-comparison.png"
    _save(fig, path); outputs.append(path)

    horizons = [row["horizon_days"] for row in main["rmst"]]
    main_values = [row["rmst_days"] or 0 for row in main["rmst"]]
    strict_values = [row["rmst_days"] or 0 for row in strict["rmst"]]
    x = np.arange(len(horizons)); width = 0.36
    fig, axis = plt.subplots(figsize=(9, 5.5))
    axis.bar(x - width / 2, main_values, width, color=BLUE, label=f"Principal (n={main['sample_size']})")
    axis.bar(x + width / 2, strict_values, width, color=ORANGE, edgecolor="#8A4B05", hatch="//", label=f"Estrita (n={strict['sample_size']})")
    axis.set_xticks(x, [f"{h} dias" for h in horizons])
    _style_axes(axis, "RMST por horizonte", "Tempo médio observado sem primeiro churn dentro de τ; não é ganho causal", "RMST (dias)")
    axis.set_xlabel("Horizonte τ"); axis.set_ylim(bottom=0); axis.legend(frameon=False, loc="upper left")
    path = figures_dir / "rmst-comparison.png"
    _save(fig, path); outputs.append(path)
    return outputs
