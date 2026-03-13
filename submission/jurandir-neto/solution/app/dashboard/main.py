from dotenv import load_dotenv

load_dotenv()

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from app.agent.agent import create_agent
from app.dashboard.queries import (
    get_filter_options,
    query_dashboard_fact,
    query_churn_drivers,
    query_churn_drivers_ts,
    query_account_risk,
    query_feature_retention,
    query_support_health,
)

st.set_page_config(page_title="RavenStack Churn Intelligence", layout="wide")

# ── Session state init ──────────────────────────────────────────────────────
if "last_exchange" not in st.session_state:
    st.session_state["last_exchange"] = None  # {"question": str, "answer": str} | None
if "agent" not in st.session_state:
    st.session_state["agent"] = create_agent()
if "prev_period" not in st.session_state:
    st.session_state["prev_period"] = None
if "pending_agent_call" not in st.session_state:
    st.session_state["pending_agent_call"] = False


# ── Sidebar ─────────────────────────────────────────────────────────────────
opts = get_filter_options()
all_ym = opts["year_months"]

st.sidebar.header("Filtros")

ym_start, ym_end = st.sidebar.select_slider(
    "Período",
    options=all_ym,
    value=(all_ym[0], all_ym[-1]),
)

industries = tuple(sorted(
    st.sidebar.multiselect("Indústria", opts["industries"])
))
countries = tuple(sorted(
    st.sidebar.multiselect("País", opts["countries"])
))
channels = tuple(sorted(
    st.sidebar.multiselect("Canal de aquisição", opts["channels"])
))
plans = tuple(sorted(
    st.sidebar.multiselect("Plano", opts["plans"])
))
billing_freqs = tuple(sorted(
    st.sidebar.multiselect("Frequência de cobrança", opts["billing_frequencies"])
))
trial_option = st.sidebar.radio("Tipo de conta", ["Todas", "Apenas trial", "Apenas pagas"])
is_trial = None if trial_option == "Todas" else (trial_option == "Apenas trial")

st.sidebar.caption(f"Dados até: {all_ym[-1]}")

period_changed = st.session_state["prev_period"] != (ym_start, ym_end)
st.session_state["prev_period"] = (ym_start, ym_end)


# ── Helper: mini agent expander ─────────────────────────────────────────────
def _render_mini_agent(label: str, ym_start: str, ym_end: str):
    with st.expander("Perguntar ao agente"):
        question = st.text_input(
            "Sua pergunta", key=f"mini_agent_input_{label}"
        )
        if st.button("Enviar", key=f"mini_agent_btn_{label}"):
            if question.strip():
                context_msg = f"[Contexto: {label}, período {ym_start}–{ym_end}]\n{question}"
                with st.spinner("Analisando..."):
                    response = st.session_state["agent"].run(context_msg)
                    answer = response.content
                st.markdown(answer)


# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Visão Geral", "Drivers de Churn", "Contas em Risco",
    "Engajamento de Features", "Saúde do Suporte", "Diagnóstico com IA"
])


