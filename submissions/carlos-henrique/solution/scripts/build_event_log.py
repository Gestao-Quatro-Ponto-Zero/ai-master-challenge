"""Build and validate the canonical RavenStack temporal event log."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Mapping

import pandas as pd


SOLUTION_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = SOLUTION_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from data_audit import compute_sha256  # noqa: E402
from data_loader import load_all, validate_all_present  # noqa: E402
from event_log import BuildResult, build_event_log, write_parquet_outputs  # noqa: E402
from event_rules import (  # noqa: E402
    EVENT_ORDER,
    RULES_VERSION,
    SCHEMA_VERSION,
    TIMEZONE_POLICY,
    event_dictionary,
)


ARTIFACTS_DIR = SOLUTION_ROOT / "artifacts"
REPORTS_DIR = SOLUTION_ROOT / "reports"
PROCESSED_DIR = SOLUTION_ROOT / "data" / "processed"
RAW_MANIFEST_PATH = ARTIFACTS_DIR / "raw_file_manifest.json"
BASE_COMMIT = "b9f341b92af080e4abf30282171994905cf0a780"


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_markdown(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8", newline="\n")


def _relative(path: Path) -> str:
    return path.relative_to(SOLUTION_ROOT).as_posix()


def _validate_source_hashes() -> tuple[dict[str, str], str]:
    if not RAW_MANIFEST_PATH.is_file():
        raise RuntimeError("Phase 1 raw_file_manifest.json is required.")
    manifest = json.loads(RAW_MANIFEST_PATH.read_text(encoding="utf-8"))
    expected = {str(item["table"]): item for item in manifest["files"]}
    actual: dict[str, str] = {}
    generation_basis: list[str] = []
    for table, path in validate_all_present().items():
        digest = compute_sha256(path)
        actual[table] = digest
        if table not in expected or digest != expected[table]["sha256"]:
            raise RuntimeError(f"Source hash mismatch for {table}; build aborted.")
        generation_basis.append(str(expected[table]["modified_at_utc"]))
    return dict(sorted(actual.items())), max(generation_basis)


def _hash_outputs(paths: list[Path]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for path in sorted(paths, key=lambda item: _relative(item)):
        result[_relative(path)] = {
            "bytes": path.stat().st_size,
            "sha256": compute_sha256(path),
        }
    return result


def _quality_table(counts: Mapping[str, int]) -> str:
    lines = ["| classificação | eventos |", "|---|---:|"]
    for key, value in sorted(counts.items()):
        lines.append(f"| `{key}` | {value:,} |".replace(",", "."))
    return "\n".join(lines)


def _event_table(counts: Mapping[str, int]) -> str:
    lines = ["| tipo de evento | eventos |", "|---|---:|"]
    for key, value in sorted(counts.items()):
        lines.append(f"| `{key}` | {value:,} |".replace(",", "."))
    return "\n".join(lines)


def _source_reconciliation_table(sources: Mapping[str, Mapping[str, int]]) -> str:
    lines = [
        "| fonte | registros | oportunidades | ativos | quarentena | removidos | diferença |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for source, item in sorted(sources.items()):
        lines.append(
            f"| `{source}` | {item['source_records']} | {item['event_opportunities']} | "
            f"{item['active_events']} | {item['quarantined_events']} | "
            f"{item['exact_duplicate_event_opportunities_removed']} | {item['unexplained_difference']} |"
        )
    return "\n".join(lines)


def _render_validation_report(result: BuildResult) -> str:
    reconciliation = result.reconciliation
    quality = result.temporal_quality
    totals = reconciliation["totals"]
    episode = quality["episodes"]
    duplicate = result.duplicate_summary
    return f"""# Validação do event log temporal — Fase 2

## 1. Objetivo

Validar uma camada temporal canônica, reproduzível e rastreável, sem executar diagnóstico de churn, journey mining, análise de receita, survival analysis ou grafo.

## 2. Fontes

Foram carregadas as cinco fontes oficiais com validação de presença e SHA-256 contra o manifest da Fase 1. Os CSVs permaneceram read-only.

## 3. Modelo do event log

Cada evento preserva entidade, tempo, tipo, origem, linha física, regra de geração, qualidade e vínculo opcional a episódio. Churn permanece no grão de conta; `candidate_subscription_id` é somente uma atribuição auditável.

## 4. Tipos de evento

