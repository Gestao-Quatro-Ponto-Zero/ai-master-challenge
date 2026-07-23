"""Run the deterministic governed Phase 3 diagnostic pipeline."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd


SOLUTION_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = SOLUTION_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from business_diagnostics import (  # noqa: E402
    build_attention_segments,
    cohort_diagnostics,
    data_health,
    product_usage_diagnostics,
    revenue_diagnostics,
    support_diagnostics,
)
from churn_diagnostics import (  # noqa: E402
    build_churn_diagnostics,
    build_reactivation_diagnostics,
    usable_events,
)
from diagnostic_features import build_account_features, build_feature_tables  # noqa: E402
from finding_engine import build_findings, build_sensitivity_analysis  # noqa: E402
from journey_diagnostics import build_journey_summary  # noqa: E402


PROCESSED = SOLUTION_ROOT / "data" / "processed"
RAW = SOLUTION_ROOT / "data" / "raw"
ARTIFACTS = SOLUTION_ROOT / "artifacts"
REPORTS = SOLUTION_ROOT / "reports"
EXPECTED_BASE_COMMIT = "75be8ef0663f0f49b425092735ffe0a3c6ed65f6"
JSON_NAMES = (
    "diagnostic_summary.json",
    "churn_diagnostics.json",
    "reactivation_diagnostics.json",
    "product_usage_diagnostics.json",
    "support_diagnostics.json",
    "revenue_diagnostics.json",
    "cohort_diagnostics.json",
    "journey_summary.json",
    "executive_findings.json",
    "sensitivity_analysis.json",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_inputs() -> dict[str, Any]:
    manifest_path = ARTIFACTS / "event_log_manifest.json"
    raw_manifest_path = ARTIFACTS / "raw_file_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    raw_manifest = json.loads(raw_manifest_path.read_text(encoding="utf-8"))
    if manifest["reconciliation_unexplained_difference"] != 0:
        raise RuntimeError("Phase 2 reconciliation is not zero.")
    verified: dict[str, bool] = {}
    for relative, metadata in manifest["output_hashes"].items():
        path = SOLUTION_ROOT / relative
        verified[relative] = path.is_file() and _sha256(path) == metadata["sha256"]
    for item in raw_manifest["files"]:
        path = RAW / item["file"]
        verified[f"data/raw/{item['file']}"] = path.is_file() and _sha256(path) == item["sha256"]
    if not all(verified.values()):
        failed = sorted(key for key, value in verified.items() if not value)
        raise RuntimeError(f"Input hash validation failed: {failed}")
    return {
        "expected_phase3_base_commit": EXPECTED_BASE_COMMIT,
        "phase2_manifest_base_commit": manifest["base_commit"],
        "verified_files": len(verified),
        "all_hashes_match": True,
        "reconciliation_unexplained_difference": 0,
    }


def _clean(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(item) for item in value]
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        return pd.Timestamp(value).isoformat()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return None if math.isnan(float(value)) or math.isinf(float(value)) else float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if value is pd.NA or value is pd.NaT:
        return None
    return value


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(_clean(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _state_table(churn: Mapping[str, Any]) -> str:
    lines = ["| Estado principal | Contas | Proporção observada |", "|---|---:|---:|"]
    for item in churn["primary_outcomes"]:
        lines.append(f"| `{item['outcome']}` | {item['accounts']} | {item['observed_proportion']:.2%} |")
    return "\n".join(lines)


def _finding_lines(findings: Mapping[str, Any]) -> str:
    lines = []
    for item in findings["findings"]:
        lines.append(
            f"- **{item['finding_id']} — {item['title']}.** {item['statement']} "
            f"Confiança `{item['confidence_level']}`; sensibilidade `{item['sensitivity_status']}`."
        )
    return "\n".join(lines) or "- Nenhum finding passou o gate."


def _segment_table(segments: pd.DataFrame) -> str:
    lines = ["| Situação | Contas | MRR associado | Prioridade |", "|---|---:|---:|---|"]
    for _, row in segments.iterrows():
        lines.append(
            f"| `{row['segment_name']}` | {row['account_count']} | {row['associated_mrr']:.2f} | `{row['priority_level']}` |"
        )
    return "\n".join(lines)


def render_reports(payloads: Mapping[str, Any], segments: pd.DataFrame) -> dict[str, str]:
    summary = payloads["diagnostic_summary.json"]
    health = summary["data_health"]
    churn = payloads["churn_diagnostics.json"]
    react = payloads["reactivation_diagnostics.json"]
    product = payloads["product_usage_diagnostics.json"]
    support = payloads["support_diagnostics.json"]
    revenue = payloads["revenue_diagnostics.json"]
    cohorts = payloads["cohort_diagnostics.json"]
    journey = payloads["journey_summary.json"]
    findings = payloads["executive_findings.json"]
    sensitivity = payloads["sensitivity_analysis.json"]
    top_journey = journey["top_complete_journeys"][0] if journey["top_complete_journeys"] else None
    top_sequence = " → ".join(top_journey["sequence"]) if top_journey else "não disponível"
    top_support = top_journey["account_support"] if top_journey else 0
    unstable = sum(item["classification"] == "UNSTABLE" for item in sensitivity["comparisons"])
    executive = f"""# Diagnóstico executivo RavenStack