# ════════════════════════════════════════════════════════════════════════════
# Tab 1 — Visão Geral
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Visão Geral")

    df = query_dashboard_fact(
        ym_start, ym_end, industries, countries, channels, plans, billing_freqs, is_trial
    )

    if df.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
    else:
        # KPIs
        total_accounts = df["account_id"].nunique()
        mrr_lost_total = df["mrr_lost"].sum()
        churned = df[df["churned_in_period"] == True]
        churn_rate_pct = (len(churned) / len(df) * 100) if len(df) > 0 else 0
        high_risk_count = df[df["risk_tier"].isin(["high"])]["account_id"].nunique()

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Contas no período", f"{total_accounts:,}")
        k2.metric("MRR Perdido", f"${mrr_lost_total:,.0f}")
        k3.metric("Churn Rate", f"{churn_rate_pct:.1f}%")
        k4.metric("Contas em alto risco", f"{high_risk_count:,}")

        st.divider()

        # Chart 1 — Churn trend (line + bar dual-axis)
        trend = df.groupby("year_month").agg(
            churn_rate_pct=("churned_in_period", lambda x: x.sum() / len(x) * 100),
            mrr_lost=("mrr_lost", "sum"),
        ).reset_index()

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=trend["year_month"], y=trend["mrr_lost"],
            name="MRR Perdido ($)", marker_color="#ff7f0e", yaxis="y2"
        ))
        fig_trend.add_trace(go.Scatter(
            x=trend["year_month"], y=trend["churn_rate_pct"],
            name="Churn Rate (%)", mode="lines+markers",
            line=dict(color="#1f77b4", width=2)
        ))
        fig_trend.update_layout(
            title="Tendência de Churn",
            yaxis=dict(title="Churn Rate (%)"),
            yaxis2=dict(title="MRR Perdido ($)", overlaying="y", side="right"),
            legend=dict(orientation="h", y=1.1),
            height=350,
        )
        st.plotly_chart(fig_trend, width="stretch")

        col_a, col_b = st.columns(2)

        with col_a:
            # Chart 2 — Reason code bar
            reason = (
                churned.groupby("churn_reason_code")["mrr_lost"]
                .sum()
                .reset_index()
                .sort_values("mrr_lost")
            )
            fig_reason = px.bar(
                reason, x="mrr_lost", y="churn_reason_code", orientation="h",
                title="MRR Perdido por Reason Code",
                color="mrr_lost", color_continuous_scale="Reds",
                labels={"mrr_lost": "MRR Perdido ($)", "churn_reason_code": "Reason Code"},
            )
            fig_reason.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig_reason, width="stretch")

        with col_b:
            # Chart 3 — Risk distribution donut
            risk_dist = df.groupby("risk_tier")["account_id"].nunique().reset_index()
            risk_dist.columns = ["risk_tier", "count"]
            color_map = {"high": "#ff7f0e", "medium": "#ffbb78", "low": "#2ca02c"}
            fig_donut = px.pie(
                risk_dist, names="risk_tier", values="count",
                title="Distribuição por Risk Tier",
                hole=0.45,
                color="risk_tier",
                color_discrete_map=color_map,
            )
            fig_donut.update_layout(height=300)
            st.plotly_chart(fig_donut, width="stretch")

    _render_mini_agent("Visão Geral", ym_start, ym_end)


# ════════════════════════════════════════════════════════════════════════════
# Tab 2 — Drivers de Churn
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Drivers de Churn por Segmento")

    segment_labels = {
        "industry": "Indústria", "country": "País",
        "channel": "Canal", "plan": "Plano"
    }
    segment_type = st.radio(
        "Segmentar por",
        ["industry", "country", "channel", "plan"],
        format_func=lambda x: segment_labels[x],
        horizontal=True,
    )

    df_drivers = query_churn_drivers(ym_start, ym_end, segment_type)

    if df_drivers.empty:
        st.warning("Nenhum dado disponível para este segmento e período.")
    else:
        col_a, col_b = st.columns(2)

        with col_a:
            df_sorted = df_drivers.sort_values("churn_rate")
            fig_seg_churn = px.bar(
                df_sorted, x="churn_rate", y="segment_value", orientation="h",
                title=f"Churn Rate por {segment_labels[segment_type]}",
                color="churn_rate", color_continuous_scale="RdYlGn_r",
                labels={"churn_rate": "Churn Rate", "segment_value": segment_labels[segment_type]},
            )
            fig_seg_churn.update_layout(height=320, showlegend=False)
            st.plotly_chart(fig_seg_churn, width="stretch")

        with col_b:
            df_sorted2 = df_drivers.sort_values("mrr_lost")
            fig_seg_mrr = px.bar(
                df_sorted2, x="mrr_lost", y="segment_value", orientation="h",
                title=f"MRR Perdido por {segment_labels[segment_type]}",
                color="mrr_lost", color_continuous_scale="Reds",
                labels={"mrr_lost": "MRR Perdido ($)", "segment_value": segment_labels[segment_type]},
            )
            fig_seg_mrr.update_layout(height=320, showlegend=False)
            st.plotly_chart(fig_seg_mrr, width="stretch")

        # Chart 3 — Stacked bar by reason code
        fig_reason_seg = px.bar(
            df_drivers, x="segment_value", y="churned_accounts",
            color="top_reason_code",
            title=f"Contas Churned por {segment_labels[segment_type]} e Reason Code",
            labels={"churned_accounts": "Contas Churned", "segment_value": segment_labels[segment_type]},
        )
        fig_reason_seg.update_layout(height=320)
        st.plotly_chart(fig_reason_seg, width="stretch")

        # Chart 4 — Time series for selected segment value
        segment_values = df_drivers["segment_value"].tolist()
        if segment_values:
            selected_val = st.selectbox(
                f"Série temporal por {segment_labels[segment_type]}",
                segment_values,
                key="ts_segment_select",
            )
            df_ts = query_churn_drivers_ts(ym_start, ym_end, segment_type, selected_val)
            if not df_ts.empty:
                fig_ts = px.line(
                    df_ts, x="year_month", y="churn_rate",
                    title=f"Churn Rate — {selected_val}",
                    markers=True,
                    labels={"year_month": "Mês", "churn_rate": "Churn Rate"},
                )
                fig_ts.update_layout(height=300)
                st.plotly_chart(fig_ts, width="stretch")

    _render_mini_agent("Drivers de Churn", ym_start, ym_end)


