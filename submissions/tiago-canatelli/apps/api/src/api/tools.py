"""Tools de análise compartilhadas pelo assistente (Claude) e pelo MCP."""

import json
from collections.abc import Callable
from typing import Any

from api import db


def get_kpi_overview() -> dict[str, Any]:
    """Números do painel geral: contas ativas, MRR, MRR em risco, churn, CSAT, concentração."""
    return {"source": "api.kpi_overview", "data": db.read_view("kpi_overview")}


def get_kpi(view: str) -> dict[str, Any]:
    """Lê uma view de KPI do schema api (ex.: tenure_hazard, cohort, persona_summary)."""
    return {"source": f"api.{view}", "data": db.read_view(view, limit=300)}


def list_at_risk_accounts(limit: int = 10, persona: str | None = None) -> dict[str, Any]:
    """Contas ativas ordenadas por MRR em risco em 90 dias, com drivers e ação sugerida."""
    data = db.rows(
        """select * from api.risk_queue where (%s::text is null or persona = %s)
           order by mrr_at_risk_90d desc limit %s""",
        (persona, persona, min(limit, 50)),
    )
    return {"source": "api.risk_queue", "data": data}


def get_account_health(account_id: str) -> dict[str, Any]:
    """Visão 360 de uma conta: estado, persona, risco, drivers, suporte, uso e último churn."""
    return {
        "source": "api.account_360",
        "data": db.read_view("account_360", {"account_id": account_id}),
    }


def query_analytics(sql: str) -> dict[str, Any]:
    """SELECT livre (só leitura) sobre views do schema api; máx. 500 linhas."""
    return {"source": "api.run_readonly_query", "sql": sql, "data": db.readonly_query(sql)}


TOOLS: dict[str, Callable[..., dict[str, Any]]] = {
    "get_kpi_overview": get_kpi_overview,
    "get_kpi": get_kpi,
    "list_at_risk_accounts": list_at_risk_accounts,
    "get_account_health": get_account_health,
    "query_analytics": query_analytics,
}

VIEWS_HELP = (
    "tenure_hazard (quarter, tenure_bucket, churn_per_100_account_months), cohort (signup_cohort, "
    "churn_3m_pct, churn_6m_pct), churn_type, churn_by_segment (segment_type, segment_value), "
    "support_health, silent_churn, reactivation, loss_concentration, feature_health, "
    "persona_summary, persona_catalog, usage_quarterly, revenue_monthly, churn_reason_vs_behavior, "
    "dq_results, catalog_tables, catalog_columns"
)

# Definições para a Claude API (JSON Schema, strict).
CLAUDE_TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_kpi_overview",
        "description": "Números-chave atuais do churn da RavenStack (painel do CEO).",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "name": "get_kpi",
        "description": f"Lê uma view de KPI. Views: {VIEWS_HELP}.",
        "input_schema": {
            "type": "object",
            "properties": {
                "view": {"type": "string", "description": "Nome da view do schema api."}
            },
            "required": ["view"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "name": "list_at_risk_accounts",
        "description": "Fila de contas ativas por MRR em risco (90 dias), com drivers e ação sugerida.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Quantas contas (máx. 50)."},
                "persona": {
                    "type": ["string", "null"],
                    "description": "Filtrar por persona (opcional).",
                },
            },
            "required": ["limit", "persona"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "name": "get_account_health",
        "description": "Visão 360 de uma conta pelo account_id (ex.: A-c70870).",
        "input_schema": {
            "type": "object",
            "properties": {"account_id": {"type": "string"}},
            "required": ["account_id"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "name": "query_analytics",
        "description": f"Um único SELECT sobre views do schema api (sem prefixo de schema). Views: {VIEWS_HELP}, risk_queue, account_360.",
        "input_schema": {
            "type": "object",
            "properties": {"sql": {"type": "string"}},
            "required": ["sql"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


def run_tool(name: str, args: dict[str, Any]) -> str:
    try:
        result = TOOLS[name](**args)
        return json.dumps(result, ensure_ascii=False, default=str)[:60000]
    except Exception as exc:  # devolvido ao modelo como erro de tool
        return json.dumps({"error": str(exc).splitlines()[0]}, ensure_ascii=False)