## 1. Executive Summary — resumo executivo

- **A leitura é utilizável com ressalvas:** {health['analytical_coverage_ratio']:.2%} dos {health['eligible_generated_events']:,} eventos gerados são analiticamente utilizáveis; a quarentena não entra em comportamento, receita ou jornadas.
- **Os estados de churn dependem fortemente dos warnings:** {churn['churn_observed_accounts']} de {churn['denominator_accounts']} contas têm churn observado na população ampliada, mas métricas instáveis não são promovidas como findings.
- **A estrutura de assinaturas exige cautela:** {health['overlapping_episode_ratio']:.2%} dos 5.000 episódios se sobrepõem e episódios abertos permanecem administrativamente censurados.
- **Ação de maior retorno e menor esforço:** corrigir cronologias upstream e validar a semântica de múltiplas assinaturas antes de operacionalizar retenção individual.

## 2. Cobertura e qualidade

Foram usados {health['valid_events']:,} eventos válidos e {health['warning_events']:,} com warning; {health['quarantined_events']:,} ficaram restritos à saúde dos dados. O indicador mede cobertura do conjunto analítico, não desempenho da RavenStack.

## 3. População

A população principal é `VALID + VALID_WITH_WARNING`; a estrita contém somente `VALID`. Ambas excluem quarentena. A janela vai de {summary['analytical_window']['minimum']} a {summary['analytical_window']['observation_end']}, com granularidade diária, tempo sem timezone e censura administrativa.

## 4. Churn observado

{_state_table(churn)}

As proporções são observadas entre contas, não taxas temporais de churn.

## 5. Churn recorrente

Há {churn['recurring_churn_accounts']} contas com dois ou mais churns utilizáveis. O intervalo mediano entre churns é {churn['intervals']['between_churns']['median_days']} dias entre {churn['intervals']['between_churns']['n']} intervalos observados.

## 6. Reativação

Há {react['reactivated_accounts']} contas com reativação explícita utilizável e {react['reactivation_events']} eventos. {react['churn_events_followed_by_reactivation']} de {react['denominator_churn_events']} churns observados possuem reativação posterior no horizonte disponível.

## 7. Uso de produto

{product['accounts_without_usage_30d']} de {product['denominator_accounts']} contas não têm uso nos 30 dias anteriores ao cutoff. Rankings usam somente categorias estruturadas de feature e comparações representam associação descritiva.

## 8. Suporte

Foram observadas {support['usable_ticket_open_events']} aberturas e {support['usable_ticket_close_events']} fechamentos utilizáveis. Satisfação está disponível em {support['satisfaction_available']} fechamentos e ausente em {support['satisfaction_missing']}.

## 9. Receita associada

O MRR somado nos episódios é {revenue['episode_mrr_total']:.2f}; {revenue['mrr_associated_with_open_episodes']:.2f} está associado a episódios abertos. Esses valores não representam automaticamente perda, recuperação ou receita reconhecida.

## 10. Coortes

Foram produzidos {cohorts['groups']} grupos por cadastro, primeira assinatura, plano inicial, MRR e uso inicial. {cohorts['small_sample_groups']} grupos têm menos de {cohorts['minimum_group_size']} contas e recebem `SMALL_SAMPLE`.

## 11. Jornadas agregadas

