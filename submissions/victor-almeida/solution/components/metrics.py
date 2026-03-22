"""
Metricas do pipeline — camada de calculo pura + renderizacao Streamlit.

Camada 1 (pura, testavel): count_active_deals, calculate_pipeline_total,
count_zombies, calculate_zombie_value, calculate_win_rate,
calculate_score_distribution, calculate_pipeline_health.

Camada 2 (Streamlit UI): render_metrics — chama as funcoes puras
e exibe com st.metric, st.plotly_chart.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from scoring.constants import ACTIVE_STAGES, SCORE_BANDS
from utils.formatters import format_currency, format_percentage


# ===========================================================================
# Camada 1 — funcoes puras (sem Streamlit)
# ===========================================================================


def count_active_deals(df: pd.DataFrame) -> int:
    """Conta deals com deal_stage em Prospecting ou Engaging."""
    if df.empty:
        return 0
    return int(df["deal_stage"].isin(ACTIVE_STAGES).sum())


def calculate_pipeline_total(df: pd.DataFrame) -> float:
    """Soma estimated_value dos deals ativos.

    estimated_value ja contem close_value (quando disponivel) ou
    sales_price como proxy.
    """
    if df.empty:
        return 0.0
    active = df[df["deal_stage"].isin(ACTIVE_STAGES)]
    return float(active["estimated_value"].sum())


def count_zombies(df: pd.DataFrame) -> int:
    """Conta deals com is_zombie == True."""
    if df.empty:
        return 0
    return int(df["is_zombie"].sum())


def calculate_zombie_value(df: pd.DataFrame) -> float:
    """Soma estimated_value dos deals zumbi."""
    if df.empty:
        return 0.0
    zombies = df[df["is_zombie"] == True]  # noqa: E712
    if zombies.empty:
        return 0.0
    return float(zombies["estimated_value"].sum())


def calculate_win_rate(df: pd.DataFrame) -> float | None:
    """Calcula win rate = Won / (Won + Lost).

    Retorna None se nao houver deals fechados (Won ou Lost).
    """
    if df.empty:
        return None
    won = int((df["deal_stage"] == "Won").sum())
    lost = int((df["deal_stage"] == "Lost").sum())
    total_closed = won + lost
    if total_closed == 0:
        return None
    return won / total_closed


def calculate_score_distribution(df: pd.DataFrame) -> list[dict]:
    """Distribui deals ativos nas 4 faixas de score.

    Retorna lista de dicts: {name, range, count, pct, color}.
    Faixas: Critico (0-40), Risco (40-60), Atencao (60-80), Alta (80-100).
    """
    active = df[df["deal_stage"].isin(ACTIVE_STAGES)] if not df.empty else df
    total = len(active)

    distribution = []
    for band in SCORE_BANDS:
        name = band["name"]
        lo, hi = band["min"], band["max"]
        range_label = f"{name} ({lo}-{hi})"

        if total == 0:
            count = 0
            pct = 0.0
        else:
            if hi >= 100:
                mask = (active["score"] >= lo) & (active["score"] <= hi)
            else:
                mask = (active["score"] >= lo) & (active["score"] < hi)
            count = int(mask.sum())
            pct = count / total if total > 0 else 0.0

        distribution.append({
            "name": range_label,
            "range": f"{lo}-{hi}",
            "count": count,
            "pct": pct,
            "color": band["color"],
        })

    return distribution


def calculate_pipeline_health(df: pd.DataFrame) -> dict:
    """Retorna saude do pipeline: {healthy, zombies, total}.

    Considera apenas deals ativos (Prospecting + Engaging).
    """
    if df.empty:
        return {"healthy": 0, "zombies": 0, "total": 0}

    active = df[df["deal_stage"].isin(ACTIVE_STAGES)]
    total = len(active)
    zombies = int(active["is_zombie"].sum())
    healthy = total - zombies

    return {"healthy": healthy, "zombies": zombies, "total": total}


# ===========================================================================
# Graficos (Plotly)
# ===========================================================================


def create_score_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """Cria grafico de barras horizontais da distribuicao de score."""
    dist = calculate_score_distribution(df)

    names = [d["name"] for d in dist]
    counts = [d["count"] for d in dist]
    colors = [d["color"] for d in dist]

    fig = go.Figure(go.Bar(
        x=counts,
        y=names,
        orientation="h",
        marker_color=colors,
        text=counts,
        textposition="auto",
    ))

    fig.update_layout(
        title="Distribuicao por Faixa de Score",
        xaxis_title="Quantidade de Deals",
        yaxis_title="",
        height=250,
        margin=dict(l=10, r=10, t=40, b=10),
        yaxis=dict(autorange="reversed"),
    )

    return fig


def create_pipeline_health_chart(df: pd.DataFrame) -> go.Figure:
    """Cria grafico donut (saudaveis vs zumbis)."""
    health = calculate_pipeline_health(df)

    labels = ["Saudaveis", "Zumbis"]
    values = [health["healthy"], health["zombies"]]
    colors = ["#2ecc71", "#e74c3c"]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.5,
        marker_colors=colors,
        textinfo="label+value",
        textposition="outside",
    ))

    fig.update_layout(
        title="Saude do Pipeline",
        height=250,
        margin=dict(l=10, r=10, t=40, b=10),
        showlegend=False,
    )

    return fig


# ===========================================================================
# Camada 2 — renderizacao Streamlit (NAO testada em unit tests)
# ===========================================================================


def render_metrics(
    df_filtered: pd.DataFrame,
    df_all: pd.DataFrame,
    active_filters: dict,
    pipeline_df: pd.DataFrame | None = None,
) -> None:
    """Renderiza metricas e graficos no Streamlit.

    Parametros:
        df_filtered: DataFrame com deals ja filtrados
        df_all: DataFrame completo (para comparacoes)
        active_filters: dict com filtros ativos {campo: valor}
        pipeline_df: Pipeline completo (com Won/Lost) para win rate
    """
    import streamlit as st

    # ── KPIs principais ──────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    active_count = count_active_deals(df_filtered)
    pipeline_total = calculate_pipeline_total(df_filtered)
    zombie_count = count_zombies(df_filtered)

    # Win rate: usar pipeline completo (com Won/Lost), filtrado pela hierarquia
    if pipeline_df is not None:
        wr_df = pipeline_df
        if active_filters.get("office") and active_filters["office"] != "Todos":
            wr_df = wr_df[wr_df["regional_office"] == active_filters["office"]]
        if active_filters.get("manager") and active_filters["manager"] != "Todos":
            wr_df = wr_df[wr_df["manager"] == active_filters["manager"]]
        if active_filters.get("agent") and active_filters["agent"] != "Todos":
            wr_df = wr_df[wr_df["sales_agent"] == active_filters["agent"]]
        win_rate = calculate_win_rate(wr_df)
    else:
        win_rate = calculate_win_rate(df_filtered)

    with col1:
        st.metric("Deals Ativos", active_count)

    with col2:
        st.metric("Pipeline Total", format_currency(pipeline_total))

    with col3:
        st.metric("Deals Zumbi", zombie_count)

    with col4:
        wr_display = format_percentage(win_rate) if win_rate is not None else "—"
        st.metric("Taxa de Conversao", wr_display)

    # ── Graficos ─────────────────────────────────────────────────────
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        fig_dist = create_score_distribution_chart(df_filtered)
        st.plotly_chart(fig_dist, use_container_width=True)

    with chart_col2:
        fig_health = create_pipeline_health_chart(df_filtered)
        st.plotly_chart(fig_health, use_container_width=True)
