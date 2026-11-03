"""Read-only management projections and explicit operational CSV schemas."""

import csv
from datetime import datetime, timezone
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ("data/diagnosis.json", "data/final-evaluation.json", "data/diagnosis-assumptions.json")
EXPORT_FIELDS = {
    "cases": ("schema_version", "exported_at", "case_id", "run_id", "created_at", "context", "model_version",
              "predicted_category", "review_queue", "outcome", "case_review_state", "corrected_category",
              "case_reviewed_at", "case_reviewer_type"),
    "metrics": ("schema_version", "exported_at", "case_id", "run_id", "created_at", "model_version", "metric",
                "value", "status", "direction", "reason", "category", "review_state"),
    "reviews": ("schema_version", "exported_at", "event_id", "case_id", "run_id", "metric", "decision",
                "corrected_category", "reviewer_type", "created_at"),
}


def load_reports(root=ROOT):
    """No raw data, model, runtime database or individual final-test cases read."""
    return tuple(json.loads((root / name).read_text()) for name in SOURCES)


def business_actions(diagnosis, evaluation, include_benchmark=True):
    overall = diagnosis["overall"]
    critical = next(r for r in diagnosis["single_dimension_groups"] if r["Ticket Priority"] == "Critical")
    standard = evaluation["assisted"]
    actions = [
        {"Achado": f"{critical['nonclosed']:,} Critical não encerrados".replace(",", "."),
         "Ação": "Conferir status/prioridade e quais tickets ainda estão ativos",
         "Responsável sugerido": "Liderança de suporte", "Indicador do piloto": "Idade por estado, reabertura e SLA após instrumentação"},
        {"Achado": f"{overall['pending_customer_response']:,} aguardam o cliente".replace(",", "."),
         "Ação": "Separar espera do cliente de esforço do agente; testar acompanhamento de pendências",
         "Responsável sugerido": "Operação", "Indicador do piloto": "Retorno após contato e minutos ativos"},
        {"Achado": f"{overall['low_csat_count']}/{overall['rated_closed']} notas são 1–2",
         "Ação": "Investigar motivos das notas e cobertura da pesquisa",
         "Responsável sugerido": "CX", "Indicador do piloto": "Notas, motivos e cobertura por população"},
        {"Achado": f"{standard['standard_cases']}/{evaluation['population']} sugestões padrão",
         "Ação": "Dimensionar triagem e especialistas; confirmar todas as sugestões",
         "Responsável sugerido": "Responsável pelo serviço IT", "Indicador do piloto": "Tempo total por fila, correções e erros por classe"},
        {"Achado": "Horas líquidas dependem de revisão, retrabalho e esforço fixo",
         "Ação": "Comparar fluxo atual e assistido num piloto com novos dados",
         "Responsável sugerido": "Operação e gestão", "Indicador do piloto": "Capacidade líquida medida, incluindo resultado negativo"},
    ]
    return actions if include_benchmark else actions[:3] + actions[4:]


def operational_export(repository, filtered_metrics, exported_at=None):
    """One case row per run; all review events for selected runs, metrics filtered."""
    stamp = exported_at or datetime.now(timezone.utc).isoformat()
    common = {"schema_version": "1", "exported_at": stamp}
    output = {"cases": [], "metrics": [], "reviews": []}
    for row in filtered_metrics:
        output["metrics"].append({**common, **{k: row.get(k) for k in EXPORT_FIELDS["metrics"] if k not in common}})
    for run_id in dict.fromkeys(row["run_id"] for row in filtered_metrics):
        detail = repository.get_run(run_id)
        run, events = detail["result"], detail["reviews"]
        case_events = [e for e in events if e["metric"] is None]
        latest = case_events[-1] if case_events else {}
        output["cases"].append({**common, **{k: run.get(k) for k in EXPORT_FIELDS["cases"] if k not in common},
                                "case_review_state": latest.get("decision", "pending"),
                                "corrected_category": latest.get("corrected_category"),
                                "case_reviewed_at": latest.get("created_at"), "case_reviewer_type": latest.get("reviewer_type")})
        for event in events:
            output["reviews"].append({**common, **{k: event.get(k) for k in EXPORT_FIELDS["reviews"] if k not in common},
                                      "case_id": run["case_id"]})
    return output


def csv_bytes(kind, rows):
    """UTF-8 BOM for spreadsheet import; no original text/name/review free text."""
    def safe(value):
        if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + value
        return value
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=EXPORT_FIELDS[kind], extrasaction="raise")
    writer.writeheader()
    writer.writerows({k: safe(v) for k, v in row.items()} for row in rows)
    return buffer.getvalue().encode("utf-8-sig")
