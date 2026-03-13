import duckdb
import pandas as pd
import streamlit as st
from pathlib import Path

GOLD_DIR = Path(__file__).resolve().parents[2] / "data" / "gold"


def _parquet(name: str) -> str:
    return str(GOLD_DIR / f"{name}.parquet")


def _conn() -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect()
    tables = [
        "gold_dashboard_fact",
        "gold_account_risk",
        "gold_churn_drivers",
        "gold_feature_retention",
        "gold_support_health",
    ]
    for t in tables:
        path = GOLD_DIR / f"{t}.parquet"
        conn.execute(f"CREATE VIEW {t} AS SELECT * FROM read_parquet('{path}')")
    return conn


@st.cache_data(ttl=3600)
def get_filter_options() -> dict:
    conn = _conn()
    ym = conn.execute(
        "SELECT DISTINCT year_month FROM gold_dashboard_fact ORDER BY year_month"
    ).df()["year_month"].tolist()
    industries = conn.execute(
        "SELECT DISTINCT industry FROM gold_dashboard_fact WHERE industry IS NOT NULL ORDER BY industry"
    ).df()["industry"].tolist()
    countries = conn.execute(
        "SELECT DISTINCT country FROM gold_dashboard_fact WHERE country IS NOT NULL ORDER BY country"
    ).df()["country"].tolist()
    channels = conn.execute(
        "SELECT DISTINCT acquisition_channel FROM gold_dashboard_fact WHERE acquisition_channel IS NOT NULL ORDER BY acquisition_channel"
    ).df()["acquisition_channel"].tolist()
    plans = conn.execute(
        "SELECT DISTINCT plan_name FROM gold_dashboard_fact WHERE plan_name IS NOT NULL ORDER BY plan_name"
    ).df()["plan_name"].tolist()
    billing_freqs = conn.execute(
        "SELECT DISTINCT billing_frequency FROM gold_dashboard_fact WHERE billing_frequency IS NOT NULL ORDER BY billing_frequency"
    ).df()["billing_frequency"].tolist()
    return {
        "year_months": ym,
        "industries": industries,
        "countries": countries,
        "channels": channels,
        "plans": plans,
        "billing_frequencies": billing_freqs,
    }


def _build_in_clause(col: str, values: list) -> tuple[str, list]:
    """Returns (sql_fragment, params_list) for an IN filter. Empty list = no filter."""
    if not values:
        return "", []
    placeholders = ", ".join(["?" for _ in values])
    return f"AND {col} IN ({placeholders})", list(values)


@st.cache_data(ttl=3600)
def query_dashboard_fact(
    ym_start: str,
    ym_end: str,
    industries: tuple,
    countries: tuple,
    channels: tuple,
    plans: tuple,
    billing_freqs: tuple,
    is_trial,
) -> pd.DataFrame:
    conn = _conn()
    params = [ym_start, ym_end]
    extra = ""

    for col, vals in [
        ("industry", industries),
        ("country", countries),
        ("acquisition_channel", channels),
        ("plan_name", plans),
        ("billing_frequency", billing_freqs),
    ]:
        clause, p = _build_in_clause(col, list(vals))
        extra += f" {clause}"
        params.extend(p)

    if is_trial is True:
        extra += " AND is_trial = true"
    elif is_trial is False:
        extra += " AND is_trial = false"

    sql = f"SELECT * FROM gold_dashboard_fact WHERE year_month BETWEEN ? AND ?{extra}"
    return conn.execute(sql, params).df()


@st.cache_data(ttl=3600)
def query_churn_drivers(
    ym_start: str,
    ym_end: str,
    segment_type: str,
) -> pd.DataFrame:
    conn = _conn()
    sql = """
        SELECT segment_value,
               SUM(churned_accounts) AS churned_accounts,
               SUM(total_accounts)   AS total_accounts,
               AVG(churn_rate)       AS churn_rate,
               SUM(mrr_lost)         AS mrr_lost,
               MAX(top_reason_code)  AS top_reason_code
        FROM gold_churn_drivers
        WHERE year_month BETWEEN ? AND ?
          AND segment_type = ?
        GROUP BY segment_value
        ORDER BY churn_rate DESC
    """
    return conn.execute(sql, [ym_start, ym_end, segment_type]).df()


@st.cache_data(ttl=3600)
def query_churn_drivers_ts(
    ym_start: str,
    ym_end: str,
    segment_type: str,
    segment_value: str,
) -> pd.DataFrame:
    conn = _conn()
    sql = """
        SELECT year_month, churn_rate, churned_accounts, mrr_lost
        FROM gold_churn_drivers
        WHERE year_month BETWEEN ? AND ?
          AND segment_type = ?
          AND segment_value = ?
        ORDER BY year_month
    """
    return conn.execute(sql, [ym_start, ym_end, segment_type, segment_value]).df()


@st.cache_data(ttl=3600)
def query_account_risk(
    risk_tiers: tuple,
    industries: tuple,
    countries: tuple,
    mrr_min: float,
    mrr_max: float,
) -> pd.DataFrame:
    conn = _conn()
    params: list = [mrr_min, mrr_max]
    extra = ""

    for col, vals in [
        ("risk_tier", risk_tiers),
        ("industry", industries),
        ("country", countries),
    ]:
        clause, p = _build_in_clause(col, list(vals))
        extra += f" {clause}"
        params.extend(p)

    sql = f"""
        SELECT * FROM gold_account_risk
        WHERE mrr BETWEEN ? AND ?{extra}
        ORDER BY risk_score DESC
    """
    return conn.execute(sql, params).df()


@st.cache_data(ttl=3600)
def query_feature_retention(ym_start: str, ym_end: str) -> pd.DataFrame:
    conn = _conn()
    sql = """
        SELECT * FROM gold_feature_retention
        WHERE year_month BETWEEN ? AND ?
        ORDER BY feature_name, year_month
    """
    return conn.execute(sql, [ym_start, ym_end]).df()


@st.cache_data(ttl=3600)
def query_support_health(
    ym_start: str,
    ym_end: str,
    industries: tuple,
) -> pd.DataFrame:
    conn = _conn()
    params = [ym_start, ym_end]
    extra = ""
    clause, p = _build_in_clause("industry", list(industries))
    extra += f" {clause}"
    params.extend(p)

    sql = f"""
        SELECT * FROM gold_support_health
        WHERE year_month BETWEEN ? AND ?{extra}
        ORDER BY industry, year_month
    """
    return conn.execute(sql, params).df()
