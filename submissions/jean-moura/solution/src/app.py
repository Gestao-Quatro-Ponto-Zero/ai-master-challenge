"""
Lead Scorer — Pipeline prioritization tool for sales teams.
Run with: streamlit run src/app.py
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Ensure project root is on sys.path for src.scorer import
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.scorer import Scorer

st.set_page_config(
    page_title="Lead Scorer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = _PROJECT_ROOT / "data"


@st.cache_data
def load_data():
    accts = pd.read_csv(DATA_DIR / "accounts.csv")
    prods = pd.read_csv(DATA_DIR / "products.csv")
    teams = pd.read_csv(DATA_DIR / "sales_teams.csv")
    pipeline = pd.read_csv(DATA_DIR / "sales_pipeline.csv")

    merged = pipeline.merge(accts, on="account", how="left")
    merged = merged.merge(prods, on="product", how="left")
    merged = merged.merge(teams, on="sales_agent", how="left")

    return accts, prods, teams, pipeline, merged


@st.cache_data
def score_data(merged):
    scorer = Scorer()
    accts = pd.read_csv(DATA_DIR / "accounts.csv")
    prods = pd.read_csv(DATA_DIR / "products.csv")
    teams = pd.read_csv(DATA_DIR / "sales_teams.csv")
    pipeline = pd.read_csv(DATA_DIR / "sales_pipeline.csv")
    scorer.fit(pipeline, accts, prods, teams)
    return scorer.score_pipeline(merged), scorer


def fmt_val(v):
    """Format value for display, handling NaN."""
    if pd.isna(v):
        return "—"
    return f"${v:,.0f}"


# ─── Load ────────────────────────────────────────────────────────────────────
accts, prods, teams, pipeline, merged = load_data()
scored_df, scorer = score_data(merged)

# ─── Sidebar filters ─────────────────────────────────────────────────────────
st.sidebar.title("🎯 Lead Scorer")
st.sidebar.markdown("### Filtros")

all_agents = sorted(scored_df["sales_agent"].dropna().unique())
all_managers = sorted(scored_df["manager"].dropna().unique())
all_regions = sorted(scored_df["regional_office"].dropna().unique())
all_stages = ["Prospecting", "Engaging", "Won", "Lost"]

selected_agent = st.sidebar.selectbox("Vendedor", ["Todos"] + all_agents)
selected_manager = st.sidebar.selectbox("Manager", ["Todos"] + all_managers)
selected_region = st.sidebar.selectbox("Região", ["Todas"] + all_regions)
selected_stages = st.sidebar.multiselect(
    "Estágios", all_stages)
min_score = st.sidebar.slider("Score mínimo", 0, 100, 0)

# ─── Apply filters ───────────────────────────────────────────────────────────
df = scored_df.copy()
if selected_agent != "Todos":
    df = df[df["sales_agent"] == selected_agent]
if selected_manager != "Todos":
    df = df[df["manager"] == selected_manager]
if selected_region != "Todas":
    df = df[df["regional_office"] == selected_region]
if selected_stages:
    df = df[df["deal_stage"].isin(selected_stages)]
df = df[df["score"] >= min_score]

# ─── Tabs (Analytics first) ──────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Analytics", "📋 Pipeline", "🔍 Deal Detail"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: ANALYTICS (primary view)
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("## 📊 Visão Gerencial do Pipeline")

    open_df = df[df["deal_stage"].isin(["Prospecting", "Engaging"])].copy()

    # ── Manager KPIs ───────────────────────────────────────────────────────
    st.subheader("Performance por Manager")
    mgr_stats = (
        open_df.groupby("manager")
        .agg(
            deals_ativos=("opportunity_id", "count"),
            valor_estimado=("sales_price", "sum"),
            score_medio=("score", "mean"),
        )
        .round(1)
        .reset_index()
    )
    # Win rate per manager (from closed deals)
    closed = df[df["deal_stage"].isin(["Won", "Lost"])].copy()
    if len(closed) > 0:
        mgr_wr = (
            closed.groupby("manager")["deal_stage"]
            .apply(lambda x: (x == "Won").mean())
            .mul(100)
            .round(1)
            .reset_index()
        )
        mgr_wr.columns = ["manager", "win_rate"]
        mgr_stats = mgr_stats.merge(mgr_wr, on="manager", how="left")

    mgr_stats["valor_estimado"] = mgr_stats["valor_estimado"].fillna(0).astype(int)

    # Manager KPI cards
    mgr_stats = mgr_stats.sort_values("score_medio", ascending=False)
    mcols = st.columns(len(mgr_stats))
    for i, (_, row) in enumerate(mgr_stats.iterrows()):
        with mcols[i]:
            st.markdown(f"**{row['manager']}**")
            st.markdown(f"🧑‍💼 {int(row['deals_ativos'])} deals")
            st.markdown(f"💰 ${row['valor_estimado']:,}")
            st.markdown(f"⭐ {row['score_medio']:.1f} score médio")
            if "win_rate" in row and pd.notna(row["win_rate"]):
                st.markdown(f"📈 {row['win_rate']}% win rate")

    st.markdown("---")

    # Manager comparison charts
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(
            mgr_stats.sort_values("deals_ativos", ascending=True),
            x="deals_ativos",
            y="manager",
            orientation="h",
            title="Deals Ativos por Manager",
            color="deals_ativos",
            color_continuous_scale="blues",
            text_auto=True,
        )
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = px.bar(
            mgr_stats.sort_values("score_medio", ascending=True),
            x="score_medio",
            y="manager",
            orientation="h",
            title="Score Médio por Manager",
            color="score_medio",
            color_continuous_scale=["#f1c40f", "#2ecc71"],
            text_auto=".1f",
        )
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        fig = px.bar(
            mgr_stats.sort_values("valor_estimado", ascending=True),
            x="valor_estimado",
            y="manager",
            orientation="h",
            title="Valor Estimado do Pipeline por Manager",
            color="valor_estimado",
            color_continuous_scale="greens",
            text_auto=".0s",
        )
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        if "win_rate" in mgr_stats.columns:
            valid_wr = mgr_stats.dropna(subset=["win_rate"])
            if len(valid_wr) > 0:
                fig = px.bar(
                    valid_wr.sort_values("win_rate", ascending=True),
                    x="win_rate",
                    y="manager",
                    orientation="h",
                    title="Win Rate por Manager",
                    color="win_rate",
                    color_continuous_scale=["#e74c3c", "#f1c40f", "#2ecc71"],
                    range_color=[0, 100],
                    text_auto=".1f",
                )
                fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ── Top Deals por Vendedor (expanders por Manager) ─────────────────────
    st.subheader("🎯 Top Deals por Vendedor")
    open_sorted = open_df.sort_values(["sales_agent", "score"], ascending=[True, False])

    mgrs_sorted = sorted(open_sorted["manager"].dropna().unique(),
                         key=lambda m: open_sorted[open_sorted["manager"] == m]["score"].mean(),
                         reverse=True)

    for idx, mgr in enumerate(mgrs_sorted):
        mgr_agents = open_sorted[open_sorted["manager"] == mgr]["sales_agent"].unique()
        mgr_region = open_sorted[open_sorted["manager"] == mgr]["regional_office"].iloc[0]
        mgr_open = open_sorted[open_sorted["manager"] == mgr]
        mgr_score = mgr_open["score"].mean()
        mgr_val = mgr_open["sales_price"].fillna(0).sum()
        expanded = idx == 0

        with st.expander(
            f"**{mgr}** ({mgr_region}) — {len(mgr_agents)} vendedores, "
            f"{len(mgr_open)} deals, &#9733; {mgr_score:.1f} score m&#233;dio, "
            f"&#128176; ${mgr_val:,.0f}",
            expanded=expanded,
        ):
            for agent in mgr_agents:
                agent_deals = open_sorted[
                    (open_sorted["sales_agent"] == agent) &
                    (open_sorted["manager"] == mgr)
                ].head(3)
                st.markdown(f"**{agent}**")
                for _, d in agent_deals.iterrows():
                    acct = d["account"] if pd.notna(d.get("account")) else "Sem conta"
                    val = d["sales_price"] if pd.notna(d.get("sales_price")) else 0
                    c = "&#128994;" if d["score"] >= 70 else "&#128993;" if d["score"] >= 40 else "&#128308;"
                    wp = d.get("win_prob", None)
                    wp_str = f" | Win: {wp:.0%}" if wp is not None and not pd.isna(wp) else ""
                    st.markdown(
                        f"&nbsp;&nbsp;&nbsp;&nbsp;{c} {acct} — "
                        f"Score: {d['score']:.0f} | {d['product']} | ${val:,.0f}{wp_str}"
                    )
    # ── Team Performance ───────────────────────────────────────────────────
    st.subheader("Performance Individual")
    closed = df[df["deal_stage"].isin(["Won", "Lost"])].copy()
    if len(closed) > 0:
        wr = (
            closed.groupby("sales_agent")["deal_stage"]
            .apply(lambda x: (x == "Won").mean())
            .sort_values()
            .reset_index()
        )
        wr.columns = ["Vendedor", "Win Rate"]
        wr["Win Rate %"] = (wr["Win Rate"] * 100).round(1)
        overall_wr = (closed["deal_stage"] == "Won").mean()

        fig = px.bar(
            wr,
            x="Win Rate %",
            y="Vendedor",
            orientation="h",
            title=f"Win Rate por Vendedor (média empresa: {overall_wr:.1%})",
            color="Win Rate %",
            color_continuous_scale=["#e74c3c", "#f1c40f", "#2ecc71"],
            range_color=[0, 100],
        )
        fig.add_vline(
            x=overall_wr * 100, line_dash="dash", line_color="gray",
            annotation_text="Média", annotation_position="top",
        )
        fig.update_layout(height=500, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum dado fechado com os filtros atuais.")

    st.markdown("---")

    # ── Pipeline Overview ──────────────────────────────────────────────────
    col_o1, col_o2 = st.columns(2)

    with col_o1:
        st.subheader("Distribuição por Estágio")
        stage_counts = df["deal_stage"].value_counts().reset_index()
        stage_counts.columns = ["Estágio", "Quantidade"]
        fig = px.pie(
            stage_counts,
            values="Quantidade",
            names="Estágio",
            color_discrete_map={
                "Won": "#2ecc71",
                "Lost": "#e74c3c",
                "Engaging": "#3498db",
                "Prospecting": "#f39c12",
            },
        )
        fig.update_traces(textinfo="label+percent")
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col_o2:
        st.subheader("Valor Estimado por Região")
        if len(open_df) > 0:
            region_val = (
                open_df.groupby("regional_office")["sales_price"]
                .sum()
                .sort_values()
                .reset_index()
            )
            region_val.columns = ["Região", "Valor Estimado"]
            fig = px.bar(
                region_val,
                x="Região",
                y="Valor Estimado",
                color="Valor Estimado",
                color_continuous_scale="blues",
                text_auto=".0s",
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhum deal aberto.")

    st.subheader("Tempo Médio por Estágio (deals fechados)")
    closed_dates = df[df["deal_stage"].isin(["Won", "Lost"])].copy()
    closed_dates["engage_date"] = pd.to_datetime(
        closed_dates["engage_date"], errors="coerce"
    )
    closed_dates["close_date"] = pd.to_datetime(
        closed_dates["close_date"], errors="coerce"
    )
    closed_dates["days_in_pipeline"] = (
        closed_dates["close_date"] - closed_dates["engage_date"]
    ).dt.days

    if len(closed_dates) > 0:
        stage_time = (
            closed_dates.groupby("deal_stage")["days_in_pipeline"]
            .agg(["mean", "median", "max", "count"])
            .round(1)
            .reset_index()
        )
        stage_time.columns = [
            "Estágio", "Média (dias)", "Mediana (dias)",
            "Máx (dias)", "Qtd Deals",
        ]
        st.dataframe(stage_time, use_container_width=True)
    else:
        st.info("Nenhum dado com datas.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: PIPELINE (deals sorted by score)
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    pipe_open = df[df["deal_stage"].isin(["Prospecting", "Engaging"])].copy()

    # Top-level metrics
    col1, col2, col3, col4 = st.columns(4)
    total_deals = len(pipe_open)
    total_value = pipe_open["sales_price"].fillna(0).sum()
    avg_score = pipe_open["score"].mean()
    top_deals = len(pipe_open[pipe_open["score"] >= 70])

    col1.metric("Deals Ativos", total_deals)
    col2.metric("Valor Estimado do Pipeline", f"${total_value:,.0f}")
    col3.metric("Score Médio", f"{avg_score:.1f}" if not pd.isna(avg_score) else "—")
    col4.metric("Deals Quentes (≥70)", top_deals)

    st.markdown("---")

    pipe_open = pipe_open.sort_values("score", ascending=False)

    def score_color(s):
        if s >= 70:
            return "🟢"
        if s >= 40:
            return "🟡"
        return "🔴"

    for _, deal in pipe_open.head(100).iterrows():
        color = score_color(deal["score"])
        has_acct = pd.notna(deal.get("account"))
        title_parts = [f"{color} Score: {deal['score']:.0f}/100"]
        if has_acct:
            title_parts.append(deal["account"])
        title_parts.extend([deal["product"], deal["sales_agent"], deal["deal_stage"]])
        title = " | ".join(title_parts)
        with st.expander(f"**{title}**"):
            breakdown = deal["score_breakdown"]
            weights = deal["score_weights"]
            win_pct = deal.get("win_prob", None)
            if win_pct is not None and not pd.isna(win_pct):
                st.markdown(f"**Probabilidade de Win:** {win_pct:.0%}")

            st.markdown("**Breakdown do Score**")
            factors = []
            for k in weights:
                sub = breakdown[k]
                w = weights[k]
                factors.append({
                    "factor": k.replace("_", " ").title(),
                    "sub_score": f"{sub:.0f}/100",
                    "weight": f"{w:.0%}",
                    "contribution": f"{sub * w:.1f}",
                })
            st.table(pd.DataFrame(factors))

    if len(pipe_open) > 100:
        st.caption(
            f"Mostrando os 100 melhores de {len(pipe_open)} deals. "
            "Ajuste os filtros para refinar."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: DEAL DETAIL
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    all_deals = df.sort_values("score", ascending=False)
    deal_options = [
        f"{'Unknown' if pd.isna(row['account']) else row['account']} — {row['product']} (Score: {row['score']:.0f})"
        for _, row in all_deals.iterrows()
    ]
    selected_deal_idx = st.selectbox(
        "Selecione um deal", range(len(deal_options)),
        format_func=lambda i: deal_options[i],
    )

    if selected_deal_idx is not None:
        deal = all_deals.iloc[selected_deal_idx]
        deal_title = deal["account"] if pd.notna(deal.get("account")) else "Deal sem conta"
        st.markdown(f"## {deal_title}")

        c1, c2, c3 = st.columns(3)
        c1.metric("Score", f"{deal['score']:.0f}/100")
        win_pct = deal.get("win_prob", None)
        if win_pct is not None and not pd.isna(win_pct):
            c1.metric("Prob. Win", f"{win_pct:.0%}")
        c2.metric("Produto", deal["product"])
        c3.metric("Vendedor", deal["sales_agent"])

        c4, c5, c6 = st.columns(3)
        c4.metric("Estágio", deal["deal_stage"])
        deal_value = (
            deal["close_value"]
            if pd.notna(deal.get("close_value"))
            else f"${deal['sales_price']:,.0f}*"
        )
        c5.metric("Valor", deal_value)
        c6.metric("Região", deal.get("regional_office", "—"))

        # Score breakdown chart
        st.markdown("### Breakdown do Score")
        bd = deal["score_breakdown"]
        wg = deal["score_weights"]

        factors_df = pd.DataFrame({
            "Fator": [k.replace("_", " ").title() for k in wg],
            "Sub-Score": [bd[k] for k in wg],
            "Peso": [wg[k] for k in wg],
            "Contribuição": [round(bd[k] * wg[k], 1) for k in wg],
        }).sort_values("Contribuição", ascending=True)

        fig = go.Figure(go.Bar(
            x=factors_df["Contribuição"],
            y=factors_df["Fator"],
            orientation="h",
            marker_color=[
                "#2ecc71" if c >= 10 else "#f1c40f" if c >= 5 else "#e74c3c"
                for c in factors_df["Contribuição"]
            ],
            text=factors_df["Contribuição"].apply(lambda x: f"{x:.1f}"),
            textposition="outside",
        ))
        fig.update_layout(
            title="Contribuição de cada fator para o score final",
            xaxis_title="Pontos no Score Final",
            yaxis_title="",
            height=350,
            margin=dict(l=0, r=0, t=40, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Ver detalhes dos fatores"):
            detail_rows = []
            for k in wg:
                raw_val = ""
                if k == "deal_stage":
                    raw_val = deal["deal_stage"]
                    comment = f"Estágio base: {raw_val} → {bd[k]:.0f}/100"
                elif k == "time_in_stage":
                    raw_val = f"{deal.get('days_in_stage', '—')} dias"
                    comment = (
                        "Mais tempo no estágio = mais momentum"
                        if bd[k] >= 50
                        else "Deal recente, ainda ganhando momentum"
                    )
                elif k == "seller_win_rate":
                    raw_val = f"{deal['sales_agent']}"
                    comment = f"Histórico do vendedor contribui {bd[k]:.0f}/100"
                elif k == "sector_win_rate":
                    raw_val = str(deal.get("sector", "—"))
                    comment = f"Conversão do setor: {bd[k]:.0f}/100"
                elif k == "product_price":
                    raw_val = f"${deal.get('sales_price', 0):,.0f}"
                    comment = (
                        "Produto de alto valor"
                        if bd[k] >= 50
                        else "Produto de menor valor"
                    )
                elif k == "account_revenue":
                    raw_val = f"${deal.get('revenue', 0):,.0f}M"
                    comment = (
                        "Conta de grande receita"
                        if bd[k] >= 50
                        else "Conta de menor receita"
                    )
                detail_rows.append({
                    "Fator": k.replace("_", " ").title(),
                    "Valor Bruto": raw_val,
                    "Sub-Score": f"{bd[k]:.0f}/100",
                    "Peso": f"{wg[k]:.0%}",
                    "Contribuição": f"{bd[k] * wg[k]:.1f} pts",
                    "Interpretação": comment,
                })
            st.table(pd.DataFrame(detail_rows))

st.sidebar.markdown("---")
st.sidebar.caption(
    f"Dados: {len(pipeline)} oportunidades, {len(accts)} contas, "
    f"{len(teams)} vendedores, {len(prods)} produtos"
)