# ════════════════════════════════════════════════════════════════════════════
# Tab 3 — Contas em Risco
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Contas em Risco")
    st.info("Snapshot atual — filtro de período não se aplica.")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        selected_tiers = tuple(sorted(st.multiselect(
            "Risk tier", ["low", "medium", "high"],
            default=["high"],
        )))
    with col_f2:
        mrr_range = st.slider("MRR ($)", 0, 35000, (0, 35000))

    df_risk = query_account_risk(
        selected_tiers, industries, countries, float(mrr_range[0]), float(mrr_range[1])
    )

    if df_risk.empty:
        st.warning("Nenhuma conta encontrada com os filtros selecionados.")
    else:
        # KPIs
        high_count = len(df_risk[df_risk["risk_tier"] == "high"])
        mrr_at_risk = df_risk[df_risk["risk_tier"].isin(["high", "medium"])]["mrr"].sum()
        high_df = df_risk[df_risk["risk_tier"] == "high"]
        avg_days_no_use = high_df["days_since_last_usage"].mean() if len(high_df) > 0 else 0

        k1, k2, k3 = st.columns(3)
        k1.metric("Contas alto risco", f"{high_count:,}")
        k2.metric("MRR em risco (high+medium)", f"${mrr_at_risk:,.0f}")
        k3.metric("Dias médios sem uso (high)", f"{avg_days_no_use:.0f}")

        st.divider()

        col_a, col_b = st.columns(2)

        with col_a:
            # Scatter: risk_score × mrr
            tier_colors = {"high": "#ff7f0e", "medium": "#ffbb78", "low": "#2ca02c"}
            fig_scatter = px.scatter(
                df_risk,
                x="risk_score", y="mrr",
                color="risk_tier",
                color_discrete_map=tier_colors,
                size="mrr",
                size_max=30,
                hover_data=["account_name", "recommended_action"],
                title="Risk Score × MRR por Conta",
                labels={"risk_score": "Risk Score", "mrr": "MRR ($)", "risk_tier": "Tier"},
            )
            fig_scatter.update_layout(height=380)
            st.plotly_chart(fig_scatter, width="stretch")

        with col_b:
            # Stacked bar: signals by tier
            signal_cols = ["signal_low_usage", "signal_high_errors", "signal_bad_support", "signal_downgrade"]
            signal_labels = {
                "signal_low_usage": "Baixo uso",
                "signal_high_errors": "Erros altos",
                "signal_bad_support": "Suporte ruim",
                "signal_downgrade": "Downgrade",
            }
            sig_data = []
            for tier in df_risk["risk_tier"].unique():
                tier_df = df_risk[df_risk["risk_tier"] == tier]
                for sc in signal_cols:
                    if sc in tier_df.columns:
                        count = tier_df[sc].sum()
                        sig_data.append({"risk_tier": tier, "signal": signal_labels[sc], "count": int(count)})
            if sig_data:
                df_sig = pd.DataFrame(sig_data)
                fig_signals = px.bar(
                    df_sig, x="risk_tier", y="count", color="signal",
                    title="Sinais por Risk Tier",
                    labels={"count": "Contas", "risk_tier": "Tier", "signal": "Sinal"},
                    barmode="stack",
                )
                fig_signals.update_layout(height=380)
                st.plotly_chart(fig_signals, width="stretch")

        # Table — top 50
        display_cols = [
            c for c in [
                "account_name", "industry", "country", "mrr", "risk_score",
                "risk_tier", "days_since_last_usage", "last_satisfaction_score",
                "recommended_action"
            ] if c in df_risk.columns
        ]
        st.dataframe(
            df_risk[display_cols].head(50),
            width="stretch",
        )

    _render_mini_agent("Contas em Risco", ym_start, ym_end)


