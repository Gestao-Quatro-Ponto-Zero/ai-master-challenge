"""Acesso a dados — lê do banco SQLite (db/foco.db). Sem lógica de score aqui.

Se o banco não existir, instrui a rodar migrate+seed. Mantém o scoring desacoplado
da origem (hoje SQLite; amanhã Postgres/CRM sem mudar features.py/model.py).
"""
import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "db" / "foco.db"


def _conn():
    if not DB_PATH.exists():
        raise SystemExit(
            f"Banco não encontrado em {DB_PATH}.\n"
            "Rode primeiro:  make migrate && make seed   (ou: python -m db.migrate && python -m db.seed)"
        )
    return sqlite3.connect(DB_PATH)


def load_open_deals() -> pd.DataFrame:
    """Deals abertos (Prospecting/Engaging) com joins e days_open. Universo a priorizar."""
    with _conn() as c:
        return pd.read_sql_query("SELECT * FROM v_open_deals", c)


def load_agent_winrate() -> pd.DataFrame:
    """Win-rate histórico por vendedor (wins, closed, win_rate)."""
    with _conn() as c:
        return pd.read_sql_query("SELECT * FROM v_agent_winrate", c)


def load_pipeline_health() -> dict:
    """KPIs de saúde do pipeline (painel RevOps)."""
    with _conn() as c:
        row = pd.read_sql_query("SELECT * FROM v_pipeline_health", c).iloc[0]
    return row.to_dict()


def load_products() -> pd.DataFrame:
    with _conn() as c:
        return pd.read_sql_query("SELECT * FROM products", c)


def outcome_from_df(df: pd.DataFrame) -> dict:
    """KPIs globais + breakdowns de outcome a partir de um DataFrame de deals.

    Aceita o DataFrame completo (todos os 8800) ou filtrado por regional.
    Retorna global, by_product, by_region, by_agent.
    """
    closed = df[df["deal_stage"].isin(["Won", "Lost"])].copy()
    won = closed[closed["deal_stage"] == "Won"].copy()
    n_total = len(df)
    n_won = len(won)
    n_lost = len(closed[closed["deal_stage"] == "Lost"])
    n_open = n_total - len(closed)
    receita = float(won["close_value"].sum())
    ticket = receita / n_won if n_won else 0.0

    def _by(group_col: str) -> pd.DataFrame:
        g = closed.groupby(group_col)
        d = g.agg(
            fechados=("deal_stage", "count"),
            won=("deal_stage", lambda x: int((x == "Won").sum())),
            receita=("close_value", "sum"),
        ).reset_index()
        d["lost"] = d["fechados"] - d["won"]
        d["win_rate"] = d["won"] / d["fechados"]
        d["ticket"] = d["receita"] / d["won"].replace(0, float("nan"))
        return d.sort_values("receita", ascending=False, na_position="last")

    return {
        "global": {
            "total": n_total,
            "won": n_won,
            "lost": n_lost,
            "open": n_open,
            "win_rate": n_won / len(closed) if len(closed) else 0.0,
            "receita_ganha": receita,
            "ticket_medio": ticket,
            "ciclo_medio": float(won["ciclo_dias"].mean()) if n_won else 0.0,
            "ciclo_p50": float(won["ciclo_dias"].median()) if n_won else 0.0,
            "ciclo_p90": float(won["ciclo_dias"].quantile(0.9)) if n_won else 0.0,
        },
        "by_product": _by("product"),
        "by_region": _by("regional_office"),
        "by_agent": _by("sales_agent"),
    }


def load_outcome() -> dict:
    """Outcome histórico (fechados) + composição total — scorecard RevOps.

    Retorna KPIs globais, breakdowns por produto/regional/vendedor e '_raw'
    (DataFrame completo para que a view possa filtrar por regional sem nova query).
    Usa TODOS os 8800 deals: fechados (Won/Lost) para outcome, abertos para
    composição do funil. Lost tem close_value=0 neste dataset.
    """
    with _conn() as c:
        df = pd.read_sql_query(
            """
            SELECT sp.deal_stage, sp.close_value, sp.product,
                   sp.sales_agent, st.regional_office, st.manager,
                   CAST(julianday(sp.close_date) - julianday(sp.engage_date) AS REAL) AS ciclo_dias
            FROM sales_pipeline sp
            LEFT JOIN sales_teams st ON sp.sales_agent = st.sales_agent
            """,
            c,
        )
    result = outcome_from_df(df)
    result["_raw"] = df
    return result
