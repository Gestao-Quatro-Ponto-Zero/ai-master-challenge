"""Configuração e acesso ao banco (Supabase). Toda leitura passa pelo schema api."""

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

MONOREPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=MONOREPO_ROOT / ".env", extra="ignore")

    database_url: SecretStr
    anthropic_api_key: SecretStr | None = None
    auth_secret: SecretStr | None = None  # assina os tokens de login do painel
    mcp_token: SecretStr | None = None  # bearer do MCP remoto
    cron_token: SecretStr | None = None  # chamado pelo pg_cron do Supabase (POST /ingest/cron)
    claude_model: str = "claude-opus-5-5"
    claude_effort: str = "medium"
    cors_origins: str = "*"


settings = Settings()  # type: ignore[call-arg]
_pool: ConnectionPool | None = None

# Views que o painel pode ler diretamente.
READABLE = {
    "kpi_overview",
    "revenue_monthly",
    "tenure_hazard",
    "cohort",
    "churn_type",
    "churn_by_segment",
    "support_health",
    "silent_churn",
    "reactivation",
    "loss_concentration",
    "feature_health",
    "persona_summary",
    "persona_catalog",
    "churn_reason_vs_behavior",
    "usage_quarterly",
    "account_360",
    "risk_queue",
    "ingestion_runs",
    "ingestion_steps",
    "dq_results",
    "catalog_tables",
    "catalog_columns",
    "prompts",
    "profiles",
}


def pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            settings.database_url.get_secret_value(),
            min_size=1,
            max_size=5,
            open=True,
            kwargs={"prepare_threshold": None, "row_factory": dict_row},
        )
    return _pool


def _clean(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    return value


def rows(sql: "str | psycopg.sql.Composable", params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with pool().connection() as conn:
        cur = conn.execute(sql, params)  # type: ignore[arg-type]
        return [{k: _clean(v) for k, v in r.items()} for r in cur.fetchall()]  # type: ignore[union-attr]


def read_view(
    name: str, where: dict[str, str] | None = None, limit: int = 2000
) -> list[dict[str, Any]]:
    if name not in READABLE:
        raise KeyError(name)
    where = where or {}
    clauses = [psycopg.sql.SQL("{} = %s").format(psycopg.sql.Identifier(k)) for k in where]
    query = psycopg.sql.SQL("select * from {}{} limit %s").format(
        psycopg.sql.Identifier("api", name),
        psycopg.sql.SQL(" where ") + psycopg.sql.SQL(" and ").join(clauses)
        if clauses
        else psycopg.sql.SQL(""),
    )
    return rows(query, (*where.values(), limit))


def readonly_query(sql: str) -> list[dict[str, Any]]:
    """Executa um SELECT sobre o schema api em transação read-only (validação no banco)."""
    with pool().connection() as conn, conn.transaction():
        conn.execute("set transaction read only")
        cur = conn.execute("select api.run_readonly_query(%s) as data", (sql,))
        row = cur.fetchone()
        data = row["data"] if row else []  # type: ignore[index, call-overload]
        return json.loads(json.dumps(data, default=_clean))  # type: ignore[no-any-return]


def execute(sql: str, params: tuple[Any, ...] = ()) -> None:
    with pool().connection() as conn:
        conn.execute(sql, params)  # type: ignore[arg-type]
