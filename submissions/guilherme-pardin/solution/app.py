import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from scoring import load_and_merge, score_all, compute_win_rates, MONTH_NAMES_PT
from ai_insights import get_recommendation, chat_completion, get_executive_summary

st.set_page_config(
    page_title="Lead Scorer",
    page_icon="📊",
    layout="wide",
)

st.markdown("""<style>
.stDeployButton{display:none!important}
header[data-testid="stHeader"]{background-color:#072B3A!important}
div[data-testid="stMetricValue"]{color:#C89B5A!important;font-size:28px!important;font-weight:800!important}
div[data-testid="stMetricLabel"]{color:#A0A0A0!important;font-size:10px!important;text-transform:uppercase!important;letter-spacing:1px!important}
button[data-baseweb="tab"][aria-selected="true"]{color:#C89B5A!important;border-bottom:2px solid #C89B5A!important}
div[data-testid="stSidebar"] .stButton>button{background-color:#C89B5A!important;color:#0B0B0B!important;font-weight:700!important;border:none!important;width:100%!important;border-radius:8px!important}
.stButton>button{border:1px solid #C89B5A!important;color:#C89B5A!important;border-radius:8px!important}
.stButton>button:hover{background-color:#C89B5A!important;color:#0B0B0B!important}
span[data-baseweb="tag"]{background-color:#0F3F52!important;color:#C89B5A!important;border:1px solid #C89B5A!important}
div[data-testid="stChatInputContainer"] textarea{border:1px solid #C89B5A!important;border-radius:8px!important}
div[data-testid="stAlert"]{border-left:4px solid #C89B5A!important}
hr{border-color:#1a3a5c!important}
</style>""", unsafe_allow_html=True)

G4_PLOTLY = dict(
    paper_bgcolor="#072B3A",
    plot_bgcolor="#0F3F52",
    font=dict(color="#FFFFFF", family="sans-serif"),
    xaxis=dict(gridcolor="#1a3a5c", linecolor="#1a3a5c"),
    yaxis=dict(gridcolor="#1a3a5c", linecolor="#1a3a5c"),
)
G4_MARGIN = dict(l=20, r=20, t=40, b=20)

TIER_COLORS = {"A": "#4ade80", "B": "#C89B5A", "C": "#f87171"}
FEATURE_CAPTION = (
    "**Como o score é calculado (máx 100 pts):** "
    "Estágio do deal (30) · Sazonalidade: win rate histórico do mês de entrada (20) · Valor do deal (20) · "
    "Win rate do setor histórico (15) · Win rate do vendedor histórico (10) · "
    "Tamanho da conta (5)"
)


@st.cache_data(ttl=3600)
def get_all_data():
    df = load_and_merge()
    scored = score_all(df)
    _, _, month_wr, _ = compute_win_rates(df)
    return scored, month_wr


# ── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.sidebar.markdown('<div style="margin-bottom:24px;padding-bottom:14px;border-bottom:1px solid #1a3a5c;"><span style="color:#C89B5A;font-weight:800;font-size:26px;">G4</span><span style="color:#fff;font-weight:300;font-size:26px;"> Lead Scorer</span></div>', unsafe_allow_html=True)
    st.markdown("---")
    api_provider = st.selectbox("Provedor de IA", ["Anthropic (Claude)", "Google (Gemini)", "OpenAI (GPT-4o mini)"])
    api_key = st.text_input("Chave da API", type="password", placeholder="Cole sua chave aqui")
    st.markdown("---")
    st.subheader("Filtros")

    if st.button("🔄 Atualizar scores", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

scored_df, month_wr = get_all_data()

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

st.markdown('<div style="margin-bottom:32px;padding-bottom:20px;border-bottom:1px solid #1a3a5c"><span style="color:#C89B5A;font-weight:800;font-size:30px;">G4</span><span style="color:#fff;font-weight:300;font-size:30px;"> Lead Scorer</span><div style="color:#A0A0A0;font-size:12px;margin-top:6px;text-transform:uppercase;letter-spacing:1.5px;">Priorização inteligente de pipeline</div></div>', unsafe_allow_html=True)

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

tab1, tab2, tab3, tab4 = st.tabs(["🗂 Pipeline", "🤖 Análise IA", "💬 Chat com IA", "📈 Gestor"])

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
                   "Valor Esperado (R$)", "Score", "Tier"]

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
            fig.update_traces(width=0.6)
            fig.update_layout(
                title="Score por feature",
                xaxis_title="Pontos",
                xaxis=dict(range=[0, 38], gridcolor="#1a3a5c", linecolor="#1a3a5c"),
                yaxis=dict(tickfont=dict(size=13), gridcolor="#1a3a5c", linecolor="#1a3a5c"),
                height=320,
                margin=dict(l=160, r=60, t=30, b=40),
                showlegend=False,
                paper_bgcolor="#072B3A",
                plot_bgcolor="#0F3F52",
                font=dict(color="#FFFFFF", family="sans-serif"),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "**Win rate vendedor+setor:** usa o histórico real da combinação "
                "vendedor + setor quando há 10+ deals. "
                "Caso contrário, usa o win rate geral do vendedor."
            )

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
                "Data Engage": str(selected_deal.get("engage_date", ""))[:10],
            }
            detail_df = pd.DataFrame(
                list(detail_fields.items()), columns=["Campo", "Valor"]
            )
            st.dataframe(detail_df, use_container_width=True, hide_index=True)

            if api_key:
                if st.button("🤖 Analisar com IA", use_container_width=True):
                    with st.spinner("Consultando IA..."):
                        insight = get_recommendation(
                            selected_deal.to_dict(), breakdown, api_key, api_provider
                        )
                    urgency_map = {"alta": "🔴 Alta", "media": "🟡 Média", "baixa": "🟢 Baixa"}
                    st.markdown(f"**Urgência:** {urgency_map.get(insight.get('urgency','media'), insight.get('urgency',''))}")
                    st.info(f"⚠️ **Principal Risco:** {insight.get('main_risk','')}")
                    st.success(f"✅ **Próxima Ação:** {insight.get('next_action','')}")
                    st.caption(f"💡 **Por que este score:** {insight.get('why_score','')}")
            else:
                st.warning("Cole sua chave de API na barra lateral para ativar a análise com IA.")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — Chat com IA
# ═══════════════════════════════════════════════════════════════════════════

CHAT_SUGGESTIONS = [
    "Quais meus 3 melhores deals para fechar essa semana?",
    "Quais setores têm mais chance de fechar?",
    "Por que meu score médio está baixo?",
    "Quais deals devo abandonar?",
]

