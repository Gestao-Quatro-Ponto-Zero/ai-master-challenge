"""
RevOps Copilot — Painel Executivo de Priorização Comercial (Segunda-feira 8h00)
G4 Educação — AI Master Challenge 003: Lead Scorer

Desenvolvido por Arthur Lima (AI Master & Tech Lead)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.data_loader import build_enriched_pipeline, SNAPSHOT_DATE
from src.survival_and_scoring import SurvivalLeadScorer, compute_empirical_survival_curve
from src.explainability import enrich_with_explainability
from src.backtest import run_temporal_backtest

# --- Page Configuration ---
st.set_page_config(
    page_title="RevOps Copilot — G4 Lead Scorer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
FEEDBACK_FILE = ARTIFACTS_DIR / "feedback_overrides.json"


# --- Data Caching & Model Fitting ---
@st.cache_data(show_spinner=False)
def load_and_score_all_data():
    df, audit = build_enriched_pipeline()
    scorer = SurvivalLeadScorer()
    scorer.fit(df)

    engaging_raw = df[df["deal_stage"] == "Engaging"].copy()
    prospecting_raw = df[df["deal_stage"] == "Prospecting"].copy()

    scored_engaging = scorer.score_engaging_deals(engaging_raw)
    enriched_engaging = enrich_with_explainability(scored_engaging)

    scored_prospecting = scorer.score_prospecting_deals(prospecting_raw)
    survival_curve = compute_empirical_survival_curve(df, SNAPSHOT_DATE)

    return df, audit, scorer, enriched_engaging, scored_prospecting, survival_curve


def save_sales_rep_override(opportunity_id: str, agent: str, reason: str, proposed_action: str):
    record = {
        "timestamp": str(pd.Timestamp.now()),
        "opportunity_id": opportunity_id,
        "sales_agent": agent,
        "feedback_reason": reason,
        "proposed_action": proposed_action,
    }
    existing = []
    if FEEDBACK_FILE.exists():
        try:
            with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []
    existing.append(record)
    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)


# --- Load Data ---
df_all, audit_summary, scorer, df_engaging, df_prospecting, df_survival = load_and_score_all_data()

# --- Sidebar: Navigation & Filters ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=60)
    st.title("🎯 RevOps Copilot")
    st.caption("Painel da Segunda-feira 8h00 | G4 AI Master")

    st.markdown("---")
    st.subheader("🏢 Filtros Operacionais")

    # Cascading selectors
    offices = ["Todos"] + sorted(df_all["regional_office"].dropna().unique().tolist())
    selected_office = st.selectbox("Escritório Regional:", offices, index=0)

    filtered_teams = df_all.copy()
    if selected_office != "Todos":
        filtered_teams = filtered_teams[filtered_teams["regional_office"] == selected_office]

    managers = ["Todos"] + sorted(filtered_teams["manager"].dropna().unique().tolist())
    selected_manager = st.selectbox("Gerente Comercial (Manager):", managers, index=0)

    if selected_manager != "Todos":
        filtered_teams = filtered_teams[filtered_teams["manager"] == selected_manager]

    agents = ["Todos"] + sorted(filtered_teams["sales_agent"].dropna().unique().tolist())
    # Pre-select a representative top closer by default to prevent blank state
    default_agent_idx = 0
    if "Moses Frase" in agents:
        default_agent_idx = agents.index("Moses Frase")
    selected_agent = st.selectbox("Vendedor (Sales Agent):", agents, index=default_agent_idx)

    st.markdown("---")
    st.subheader("🛡️ Auditoria de Dados")
    st.caption(f"Deals Analisados: **{audit_summary['total_rows']:,}**")
    st.caption(f"Pipeline Ativo: **{audit_summary['engaging_count'] + audit_summary['prospecting_count']:,}**")
    st.caption(f"FK Bug 'GTXPro' Corrigido: **{audit_summary['gtxpro_foreign_key_fixed']} rows**")
    st.caption(f"MAE Estimador Mediana: **${audit_summary['mae_median_estimator']}**")


# --- Filter Active Subsets ---
view_engaging = df_engaging.copy()
view_prospecting = df_prospecting.copy()

if selected_office != "Todos":
    view_engaging = view_engaging[view_engaging["regional_office"] == selected_office]
    view_prospecting = view_prospecting[view_prospecting["regional_office"] == selected_office]

if selected_manager != "Todos":
    view_engaging = view_engaging[view_engaging["manager"] == selected_manager]
    view_prospecting = view_prospecting[view_prospecting["manager"] == selected_manager]

if selected_agent != "Todos":
    view_engaging = view_engaging[view_engaging["sales_agent"] == selected_agent]
    view_prospecting = view_prospecting[view_prospecting["sales_agent"] == selected_agent]


# --- Header ---
st.title("🚀 RevOps Lead Scorer & Pipeline Velocity Engine")
st.markdown(
    "Motor de inteligência preditiva baseado em **Sobrevivência Empírica**, "
    "**Velocidade de Receita ($EV/Dia$)** e **Explicabilidade Comercial Acionável**."
)

tab_closers, tab_sdrs, tab_simulator, tab_governance = st.tabs(
    [
        "🎯 Carteira Quente (Closers)",
        "⚡ Fila de Prospecção (SDRs)",
        "🧪 Simulador de Deal (Sandbox)",
        "📊 Governança & Backtest Out-of-Time",
    ]
)


# ==============================================================================
# TAB 1: CARTEIRA QUENTE DE CLOSERS (ENGAGING)
# ==============================================================================
with tab_closers:
    st.subheader("🎯 Carteira Ativa de Fechamento (`Engaging`)")

    # Metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    total_ev = view_engaging["expected_value"].sum()
    avg_ev_day = view_engaging["ev_per_day"].mean() if len(view_engaging) > 0 else 0.0
    zombies_count = view_engaging["is_zombie_suspect"].sum()
    accelerate_count = (view_engaging["action_tier"] == "🚀 Acelerar Fechamento").sum()
    rescue_count = (view_engaging["action_tier"] == "🛠️ Intervenção de Resgate").sum()

    col1.metric("Oportunidades em Aberto", f"{len(view_engaging):,}")
    col2.metric("Receita Esperada Ponderada ($EV)", f"${total_ev:,.0f}")
    col3.metric("Velocidade Média de Pipeline", f"${avg_ev_day:,.0f}/dia")
    col4.metric("Acelerar Fechamento 🚀", f"{accelerate_count}")
    col5.metric("Alerta Zombie Suspects 🧹", f"{zombies_count}", delta=f"-{zombies_count}", delta_color="inverse")

    st.markdown("---")

    # Interactive Bubble Plot
    if len(view_engaging) > 0:
        c_left, c_right = st.columns([3, 2])
        with c_left:
            st.markdown("##### 📍 Matriz de Decisão: Valor Esperado ($EV$) vs. Tempo de Ciclo (Aging)")
            fig = px.scatter(
                view_engaging.reset_index(),
                x="cycle_days",
                y="expected_value",
                size="expected_won_value",
                color="action_tier",
                hover_name="account_display",
                hover_data=["opportunity_id", "product", "sales_agent", "p_win", "ev_per_day"],
                color_discrete_map={
                    "🚀 Acelerar Fechamento": "#10B981",
                    "🛠️ Intervenção de Resgate": "#F59E0B",
                    "🧹 Higienizar / Auditar Zombie": "#EF4444",
                },
                labels={
                    "cycle_days": "Idade da Oportunidade (Dias no Funil)",
                    "expected_value": "Valor Esperado Monetário ($EV = P × Valor)",
                    "action_tier": "Faixa de Ação",
                },
                height=380,
            )
            fig.add_vline(x=57, line_dash="dash", line_color="#64748B", annotation_text="Mediana Histórica (57d)")
            fig.add_vline(x=118, line_dash="dot", line_color="#DC2626", annotation_text="Limiar P95 Zombie (118d)")
            fig.update_layout(margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig, use_container_width=True)

        with c_right:
            st.markdown("##### 📊 Distribuição por Faixa de Ação Tática")
            tier_dist = view_engaging["action_tier"].value_counts().reset_index()
            tier_dist.columns = ["Faixa de Ação", "Total"]
            fig_pie = px.pie(
                tier_dist,
                names="Faixa de Ação",
                values="Total",
                color="Faixa de Ação",
                color_discrete_map={
                    "🚀 Acelerar Fechamento": "#10B981",
                    "🛠️ Intervenção de Resgate": "#F59E0B",
                    "🧹 Higienizar / Auditar Zombie": "#EF4444",
                },
                hole=0.45,
                height=380,
            )
            fig_pie.update_layout(margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_pie, use_container_width=True)

        # Ranked Table
        st.markdown("##### 📋 Tabela de Prioridade da Semana (Top Deals)")
        display_cols = [
            "opportunity_id",
            "priority_score",
            "action_tier",
            "account_display",
            "product",
            "sales_agent",
            "expected_won_value",
            "p_win",
            "ev_per_day",
            "cycle_days",
            "sla_recommendation",
        ]
        st.dataframe(
            view_engaging[display_cols].rename(
                columns={
                    "opportunity_id": "ID",
                    "priority_score": "Score (0-100)",
                    "action_tier": "Ação Recomendada",
                    "account_display": "Conta",
                    "product": "Produto",
                    "sales_agent": "Vendedor",
                    "expected_won_value": "Ticket Est. ($)",
                    "p_win": "P(Win)",
                    "ev_per_day": "Yield ($/Dia)",
                    "cycle_days": "Idade (d)",
                    "sla_recommendation": "SLA Tático",
                }
            ),
            use_container_width=True,
            height=280,
        )

        st.markdown("---")

        # Opportunity Inspector & Rep Override
        st.subheader("🔍 Ficha de Detalhe do Deal & Loop de Feedback do Vendedor")
        deal_options = view_engaging["opportunity_id"].tolist()
        selected_opp = st.selectbox(
            "Selecione uma Oportunidade para Inspecionar:",
            deal_options,
            index=0 if len(deal_options) > 0 else None,
        )

        if selected_opp:
            deal_row = view_engaging[view_engaging["opportunity_id"] == selected_opp].iloc[0]

            col_detail_left, col_detail_right = st.columns([3, 2])

            with col_detail_left:
                st.markdown(f"#### 🏷️ Deal `{deal_row['opportunity_id']}` — {deal_row['account_display']}")
                st.markdown(f"**Vendedor:** {deal_row['sales_agent']} | **Produto:** {deal_row['product']} | **Ticket Estimado:** ${deal_row['expected_won_value']:,.0f}")
                st.markdown(f"**Score de Prioridade:** `{deal_row['priority_score']}/100` | **Probabilidade Calibrada:** `{deal_row['p_win']*100:.1f}%` | **Velocidade:** `${deal_row['ev_per_day']:,.0f}/dia`")

                st.markdown("##### 💡 Os 3 Fatores Decisivos da Nota (Explainability):")
                st.info(f"1. {deal_row['driver_1']}")
                st.info(f"2. {deal_row['driver_2']}")
                st.info(f"3. {deal_row['driver_3']}")

                st.markdown("##### 📌 Próximo Passo Prescritivo:")
                st.success(f"**{deal_row['recommended_next_step']}** (SLA: *{deal_row['sla_recommendation']}*)")

                with st.expander("📝 Ver Script de Abordagem Sugerido (Talk Track)"):
                    st.code(deal_row["suggested_script"], language="text")

            with col_detail_right:
                st.markdown("#### 💬 Loop de Override do Vendedor")
                st.caption(
                    "O vendedor possui contexto de campo que o CRM não vê. "
                    "Registre discordâncias para alimentar a calibração contínua do modelo."
                )

                feedback_reason = st.selectbox(
                    "Motivo da Discordância:",
                    [
                        "Troca de Decisor / Sponsor no Cliente",
                        "Budget Congelado Temporariamente (Retomada Agendada)",
                        "Negociação Concluída Verbalmente (Aguardando Minuta)",
                        "Concorrente Fechou com Preço Predatório",
                        "Lead Sem Perfil / Desqualificado Definitivamente",
                        "Outro Contexto de Campo",
                    ],
                )
                feedback_notes = st.text_area(
                    "Observações Adicionais do Vendedor:",
                    placeholder="Ex: Falei com o CFO hoje às 9h, a verba foi aprovada para o próximo dia 10.",
                    height=100,
                )

                if st.button("💾 Enviar Feedback / Marcar Override"):
                    save_sales_rep_override(
                        deal_row["opportunity_id"],
                        deal_row["sales_agent"],
                        feedback_reason,
                        feedback_notes,
                    )
                    st.success("✅ Feedback registrado com sucesso! O histórico foi salvo para auditoria de RevOps.")
    else:
        st.warning("Nenhuma oportunidade encontrada para os filtros selecionados.")


# ==============================================================================
# TAB 2: FILA DE PROSPECÇÃO DE SDRS (PROSPECTING)
# ==============================================================================
with tab_sdrs:
    st.subheader("⚡ Fila de Qualificação de SDRs (`Prospecting` — 500 Leads)")
    st.markdown(
        "Oportunidades em estágio de pré-contato sem `engage_date`. "
        "Ranqueadas por **Score de Fit ICP** e **Ticket Inicial Esperado**, evitando misturar com a carteira de Closers."
    )

    col_sdr1, col_sdr2, col_sdr3, col_sdr4 = st.columns(4)
    total_prosp_ev = view_prospecting["expected_value_icp"].sum()
    unlinked_count = (~view_prospecting["has_account"]).sum()
    avg_sdr_fit = view_prospecting["sdr_fit_score"].mean() if len(view_prospecting) > 0 else 0.0

    col_sdr1.metric("Leads na Fila de SDR", f"{len(view_prospecting):,}")
    col_sdr2.metric("Pipeline Potencial Ponderado", f"${total_prosp_ev:,.0f}")
    col_sdr3.metric("Média Score Fit ICP", f"{avg_sdr_fit:.1f}/100")
    col_sdr4.metric("Contas Não Vinculadas (CRM Gap)", f"{unlinked_count}", delta=f"{unlinked_count} órfãs", delta_color="inverse")

    st.markdown("---")

    st.markdown("##### 📋 Fila Prioritária para 1º Toque Comercial")
    sdr_cols = [
        "opportunity_id",
        "sdr_fit_score",
        "sdr_playbook",
        "account_display",
        "product",
        "sales_agent",
        "expected_won_value",
        "p_win_icp",
    ]
    st.dataframe(
        view_prospecting[sdr_cols].rename(
            columns={
                "opportunity_id": "ID",
                "sdr_fit_score": "Fit Score (0-100)",
                "sdr_playbook": "Playbook Recomendado",
                "account_display": "Conta Alvo",
                "product": "Produto",
                "sales_agent": "SDR Designado",
                "expected_won_value": "Ticket Potencial ($)",
                "p_win_icp": "P(Win ICP)",
            }
        ),
        use_container_width=True,
        height=380,
    )


# ==============================================================================
# TAB 3: SIMULADOR DE NOVO DEAL (SANDBOX)
# ==============================================================================
with tab_simulator:
    st.subheader("🧪 Simulador & Qualificador de Oportunidades (Sandbox)")
    st.markdown(
        "Permite ao vendedor ou gestor simular um lead novo antes de formalizar no CRM, "
        "projetando a probabilidade de fechamento e a curva de envelhecimento."
    )

    col_sim_in, col_sim_out = st.columns([2, 3])

    with col_sim_in:
        sim_agent = st.selectbox("Vendedor Responsável:", sorted(df_all["sales_agent"].unique().tolist()), index=0)
        sim_product = st.selectbox("Produto Cotado:", sorted(df_all["product"].unique().tolist()), index=0)
        sim_has_acc = st.checkbox("Conta Já Cadastrada no CRM?", value=True)
        sim_is_enterprise = st.checkbox("Porte da Conta é Enterprise?", value=False)
        sim_age_days = st.slider("Idade Atual da Negociação (Dias desde 1º contato):", min_value=1, max_value=180, value=25)

        # Base value from catalog/median
        prod_val = float(df_all[df_all["product"] == sim_product]["sales_price"].iloc[0])
        sim_custom_val = st.number_input("Valor Estimado do Contrato ($):", min_value=50.0, max_value=100000.0, value=prod_val, step=500.0)

    with col_sim_out:
        # Calculate simulation directly using the canonical scorer to guarantee 100% formula parity
        sim_df = pd.DataFrame([{
            "opportunity_id": "SIM-001",
            "sales_agent": sim_agent,
            "product": sim_product,
            "has_account": sim_has_acc,
            "account": "Conta Simulada" if sim_has_acc else np.nan,
            "account_display": "Conta Simulada" if sim_has_acc else "⚠️ Conta Não Vinculada",
            "is_enterprise_account": sim_is_enterprise,
            "cycle_days": float(sim_age_days),
            "expected_won_value": float(sim_custom_val),
            "deal_stage": "Engaging",
        }])
        sim_scored = scorer.score_engaging_deals(sim_df).iloc[0]
        sim_p_win = float(sim_scored["p_win"])
        sim_ev_day = float(sim_scored["ev_per_day"])
        sim_score = float(sim_scored["priority_score"])

        st.markdown("#### 🎯 Resultado da Qualificação")
        m1, m2, m3 = st.columns(3)
        m1.metric("Score de Prioridade", f"{sim_score:.1f}/100")
        m2.metric("Probabilidade de Vitória", f"{sim_p_win*100:.1f}%")
        m3.metric("Velocidade Esperada", f"${sim_ev_day:,.0f}/dia")

        # Life decay simulation curve using the exact scorer
        future_ages = np.arange(1, 160, 5)
        curve_records = []
        for f_age in future_ages:
            s_row = sim_df.copy()
            s_row["cycle_days"] = float(f_age)
            res = scorer.score_engaging_deals(s_row).iloc[0]
            curve_records.append({"Dias no Pipeline": f_age, "Probabilidade de Fechamento": res["p_win"] * 100})

        df_sim_curve = pd.DataFrame(curve_records)
        fig_sim = px.line(
            df_sim_curve,
            x="Dias no Pipeline",
            y="Probabilidade de Fechamento",
            title=f"Curva de Propensão ao Longo do Tempo ({sim_product} com {sim_agent})",
            labels={"Probabilidade de Fechamento": "P(Win) %"},
        )
        fig_sim.add_vline(x=sim_age_days, line_dash="dash", line_color="#EF4444", annotation_text="Ponto Atual")
        fig_sim.add_vline(x=118, line_dash="dot", line_color="#DC2626", annotation_text="Zona Zombie (P95)")
        st.plotly_chart(fig_sim, use_container_width=True)


# ==============================================================================
# TAB 4: GOVERNANÇA, CALIBRAÇÃO & BACKTEST OUT-OF-TIME
# ==============================================================================
with tab_governance:
    st.subheader("📊 Auditoria Metodológica & Backtest Temporal Out-of-Time")
    st.markdown(
        "Validação científica obrigatória: Treino realizado em dados até **30/06/2017** "
        "e teste cego avaliado em **4.032 negócios reais** fechados posteriormente."
    )

    report = run_temporal_backtest()

    st.markdown("##### 🏆 Desempenho Comparativo contra 3 Baselines Clássicos")
    st.markdown(report.to_markdown_table())

    st.markdown("---")

    c_gov_left, c_gov_right = st.columns(2)

    with c_gov_left:
        st.markdown("##### 🎯 Diagrama de Confiabilidade (Reliability Curve)")
        st.caption("Verificação da calibração probabilística: Previsto vs. Observado em quintis.")
        df_calib = pd.DataFrame(report.calibration_bins)
        fig_calib = go.Figure()
        fig_calib.add_trace(
            go.Scatter(
                x=df_calib["predicted_prob_mean"],
                y=df_calib["observed_win_rate"],
                mode="lines+markers",
                name="Nosso Modelo",
                line=dict(color="#0F52BA", width=3),
            )
        )
        fig_calib.add_trace(
            go.Scatter(
                x=[0.4, 0.8],
                y=[0.4, 0.8],
                mode="lines",
                name="Calibração Perfeita (y = x)",
                line=dict(color="#94A3B8", dash="dash"),
            )
        )
        fig_calib.update_layout(
            xaxis_title="Probabilidade Prevista Média",
            yaxis_title="Taxa de Vitória Real Observada",
            height=340,
            margin=dict(l=10, r=10, t=20, b=10),
        )
        st.plotly_chart(fig_calib, use_container_width=True)

    with c_gov_right:
        st.markdown("##### 📈 Curva Empírica de Sobrevivência (Kaplan-Meier Proxy)")
        st.caption("Evidência do viés de censura à direita em 138 dias e taxa de descarte precoce.")
        fig_surv = go.Figure()
        fig_surv.add_trace(
            go.Scatter(
                x=df_survival["age_threshold_days"],
                y=df_survival["naive_closed_only_win_rate"] * 100,
                mode="lines+markers",
                name="Win Rate Fechados Ingênuo (%)",
                line=dict(color="#EF4444", dash="dot"),
            )
        )
        fig_surv.add_trace(
            go.Scatter(
                x=df_survival["age_threshold_days"],
                y=df_survival["true_unconditional_win_rate"] * 100,
                mode="lines+markers",
                name="Taxa Incondicional Real (%)",
                line=dict(color="#10B981", width=3),
            )
        )
        fig_surv.update_layout(
            xaxis_title="Idade Mínima do Deal (Dias)",
            yaxis_title="Taxa de Vitória (%)",
            height=340,
            margin=dict(l=10, r=10, t=20, b=10),
        )
        st.plotly_chart(fig_surv, use_container_width=True)
