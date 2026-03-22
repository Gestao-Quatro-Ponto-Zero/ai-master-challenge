"""
Sistema de Deteccao de Deal Zumbi.

Classifica deals ativos que ultrapassaram o tempo esperado no stage,
identifica contas com padrao recorrente de losses, e gera metricas
de resumo para managers e vendedores.

Referencia: specs/deal_zombie.md
"""

from __future__ import annotations

import pandas as pd

from scoring.constants import (
    REFERENCE_DATE,
    STAGE_REFERENCE_DAYS,
    ZOMBIE_THRESHOLD,
)
from utils.constants import RECURRENT_LOSS_THRESHOLD

# === Constantes do modulo ===
ENGAGING_REFERENCE_DAYS = STAGE_REFERENCE_DAYS["Engaging"]  # 88 dias (P75 Won)
ZOMBIE_THRESHOLD_MULTIPLIER = ZOMBIE_THRESHOLD  # 2.0
ZOMBIE_CHRONIC_MULTIPLIER = 3.0
HIGH_RISK_LOSS_THRESHOLD = 5


# ---------------------------------------------------------------------------
# 3.1 — classify_zombies
# ---------------------------------------------------------------------------


def classify_zombies(
    deals_df: pd.DataFrame,
    products_df: pd.DataFrame,
    reference_date: pd.Timestamp = None,
) -> pd.DataFrame:
    """Classifica deals ativos como zumbi, zumbi cronico ou zumbi critico.

    Apenas deals em Engaging podem ser classificados como zumbi (Prospecting
    nao possui dados temporais no dataset).

    Args:
        deals_df: DataFrame com deals ativos (Prospecting + Engaging).
            Colunas esperadas: opportunity_id, deal_stage, engage_date,
            product, close_value, account.
        products_df: DataFrame de produtos com colunas: product, sales_price.
        reference_date: Data de referencia para calculo de tempo.
            Default: 2017-12-31.

    Returns:
        O deals_df original acrescido das colunas:
        days_in_stage, stage_reference_days, time_ratio, is_zombie,
        zombie_severity, estimated_value, is_zombie_critical, zombie_label.
    """
    if reference_date is None:
        reference_date = REFERENCE_DATE

    df = deals_df.copy()

    # --- Dias no stage (vectorized) ---
    # Apenas Engaging tem engage_date; Prospecting fica NaN
    is_engaging = df["deal_stage"] == "Engaging"
    df["days_in_stage"] = pd.Series(dtype="float64", index=df.index)
    if is_engaging.any():
        engage_dates = pd.to_datetime(df.loc[is_engaging, "engage_date"])
        df.loc[is_engaging, "days_in_stage"] = (
            (reference_date - engage_dates).dt.days.clip(lower=0)
        )

    # --- Referencia do stage ---
    df["stage_reference_days"] = df["deal_stage"].map(
        lambda s: ENGAGING_REFERENCE_DAYS if s == "Engaging" else None
    )

    # --- Time ratio ---
    df["time_ratio"] = pd.Series(dtype="float64", index=df.index)
    has_ref = df["stage_reference_days"].notna() & df["days_in_stage"].notna()
    if has_ref.any():
        df.loc[has_ref, "time_ratio"] = (
            df.loc[has_ref, "days_in_stage"] / df.loc[has_ref, "stage_reference_days"]
        ).round(2)

    # --- Zombie flag ---
    df["is_zombie"] = df["time_ratio"].notna() & (
        df["time_ratio"] > ZOMBIE_THRESHOLD_MULTIPLIER
    )

    # --- Zombie severity ---
    df["zombie_severity"] = None
    zombie_mask = df["is_zombie"]
    chronic_mask = zombie_mask & (df["time_ratio"] > ZOMBIE_CHRONIC_MULTIPLIER)

    df.loc[zombie_mask & ~chronic_mask, "zombie_severity"] = "zombie"
    df.loc[chronic_mask, "zombie_severity"] = "zombie_chronic"

    # --- Estimated value (vectorized via merge) ---
    # Usar close_value se > 0, senao preco do produto
    price_map = products_df.set_index("product")["sales_price"]
    product_price = df["product"].map(price_map).fillna(0.0).astype(float)

    close_val = pd.to_numeric(df["close_value"], errors="coerce")
    has_close_value = close_val.notna() & (close_val > 0)
    df["estimated_value"] = product_price
    if has_close_value.any():
        df.loc[has_close_value, "estimated_value"] = close_val[has_close_value]

    # --- Zombie critical (valor > P75 dos deals ativos) ---
    # Para calcular o P75 de referencia, usar os precos dos produtos como
    # distribuicao base quando ha poucos deals (garante estabilidade).
    df["is_zombie_critical"] = False
    if df["estimated_value"].notna().any():
        if len(df) >= 4:
            value_p75 = df["estimated_value"].quantile(0.75)
        else:
            # Com poucos deals o P75 fica degenerado; usar distribuicao
            # dos precos dos produtos como referencia estavel.
            value_p75 = products_df["sales_price"].quantile(0.75)
        df["is_zombie_critical"] = df["is_zombie"] & (
            df["estimated_value"] > value_p75
        )

    # --- Zombie label ---
    # Prioridade: Zumbi Critico > Zumbi Cronico > Zumbi
    df["zombie_label"] = None
    df.loc[df["is_zombie"] & ~chronic_mask & ~df["is_zombie_critical"], "zombie_label"] = "Zumbi"
    df.loc[chronic_mask & ~df["is_zombie_critical"], "zombie_label"] = "Zumbi Cronico"
    df.loc[df["is_zombie_critical"], "zombie_label"] = "Zumbi Critico"

    return df