A jornada completa mais frequente, após colapsar duplicatas consecutivas e limitar a 12 passos, foi `{top_sequence}`, observada em {top_support} contas. Trata-se de resumo ordenado, não de mineração formal.

## 12. Situações prioritárias

{_segment_table(segments)}

As situações são regras descritivas agregadas, não scores preditivos.

## 13. Findings

{_finding_lines(findings)}

## 14. Análise de sensibilidade

Todas as métricas principais foram recalculadas nas populações estrita e ampliada. {unstable} de {len(sensitivity['comparisons'])} métricas numéricas foram classificadas `UNSTABLE`; nenhuma delas sustenta finding principal.

## 15. Limitações

- timestamps diários e ausência de timezone impedem interpretação intradiária;
- censura administrativa e tempos de seguimento desiguais permanecem;
- warnings expandem substancialmente a cobertura de churn e reativação;
- suporte não possui atribuição única a assinatura;
- MRR associado não demonstra perda ou recuperação financeira;
- nenhuma associação aqui demonstra mecanismo explicativo.

## 16. Próximos passos

Preservar populações, cutoffs e censura na Fase 4; investigar qualidade upstream; validar a semântica de sobreposição com billing; e manter revisão humana antes de qualquer ação por conta.

**Fontes internas:** `event_log.parquet`, `subscription_episodes.parquet`, `quarantined_events.parquet` apenas para qualidade, e `ravenstack_support_tickets.csv` apenas para resolução de fechamentos utilizáveis.
"""
    health_report = f"""# Data Health — Fase 3

## 1. Cobertura

Cobertura analítica: **{health['analytical_coverage_ratio']:.2%}** ({health['valid_events'] + health['warning_events']:,}/{health['eligible_generated_events']:,}). Há eventos utilizáveis para {health['accounts_with_usable_event']} contas.

## 2. Validade

Eventos `VALID`: **{health['valid_events']:,}**. A população estrita cobre {health['strict_coverage_ratio']:.2%} dos eventos gerados.

## 3. Warnings

Eventos `VALID_WITH_WARNING`: **{health['warning_events']:,}**, equivalentes a {health['warning_ratio_among_usable']:.2%} da população utilizável. {health['subscriptions_with_warning']:,} episódios têm warning.

## 4. Quarentena

Eventos em quarentena: **{health['quarantined_events']:,}** ({health['quarantine_ratio']:.2%}); {health['accounts_affected_by_quarantine']} contas são afetadas. Eles não entram em métricas de negócio.

## 5. Impacto analítico

A cobertura reduz especialmente evidência de uso e suporte. A sobreposição atinge {health['overlapping_episode_ratio']:.2%} dos episódios e impede atribuição simples de churn ou MRR.

## 6. População estrita e ampliada

O arquivo `sensitivity_analysis.json` recalcula métricas em `VALID` e `VALID + VALID_WITH_WARNING`. Resultados `UNSTABLE` não foram promovidos.

## 7. Recomendações de governança

Corrigir cronologias na origem, versionar regras de promoção da quarentena, monitorar cobertura por evento/período/conta e validar a semântica de múltiplas assinaturas.
"""
    churn_report = f"""# Diagnóstico descritivo de churn e reativação

## População e denominador

{churn['population']}. Denominador: {churn['denominator_accounts']} contas. Proporções são observadas, não taxas temporais.

## Estados principais

{_state_table(churn)}

## Recorrência e intervalos

- churn observado: {churn['churn_observed_accounts']} contas ({churn['observed_churn_proportion']:.2%});
- churn recorrente: {churn['recurring_churn_accounts']} contas ({churn['observed_recurring_churn_proportion']:.2%});
- tempo mediano cadastro → primeiro churn: {churn['intervals']['signup_to_first_churn']['median_days']} dias;
- intervalo mediano entre churns: {churn['intervals']['between_churns']['median_days']} dias;
- intervalo mediano churn → reativação: {react['churn_to_reactivation_interval']['median_days']} dias;
- intervalo mediano reativação → novo churn: {react['reactivation_to_new_churn_interval']['median_days']} dias.

## Comparações

As comparações de uso, suporte, satisfação, MRR e assinaturas estão em `churn_diagnostics.json`, com média, mediana, quartis, diferença, razão, n e missingness.

## Ressalvas