{_event_table(reconciliation['events_by_type'])}

Não foram criados eventos comportamentais derivados, upgrade ou downgrade, pois não existe timestamp inequívoco para essas transições no snapshot.

## 5. Volume por evento

- oportunidades de evento: {totals['event_opportunities']};
- eventos gerados: {totals['events_generated']};
- event log ativo: {reconciliation['active_event_count']};
- quarentena: {totals['quarantined_events']}.

## 6. Reconciliação

{_source_reconciliation_table(reconciliation['sources'])}

A reconciliação usa oportunidades de evento porque uma assinatura pode gerar início e fim e um ticket pode gerar abertura e fechamento. Diferença não explicada: **{totals['unexplained_difference']}**.

## 7. Qualidade

{_quality_table(quality['quality_status_counts'])}

Eventos com cronologia impossível foram preservados na quarentena. Warnings permanecem utilizáveis apenas com filtros explícitos.

## 8. Duplicatas

- duplicatas exatas removidas: {duplicate['exact_duplicate_rows_removed']};
- linhas afetadas por `DUPLICATE_SOURCE_ID`: {duplicate['duplicate_source_id_rows']};
- excedentes de `usage_id`: {duplicate['duplicate_source_id_excess']};
- linhas afetadas por `DUPLICATE_CANDIDATE_KEY`: {duplicate['duplicate_candidate_key_rows']};
- excedentes da chave candidata: {duplicate['duplicate_candidate_key_excess']}.

Registros distintos com ID ou chave candidata repetidos foram preservados e sinalizados; nenhuma soma ou descarte silencioso foi aplicado.

## 9. Churn recorrente

- contas sem churn explícito: {quality['churn_recurrence']['accounts_without_churn']};
- contas com um churn: {quality['churn_recurrence']['accounts_with_one_churn']};
- contas com múltiplos churns: {quality['churn_recurrence']['accounts_with_multiple_churns']};
- máximo de churns por conta: {quality['churn_recurrence']['maximum_churns_per_account']}.

## 10. Reativação

Foram preservadas {quality['reactivation']['events']} reativações explícitas em {quality['reactivation']['accounts']} contas. Reativações sem churn anterior utilizável: {quality['reactivation']['without_prior_churn']}.

## 11. Episódios

- episódios: {episode['total']};
- abertos: {episode['open']};
- encerrados: {episode['closed']};
- com sobreposição: {episode['overlapping']}.

Cada `subscription_id` permanece um episódio independente; churn não encerra assinatura automaticamente.

## 12. Limitações

- datas sem hora são representadas à meia-noite, sem inferência intradiária;
- o timezone é `NAIVE_SOURCE_TIME`;
- grande parte dos usos contradiz o início/fim da assinatura e fica em quarentena;
- múltiplas assinaturas ativas tornam a atribuição de churn ambígua;
- snapshot não prova estabilidade histórica dos IDs nem disponibilidade as-of de atributos mutáveis.

## 13. Uso permitido

Reconstrução de jornadas, diagnóstico descritivo e análises temporais futuras usando apenas eventos ativos, cutoffs as-of e segmentação explícita por qualidade.

## 14. Uso proibido

Usar quarentena como evidência válida, interpretar desempate como causal, transformar flags snapshot em eventos, usar texto livre, atribuir churn ambiguamente ou calcular features com informação posterior ao cutoff.

## 15. Gate para Fase 3

**`PASS_WITH_WARNINGS`**. O event log está reconciliado e auditável, mas qualquer diagnóstico deve excluir quarentena, respeitar warnings e declarar a política temporal utilizada.
"""


def _render_temporal_rules(result: BuildResult) -> str:
    flags = result.temporal_quality["quality_flag_counts"]
    flag_lines = "\n".join(f"- `{key}`: {value};" for key, value in sorted(flags.items()))
    return f"""# Regras temporais canônicas — Fase 2

## Relógio canônico

- tipo: `datetime64[ns]`;
- timezone: `{TIMEZONE_POLICY}`;
- datas sem hora: meia-noite como representação técnica;
- granularidade de datas: diária;
- nenhuma sequência intradiária é inferida para datas sem hora.

## Ordenação no mesmo dia