# ════════════════════════════════════════════════════════════════════════════
# Tab 4 — Engajamento de Features
# ════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Engajamento de Features")

    df_feat = query_feature_retention(ym_start, ym_end)

    if df_feat.empty:
        st.warning("Nenhum dado disponível para o período selecionado.")
    else:
        # Aggregate by feature for cross-period views
        feat_agg = df_feat.groupby("feature_name").agg(
            retention_lift=("retention_lift", "mean"),
            retained_avg_usage=("retained_avg_usage", "mean"),
            churned_avg_usage=("churned_avg_usage", "mean"),
            retained_avg_errors=("retained_avg_errors", "mean"),
            churned_avg_errors=("churned_avg_errors", "mean"),
        ).reset_index().sort_values("retention_lift", ascending=False)

        # Chart 1 — Retention lift by feature
        fig_lift = px.bar(
            feat_agg.sort_values("retention_lift"),
            x="retention_lift", y="feature_name", orientation="h",
            title="Retention Lift por Feature (médio no período)",
            color="retention_lift", color_continuous_scale="RdYlGn",
            labels={"retention_lift": "Retention Lift", "feature_name": "Feature"},
        )
        fig_lift.update_layout(height=500, showlegend=False)
        st.plotly_chart(fig_lift, width="stretch")

        col_a, col_b = st.columns(2)

        with col_a:
            # Chart 2 — Usage compare retained vs churned
            feat_top = feat_agg.head(15)
            fig_usage = go.Figure()
            fig_usage.add_trace(go.Bar(
                name="Retained (uso médio)", x=feat_top["feature_name"],
                y=feat_top["retained_avg_usage"], marker_color="#2ca02c"
            ))
            fig_usage.add_trace(go.Bar(
                name="Churned (uso médio)", x=feat_top["feature_name"],
                y=feat_top["churned_avg_usage"], marker_color="#d62728"
            ))
            fig_usage.update_layout(
                title="Uso: Retained vs Churned (top 15 features)",
                barmode="group", height=350,
                xaxis_tickangle=-45,
            )
            st.plotly_chart(fig_usage, width="stretch")

        with col_b:
            # Chart 3 — Errors compare
            fig_errors = go.Figure()
            fig_errors.add_trace(go.Bar(
                name="Retained (erros médios)", x=feat_top["feature_name"],
                y=feat_top["retained_avg_errors"], marker_color="#2ca02c"
            ))
            fig_errors.add_trace(go.Bar(
                name="Churned (erros médios)", x=feat_top["feature_name"],
                y=feat_top["churned_avg_errors"], marker_color="#d62728"
            ))
            fig_errors.update_layout(
                title="Erros: Retained vs Churned (top 15 features)",
                barmode="group", height=350,
                xaxis_tickangle=-45,
            )
            st.plotly_chart(fig_errors, width="stretch")

        # Chart 4 — Time series for selected feature
        features_list = sorted(df_feat["feature_name"].unique().tolist())
        selected_feat = st.selectbox("Série temporal por feature", features_list, key="feat_ts_select")
        df_feat_ts = df_feat[df_feat["feature_name"] == selected_feat].sort_values("year_month")
        if not df_feat_ts.empty:
            fig_feat_ts = px.line(
                df_feat_ts, x="year_month", y="retention_lift",
                title=f"Retention Lift — {selected_feat}",
                markers=True,
                labels={"year_month": "Mês", "retention_lift": "Retention Lift"},
            )
            fig_feat_ts.update_layout(height=300)
            st.plotly_chart(fig_feat_ts, width="stretch")

    _render_mini_agent("Engajamento de Features", ym_start, ym_end)


