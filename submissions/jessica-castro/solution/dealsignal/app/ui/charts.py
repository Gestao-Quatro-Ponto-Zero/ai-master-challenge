"""
DealSignal UI — Operational pipeline charts.

4 charts for the seller dashboard, laid out 2×2:
  Row 1: Top Opportunities | Pipeline por Rating
  Row 2: Fricções do Pipeline | Mapa de Velocidade

All charts follow the app's visual theme:
  transparent background, light grid, sans-serif font, st.container(border=True).
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


from config.constants import RATING_COLORS, RATING_ORDER

# ── Visual constants ───────────────────────────────────────────────────────────

_CHART_BG     = "rgba(0,0,0,0)"
_GRID_COLOR   = "rgba(128,128,128,0.12)"
_FONT         = dict(family="sans-serif", size=12, color="#333")
_MARGINS      = dict(l=10, r=10, t=10, b=30)
_MARGINS_HBAR = dict(l=10, r=160, t=10, b=10)  # margem extra p/ labels externos nos gráficos horizontais
_CHART_HEIGHT = 120


def _fmt(value: float) -> str:
    """Abrevia valores monetários: $1.2M, $586K, $3K."""
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value / 1_000:.0f}K"
    return f"${value:.0f}"

# ── Paleta unificada ──────────────────────────────────────────────────────────
_GREEN  = "#2e7d32"
_ORANGE = "#f57c00"
_RED    = "#c62828"
_GRAY   = "#78909c"

_HEALTH_COLOR = {
    "Saudável": _GREEN,
    "Atenção":  _ORANGE,
    "Em risco": _RED,
}

_FRICTION_FRIENDLY = {
    "execucao": "Fechamento em Execução",
    "decisao":  "Decisão Travada",
    "urgencia": "Urgência Baixa",
    "valor":    "Valor Pouco Claro",
}

_FRICTION_COLORS = {
    "Fechamento em Execução": _GREEN,
    "Decisão Travada":        _ORANGE,
    "Urgência Baixa":         _RED,
    "Valor Pouco Claro":      _GRAY,
}


def _base_layout(height: int = 380, margin: dict = None, **kwargs) -> dict:
    """Returns shared Plotly layout kwargs."""
    return dict(
        plot_bgcolor=_CHART_BG,
        paper_bgcolor=_CHART_BG,
        font=_FONT,
        margin=margin if margin is not None else _MARGINS,
        height=height,
        **{"showlegend": False, **kwargs},
    )


# ── Friction helpers ───────────────────────────────────────────────────────────

def _classify_friction(row) -> str:
    """
    Approximates dominant friction for a single row using column proxies.
    Reuses identify_friction() — no compute_engine_scores needed.
    """
    from engine.next_best_action import identify_friction

    is_stale  = int(row.get("is_stale_flag") or 0)
    dm_days   = float(row.get("days_since_engage") or 30)
    seller_pct = row.get("seller_rank_percentile")
    prod_pct   = row.get("product_rank_percentile")

    sp = float(seller_pct) * 100 if pd.notna(seller_pct) and seller_pct is not None else 50.0
    pp = float(prod_pct)   * 100 if pd.notna(prod_pct)   and prod_pct   is not None else 50.0

    if is_stale:
        dm, stagnation = 25, 10
    elif dm_days <= 14:
        dm, stagnation = 80, 80
    elif dm_days <= 30:
        dm, stagnation = 60, 80
    elif dm_days <= 60:
        dm, stagnation = 45, 50
    else:
        dm, stagnation = 30, 25

    digital = row.get("digital_maturity_index")

    ctx = {
        "win_prob":         float(row.get("win_probability") or 0.0),
        "sp":               sp,
        "dm":               dm,
        "pp":               pp,
        "stagnation_health": stagnation,
        "is_stale":         is_stale,
        "seller_rank_pct":  float(seller_pct) if pd.notna(seller_pct) and seller_pct is not None else None,
        "digital_maturity": float(digital)    if pd.notna(digital)    and digital    is not None else None,
    }
    return identify_friction(ctx)["friction"]


@st.cache_data(show_spinner=False)
def _compute_friction_series(df_hash: int, records_json: str) -> list:
    """Cached computation of friction labels for all rows."""
    import json
    records = json.loads(records_json)
    df = pd.DataFrame(records)
    return df.apply(_classify_friction, axis=1).tolist()


# ── Chart 1 — Pipeline em Risco ───────────────────────────────────────────────

def render_top_opportunities(df: pd.DataFrame) -> "str | None":
    with st.container(border=True):
        st.markdown("#### Pipeline em Risco")
        st.caption("Deals agrupados por dias sem engajamento")
        if df.empty:
            st.info("Nenhum dado disponível.")
            return

        cols = ["days_since_engage", "expected_revenue"]
        work = df[[c for c in cols if c in df.columns]].dropna(subset=["days_since_engage"]).copy()
        if work.empty:
            st.info("Nenhum dado disponível.")
            return

        bins   = [0, 30, 60, 90, float("inf")]
        labels = ["0–30 dias", "30–60 dias", "60–90 dias", "90+ dias"]
        colors = [_GREEN, _ORANGE, _RED, _GRAY]

        work["faixa"] = pd.cut(work["days_since_engage"], bins=bins, labels=labels, right=False)
        counts = (
            work.groupby("faixa", observed=False)
            .agg(deals=("days_since_engage", "count"),
                 revenue=("expected_revenue", "sum"))
            .reindex(labels)
            .fillna(0)
            .reset_index()
        )
        counts["deals"] = counts["deals"].astype(int)
        counts["text"]  = counts.apply(
            lambda r: f"{_fmt(r['revenue'])} ({r['deals']})", axis=1
        )

        fig = go.Figure(go.Bar(
            x=counts["deals"],
            y=counts["faixa"],
            orientation="h",
            marker_color=colors,
            text=counts["text"],
            textposition="outside",
            cliponaxis=False,
            textfont=dict(size=12),
        ))
        fig.update_layout(
            **_base_layout(height=_CHART_HEIGHT, margin=_MARGINS_HBAR),
            xaxis=dict(gridcolor=_GRID_COLOR, zeroline=False, showticklabels=False),
            yaxis=dict(gridcolor=_GRID_COLOR, zeroline=False, tickfont=dict(size=12), autorange="reversed"),
        )
        event = st.plotly_chart(fig, theme="streamlit", use_container_width=True,
                                on_select="rerun", key="chart_days")
        pts = event.selection.points if event and event.selection else []
        return pts[0]["y"] if pts else None


# ── Chart 2 — Pipeline por Rating ─────────────────────────────────────────────

def render_pipeline_by_rating(df: pd.DataFrame) -> "str | None":
    with st.container(border=True):
        st.markdown("#### Distribuição por Rating")
        if df.empty:
            st.info("Nenhum dado disponível.")
            return

        counts = (
            df.groupby("deal_rating")
            .agg(deals=("opportunity_id", "count"),
                 revenue=("expected_revenue", "sum"))
            .reindex(RATING_ORDER)
            .fillna(0)
            .reset_index()
        )
        counts["deals"] = counts["deals"].astype(int)
        counts["text"]  = counts.apply(
            lambda r: f"{_fmt(r['revenue'])} ({r['deals']})", axis=1
        )
        counts.columns = ["rating", "deals", "revenue", "text"]

        colors = [RATING_COLORS.get(r, "#888") for r in counts["rating"]]

        fig = go.Figure(go.Bar(
            x=counts["rating"],
            y=counts["deals"],
            marker_color=colors,
            text=counts["text"],
            textposition="outside",
            cliponaxis=False,
            textfont=dict(size=11),
        ))
        fig.update_layout(
            **_base_layout(height=_CHART_HEIGHT),
            xaxis=dict(gridcolor=_GRID_COLOR, zeroline=False, categoryorder="array", categoryarray=RATING_ORDER),
            yaxis=dict(gridcolor=_GRID_COLOR, zeroline=False),
        )
        event = st.plotly_chart(fig, theme="streamlit", use_container_width=True,
                                on_select="rerun", key="chart_rating")
        pts = event.selection.points if event and event.selection else []
        return pts[0]["x"] if pts else None


# ── Chart 3 — Fricções do Pipeline ────────────────────────────────────────────

def render_friction_distribution(df: pd.DataFrame) -> None:
    with st.container(border=True):
        st.markdown("#### Principais Fricções")
        if df.empty:
            st.info("Nenhum dado disponível.")
            return

        cols_needed = ["win_probability", "days_since_engage", "is_stale_flag",
                       "seller_rank_percentile", "product_rank_percentile", "expected_revenue"]
        work = df[[c for c in cols_needed if c in df.columns]].copy()

        df_hash      = hash(df["opportunity_id"].astype(str).sort_values().str.cat())
        records_json = work.to_json(orient="records")

        friction_keys   = _compute_friction_series(df_hash, records_json)
        friction_labels = [_FRICTION_FRIENDLY.get(k, k) for k in friction_keys]

        work = work.copy()
        work["fricao"] = friction_labels

        order = ["Fechamento em Execução", "Decisão Travada", "Urgência Baixa", "Valor Pouco Claro"]
        counts = (
            work.groupby("fricao")
            .agg(deals=("fricao", "count"),
                 revenue=("expected_revenue", "sum"))
            .reindex(order)
            .fillna(0)
            .reset_index()
        )
        counts["deals"] = counts["deals"].astype(int)
        counts["text"]  = counts.apply(
            lambda r: f"{_fmt(r['revenue'])} ({r['deals']})", axis=1
        )
        counts = counts.sort_values("deals", ascending=True)

        colors = [_FRICTION_COLORS.get(f, "#aaa") for f in counts["fricao"]]

        fig = go.Figure(go.Bar(
            x=counts["deals"],
            y=counts["fricao"],
            orientation="h",
            marker_color=colors,
            text=counts["text"],
            textposition="outside",
            cliponaxis=False,
            textfont=dict(size=12),
        ))
        fig.update_layout(
            **_base_layout(height=_CHART_HEIGHT, margin=_MARGINS_HBAR),
            xaxis=dict(gridcolor=_GRID_COLOR, zeroline=False, showticklabels=False),
            yaxis=dict(gridcolor=_GRID_COLOR, zeroline=False, tickfont=dict(size=11)),
        )
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)


# ── Chart 4 — Mapa de Velocidade do Pipeline ──────────────────────────────────

def render_velocity_map(df: pd.DataFrame) -> "str | None":
    with st.container(border=True):
        st.markdown("#### Quadrante de Prioridade do Pipeline")
        st.caption("Probabilidade de fechamento vs tempo desde o último engajamento")
        if df.empty:
            st.info("Nenhum dado disponível.")
            return None

        work = df[["opportunity_id", "win_probability", "days_since_engage", "deal_health_status", "account", "product"]].dropna(
            subset=["win_probability", "days_since_engage"]
        ).head(10).copy()
        if work.empty:
            st.info("Nenhum dado disponível.")
            return

        work["win_pct"] = (work["win_probability"] * 100).round(1)
        work["label"]   = work["account"] + " · " + work["product"]

        x_cut = 60   # % probability threshold
        y_cut = 60   # days threshold

        x_max = max(105, work["win_pct"].max() + 5)
        y_max = max(y_cut * 2.5, work["days_since_engage"].max() * 1.1)

        # Quadrant background shading
        _Q_SHAPES = [
            # top-left: EM RISCO (low prob, many days) — very light red
            dict(type="rect", xref="x", yref="y",
                 x0=0, x1=x_cut, y0=y_cut, y1=y_max,
                 fillcolor="rgba(239,68,68,0.05)", line_width=0),
            # top-right: OPORTUNIDADE ESQUECIDA (high prob, many days) — very light orange
            dict(type="rect", xref="x", yref="y",
                 x0=x_cut, x1=x_max, y0=y_cut, y1=y_max,
                 fillcolor="rgba(251,191,36,0.07)", line_width=0),
            # bottom-left: BAIXA PRIORIDADE (low prob, few days) — very light grey
            dict(type="rect", xref="x", yref="y",
                 x0=0, x1=x_cut, y0=0, y1=y_cut,
                 fillcolor="rgba(148,163,184,0.07)", line_width=0),
            # bottom-right: FOCO DO VENDEDOR (high prob, few days) — very light green
            dict(type="rect", xref="x", yref="y",
                 x0=x_cut, x1=x_max, y0=0, y1=y_cut,
                 fillcolor="rgba(46,125,50,0.07)", line_width=0),
        ]

        # Quadrant divider lines
        _Q_LINES = [
            dict(type="line", xref="x", yref="y",
                 x0=x_cut, x1=x_cut, y0=0, y1=y_max,
                 line=dict(color="rgba(100,116,139,0.35)", width=1.5, dash="dot")),
            dict(type="line", xref="x", yref="y",
                 x0=0, x1=x_max, y0=y_cut, y1=y_cut,
                 line=dict(color="rgba(100,116,139,0.35)", width=1.5, dash="dot")),
        ]

        # Quadrant label annotations
        _Q_LABELS = [
            dict(x=x_cut / 2,            y=y_max * 0.93,
                 text="<b>EM RISCO</b><br><span style='font-size:10px'>Baixa chance e estagnação</span>",
                 showarrow=False, font=dict(size=11, color="rgba(185,28,28,0.7)"),
                 xref="x", yref="y", xanchor="center"),
            dict(x=(x_cut + x_max) / 2,  y=y_max * 0.93,
                 text="<b>OPORTUNIDADE ESQUECIDA</b><br><span style='font-size:10px'>Deal com potencial alto mas parado</span>",
                 showarrow=False, font=dict(size=11, color="rgba(180,83,9,0.7)"),
                 xref="x", yref="y", xanchor="center"),
            dict(x=x_cut / 2,            y=y_cut * 0.12,
                 text="<b>BAIXA PRIORIDADE</b><br><span style='font-size:10px'>Deal inicial ou pouco qualificado</span>",
                 showarrow=False, font=dict(size=11, color="rgba(71,85,105,0.7)"),
                 xref="x", yref="y", xanchor="center"),
            dict(x=(x_cut + x_max) / 2,  y=y_cut * 0.12,
                 text="<b>FOCO DO VENDEDOR</b><br><span style='font-size:10px'>Alta probabilidade e avanço recente</span>",
                 showarrow=False, font=dict(size=11, color="rgba(21,128,61,0.8)"),
                 xref="x", yref="y", xanchor="center"),
        ]

        fig = go.Figure()
        for status, color in _HEALTH_COLOR.items():
            subset = work[work["deal_health_status"] == status]
            if subset.empty:
                continue
            fig.add_trace(go.Scatter(
                x=subset["win_pct"],
                y=subset["days_since_engage"],
                mode="markers",
                name=status,
                marker=dict(size=16, color=color, opacity=0.7, line=dict(width=0)),
                text=subset["label"],
                customdata=subset["opportunity_id"].tolist(),
                hovertemplate="%{text}<br>Prob: %{x:.1f}%<br>Dias: %{y}<extra></extra>",
            ))

        fig.update_layout(
            plot_bgcolor=_CHART_BG,
            paper_bgcolor=_CHART_BG,
            font=_FONT,
            height=_CHART_HEIGHT * 3,
            margin=dict(l=60, r=20, t=20, b=55),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top", y=-0.18,
                xanchor="left", x=0,
                font=dict(size=11),
            ),
            shapes=_Q_SHAPES + _Q_LINES,
            annotations=_Q_LABELS,
            xaxis=dict(
                title="Probabilidade de Fechamento (%)",
                gridcolor=_GRID_COLOR,
                zeroline=False,
                ticksuffix="%",
                range=[0, x_max],
            ),
            yaxis=dict(
                title="Dias desde engajamento",
                gridcolor=_GRID_COLOR,
                zeroline=False,
                range=[0, y_max],
            ),
        )
        event = st.plotly_chart(fig, theme="streamlit", use_container_width=True,
                                on_select="rerun", key="chart_quadrant",
                                config={"scrollZoom": False, "displayModeBar": False})
        pts = event.selection.points if event and event.selection else []
        return pts[0]["customdata"] if pts else None