# ---------------------------------------------------------------------------
# 3.3 — classify_accounts
# ---------------------------------------------------------------------------


def classify_accounts(pipeline_df: pd.DataFrame) -> pd.DataFrame:
    """Calcula metricas de saude por conta baseado em historico de wins/losses.

    Args:
        pipeline_df: DataFrame completo do pipeline (incluindo Won e Lost).
            Deve conter colunas: account, deal_stage.

    Returns:
        DataFrame com uma linha por conta e colunas:
        account, total_deals, total_won, total_lost, win_rate,
        is_recurrent_loss, is_high_risk.
    """
    result_columns = [
        "account",
        "total_deals",
        "total_won",
        "total_lost",
        "win_rate",
        "is_recurrent_loss",
        "is_high_risk",
    ]

    # Remover linhas sem account
    df = pipeline_df.dropna(subset=["account"]).copy()

    if df.empty:
        return pd.DataFrame(columns=result_columns)

    stats = (
        df.groupby("account")
        .agg(
            total_deals=("deal_stage", "count"),
            total_won=("deal_stage", lambda x: (x == "Won").sum()),
            total_lost=("deal_stage", lambda x: (x == "Lost").sum()),
        )
        .reset_index()
    )

    # Win rate: Won / (Won + Lost), com fallback para 0 se nenhum fechado
    total_closed = stats["total_won"] + stats["total_lost"]
    stats["win_rate"] = 0.0
    closed_mask = total_closed > 0
    stats.loc[closed_mask, "win_rate"] = (
        stats.loc[closed_mask, "total_won"] / total_closed[closed_mask]
    )

    # Flags
    stats["is_recurrent_loss"] = stats["total_lost"] >= RECURRENT_LOSS_THRESHOLD
    stats["is_high_risk"] = stats["total_lost"] >= HIGH_RISK_LOSS_THRESHOLD

    return stats[result_columns]


# ---------------------------------------------------------------------------
# 3.4 — get_zombie_summary
# ---------------------------------------------------------------------------