A ordem técnica é: ACCOUNT_CREATED, SUBSCRIPTION_STARTED, FEATURE_USED, SUPPORT_TICKET_OPENED, SUPPORT_TICKET_CLOSED, CHURN_RECORDED, REACTIVATION_RECORDED e SUBSCRIPTION_ENDED. O valor está em `event_order_on_same_day`, não representa causalidade e recebe `SAME_DAY_ORDER_ASSIGNED` quando há colisão de conta/data.

## Regras por fonte

- accounts: `signup_date` gera no máximo um `ACCOUNT_CREATED` por registro não duplicado;
- subscriptions: `start_date` gera `SUBSCRIPTION_STARTED`; `end_date` não nulo gera `SUBSCRIPTION_ENDED`;
- feature_usage: `usage_date` gera `FEATURE_USED` e resolve conta exclusivamente pela FK validada de assinatura;
- support_tickets: `submitted_at` gera abertura e `closed_at` não nulo gera fechamento;
- churn_events: `is_reactivation=false` gera churn e `true` gera reativação explícita.

Não são gerados upgrade, downgrade, satisfação separada ou eventos comportamentais derivados por ausência de timestamp inequívoco.

## Quarentena

IDs obrigatórios ausentes, timestamp inválido, evento pré-conta, uso pré/pós-assinatura, fim anterior ao início, fechamento anterior à abertura e reativação sem churn anterior utilizável são fatais. Churn anterior à primeira assinatura também fica em quarentena por política conservadora.

## Warnings

IDs/chaves candidatas de uso repetidos, múltiplas assinaturas ativas, churn sem assinatura ativa, atribuição ambígua, ticket pós-churn, assinatura aberta após churn e desempate no mesmo dia permanecem visíveis como `VALID_WITH_WARNING` quando não coexistem com erro fatal.

## Deduplicação

Somente duplicatas integrais secundárias podem ser removidas. Duplicatas distintas de `usage_id` ou da chave candidata são preservadas, recebem IDs determinísticos diferentes por `source_row_number` e não são agregadas.

## Churn recorrente e reativação

Churn é evento recorrente de conta com sequência, anterior, próximo e dias desde o anterior. Reativação é explícita, separada e não apaga churn. Ausência de churn futuro não implica retenção.

## Atribuição a assinatura

Somente uma assinatura ativa produz `EXACT_ACTIVE_MATCH` e `candidate_subscription_id`. Múltiplas ativas, ausência de ativa e casos ambíguos permanecem sem vínculo inventado.

## Leakage

Não entram no event log `account_name`, `feedback_text`, `reason_code`, refund, churn flags, upgrade/downgrade flags ou status snapshot sem timestamp. Métricas de fechamento só aparecem no evento de fechamento.

## Flags observadas

{flag_lines}

## Limitações

O snapshot contém conflitos temporais materiais, não declara timezone e não prova a disponibilidade histórica de campos mutáveis. A ordenação técnica deve ser tratada como desempate, nunca como evidência causal.
"""


def _render_quarantine_report(result: BuildResult) -> str:
    quarantine = result.quarantined_events
    total = len(quarantine)
    generated = result.reconciliation["totals"]["events_generated"]
    source_counts = quarantine["source_table"].value_counts().sort_index().to_dict()
    flag_counts: dict[str, int] = {}
    for serialized in quarantine["quality_flags"]:
        for flag in str(serialized).split("|"):
            if flag:
                flag_counts[flag] = flag_counts.get(flag, 0) + 1
    source_lines = "\n".join(
        f"- `{source}`: {count} ({count / generated:.2%} dos eventos gerados);"
        for source, count in sorted(source_counts.items())
    )
    flag_lines = "\n".join(
        f"- `{flag}`: {count};" for flag, count in sorted(flag_counts.items())
    )
    return f"""# Relatório de quarentena temporal — Fase 2

## Total

Eventos em quarentena: **{total}** de {generated} ({total / generated:.2%}).

## Por fonte

{source_lines}

## Motivos

{flag_lines}

Um evento pode possuir mais de um motivo; por isso a soma das flags não representa eventos únicos.

## Impacto

A quarentena reduz a cobertura analítica, principalmente de uso e suporte, mas impede que cronologias impossíveis contaminem sequências, features as-of e conclusões futuras.

## Possibilidade de recuperação

- eventos pré/pós-assinatura exigem correção ou explicação da fonte e não podem ser reativados por conveniência;
- eventos pré-conta exigem reconciliação de calendários ou identidade;
- churn anterior à primeira assinatura exige definição de produto ou correção upstream;
- IDs/timestamps inválidos exigem reparo rastreável na origem;
- duplicatas distintas permanecem no log ativo com warning e não dependem de recuperação.

