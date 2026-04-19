import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from scoring import load_and_merge, score_all
from ai_insights import get_recommendation

st.set_page_config(
    page_title="Lead Scorer",
    page_icon="📊",
    layout="wide",
)

TIER_COLORS = {"A": "#d4edda", "B": "#fff3cd", "C": "#f8d7da"}  # kept for other uses
FEATURE_CAPTION = (
    "**Como o score é calculado (máx 100 pts):** "
    "Estágio do deal (30) · Tempo no pipeline (20) · Valor do deal (20) · "
    "Win rate do setor histórico (15) · Win rate do vendedor histórico (10) · "
    "Tamanho da conta (5)"
)


@st.cache_data(ttl=3600)
def get_scored_df():
    df = load_and_merge()
    return score_all(df)


# ── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("📊 Lead Scorer")
    st.markdown("---")

    api_key = st.text_input(
        "Chave Anthropic (opcional)",
        type="password",
        placeholder="sk-ant-...",
        help="Cole sua chave para análise com IA",
    )

    st.markdown("---")
    st.subheader("Filtros")

    if st.button("🔄 Atualizar scores", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

scored_df = get_scored_df()

# Build filter options from scored data
all_agents = sorted(scored_df["sales_agent"].dropna().unique())
all_managers = sorted(scored_df["manager"].dropna().unique())
all_regions = sorted(scored_df["regional_office"].dropna().unique())

with st.sidebar:
    selected_agent = st.selectbox("Vendedor", ["Todos"] + all_agents)
    selected_manager = st.selectbox("Manager", ["Todos"] + all_managers)
    selected_region = st.selectbox("Região", ["Todos"] + all_regions)
    selected_tiers = st.multiselect("Tier", ["A", "B", "C"], default=["A", "B"])

# ── Apply filters ────────────────────────────────────────────────────────────

view = scored_df.copy()
if selected_agent != "Todos":
    view = view[view["sales_agent"] == selected_agent]
if selected_manager != "Todos":
    view = view[view["manager"] == selected_manager]
if selected_region != "Todos":
    view = view[view["regional_office"] == selected_region]
if selected_tiers:
    view = view[view["tier"].isin(selected_tiers)]

view = view.reset_index(drop=True)

# ── Header metrics ───────────────────────────────────────────────────────────

st.markdown("# 📊 Lead Scorer — Priorização de Pipeline")

tier_a = view[view["tier"] == "A"]
col1, col2, col3, col4 = st.columns(4)
col1.metric("Deals visíveis", len(view))
col2.metric("Tier A", len(tier_a))
col3.metric(
    "Valor Tier A",
    f"R$ {tier_a['effective_value'].sum():,.0f}".replace(",", "."),
)
col4.metric("Score médio", f"{round(view['score'].mean())}" if len(view) > 0 else "—")

# ── Tabs ─────────────────────────────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs(["🗂 Pipeline", "🤖 Análise IA", "📈 Gestor"])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — Pipeline
# ═══════════════════════════════════════════════════════════════════════════

with tab1:
    # Global dark-mode CSS for the pipeline table wrapper
    st.markdown(
        """
        <style>
          .ls-wrap { background:#1e1e1e; border-radius:8px; padding:4px; }
          .ls-table { border-collapse:collapse; width:100%; font-size:0.88rem;
                      font-family:sans-serif; background:#1e1e1e; }
          .ls-table thead th { position:sticky; top:0; z-index:2; }
          .ls-table tr:hover td { filter:brightness(1.12); }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if view.empty:
        st.info("Nenhum deal encontrado com os filtros atuais.")
    else:
        # Dark-mode tier palette
        ROW_BG   = {"A": "#1a3a2a", "B": "#3a2e0a", "C": "#3a1a1a"}
        ROW_FG   = {"A": "#4ade80", "B": "#fbbf24", "C": "#f87171"}
        BADGE_BG = {"A": "#166534", "B": "#92400e", "C": "#991b1b"}
        BAR_FG   = {"A": "#4ade80", "B": "#fbbf24", "C": "#f87171"}
        DEFAULT_BG = "#1e1e1e"
        DEFAULT_FG = "#e5e5e5"

        def score_bar_html(score: int, tier: str) -> str:
            pct = min(int(score), 100)
            bar_color = BAR_FG.get(tier, "#9ca3af")
            fg = ROW_FG.get(tier, DEFAULT_FG)
            return (
                f'<div style="display:flex;align-items:center;gap:6px">'
                f'<span style="font-weight:700;min-width:26px;color:{fg}">{score}</span>'
                f'<div style="flex:1;background:#374151;border-radius:4px;height:9px;min-width:55px">'
                f'<div style="width:{pct}%;background:{bar_color};height:9px;border-radius:4px"></div>'
                f'</div></div>'
            )

        def tier_badge_html(tier: str) -> str:
            bg = BADGE_BG.get(tier, "#374151")
            fg = ROW_FG.get(tier, DEFAULT_FG)
            return (
                f'<span style="background:{bg};color:{fg};padding:2px 10px;'
                f'border-radius:12px;font-weight:700;font-size:0.83rem">{tier}</span>'
            )

        headers = ["Conta", "Estágio", "Vendedor", "Região",
                   "Valor Esperado (R$)", "Dias no Pipeline", "Score", "Tier"]

        rows_html = ""
        for _, row in view.head(100).iterrows():
            tier = row["tier"]
            bg = ROW_BG.get(tier, DEFAULT_BG)
            fg = ROW_FG.get(tier, DEFAULT_FG)
            val_fmt = "R$ {:,.0f}".format(float(row["effective_value"])).replace(",", ".")
            score_cell = score_bar_html(int(row["score"]), tier)
            badge = tier_badge_html(tier)
            cells = [
                row["account"],
                row["deal_stage"],
                row["sales_agent"],
                row.get("regional_office", ""),
                val_fmt,
                str(int(row["days_in_pipeline"])),
                score_cell,
                badge,
            ]
            tds = "".join(
                f'<td style="padding:6px 10px;color:{fg};white-space:nowrap">{c}</td>'
                for c in cells
            )
            rows_html += f'<tr style="background:{bg}">{tds}</tr>\n'

        ths = "".join(
            f'<th style="padding:8px 10px;background:#111827;color:#d1d5db;'
            f'white-space:nowrap;text-align:left;border-bottom:1px solid #374151">{h}</th>'
            for h in headers
        )
        html_table = f"""
        <div class="ls-wrap">
          <div style="overflow-x:auto;max-height:520px;overflow-y:auto">
            <table class="ls-table">
              <thead><tr>{ths}</tr></thead>
              <tbody>{rows_html}</tbody>
            </table>
          </div>
        </div>
        """
        st.html(html_table)
        st.caption(f"Exibindo até 100 de {len(view)} deals · {FEATURE_CAPTION}")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — Análise IA
# ═══════════════════════════════════════════════════════════════════════════

with tab2:
    if view.empty:
        st.info("Nenhum deal encontrado com os filtros atuais.")
    else:
        top20 = view.head(20)
        deal_labels = [
            f"#{i+1} · {row['account']} · {row['deal_stage']} · Score {row['score']} ({row['tier']})"
            for i, row in top20.iterrows()
        ]
        selected_idx = st.selectbox(
            "Selecione um deal para análise",
            range(len(top20)),
            format_func=lambda i: deal_labels[i],
        )

        selected_deal = top20.iloc[selected_idx]
        breakdown = selected_deal["breakdown"]

        left, right = st.columns([1, 2])

        with left:
            st.metric("Score", selected_deal["score"])
            tier_val = selected_deal["tier"]
            tier_bg = {"A": "🟢", "B": "🟡", "C": "🔴"}.get(tier_val, "")
            st.metric("Tier", f"{tier_bg} {tier_val}")

            # Horizontal bar chart of breakdown
            labels = list(breakdown.keys())
            values = list(breakdown.values())
            max_pts = [30, 20, 20, 15, 10, 5]

            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=labels,
                x=values,
                orientation="h",
                marker_color=["#2196F3", "#4CAF50", "#FF9800", "#9C27B0", "#F44336", "#00BCD4"],
                text=[f"{v} pts" for v in values],
                textposition="outside",
            ))
            fig.update_layout(
                title="Score por feature",
                xaxis_title="Pontos",
                height=320,
                margin=dict(l=10, r=60, t=40, b=10),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

        with right:
            # Full deal fields table
            detail_fields = {
                "Conta": selected_deal.get("account", ""),
                "Estágio": selected_deal.get("deal_stage", ""),
                "Produto": selected_deal.get("product", ""),
                "Série": selected_deal.get("series", ""),
                "Vendedor": selected_deal.get("sales_agent", ""),
                "Manager": selected_deal.get("manager", ""),
                "Região": selected_deal.get("regional_office", ""),
                "Setor": selected_deal.get("sector", ""),
                "Receita da Conta (USD M)": f"${float(selected_deal.get('revenue', 0)):,.1f}M",
                "Funcionários": int(selected_deal.get("employees", 0)),
                "Valor Esperado": f"R$ {float(selected_deal.get('effective_value', 0)):,.0f}".replace(",", "."),
                "Dias no Pipeline": selected_deal.get("days_in_pipeline", ""),
                "Data Engage": str(selected_deal.get("engage_date", ""))[:10],
            }
            detail_df = pd.DataFrame(
                list(detail_fields.items()), columns=["Campo", "Valor"]
            )
            st.dataframe(detail_df, use_container_width=True, hide_index=True)

            if api_key:
                if st.button("🤖 Analisar com IA", use_container_width=True):
                    with st.spinner("Consultando Claude..."):
                        insight = get_recommendation(
                            selected_deal.to_dict(), breakdown, api_key
                        )
                    urgency_map = {"alta": "🔴 Alta", "media": "🟡 Média", "baixa": "🟢 Baixa"}
                    st.markdown(f"**Urgência:** {urgency_map.get(insight.get('urgency','media'), insight.get('urgency',''))}")
                    st.info(f"⚠️ **Principal Risco:** {insight.get('main_risk','')}")
                    st.success(f"✅ **Próxima Ação:** {insight.get('next_action','')}")
                    st.caption(f"💡 **Por que este score:** {insight.get('why_score','')}")
            else:
                st.warning("Cole sua chave Anthropic na barra lateral para obter recomendações com IA.")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — Gestor
# ═══════════════════════════════════════════════════════════════════════════

with tab3:
    if view.empty:
        st.info("Nenhum deal encontrado com os filtros atuais.")
    else:
        # Grouped bar: deals per agent by tier
        agent_tier = (
            view.groupby(["sales_agent", "tier"])
            .size()
            .reset_index(name="count")
        )
        agent_a = agent_tier[agent_tier["tier"] == "A"].rename(columns={"count": "Tier A"})
        agent_b = agent_tier[agent_tier["tier"] == "B"].rename(columns={"count": "Tier B"})
        agent_summary = (
            agent_a[["sales_agent", "Tier A"]]
            .merge(agent_b[["sales_agent", "Tier B"]], on="sales_agent", how="outer")
            .fillna(0)
            .sort_values("Tier A", ascending=False)
        )
        agent_summary["Total"] = agent_summary["Tier A"] + agent_summary["Tier B"]
        agent_summary = agent_summary.nlargest(15, "Total").drop(columns="Total")

        fig_agents = go.Figure()
        fig_agents.add_trace(go.Bar(
            name="Tier A",
            x=agent_summary["sales_agent"],
            y=agent_summary["Tier A"],
            marker_color="#28a745",
        ))
        fig_agents.add_trace(go.Bar(
            name="Tier B",
            x=agent_summary["sales_agent"],
            y=agent_summary["Tier B"],
            marker_color="#ffc107",
        ))
        fig_agents.update_layout(
            barmode="group",
            title="Top 15 Vendedores — Tier A (verde) e Tier B (amarelo)",
            xaxis_tickangle=-45,
            height=420,
        )
        st.plotly_chart(fig_agents, use_container_width=True)

        # Manager summary table
        st.markdown("### Resumo por Manager")
        mgr_summary = []
        for mgr, grp in view.groupby("manager"):
            agents_count = grp["sales_agent"].nunique()
            deals_a = len(grp[grp["tier"] == "A"])
            deals_b = len(grp[grp["tier"] == "B"])
            valor = grp["effective_value"].sum()
            mgr_summary.append({
                "Manager": mgr,
                "Vendedores": agents_count,
                "Deals Tier A": deals_a,
                "Deals Tier B": deals_b,
                "Valor Pipeline": f"R$ {valor:,.0f}".replace(",", "."),
            })
        mgr_df = pd.DataFrame(mgr_summary).sort_values("Deals Tier A", ascending=False)
        st.dataframe(mgr_df, use_container_width=True, hide_index=True)

        # Scatter: days_in_pipeline vs score
        st.markdown("### Distribuição de Score × Tempo no Pipeline")
        color_map = {"A": "#28a745", "B": "#ffc107", "C": "#dc3545"}
        scatter_df = view.copy()
        scatter_df["cor"] = scatter_df["tier"].map(color_map)

        fig_scatter = px.scatter(
            scatter_df,
            x="days_in_pipeline",
            y="score",
            color="tier",
            color_discrete_map=color_map,
            hover_data={"account": True, "sales_agent": True, "deal_stage": True},
            labels={
                "days_in_pipeline": "Dias no Pipeline",
                "score": "Score",
                "tier": "Tier",
            },
            title="Score × Dias no Pipeline",
            height=420,
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

# ── Footer ───────────────────────────────────────────────────────────────────

st.markdown("---")
st.caption(
    f"Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')} · "
    + FEATURE_CAPTION
)
