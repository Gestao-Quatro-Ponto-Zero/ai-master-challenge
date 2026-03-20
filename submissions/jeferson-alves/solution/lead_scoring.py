from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


STAGE_PRIORS = {
    "Engaging": 0.68,
    "Prospecting": 0.42,
}

WEIGHTS = {
    "stage": 0.26,
    "agent": 0.18,
    "account": 0.14,
    "product": 0.12,
    "manager": 0.10,
    "region": 0.08,
    "freshness": 0.07,
    "value": 0.05,
}


@dataclass(frozen=True)
class ScoreContext:
    snapshot_date: pd.Timestamp
    global_win_rate: float
    won_cycle_median: float
    lost_cycle_median: float


def normalize_product_name(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def smoothed_rate(
    frame: pd.DataFrame,
    group_col: str,
    global_rate: float,
    min_weight: int = 15,
) -> pd.DataFrame:
    grouped = frame.groupby(group_col)["won_flag"].agg(["mean", "count"]).reset_index()
    grouped["smoothed_rate"] = (
        grouped["mean"] * grouped["count"] + global_rate * min_weight
    ) / (grouped["count"] + min_weight)
    return grouped[[group_col, "smoothed_rate", "count"]]


def percentile_score(series: pd.Series) -> pd.Series:
    if series.nunique(dropna=False) <= 1:
        return pd.Series(0.5, index=series.index)
    ranked = series.rank(method="average", pct=True)
    return ranked.fillna(0.5)


def build_context(closed_deals: pd.DataFrame, snapshot_date: pd.Timestamp) -> ScoreContext:
    won_cycle_median = float(
        closed_deals.loc[closed_deals["won_flag"] == 1, "days_to_close"].median()
    )
    lost_cycle_median = float(
        closed_deals.loc[closed_deals["won_flag"] == 0, "days_to_close"].median()
    )
    global_win_rate = float(closed_deals["won_flag"].mean())
    return ScoreContext(
        snapshot_date=snapshot_date,
        global_win_rate=global_win_rate,
        won_cycle_median=won_cycle_median,
        lost_cycle_median=lost_cycle_median,
    )


def load_and_score(data_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, ScoreContext]:
    data_path = Path(data_dir)

    accounts = pd.read_csv(data_path / "accounts.csv")
    products = pd.read_csv(data_path / "products.csv")
    sales_teams = pd.read_csv(data_path / "sales_teams.csv")
    pipeline = pd.read_csv(data_path / "sales_pipeline.csv")

    products["product_key"] = products["product"].map(normalize_product_name)
    pipeline["product_key"] = pipeline["product"].map(normalize_product_name)

    pipeline["engage_date"] = pd.to_datetime(pipeline["engage_date"], errors="coerce")
    pipeline["close_date"] = pd.to_datetime(pipeline["close_date"], errors="coerce")
    pipeline["close_value"] = pd.to_numeric(pipeline["close_value"], errors="coerce")
    pipeline["account"] = pipeline["account"].fillna("Unknown account")

    merged = (
        pipeline.merge(
            products[["product_key", "product", "series", "sales_price"]].rename(
                columns={"product": "product_catalog_name"}
            ),
            on="product_key",
            how="left",
        )
        .merge(accounts, on="account", how="left")
        .merge(sales_teams, on="sales_agent", how="left")
    )

    snapshot_date = max(
        merged["engage_date"].max(),
        merged["close_date"].dropna().max(),
    )

    closed_deals = merged[merged["deal_stage"].isin(["Won", "Lost"])].copy()
    closed_deals["won_flag"] = (closed_deals["deal_stage"] == "Won").astype(int)
    closed_deals["days_to_close"] = (
        closed_deals["close_date"] - closed_deals["engage_date"]
    ).dt.days

    context = build_context(closed_deals, snapshot_date)

    lookups: dict[str, pd.DataFrame] = {}
    for column in ["sales_agent", "account", "product_key", "manager", "regional_office"]:
        lookups[column] = smoothed_rate(closed_deals, column, context.global_win_rate)

    open_deals = merged[~merged["deal_stage"].isin(["Won", "Lost"])].copy()
    open_deals["deal_age_days"] = (
        context.snapshot_date - open_deals["engage_date"]
    ).dt.days.clip(lower=0)
    open_deals["deal_age_days"] = open_deals["deal_age_days"].fillna(0)
    open_deals["has_account_data"] = open_deals["sector"].notna().astype(int)
    open_deals["has_engage_date"] = open_deals["engage_date"].notna().astype(int)
    open_deals["expected_deal_value"] = open_deals["sales_price"].fillna(
        open_deals["close_value"]
    )
    fallback_value = float(
        closed_deals.loc[closed_deals["won_flag"] == 1, "close_value"].median()
    )
    open_deals["expected_deal_value"] = open_deals["expected_deal_value"].fillna(fallback_value)

    for column, lookup in lookups.items():
        open_deals = open_deals.merge(lookup, on=column, how="left", suffixes=("", f"_{column}"))
        open_deals[f"{column}_win_rate"] = open_deals["smoothed_rate"].fillna(context.global_win_rate)
        open_deals[f"{column}_sample_size"] = open_deals["count"].fillna(0).astype(int)
        open_deals = open_deals.drop(columns=["smoothed_rate", "count"])

    open_deals["stage_prior"] = open_deals["deal_stage"].map(STAGE_PRIORS).fillna(
        context.global_win_rate
    )

    open_deals["freshness_factor"] = 1 - percentile_score(open_deals["deal_age_days"])
    open_deals.loc[open_deals["deal_stage"] == "Prospecting", "freshness_factor"] = 0.45
    open_deals.loc[open_deals["has_engage_date"] == 0, "freshness_factor"] = 0.40

    value_basis = np.log1p(open_deals["expected_deal_value"])
    open_deals["value_factor"] = percentile_score(value_basis)

    open_deals["estimated_win_rate"] = (
        WEIGHTS["stage"] * open_deals["stage_prior"]
        + WEIGHTS["agent"] * open_deals["sales_agent_win_rate"]
        + WEIGHTS["account"] * open_deals["account_win_rate"]
        + WEIGHTS["product"] * open_deals["product_key_win_rate"]
        + WEIGHTS["manager"] * open_deals["manager_win_rate"]
        + WEIGHTS["region"] * open_deals["regional_office_win_rate"]
        + WEIGHTS["freshness"] * open_deals["freshness_factor"]
        + WEIGHTS["value"] * open_deals["value_factor"]
    )

    open_deals["estimated_win_rate"] = open_deals["estimated_win_rate"].clip(0.05, 0.95)
    open_deals["priority_score"] = (open_deals["estimated_win_rate"] * 100).round(1)
    open_deals["expected_revenue"] = (
        open_deals["estimated_win_rate"] * open_deals["expected_deal_value"]
    ).round(0)

    open_deals["priority_tier"] = pd.cut(
        open_deals["priority_score"],
        bins=[0, 52, 64, 75, 100],
        labels=["Low", "Watch", "Focus", "Hot"],
        include_lowest=True,
    ).astype(str)

    open_deals["score_gap_vs_baseline"] = open_deals["estimated_win_rate"] - context.global_win_rate
    open_deals["account_label"] = open_deals["account"].replace("Unknown account", "Conta nao informada")
    open_deals["product_label"] = open_deals["product_catalog_name"].fillna(open_deals["product"])

    open_deals["recommended_action"] = open_deals.apply(recommend_action, axis=1)
    open_deals["explanation"] = open_deals.apply(
        lambda row: " | ".join(build_reason_list(row, context.global_win_rate)),
        axis=1,
    )

    open_deals["rank"] = open_deals["priority_score"].rank(
        method="first", ascending=False
    ).astype(int)

    open_deals = open_deals.sort_values(
        ["priority_score", "expected_revenue", "sales_agent"],
        ascending=[False, False, True],
    )

    summary = build_team_summary(open_deals)
    return open_deals, summary, context


def build_reason_list(row: pd.Series, global_win_rate: float) -> list[str]:
    reasons: list[str] = []

    if row["deal_stage"] == "Engaging":
        reasons.append("Ja esta em Engaging, mais perto de fechamento")
    else:
        reasons.append("Ainda esta em Prospecting, precisa avancar de etapa")

    if row["sales_agent_win_rate"] >= global_win_rate + 0.03:
        reasons.append(
            f"Historico forte do vendedor ({row['sales_agent_win_rate']:.0%} de win rate)"
        )
    elif row["sales_agent_win_rate"] <= global_win_rate - 0.03:
        reasons.append(
            f"Historico abaixo da media do vendedor ({row['sales_agent_win_rate']:.0%})"
        )

    if row["account"] == "Unknown account":
        reasons.append("Conta nao identificada, reduz confianca na priorizacao")
    elif row["account_win_rate"] >= global_win_rate + 0.04:
        reasons.append(
            f"Conta com bom historico ({row['account_win_rate']:.0%} de ganho)"
        )
    elif row["account_win_rate"] <= global_win_rate - 0.04:
        reasons.append(
            f"Conta com historico fraco ({row['account_win_rate']:.0%} de ganho)"
        )

    if row["freshness_factor"] >= 0.65:
        reasons.append("Deal relativamente fresco no pipeline")
    elif row["deal_age_days"] > 120:
        reasons.append(f"Deal envelhecido ha {int(row['deal_age_days'])} dias")

    if row["value_factor"] >= 0.80:
        reasons.append("Potencial financeiro acima da maior parte do pipeline")

    return reasons[:4]


def recommend_action(row: pd.Series) -> str:
    if row["account"] == "Unknown account":
        return "Completar dados da conta antes de investir mais tempo comercial"
    if row["deal_stage"] == "Prospecting" and row["priority_score"] >= 65:
        return "Mover para discovery e qualificar ainda esta semana"
    if row["deal_stage"] == "Engaging" and row["priority_score"] >= 75:
        return "Fazer follow-up executivo e buscar proximo passo com data marcada"
    if row["deal_age_days"] >= 120 and row["priority_score"] < 60:
        return "Requalificar rapido ou encerrar para liberar foco do vendedor"
    return "Manter acompanhamento padrao e revisar no proximo ciclo"


def build_team_summary(open_deals: pd.DataFrame) -> pd.DataFrame:
    team_summary = (
        open_deals.groupby(["manager", "regional_office", "sales_agent"], dropna=False)
        .agg(
            open_deals=("opportunity_id", "count"),
            avg_score=("priority_score", "mean"),
            hot_deals=("priority_tier", lambda values: int((values == "Hot").sum())),
            focus_deals=("priority_tier", lambda values: int(values.isin(["Hot", "Focus"]).sum())),
            expected_revenue=("expected_revenue", "sum"),
        )
        .reset_index()
        .sort_values(["hot_deals", "expected_revenue", "avg_score"], ascending=[False, False, False])
    )
    team_summary["avg_score"] = team_summary["avg_score"].round(1)
    team_summary["expected_revenue"] = team_summary["expected_revenue"].round(0)
    return team_summary


def component_frame(row: pd.Series) -> pd.DataFrame:
    components = [
        ("Stage", WEIGHTS["stage"] * row["stage_prior"]),
        ("Sales agent", WEIGHTS["agent"] * row["sales_agent_win_rate"]),
        ("Account", WEIGHTS["account"] * row["account_win_rate"]),
        ("Product", WEIGHTS["product"] * row["product_key_win_rate"]),
        ("Manager", WEIGHTS["manager"] * row["manager_win_rate"]),
        ("Region", WEIGHTS["region"] * row["regional_office_win_rate"]),
        ("Freshness", WEIGHTS["freshness"] * row["freshness_factor"]),
        ("Value", WEIGHTS["value"] * row["value_factor"]),
    ]
    frame = pd.DataFrame(components, columns=["component", "contribution"])
    frame["contribution"] = (frame["contribution"] * 100).round(1)
    return frame.sort_values("contribution", ascending=True)


def format_currency(value: float) -> str:
    if pd.isna(value):
        return "$0"
    rounded = int(round(float(value), 0))
    return f"${rounded:,.0f}"


def score_summary(open_deals: pd.DataFrame) -> dict[str, float]:
    hot_mask = open_deals["priority_tier"] == "Hot"
    focus_mask = open_deals["priority_tier"].isin(["Hot", "Focus"])
    return {
        "open_deals": int(len(open_deals)),
        "avg_score": float(open_deals["priority_score"].mean()),
        "hot_deals": int(hot_mask.sum()),
        "focus_deals": int(focus_mask.sum()),
        "expected_revenue": float(open_deals["expected_revenue"].sum()),
    }


def safe_ratio(value: float) -> str:
    return f"{value * 100:.1f}%"