## Recomendação futura

Manter a quarentena imutável por build, monitorar taxas por regra e somente promover registros mediante evidência upstream versionada. Nenhum ID completo, nome ou texto livre é listado neste relatório.
"""


def build_outputs() -> dict[str, Any]:
    """Run the complete deterministic Phase 2 build."""

    if importlib.util.find_spec("pyarrow") is None:
        raise RuntimeError("PyArrow is required to write the authorized Parquet outputs.")
    source_hashes, generation_timestamp = _validate_source_hashes()
    frames, _ = load_all()
    result = build_event_log(frames)
    if result.reconciliation["totals"]["unexplained_difference"] != 0:
        raise RuntimeError("Critical reconciliation failure: unexplained difference is non-zero.")

    parquet_paths = write_parquet_outputs(result, PROCESSED_DIR)
    dictionary_path = ARTIFACTS_DIR / "event_type_dictionary.json"
    quality_path = ARTIFACTS_DIR / "temporal_quality_summary.json"
    reconciliation_path = ARTIFACTS_DIR / "reconciliation_report.json"
    validation_path = REPORTS_DIR / "event-log-validation.md"
    rules_path = REPORTS_DIR / "temporal-rules.md"
    quarantine_path = REPORTS_DIR / "quarantine-report.md"

    _write_json(dictionary_path, event_dictionary())
    quality_payload = dict(result.temporal_quality)
    quality_payload["duplicate_summary"] = result.duplicate_summary
    _write_json(quality_path, quality_payload)
    _write_json(reconciliation_path, result.reconciliation)
    _write_markdown(validation_path, _render_validation_report(result))
    _write_markdown(rules_path, _render_temporal_rules(result))
    _write_markdown(quarantine_path, _render_quarantine_report(result))

    hashable_outputs = list(parquet_paths.values()) + [
        dictionary_path,
        quality_path,
        reconciliation_path,
        validation_path,
        rules_path,
        quarantine_path,
    ]
    output_hashes = _hash_outputs(hashable_outputs)
    combined = pd.concat(
        [result.event_log, result.quarantined_events], ignore_index=True
    )
    manifest = {
        "generation_timestamp": generation_timestamp,
        "generation_timestamp_basis": "maximum source modified_at_utc from the Phase 1 raw manifest",
        "schema_version": SCHEMA_VERSION,
        "rules_version": RULES_VERSION,
        "base_commit": BASE_COMMIT,
        "source_hashes": source_hashes,
        "output_hashes": output_hashes,
        "outputs": {
            "event_log": {"rows": len(result.event_log), "columns": len(result.event_log.columns)},
            "quarantined_events": {"rows": len(result.quarantined_events), "columns": len(result.quarantined_events.columns)},
            "subscription_episodes": {"rows": len(result.subscription_episodes), "columns": len(result.subscription_episodes.columns)},
        },
        "temporal_period": {
            "minimum": pd.to_datetime(combined["event_time"], errors="coerce").min().isoformat(),
            "maximum": pd.to_datetime(combined["event_time"], errors="coerce").max().isoformat(),
        },
        "event_types": sorted(combined["event_type"].unique().tolist()),
        "timezone_policy": TIMEZONE_POLICY,
        "same_day_order_policy": dict(EVENT_ORDER),
        "quarantine_policy": "fatal temporal or identity flags are separated; records are never silently discarded",
        "reconciliation_unexplained_difference": result.reconciliation["totals"]["unexplained_difference"],
    }
    manifest_path = ARTIFACTS_DIR / "event_log_manifest.json"
    _write_json(manifest_path, manifest)
    return {
        "result": result,
        "manifest_path": manifest_path,
        "all_outputs": hashable_outputs + [manifest_path],
    }


def main() -> int:
    payload = build_outputs()
    result: BuildResult = payload["result"]
    totals = result.reconciliation["totals"]
    print("build-status=OK")
    print(f"events-generated={totals['events_generated']}")
    print(f"events-active={len(result.event_log)}")
    print(f"events-quarantined={len(result.quarantined_events)}")
    print(f"episodes={len(result.subscription_episodes)}")
    print(f"unexplained-difference={totals['unexplained_difference']}")
    print("phase3-gate=PASS_WITH_WARNINGS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