def get_zombie_summary(classified_df: pd.DataFrame) -> dict:
    """Gera metricas de resumo sobre deals zumbis para uso na UI.

    Args:
        classified_df: DataFrame retornado por classify_zombies().

    Returns:
        Dict com chaves: total_active_deals, total_zombies, total_zombies_critical,
        total_zombies_chronic, pct_zombies, pipeline_total, pipeline_inflated,
        pipeline_inflated_critical, pct_pipeline_inflated, zombies_by_stage,
        top_zombie_accounts.
    """
    total_active = len(classified_df)
    zombie_mask = classified_df["is_zombie"]
    critical_mask = classified_df["is_zombie_critical"]
    chronic_mask = classified_df["zombie_severity"] == "zombie_chronic"

    total_zombies = int(zombie_mask.sum())
    total_critical = int(critical_mask.sum())
    total_chronic = int(chronic_mask.sum())

    pct_zombies = (total_zombies / total_active * 100) if total_active > 0 else 0.0

    # Pipeline values
    pipeline_total = float(classified_df["estimated_value"].sum())
    pipeline_inflated = float(
        classified_df.loc[zombie_mask, "estimated_value"].sum()
    )
    pipeline_inflated_critical = float(
        classified_df.loc[critical_mask, "estimated_value"].sum()
    )
    pct_pipeline_inflated = (
        (pipeline_inflated / pipeline_total * 100) if pipeline_total > 0 else 0.0
    )

    # Zombies by stage
    zombies_by_stage = {}
    zombie_deals = classified_df[zombie_mask]
    if not zombie_deals.empty:
        stage_counts = zombie_deals["deal_stage"].value_counts().to_dict()
        zombies_by_stage = {str(k): int(v) for k, v in stage_counts.items()}

    # Top zombie accounts (top 10 by zombie count)
    top_zombie_accounts = []
    if not zombie_deals.empty and "account" in zombie_deals.columns:
        account_zombies = (
            zombie_deals.dropna(subset=["account"])
            .groupby("account")
            .size()
            .sort_values(ascending=False)
            .head(10)
        )
        top_zombie_accounts = [
            {"account": acc, "zombie_count": int(cnt)}
            for acc, cnt in account_zombies.items()
        ]

    return {
        "total_active_deals": total_active,
        "total_zombies": total_zombies,
        "total_zombies_critical": total_critical,
        "total_zombies_chronic": total_chronic,
        "pct_zombies": round(pct_zombies, 1),
        "pipeline_total": round(pipeline_total, 2),
        "pipeline_inflated": round(pipeline_inflated, 2),
        "pipeline_inflated_critical": round(pipeline_inflated_critical, 2),
        "pct_pipeline_inflated": round(pct_pipeline_inflated, 1),
        "zombies_by_stage": zombies_by_stage,
        "top_zombie_accounts": top_zombie_accounts,
    }


# ---------------------------------------------------------------------------
# 3.5 — get_zombie_summary_by_seller
# ---------------------------------------------------------------------------


def get_zombie_summary_by_seller(
    classified_df: pd.DataFrame,
    sales_teams_df: pd.DataFrame,
) -> pd.DataFrame:
    """Gera metricas de resumo agrupadas por vendedor para visao de manager.

    Args:
        classified_df: DataFrame retornado por classify_zombies().
        sales_teams_df: DataFrame de vendedores com manager e regional_office.

    Returns:
        DataFrame com uma linha por vendedor e colunas:
        sales_agent, manager, regional_office, total_active, total_zombies,
        total_zombies_critical, pct_zombies, pipeline_value, inflated_value.
    """
    result_columns = [
        "sales_agent",
        "manager",
        "regional_office",
        "total_active",
        "total_zombies",
        "total_zombies_critical",
        "pct_zombies",
        "pipeline_value",
        "inflated_value",
    ]

    if classified_df.empty:
        return pd.DataFrame(columns=result_columns)

    # Agregar por vendedor
    seller_stats = (
        classified_df.groupby("sales_agent")
        .agg(
            total_active=("is_zombie", "count"),
            total_zombies=("is_zombie", "sum"),
            total_zombies_critical=("is_zombie_critical", "sum"),
            pipeline_value=("estimated_value", "sum"),
        )
        .reset_index()
    )

    # Valor inflado: soma de estimated_value dos zumbis por vendedor
    zombie_deals = classified_df[classified_df["is_zombie"]]
    if not zombie_deals.empty:
        inflated = (
            zombie_deals.groupby("sales_agent")["estimated_value"]
            .sum()
            .reset_index(name="inflated_value")
        )
        seller_stats = seller_stats.merge(inflated, on="sales_agent", how="left")
    else:
        seller_stats["inflated_value"] = 0.0

    seller_stats["inflated_value"] = seller_stats["inflated_value"].fillna(0.0)

    # Percentual de zumbis
    seller_stats["pct_zombies"] = 0.0
    has_deals = seller_stats["total_active"] > 0
    seller_stats.loc[has_deals, "pct_zombies"] = (
        seller_stats.loc[has_deals, "total_zombies"]
        / seller_stats.loc[has_deals, "total_active"]
        * 100
    ).round(1)

    # Converter contadores para int
    seller_stats["total_zombies"] = seller_stats["total_zombies"].astype(int)
    seller_stats["total_zombies_critical"] = seller_stats[
        "total_zombies_critical"
    ].astype(int)

    # JOIN com sales_teams para manager e regional_office
    team_cols = ["sales_agent", "manager", "regional_office"]
    available_cols = [c for c in team_cols if c in sales_teams_df.columns]
    seller_stats = seller_stats.merge(
        sales_teams_df[available_cols],
        on="sales_agent",
        how="left",
    )

    return seller_stats[result_columns].sort_values(
        "inflated_value", ascending=False
    ).reset_index(drop=True)