# ════════════════════════════════════════════════════════════════════════════
# Tab 5 — Saúde do Suporte
# ════════════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("Saúde do Suporte")

    df_sup = query_support_health(ym_start, ym_end, industries)

    if df_sup.empty:
        st.warning("Nenhum dado disponível para o período e filtros selecionados.")
    else:
        # KPIs
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("CSAT médio", f"{df_sup['avg_satisfaction_score'].mean():.2f}")
        k2.metric("Tempo médio resolução (h)", f"{df_sup['avg_resolution_time'].mean():.1f}")
        k3.metric("Taxa de escalação", f"{df_sup['escalation_rate'].mean():.1%}")
        k4.metric("Churn (contas c/ 3+ tickets)", f"{df_sup['churn_rate_high_tickets'].mean():.1%}")

        st.divider()

        # Chart 1 — CSAT trend by industry
        fig_csat = px.line(
            df_sup, x="year_month", y="avg_satisfaction_score", color="industry",
            title="CSAT por Indústria ao longo do tempo",
            markers=True,
            labels={"year_month": "Mês", "avg_satisfaction_score": "CSAT médio", "industry": "Indústria"},
        )
        fig_csat.add_hline(y=3.0, line_dash="dash", line_color="red", annotation_text="Limite de alerta (3.0)")
        fig_csat.update_layout(height=350)
        st.plotly_chart(fig_csat, width="stretch")

        # Chart 2 — Heatmap: industry × year_month (resolution time)
        heatmap_data = df_sup.pivot_table(
            index="industry", columns="year_month", values="avg_resolution_time"
        )
        if not heatmap_data.empty:
            fig_heatmap = px.imshow(
                heatmap_data,
                title="Tempo Médio de Resolução (h) — Indústria × Mês",
                color_continuous_scale="RdYlGn_r",
                aspect="auto",
                labels={"x": "Mês", "y": "Indústria", "color": "Resolução (h)"},
            )
            fig_heatmap.update_layout(height=300)
            st.plotly_chart(fig_heatmap, width="stretch")

        col_a, col_b = st.columns(2)

        with col_a:
            # Chart 3 — Scatter: escalation_rate × churn_rate_high_tickets
            sup_agg = df_sup.groupby("industry").agg(
                escalation_rate=("escalation_rate", "mean"),
                churn_rate_high_tickets=("churn_rate_high_tickets", "mean"),
                avg_satisfaction_score=("avg_satisfaction_score", "mean"),
            ).reset_index()
            fig_sup_scatter = px.scatter(
                sup_agg,
                x="escalation_rate", y="churn_rate_high_tickets",
                color="industry", size="avg_satisfaction_score",
                title="Escalação × Churn (contas c/ muitos tickets)",
                labels={
                    "escalation_rate": "Taxa de Escalação",
                    "churn_rate_high_tickets": "Churn Rate (alto ticket)",
                    "industry": "Indústria",
                },
            )
            fig_sup_scatter.update_layout(height=350)
            st.plotly_chart(fig_sup_scatter, width="stretch")

        with col_b:
            # Chart 4 — FRT vs CSAT scatter with trendline
            fig_frt_csat = px.scatter(
                df_sup,
                x="avg_first_response_time", y="avg_satisfaction_score",
                color="industry",
                trendline="ols",
                title="Tempo 1ª Resposta × CSAT",
                labels={
                    "avg_first_response_time": "Tempo 1ª Resposta (min)",
                    "avg_satisfaction_score": "CSAT médio",
                    "industry": "Indústria",
                },
            )
            fig_frt_csat.update_layout(height=350)
            st.plotly_chart(fig_frt_csat, width="stretch")

    _render_mini_agent("Saúde do Suporte", ym_start, ym_end)


# ════════════════════════════════════════════════════════════════════════════
# Tab 6 — Diagnóstico com IA
# ════════════════════════════════════════════════════════════════════════════
with tab6:
    st.subheader("Diagnóstico com IA")

    if period_changed:
        st.warning(f"Período alterado para {ym_start}–{ym_end}.")
        if st.button("Diagnosticar período selecionado"):
            question = (
                f"Faça um diagnóstico completo do churn para o período de {ym_start} a {ym_end}.\n"
                f"P1 — O que está causando o churn? Reason codes dominantes + correlações com uso e suporte.\n"
                f"P2 — Quais segmentos estão mais em risco? Indústrias/países/planos acima da média + contas com maior MRR em risco.\n"
                f"P3 — Quais ações concretas a empresa deve tomar? 2-3 ações com público-alvo e impacto estimado."
            )
            st.session_state["last_exchange"] = {"question": question, "answer": None}
            st.session_state["pending_agent_call"] = True
            st.rerun()

    # Process pending agent call
    if st.session_state["pending_agent_call"]:
        st.session_state["pending_agent_call"] = False
        exchange = st.session_state["last_exchange"]
        if exchange and exchange["answer"] is None:
            with st.spinner("Analisando dados..."):
                response = st.session_state["agent"].run(exchange["question"])
                st.session_state["last_exchange"]["answer"] = response.content

    # Display only the last question/answer pair
    if st.session_state["last_exchange"]:
        exchange = st.session_state["last_exchange"]
        with st.chat_message("user"):
            st.markdown(exchange["question"])
        if exchange["answer"]:
            with st.chat_message("assistant"):
                st.markdown(exchange["answer"])

    # Chat input
    user_input = st.chat_input("Faça uma pergunta ao agente de churn...")
    if user_input:
        st.session_state["last_exchange"] = {"question": user_input, "answer": None}
        st.session_state["pending_agent_call"] = True
        st.rerun()

    if st.button("Limpar"):
        st.session_state["last_exchange"] = None
        st.rerun()