Ausência de churn é `NO_CHURN_OBSERVED`; eventos com warning alteram materialmente os estados; nenhuma comparação demonstra mecanismo explicativo.
"""
    revenue_report = f"""# Diagnóstico descritivo de receita

## Definição

MRR é relatado como valor associado. No grão conta, `total_mrr_current` soma episódios ativos no cutoff governado; no grão episódio, MRR permanece independente.

## Totais

- MRR de episódios: {revenue['episode_mrr_total']:.2f};
- MRR em episódios abertos: {revenue['mrr_associated_with_open_episodes']:.2f};
- MRR em episódios encerrados: {revenue['mrr_associated_with_closed_episodes']:.2f};
- MRR no cutoff de contas com churn observado: {revenue['mrr_associated_with_churned_accounts']:.2f};
- MRR no cutoff de contas reativadas: {revenue['mrr_associated_with_reactivated_accounts']:.2f}.

## Faixas e estados

Faixas usam quartis de MRR ativo no cutoff, com desempate estável. Valores detalhados por estado e faixa estão em `revenue_diagnostics.json`.

## Limitações

Sobreposição torna MRR de episódios não aditivo como exposição de conta. Os valores não comprovam perda, recuperação ou reconhecimento financeiro.
"""
    journey_report = f"""# Jornadas agregadas descritivas

## Método

Eventos consecutivos repetidos são colapsados, a ordem estável é preservada e cada sequência é limitada a 12 passos. Quarentena é excluída.

## Jornadas completas

Top 1: `{top_sequence}` — {top_support}/{journey['denominators']['complete_accounts']} contas.

## Prefixos pré-churn

Foram resumidas {journey['denominators']['accounts_with_first_churn']} contas com prefixo até o primeiro churn.

## Churn e reativação

Há {journey['denominators']['accounts_with_churn_reactivation_pair']} contas com sequência churn → reativação e {journey['denominators']['accounts_with_post_reactivation_sequence']} com sequência pós-reativação.

## Suporte e limitações

Cada ranking registra suporte absoluto, relativo e denominador em `journey_summary.json`. A ordem no mesmo dia é técnica; as sequências são agregados descritivos, sem mineração formal ou grafo.
"""
    return {
        "executive-diagnostic.md": executive,
        "data-health.md": health_report,
        "churn-diagnostic.md": churn_report,
        "revenue-diagnostic.md": revenue_report,
        "journey-diagnostic.md": journey_report,
    }



def _pythonize_string_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Avoid expensive Arrow scalar slicing in bounded account/episode loops."""

    work = frame.copy()
    for column in work.columns:
        if str(work[column].dtype) == "str":
            work[column] = work[column].astype(object)
    return work

def validate_outputs(accounts: pd.DataFrame, subscriptions: pd.DataFrame, segments: pd.DataFrame, payloads: Mapping[str, Any]) -> None:
    if len(accounts) != 500 or accounts["account_id"].nunique() != 500:
        raise AssertionError("Account feature validation failed.")
    if len(subscriptions) != 5000 or subscriptions["episode_id"].nunique() != 5000:
        raise AssertionError("Subscription feature validation failed.")
    if len(segments) > 5 or "account_id" in segments.columns:
        raise AssertionError("Attention segment governance failed.")
    forbidden = {"account_name", "feedback_text", "reason_code", "refund_amount_usd", "churn_flag"}
    if not forbidden.isdisjoint(accounts.columns) or not forbidden.isdisjoint(subscriptions.columns):
        raise AssertionError("Leakage/privacy validation failed.")
    if set(payloads) != set(JSON_NAMES):
        raise AssertionError("Mandatory artifact set is incomplete.")
    if payloads["diagnostic_summary.json"]["input_validation"]["reconciliation_unexplained_difference"] != 0:
        raise AssertionError("Reconciliation validation failed.")


