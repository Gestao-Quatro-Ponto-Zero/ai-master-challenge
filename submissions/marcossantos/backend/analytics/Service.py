"""
analytics/service.py
--------------------
Toda a lógica de agregação para analytics.
Recebe o pipeline + métricas do loader e retorna os dados calculados.

Separado do router para manter as rotas limpas e facilitar testes.
"""

import pandas as pd
import numpy as np
from typing import Optional

from .models import (
    AgentStats,
    TeamAnalyticsResponse,
    StageCount,
    ProductFunnelStats,
    FunnelAnalyticsResponse,
    RiskDeal,
    RegionRiskSummary,
    AtRiskResponse,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(val, default=0.0) -> float:
    try:
        v = float(val)
        return default if (v != v) else v  # NaN check
    except Exception:
        return default


def _agent_status(win_rate: float, global_win_rate: float) -> str:
    if win_rate >= global_win_rate * 1.15:
        return "strong"
    elif win_rate >= global_win_rate * 0.85:
        return "average"
    else:
        return "needs_coaching"


# ---------------------------------------------------------------------------
# 1. Team Analytics
# ---------------------------------------------------------------------------

def compute_team_analytics(
    pipeline: pd.DataFrame,
    metrics: dict,
    manager_filter: Optional[str] = None,
    region_filter: Optional[str] = None,
) -> TeamAnalyticsResponse:
    """
    Calcula métricas por vendedor para a visão do manager.
    Filtra por manager ou região se fornecido.
    """
    df = pipeline.copy()

    # Aplica filtros
    if manager_filter and "manager" in df.columns:
        df = df[df["manager"].astype(str).str.lower() == manager_filter.lower()]
    if region_filter and "regional_office" in df.columns:
        df = df[df["regional_office"].astype(str).str.lower() == region_filter.lower()]

    global_wr = metrics.get("global_win_rate", 0.5)

    # Dados históricos (fechados)
    closed = df[df["deal_stage"].isin(["Won", "Lost"])]
    active = df[df["deal_stage"].isin(["Prospecting", "Engaging"])]

    agent_stats_list = []

    for agent, group in df.groupby("sales_agent"):
        ag_closed = group[group["deal_stage"].isin(["Won", "Lost"])]
        ag_won    = group[group["deal_stage"] == "Won"]
        ag_lost   = group[group["deal_stage"] == "Lost"]
        ag_active = group[group["deal_stage"].isin(["Prospecting", "Engaging"])]

        won_count  = len(ag_won)
        lost_count = len(ag_lost)
        total_closed = won_count + lost_count
        win_rate = won_count / total_closed if total_closed > 0 else 0.0

        # Score dos deals ativos (usando tier se disponível)
        hot_deals = 0
        if "score" in ag_active.columns:
            hot_deals = int((ag_active["score"] >= 70).sum())
        else:
            # Estima com base no stage
            hot_deals = int((ag_active["deal_stage"] == "Engaging").sum())

        pipeline_value = _safe_float(ag_active["close_value"].fillna(0).sum())
        avg_deal_value = _safe_float(ag_won["close_value"].mean()) if won_count > 0 else 0.0

        meta = group.iloc[0]

        agent_stats_list.append(AgentStats(
            sales_agent=str(agent),
            manager=str(meta.get("manager", "")) or None,
            regional_office=str(meta.get("regional_office", "")) or None,
            total_deals=total_closed,
            won_deals=won_count,
            lost_deals=lost_count,
            win_rate=round(win_rate, 4),
            active_deals=len(ag_active),
            hot_deals=hot_deals,
            pipeline_value=round(pipeline_value, 2),
            avg_deal_value=round(avg_deal_value, 2),
            status=_agent_status(win_rate, global_wr),
        ))

    # Ordena: strong primeiro, depois por win_rate desc
    status_order = {"strong": 0, "average": 1, "needs_coaching": 2}
    agent_stats_list.sort(key=lambda a: (status_order[a.status], -a.win_rate))

    # Métricas do time
    total_closed_team = len(closed)
    team_won          = len(closed[closed["deal_stage"] == "Won"]) if total_closed_team > 0 else 0
    team_win_rate     = team_won / total_closed_team if total_closed_team > 0 else 0.0
    pipeline_value    = _safe_float(active["close_value"].fillna(0).sum())

    manager_val = manager_filter or (df["manager"].iloc[0] if "manager" in df.columns and len(df) > 0 else None)
    region_val  = region_filter  or (df["regional_office"].iloc[0] if "regional_office" in df.columns and len(df) > 0 else None)

    return TeamAnalyticsResponse(
        manager=str(manager_val) if manager_val else None,
        regional_office=str(region_val) if region_val else None,
        team_win_rate=round(team_win_rate, 4),
        global_win_rate=round(global_wr, 4),
        total_agents=len(agent_stats_list),
        total_active=len(active),
        pipeline_value=round(pipeline_value, 2),
        agents=agent_stats_list,
    )


# ---------------------------------------------------------------------------
# 2. Funnel Analytics
# ---------------------------------------------------------------------------

def compute_funnel_analytics(
    pipeline: pd.DataFrame,
    metrics: dict,
    manager_filter: Optional[str] = None,
    region_filter: Optional[str] = None,
) -> FunnelAnalyticsResponse:
    """
    Calcula conversão por stage e por produto.
    """
    df = pipeline.copy()

    if manager_filter and "manager" in df.columns:
        df = df[df["manager"].astype(str).str.lower() == manager_filter.lower()]
    if region_filter and "regional_office" in df.columns:
        df = df[df["regional_office"].astype(str).str.lower() == region_filter.lower()]

    active = df[df["deal_stage"].isin(["Prospecting", "Engaging"])]
    total_active = len(active)

    # Por stage
    stage_counts = []
    for stage in ["Prospecting", "Engaging"]:
        count = int((active["deal_stage"] == stage).sum())
        pct   = round(count / total_active * 100, 1) if total_active > 0 else 0.0
        stage_counts.append(StageCount(stage=stage, count=count, pct=pct))

    # Por produto
    product_stats = []
    product_velocity = metrics.get("product_velocity", {})

    for product, group in df.groupby("product"):
        won    = group[group["deal_stage"] == "Won"]
        lost   = group[group["deal_stage"] == "Lost"]
        act    = group[group["deal_stage"].isin(["Prospecting", "Engaging"])]

        won_count  = len(won)
        lost_count = len(lost)
        total_cl   = won_count + lost_count
        win_rate   = won_count / total_cl if total_cl > 0 else 0.0

        vel = product_velocity.get(product)
        avg_days = round(vel["avg_days"], 1) if vel and vel.get("avg_days") else None

        series = group["series"].iloc[0] if "series" in group.columns else None

        product_stats.append(ProductFunnelStats(
            product=str(product),
            series=str(series) if series and series == series else None,
            won=won_count,
            lost=lost_count,
            active=len(act),
            win_rate=round(win_rate, 4),
            avg_days_to_close=avg_days,
        ))

    # Ordena por win_rate desc
    product_stats.sort(key=lambda p: -p.win_rate)

    return FunnelAnalyticsResponse(
        total_active=total_active,
        by_stage=stage_counts,
        by_product=product_stats,
    )


# ---------------------------------------------------------------------------
# 3. At-Risk Analytics
# ---------------------------------------------------------------------------

def compute_at_risk(
    pipeline: pd.DataFrame,
    metrics: dict,
    manager_filter: Optional[str] = None,
    region_filter: Optional[str] = None,
    min_ratio: float = 1.5,
) -> AtRiskResponse:
    """
    Identifica deals em risco (acima da média do produto) e agrupa por região.
    """
    df = pipeline.copy()

    if manager_filter and "manager" in df.columns:
        df = df[df["manager"].astype(str).str.lower() == manager_filter.lower()]
    if region_filter and "regional_office" in df.columns:
        df = df[df["regional_office"].astype(str).str.lower() == region_filter.lower()]

    active = df[df["deal_stage"].isin(["Prospecting", "Engaging"])].copy()

    product_velocity = metrics.get("product_velocity", {})
    global_avg = 30

    risk_deals = []

    for _, deal in active.iterrows():
        product  = deal.get("product", "")
        days     = int(deal.get("days_in_pipeline", 0) or 0)
        value    = _safe_float(deal.get("close_value", 0))

        vel = product_velocity.get(product)
        avg_days = vel["avg_days"] if vel and vel.get("avg_days") else global_avg
        avg_days = max(avg_days, 1)

        ratio = days / avg_days
        if ratio < min_ratio:
            continue

        days_above = max(0, days - int(avg_days))

        risk_deals.append(RiskDeal(
            opportunity_id=str(deal.get("opportunity_id", "")),
            account=str(deal.get("account", "")) or None,
            sales_agent=str(deal.get("sales_agent", "")) or None,
            product=str(product) or None,
            deal_stage=str(deal.get("deal_stage", "")) or None,
            close_value=round(value, 2),
            days_in_pipeline=days,
            days_above_avg=days_above,
            risk_ratio=round(ratio, 2),
            score=int(deal.get("score", 0)) if "score" in deal and deal.get("score") == deal.get("score") else None,
        ))

    # Ordena por ratio desc (mais crítico primeiro)
    risk_deals.sort(key=lambda d: -d.risk_ratio)

    critical = [d for d in risk_deals if d.risk_ratio >= 2.0]
    warning  = [d for d in risk_deals if 1.5 <= d.risk_ratio < 2.0]
    total_value = sum(d.close_value for d in risk_deals)

    # Agrupa por região
    region_map: dict[str, dict] = {}
    for d in risk_deals:
        # Busca regional_office do deal original
        mask = active["opportunity_id"].astype(str) == d.opportunity_id
        region_rows = active[mask]
        region = str(region_rows.iloc[0].get("regional_office", "Sem região")) if len(region_rows) > 0 else "Sem região"

        if region not in region_map:
            region_map[region] = {"total": 0, "critical": 0, "warning": 0, "value": 0.0}

        region_map[region]["total"]  += 1
        region_map[region]["value"]  += d.close_value
        if d.risk_ratio >= 2.0:
            region_map[region]["critical"] += 1
        else:
            region_map[region]["warning"]  += 1

    by_region = [
        RegionRiskSummary(
            regional_office=region,
            total_at_risk=v["total"],
            critical_count=v["critical"],
            warning_count=v["warning"],
            total_value_at_risk=round(v["value"], 2),
        )
        for region, v in region_map.items()
    ]
    by_region.sort(key=lambda r: -r.total_at_risk)

    return AtRiskResponse(
        total_at_risk=len(risk_deals),
        critical_count=len(critical),
        warning_count=len(warning),
        total_value=round(total_value, 2),
        by_region=by_region,
        deals=risk_deals,
    )