with tab3:
    st.session_state.setdefault("chat_messages", [])

    chat_agents  = sorted(scored_df["sales_agent"].dropna().unique())
    chat_regions = sorted(scored_df["regional_office"].dropna().unique())

    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        chat_agent = st.selectbox("Vendedor", ["Todos"] + chat_agents, key="chat_agent")
    with cc2:
        chat_tier = st.selectbox("Tier", ["Todos", "A", "B", "C"], key="chat_tier")
    with cc3:
        chat_region = st.selectbox("Região", ["Todos"] + chat_regions, key="chat_region")

    chat_view = scored_df.copy()
    if chat_agent  != "Todos": chat_view = chat_view[chat_view["sales_agent"]     == chat_agent]
    if chat_tier   != "Todos": chat_view = chat_view[chat_view["tier"]            == chat_tier]
    if chat_region != "Todos": chat_view = chat_view[chat_view["regional_office"] == chat_region]
    chat_view = chat_view.reset_index(drop=True)

    ctx_label = chat_agent if chat_agent != "Todos" else "todos os vendedores"
    st.caption(f"{len(chat_view)} deals | {ctx_label}")
    st.markdown("---")

    def build_pipeline_context(df) -> str:
        lines = []
        for rank, (_, r) in enumerate(df.head(50).iterrows(), 1):
            bd = r.get("breakdown", {})
            sk = next((k for k in bd if k.startswith("Sazonalidade")), "")
            season = sk.split(" — ", 1)[1] if " — " in sk else "N/A"
            val = f"R$ {float(r['effective_value']):,.0f}".replace(",", ".")
            wr_agent_key = next((k for k in bd if k.startswith("Win rate vendedor")), "")
            wr_agent_pts = bd.get(wr_agent_key, "?")
            wr_agent_type = "combo" if "+" in wr_agent_key else "geral"
            lines.append(
                f"#{rank} | {r['account']} | {r['deal_stage']} | "
                f"Score {r['score']} ({r['tier']}) | {val} | "
                f"Setor: {r['sector']} | WR setor: {bd.get('Win rate do setor','?')}pts | "
                f"WR vendedor({wr_agent_type}): {wr_agent_pts}pts | Sazon: {season}"
            )
        summary = (
            f"Total: {len(df)} | Tier A: {(df['tier']=='A').sum()} | "
            f"Tier B: {(df['tier']=='B').sum()} | "
            f"Score médio: {round(df['score'].mean()) if len(df) else 0}\n"
        )
        return summary + "\n".join(lines)

    if not api_key:
        st.warning("Cole sua chave de API na barra lateral para usar o chat com IA.")
    else:
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if not st.session_state.chat_messages:
            st.markdown("**Sugestões:**")
            scols = st.columns(2)
            for i, sug in enumerate(CHAT_SUGGESTIONS):
                if scols[i % 2].button(sug, key=f"sug_{i}", use_container_width=True):
                    st.session_state.chat_messages.append({"role": "user", "content": sug})
                    with st.chat_message("user"):
                        st.markdown(sug)
                    with st.chat_message("assistant"):
                        with st.spinner("Consultando IA..."):
                            reply = chat_completion(
                                st.session_state.chat_messages,
                                build_pipeline_context(chat_view),
                                api_key,
                                api_provider,
                            )
                        st.markdown(reply)
                    st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                    st.rerun()

        if prompt := st.chat_input("Pergunte sobre seu pipeline..."):
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Consultando IA..."):
                    reply = chat_completion(
                        st.session_state.chat_messages,
                        build_pipeline_context(chat_view),
                        api_key,
                        api_provider,
                    )
                st.markdown(reply)
            st.session_state.chat_messages.append({"role": "assistant", "content": reply})

        if st.button("🗑 Limpar conversa"):
            st.session_state.chat_messages = []
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# TAB 4 — Gestor
# ═══════════════════════════════════════════════════════════════════════════