def build_outputs() -> dict[str, Any]:
    input_validation = validate_inputs()
    events = _pythonize_string_columns(pd.read_parquet(PROCESSED / "event_log.parquet"))
    quarantine = _pythonize_string_columns(pd.read_parquet(PROCESSED / "quarantined_events.parquet"))
    episodes = _pythonize_string_columns(pd.read_parquet(PROCESSED / "subscription_episodes.parquet"))
    raw_support = pd.read_csv(RAW / "ravenstack_support_tickets.csv")

    print("stage=account-and-subscription-features-main", flush=True)
    main = build_feature_tables(events, episodes, quarantine, raw_support, strict=False)
    print("stage=account-features-strict", flush=True)
    strict_accounts = build_account_features(events, episodes, quarantine, raw_support, strict=True)
    print("stage=diagnostics", flush=True)
    health = data_health(events, quarantine, episodes)
    main_events = usable_events(events)
    churn = build_churn_diagnostics(main.accounts, main_events)
    reactivation = build_reactivation_diagnostics(main.accounts, main_events)
    product = product_usage_diagnostics(main.accounts, events)
    support = support_diagnostics(main.accounts, events)
    revenue = revenue_diagnostics(main.accounts, main.subscriptions)
    cohorts = cohort_diagnostics(main.accounts, main.subscriptions)
    journeys = build_journey_summary(events)
    strict_journeys = build_journey_summary(events, strict=True)
    sensitivity = build_sensitivity_analysis(main.accounts, strict_accounts, journeys, strict_journeys)
    findings = build_findings(health, product, support, revenue, sensitivity)
    segments = build_attention_segments(main.accounts)
    print("stage=outputs", flush=True)
    summary = {
        "methodology": "Governed descriptive diagnosis at separate account, episode and event grains; no prediction, survival model, graph or causal claim.",
        "population": {
            "main": "VALID + VALID_WITH_WARNING; quarantine excluded",
            "strict": "VALID only; quarantine excluded",
            "quarantine": "Data health only",
        },
        "analytical_window": {
            "minimum": pd.to_datetime(main_events["event_time"]).min(),
            "maximum": pd.to_datetime(main_events["event_time"]).max(),
            "observation_end": main.observation_end,
            "granularity": "DAILY_WITH_SOURCE_DATETIME_WHERE_AVAILABLE",
            "timezone": "NAIVE_SOURCE_TIME",
            "censoring": "ADMINISTRATIVE_AT_OBSERVATION_END",
        },
        "input_validation": input_validation,
        "data_health": health,
        "outputs": {
            "account_rows": int(len(main.accounts)),
            "episode_rows": int(len(main.subscriptions)),
            "attention_segments": int(len(segments)),
            "principal_findings": int(findings["finding_count"]),
        },
        "gate": "PASS_WITH_WARNINGS",
        "limitations": [
            "Warning events materially affect outcome coverage.",
            "Administrative censoring and daily timestamps constrain interpretation.",
            "Quarantine is excluded from all behavior, revenue and journey evidence.",
        ],
    }
    payloads: dict[str, Any] = {
        "diagnostic_summary.json": summary,
        "churn_diagnostics.json": churn,
        "reactivation_diagnostics.json": reactivation,
        "product_usage_diagnostics.json": product,
        "support_diagnostics.json": support,
        "revenue_diagnostics.json": revenue,
        "cohort_diagnostics.json": cohorts,
        "journey_summary.json": journeys,
        "executive_findings.json": findings,
        "sensitivity_analysis.json": sensitivity,
    }
    validate_outputs(main.accounts, main.subscriptions, segments, payloads)

    main.accounts.to_parquet(PROCESSED / "account_diagnostic_features.parquet", index=False)
    main.subscriptions.to_parquet(PROCESSED / "subscription_diagnostic_features.parquet", index=False)
    segments.to_parquet(PROCESSED / "retention_attention_segments.parquet", index=False)
    for name, payload in payloads.items():
        _write_json(ARTIFACTS / name, payload)
    for name, content in render_reports(payloads, segments).items():
        (REPORTS / name).write_text(content.strip() + "\n", encoding="utf-8", newline="\n")
    return {"payloads": payloads, "accounts": main.accounts, "subscriptions": main.subscriptions, "segments": segments}


def main() -> int:
    result = build_outputs()
    health = result["payloads"]["diagnostic_summary.json"]["data_health"]
    print("diagnostics-status=OK")
    print(f"accounts={len(result['accounts'])}")
    print(f"episodes={len(result['subscriptions'])}")
    print(f"analytical-coverage={health['analytical_coverage_ratio']:.6f}")
    print(f"findings={result['payloads']['executive_findings.json']['finding_count']}")
    print("phase4-gate=PASS_WITH_WARNINGS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