with tab4:
    if view.empty:
        st.info("Nenhum deal encontrado com os filtros atuais.")
    else:
        # ── Resumo Executivo do Pipeline ──────────────────────────────────────
        st.markdown("### Resumo Executivo do Pipeline")

        _tier_a_v = view[view["tier"] == "A"]
        _tier_b_v = view[view["tier"] == "B"]
        _exec_stats = {
            "total_deals":   len(view),
            "tier_a_count":  len(_tier_a_v),
            "tier_a_value":  _tier_a_v["effective_value"].sum(),
            "tier_b_count":  len(_tier_b_v),
            "avg_score":     view["score"].mean() if len(view) else 0,
            "top_seller": (
                _tier_a_v["sales_agent"].value_counts().index[0]
                if len(_tier_a_v) else "N/A"
            ),
            "top_sector": (
                _tier_a_v["sector"].value_counts().index[0]
                if len(_tier_a_v) else "N/A"
            ),
            "best_month":  MONTH_NAMES_PT.get(max(month_wr, key=month_wr.get), "N/A") if month_wr else "N/A",
            "worst_month": MONTH_NAMES_PT.get(min(month_wr, key=month_wr.get), "N/A") if month_wr else "N/A",
            "best_wr":     max(month_wr.values()) if month_wr else 0,
            "worst_wr":    min(month_wr.values()) if month_wr else 0,
        }

        _summary_key = f"exec_summary_{hash(frozenset((k, str(v)) for k, v in _exec_stats.items()))}"

        if api_key:
            if _summary_key not in st.session_state:
                if st.button("✨ Gerar resumo com IA", use_container_width=False):
                    with st.spinner("Consultando IA..."):
                        st.session_state[_summary_key] = get_executive_summary(
                            _exec_stats, api_key, api_provider
                        )
            if _summary_key in st.session_state:
                st.info(st.session_state[_summary_key])
                if st.button("🔄 Regenerar resumo", key="regen_exec"):
                    del st.session_state[_summary_key]
                    st.rerun()
        else:
            st.warning("Cole sua chave de API na barra lateral para gerar o resumo executivo com IA.")

        st.markdown("---")

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
            marker_color="#4ade80",
        ))
        fig_agents.add_trace(go.Bar(
            name="Tier B",
            x=agent_summary["sales_agent"],
            y=agent_summary["Tier B"],
            marker_color="#C89B5A",
        ))
        fig_agents.update_layout(
            barmode="group",
            title="Top 15 Vendedores — Tier A (verde) e Tier B (dourado)",
            xaxis_tickangle=-45,
            height=420,
            **G4_PLOTLY,
        )
        fig_agents.update_layout(margin=G4_MARGIN)
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

        # Scatter: effective_value vs score
        st.markdown("### Distribuição de Score × Valor do Deal")
        color_map = {"A": "#4ade80", "B": "#C89B5A", "C": "#f87171"}

        fig_scatter = px.scatter(
            view,
            x="effective_value",
            y="score",
            color="tier",
            color_discrete_map=color_map,
            hover_data={"account": True, "sales_agent": True, "deal_stage": True},
            labels={
                "effective_value": "Valor Esperado (R$)",
                "score": "Score",
                "tier": "Tier",
            },
            title="Score × Valor do Deal",
            height=420,
        )
        fig_scatter.update_layout(**G4_PLOTLY)
        fig_scatter.update_layout(margin=G4_MARGIN)
        st.plotly_chart(fig_scatter, use_container_width=True)

        # Win rate histórico por mês de entrada no pipeline
        st.markdown("### Win rate histórico por mês de entrada no pipeline")

        @st.cache_data(ttl=3600)
        def _get_month_counts():
            df = load_and_merge()
            closed = df[df["deal_stage"].isin(["Won", "Lost"])].copy()
            closed["engage_month"] = closed["engage_date"].dt.month
            return closed.groupby("engage_month").size().to_dict()
        _month_counts = _get_month_counts()

        months_sorted = sorted(month_wr.keys())
        month_labels  = [MONTH_NAMES_PT[m] for m in months_sorted]
        month_values  = [round(month_wr[m] * 100, 1) for m in months_sorted]
        bar_colors    = ["#4ade80" if v >= 65 else ("#C89B5A" if v >= 55 else "#f87171") for v in month_values]
        bar_texts     = [f"{v}% ({_month_counts.get(m, 0)} deals)" for m, v in zip(months_sorted, month_values)]

        fig_month = go.Figure(go.Bar(
            x=month_labels,
            y=month_values,
            marker_color=bar_colors,
            text=bar_texts,
            textposition="outside",
        ))
        fig_month.update_layout(
            title="Win rate por mês de entrada no pipeline",
            yaxis_title="Win Rate (%)",
            yaxis_range=[0, max(month_values) * 1.25],
            height=400,
            showlegend=False,
            **G4_PLOTLY,
        )
        fig_month.update_layout(margin=G4_MARGIN)
        st.plotly_chart(fig_month, use_container_width=True)
        st.caption(
            "Meses com win rate alto geram mais pontos de sazonalidade no score. "
            "Base: todos os deals Won e Lost históricos."
        )

# ── Footer ───────────────────────────────────────────────────────────────────

st.markdown("---")
st.caption(
    f"Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')} · "
    + FEATURE_CAPTION
)
