"""
RevOps Copilot — Painel Operacional de Priorização Comercial (Horizonte 90 Dias)
G4 Educação — AI Master Challenge 003: Lead Scorer

Desenvolvido por Arthur Lima
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.data_loader import SNAPSHOT_DATE, build_enriched_pipeline
from src.survival_and_scoring import (
    EmpiricalHorizonScorer,
    compute_age_stage_distribution,
    score_single_deal_simulation,
)
from src.explainability import enrich_with_explainability
from src.feedback_store import FeedbackStore, active_overrides
from src.backtest import (
    run_conditional_resolved_evaluation,
    run_multi_cutoff_queue_evaluation,
)

st.set_page_config(
    page_title="RevOps Copilot — G4 Lead Scorer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
FEEDBACK_FILE = ARTIFACTS_DIR / "feedback_overrides.json"
feedback_store = FeedbackStore(FEEDBACK_FILE)


def load_override_records() -> List[Dict[str, str]]:
    try:
        return feedback_store.read()
    except (ValueError, OSError, TimeoutError) as exc:
        st.error(f"Não foi possível ler o histórico de overrides: {exc}")
        st.stop()


def get_active_overrides_map(records: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    """Replays local history, including queue-reset events, without deleting records."""
    return active_overrides(records)


def append_override_record(record: dict) -> None:
    try:
        feedback_store.append(record)
    except (ValueError, OSError, TimeoutError) as exc:
        st.error(f"Override não gravado; o histórico foi preservado: {exc}")
        st.stop()


def save_sales_rep_override(
    opportunity_id: str,
    agent: str,
    disposition: str,
    reason: str,
    notes: str,
) -> None:
    record = {
        "timestamp": str(pd.Timestamp.now()),
        "opportunity_id": opportunity_id,
        "sales_agent": agent,
        "disposition": disposition,
        "feedback_reason": reason,
        "proposed_action": notes,
    }
    append_override_record(record)


def clear_all_overrides() -> None:
    append_override_record({"event": "reset_all", "timestamp": str(pd.Timestamp.now())})


@st.cache_data(show_spinner=False)
def load_base_model_and_data():
    df, audit = build_enriched_pipeline()
    scorer = EmpiricalHorizonScorer()
    scorer.fit(df, as_of_date=SNAPSHOT_DATE)
    prospecting_raw = df[df["deal_stage"] == "Prospecting"].copy()
    scored_prospecting = scorer.score_prospecting_deals(prospecting_raw)
    age_dist = compute_age_stage_distribution(df, SNAPSHOT_DATE)
    return df, audit, scorer, scored_prospecting, age_dist


@st.cache_data(show_spinner=False)
def load_cached_backtests():
    queue_reports = run_multi_cutoff_queue_evaluation()
    cond_report = run_conditional_resolved_evaluation()
    return queue_reports, cond_report


df_all, audit_summary, scorer, df_prospecting, df_age_dist = load_base_model_and_data()
override_records = load_override_records()
active_overrides = get_active_overrides_map(override_records)

# Score Engaging dynamically with live overrides so UI updates immediately on click
engaging_raw = df_all[df_all["deal_stage"] == "Engaging"].copy()
df_engaging = enrich_with_explainability(
    scorer.score_engaging_deals(engaging_raw, overrides=active_overrides)
)

# --- Sidebar: Navigation & Filters ---
with st.sidebar:
    st.title("🎯 RevOps Copilot")
    st.caption("Priorização de Fila Comercial (Horizonte 90d) | G4 AI Master")

    st.markdown("---")
    st.subheader("🏢 Filtros Operacionais")

    offices = ["Todos"] + sorted(df_all["regional_office"].dropna().unique().tolist())
    selected_office = st.selectbox("Escritório Regional:", offices, index=0)

    filtered_teams = df_all[df_all["deal_stage"].notnull()].copy()
    if selected_office != "Todos":
        filtered_teams = filtered_teams[
            filtered_teams["regional_office"] == selected_office
        ]

    managers = ["Todos"] + sorted(filtered_teams["manager"].dropna().unique().tolist())
    selected_manager = st.selectbox("Gerente Comercial (Manager):", managers, index=0)

    if selected_manager != "Todos":
        filtered_teams = filtered_teams[filtered_teams["manager"] == selected_manager]

    agents = ["Todos"] + sorted(filtered_teams["sales_agent"].dropna().unique().tolist())
    default_agent_idx = agents.index("Moses Frase") if "Moses Frase" in agents else 0
    selected_agent = st.selectbox(
        "Vendedor (Sales Agent):", agents, index=default_agent_idx
    )

    st.markdown("---")
    st.subheader("🔄 Overrides Ativos")
    st.caption(f"Ajustes manuais na fila: **{len(active_overrides)}**")
    if len(active_overrides) > 0:
        if st.button("🔄 Restaurar Fila (Preservar Histórico)"):
            clear_all_overrides()
            st.rerun()

    st.markdown("---")
    st.subheader("🛡️ Auditoria Empírica do CRM")
    st.caption(f"Registros no Pipeline: **{audit_summary['total_rows']:,}**")
    st.caption(
        f"Vendedores c/ Histórico: **{audit_summary['active_agents_count']}** (+{len(audit_summary['inactive_agents_in_teams'])} sem deals)"
    )
    st.caption(
        f"FK Bug `GTXPro` Corrigido: **{audit_summary['gtxpro_foreign_key_fixed']} linhas**"
    )
    st.caption(
        f"Engaging s/ Conta (Higiene): **{audit_summary['missing_account_engaging']:,} / {audit_summary['engaging_count']:,}**"
    )
    st.caption(
        f"Prospecting no Central: **{audit_summary['prospecting_central_share_pct']}% (500/500)**"
    )


# --- Filter Active Subsets ---
view_engaging = df_engaging.copy()
view_prospecting = df_prospecting.copy()

if selected_office != "Todos":
    view_engaging = view_engaging[view_engaging["regional_office"] == selected_office]
    view_prospecting = view_prospecting[
        view_prospecting["regional_office"] == selected_office
    ]

if selected_manager != "Todos":
    view_engaging = view_engaging[view_engaging["manager"] == selected_manager]
    view_prospecting = view_prospecting[
        view_prospecting["manager"] == selected_manager
    ]

if selected_agent != "Todos":
    view_engaging = view_engaging[view_engaging["sales_agent"] == selected_agent]
    view_prospecting = view_prospecting[
        view_prospecting["sales_agent"] == selected_agent
    ]


# --- Header ---
st.title("🎯 Priorização de Pipeline Comercial — Horizonte de 90 Dias")
st.markdown(
    "Ordenação parcimoniosa por **Receita Esperada em 90 Dias (`EV_90d = P_90d × Ticket Mediano`)**, "
    "separando explicitamente **estimativa estatística**, **higiene cadastral do CRM** e **overrides de campo**."
)

tab_closers, tab_sdrs, tab_simulator, tab_governance = st.tabs(
    [
        "🎯 Fila de Fechamento (Engaging)",
        "⚡ Triagem de Pré-Contato (Prospecting)",
        "🧪 Simulador Canônico (Sandbox)",
        "📊 Validação Out-of-Time (Dois Regimes)",
    ]
)


# ==============================================================================
# TAB 1: FILA DE FECHAMENTO (ENGAGING)
# ==============================================================================
with tab_closers:
    st.subheader("🎯 Fila Ativa em Negociação (`Engaging`)")

    col1, col2, col3, col4, col5 = st.columns(5)
    total_ev90 = view_engaging["ev_90d"].sum()
    active_window_count = int(
        (view_engaging["action_tier"].str.contains("Priorizar")).sum()
    )
    stale_count = int(view_engaging["is_stale_p95"].sum())
    missing_acc_count = int((~view_engaging["has_account"]).sum())

    col1.metric("Deals na Fila", f"{len(view_engaging):,}")
    col2.metric("Receita Esperada em 90d (EV_90d)", f"${total_ev90:,.0f}")
    col3.metric("Janela Ativa / Promovidos 🚀", f"{active_window_count}")
    col4.metric("Acima do P95 (>116d) 🧹", f"{stale_count}")
    col5.metric("Sem Conta no CRM (Higiene) ⚠️", f"{missing_acc_count}")

    st.markdown("---")

    if len(view_engaging) > 0:
        c_left, c_right = st.columns([3, 2])
        with c_left:
            st.markdown(
                "##### 📍 Receita Esperada em 90d (`EV_90d`) vs. Idade no Funil (`cycle_days`)"
            )
            color_map = {
                "🚀 Priorizar (Janela Ativa)": "#10B981",
                "⬆️ Priorizado Manualmente (Override)": "#2563EB",
                "🛠️ Revisar Gargalo (>Mediana)": "#F59E0B",
                "🧹 Higienizar (>P95 Ciclo)": "#EF4444",
                "⏸️ Pausado em Campo (Override)": "#64748B",
                "🗑️ Desqualificado em Campo (Override)": "#334155",
            }
            fig = px.scatter(
                view_engaging,
                x="cycle_days",
                y="ev_90d",
                size="expected_won_value",
                color="action_tier",
                hover_name="account_display",
                hover_data=[
                    "opportunity_id",
                    "product",
                    "sales_agent",
                    "p_win_90d",
                    "crm_hygiene_status",
                ],
                color_discrete_map=color_map,
                labels={
                    "cycle_days": "Idade da Oportunidade no Corte (Dias)",
                    "ev_90d": "Receita Esperada em 90d (US$)",
                    "action_tier": "Faixa Operacional",
                },
                height=380,
            )
            fig.add_vline(
                x=57,
                line_dash="dash",
                line_color="#64748B",
                annotation_text="Mediana Won (57d)",
            )
            fig.add_vline(
                x=116,
                line_dash="dot",
                line_color="#DC2626",
                annotation_text="P95 Won (116d)",
            )
            fig.update_layout(margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig, use_container_width=True)

        with c_right:
            st.markdown("##### 📊 Distribuição por Faixa Operacional")
            tier_dist = view_engaging["action_tier"].value_counts().reset_index()
            tier_dist.columns = ["Faixa Operacional", "Total"]
            fig_pie = px.pie(
                tier_dist,
                names="Faixa Operacional",
                values="Total",
                color="Faixa Operacional",
                color_discrete_map=color_map,
                hole=0.45,
                height=380,
            )
            fig_pie.update_layout(margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("##### 📋 Fila Ordenada (Overrides de Campo + `EV_90d` Decrescente)")
        display_cols = [
            "opportunity_id",
            "action_tier",
            "ev_90d",
            "p_win_90d",
            "expected_won_value",
            "cycle_days",
            "product",
            "account_display",
            "crm_hygiene_status",
            "sales_agent",
            "sla_recommendation",
        ]
        st.dataframe(
            view_engaging[display_cols].rename(
                columns={
                    "opportunity_id": "ID",
                    "action_tier": "Faixa Operacional",
                    "ev_90d": "EV 90d ($)",
                    "p_win_90d": "P(Win 90d)",
                    "expected_won_value": "Ticket Mediano ($)",
                    "cycle_days": "Idade (d)",
                    "product": "Produto",
                    "account_display": "Conta",
                    "crm_hygiene_status": "Higiene CRM",
                    "sales_agent": "Vendedor",
                    "sla_recommendation": "SLA Sugerido",
                }
            ),
            use_container_width=True,
            height=290,
        )

        st.markdown("---")

        st.subheader("🔍 Inspeção do Deal & Override Funcional na Fila")
        deal_options = view_engaging["opportunity_id"].tolist()
        selected_opp = st.selectbox(
            "Selecione uma Oportunidade:",
            deal_options,
            index=0 if len(deal_options) > 0 else None,
        )

        if selected_opp:
            deal_row = view_engaging[
                view_engaging["opportunity_id"] == selected_opp
            ].iloc[0]
            col_detail_left, col_detail_right = st.columns([3, 2])

            with col_detail_left:
                st.markdown(
                    f"#### 🏷️ Deal `{deal_row['opportunity_id']}` — {deal_row['account_display']}"
                )
                st.markdown(
                    f"**Vendedor:** {deal_row['sales_agent']} | **Produto:** {deal_row['product']} | "
                    f"**Ticket Mediano:** ${deal_row['expected_won_value']:,.0f}"
                )
                st.markdown(
                    f"**EV 90d (Estatístico):** `${deal_row['ev_90d']:,.2f}` | "
                    f"**P(Win em 90d):** `{deal_row['p_win_90d']*100:.1f}%` | "
                    f"**Higiene CRM:** `{deal_row['crm_hygiene_status']}`"
                )

                st.markdown("##### 💡 Decomposição Transparente (Sem Caixa-Preta):")
                st.info(f"1. {deal_row['driver_1']}")
                st.info(f"2. {deal_row['driver_2']}")
                st.info(f"3. {deal_row['driver_3']}")

                st.markdown("##### 📌 Ação Operacional Sugerida (Regra de Playbook):")
                st.success(
                    f"**{deal_row['recommended_next_step']}** (SLA: *{deal_row['sla_recommendation']}*)"
                )

                with st.expander("📝 Ver Template de Contato Sugerido"):
                    st.code(deal_row["suggested_script"], language="text")

            with col_detail_right:
                st.markdown("#### 🔄 Override Operacional do Vendedor")
                st.caption(
                    "Altera imediatamente a posição deste negócio na fila operacional "
                    "(promover, pausar ou arquivar), mantendo `P(Win 90d)` e `EV_90d` "
                    "originais intactos para auditoria."
                )

                disp_labels = {
                    "promote": "⬆️ Promover p/ Topo da Fila (Sinal Quente de Campo)",
                    "pause": "⏸️ Pausar / Congelar (Aguardar Orçamento)",
                    "archive": "🗑️ Arquivar / Desqualificar (Remover da Fila Ativa)",
                    "none": "🔄 Restaurar Posição Estatística Padrão",
                }
                current_disp = str(deal_row.get("override_disposition", "none"))
                disp_keys = list(disp_labels.keys())
                default_disp_idx = (
                    disp_keys.index(current_disp) if current_disp in disp_keys else 0
                )

                chosen_disp = st.selectbox(
                    "Ação na Fila:",
                    options=disp_keys,
                    format_func=lambda k: disp_labels[k],
                    index=default_disp_idx,
                )
                feedback_reason = st.selectbox(
                    "Motivo de Campo:",
                    [
                        "Aprovação verbal / Minuta em assinatura",
                        "Budget congelado temporariamente com data de retorno",
                        "Troca de decisor no cliente",
                        "Perdido p/ concorrente / Sem perfil real",
                        "Revisão gerencial de carteira",
                    ],
                )
                feedback_notes = st.text_area(
                    "Observações:",
                    placeholder="Ex.: Cliente confirmou assinatura para sexta-feira após call com diretor.",
                    height=85,
                )

                if st.button("💾 Aplicar Override na Fila"):
                    save_sales_rep_override(
                        str(deal_row["opportunity_id"]),
                        str(deal_row["sales_agent"]),
                        chosen_disp,
                        feedback_reason,
                        feedback_notes,
                    )
                    st.rerun()
    else:
        st.warning("Nenhuma oportunidade em `Engaging` para os filtros selecionados.")


# ==============================================================================
# TAB 2: TRIAGEM DE PRÉ-CONTATO (PROSPECTING)
# ==============================================================================
with tab_sdrs:
    st.subheader("⚡ Triagem Operacional de Pré-Contato (`Prospecting` — 500 Leads)")
    st.info(
        "**Nota de Transparência Metodológica:** Todos os 500 registros em `Prospecting` pertencem ao escritório "
        "`Central` e não possuem `engage_date` nem histórico de descarte pré-contato no CRM. Por isso, esta aba "
        "aplica uma **regra determinística de triagem operacional** (prontidão cadastral + ticket mediano do produto), "
        "e **não** um modelo probabilístico."
    )

    col_sdr1, col_sdr2, col_sdr3 = st.columns(3)
    ready_count = int(view_prospecting["has_account"].sum())
    unlinked_prosp = int((~view_prospecting["has_account"]).sum())
    pot_ticket_sum = float(view_prospecting["expected_won_value"].sum())

    col_sdr1.metric("Leads em Prospecting", f"{len(view_prospecting):,}")
    col_sdr2.metric("Prontos p/ 1º Contato (Com Conta)", f"{ready_count:,}")
    col_sdr3.metric(
        "Pendentes de Enriquecimento (Sem Conta)",
        f"{unlinked_prosp:,}",
        help="Leads sem conta vinculada no CRM; exigem identificação da empresa antes da abordagem.",
    )

    st.markdown("---")
    if len(view_prospecting) > 0:
        sdr_cols = [
            "opportunity_id",
            "sdr_triage_lane",
            "sdr_playbook",
            "expected_won_value",
            "product",
            "account_display",
            "sales_agent",
            "agent_hist_win_rate",
        ]
        st.dataframe(
            view_prospecting[sdr_cols].rename(
                columns={
                    "opportunity_id": "ID",
                    "sdr_triage_lane": "Faixa de Triagem",
                    "sdr_playbook": "Ação Operacional",
                    "expected_won_value": "Ticket Mediano Produto ($)",
                    "product": "Produto",
                    "account_display": "Conta",
                    "sales_agent": "Vendedor (Central)",
                    "agent_hist_win_rate": "Win Rate Fechado Rep",
                }
            ),
            use_container_width=True,
            height=380,
        )
    else:
        st.info(
            "Nenhum lead em `Prospecting` para o filtro selecionado (os escritorios `East` e `West` possuem 0 registros nesse estágio)."
        )


# ==============================================================================
# TAB 3: SIMULADOR CANÔNICO (SANDBOX)
# ==============================================================================
with tab_simulator:
    st.subheader("🧪 Simulador Canônico de Oportunidade (`score_single_deal_simulation`)")
    st.markdown(
        "Executa exatamente a mesma função canônica do motor em lote para inspecionar como "
        "`P_90d` e `EV_90d` variam conforme a idade no funil, mantendo higiene cadastral separada."
    )

    col_sim_in, col_sim_out = st.columns([2, 3])

    with col_sim_in:
        active_agents_list = sorted(
            df_all[df_all["deal_stage"].notnull()]["sales_agent"].dropna().unique().tolist()
        )
        sim_agent = st.selectbox("Vendedor Responsável:", active_agents_list, index=0)
        sim_product = st.selectbox(
            "Produto Cotado:",
            sorted(df_all["product"].dropna().unique().tolist()),
            index=0,
        )
        sim_has_acc = st.checkbox("Conta Vinculada no CRM?", value=True)
        sim_age_days = st.slider(
            "Idade Atual no Funil (Dias desde `engage_date`):",
            min_value=0,
            max_value=180,
            value=25,
        )
        default_ticket = float(
            df_all[df_all["product"] == sim_product]["expected_won_value"].median()
        )
        sim_custom_val = st.number_input(
            "Ticket Estimado do Produto ($):",
            min_value=50.0,
            max_value=100000.0,
            value=default_ticket,
            step=250.0,
        )

    with col_sim_out:
        sim_res = score_single_deal_simulation(
            scorer=scorer,
            sales_agent=sim_agent,
            product=sim_product,
            has_account=sim_has_acc,
            cycle_days=float(sim_age_days),
            expected_won_value=float(sim_custom_val),
        )

        m1, m2, m3 = st.columns(3)
        m1.metric("Receita Esperada (EV_90d)", f"${float(sim_res['ev_90d']):,.2f}")
        m2.metric("P(Win em 90d)", f"{float(sim_res['p_win_90d'])*100:.1f}%")
        m3.metric("Higiene Cadastral", str(sim_res["crm_hygiene_status"]).split()[0])
        st.caption(
            f"**Faixa Operacional:** `{sim_res['action_tier']}` — Note que desmarcar 'Conta Vinculada' "
            "aciona pendência cadastral sem distorcer artificialmente `P(Win em 90d)`."
        )

        ages_grid = np.arange(0, 175, 5)
        curve_rows = [
            score_single_deal_simulation(
                scorer=scorer,
                sales_agent=sim_agent,
                product=sim_product,
                has_account=sim_has_acc,
                cycle_days=float(a),
                expected_won_value=float(sim_custom_val),
            )
            for a in ages_grid
        ]
        df_sim_curve = pd.DataFrame(
            {
                "Idade no Funil (Dias)": ages_grid,
                "P(Win em 90d) %": [float(r["p_win_90d"]) * 100.0 for r in curve_rows],
            }
        )
        fig_sim = px.line(
            df_sim_curve,
            x="Idade no Funil (Dias)",
            y="P(Win em 90d) %",
            title=f"Curva Empírica de Conversão em 90 Dias ({sim_product} — {sim_agent})",
        )
        fig_sim.add_vline(
            x=sim_age_days,
            line_dash="dash",
            line_color="#2563EB",
            annotation_text="Idade Selecionada",
        )
        fig_sim.add_vline(
            x=float(sim_res["product_p95_cycle"]),
            line_dash="dot",
            line_color="#DC2626",
            annotation_text="Limiar P95 Won",
        )
        st.plotly_chart(fig_sim, use_container_width=True)


# ==============================================================================
# TAB 4: VALIDAÇÃO OUT-OF-TIME (DOIS REGIMES + ABLAÇÃO)
# ==============================================================================
with tab_governance:
    st.subheader("📊 Auditoria Metodológica & Validação Out-of-Time em Dois Regimes")
    queue_reports, cond_report = load_cached_backtests()

    st.markdown(
        "#### 1. Avaliação Primária: Fila Aberta Completa no Corte (Horizonte Prospectivo de +90 Dias, Sem Censura)\n"
        "Avalia **todas** as oportunidades abertas em `Engaging` na data de corte (`N = 2.257` em `31/07`, "
        "`N = 2.265` em `31/08` e `N = 2.409` em `30/09/2017`), usando apenas variáveis observáveis no corte "
        "(excluindo `account` para evitar *snapshot leakage*) e medindo a receita `Won` efetivamente fechada nos 90 dias seguintes."
    )

    st.caption("Cortes móveis com janelas sobrepostas: oportunidades podem reaparecer. Não somar receitas como receita única nem tratar os cortes como replicações independentes.")

    selected_cut_idx = st.radio(
        "Selecione a Data de Corte Out-of-Time:",
        options=list(range(len(queue_reports))),
        format_func=lambda i: f"Corte {queue_reports[i].split_date} (N = {queue_reports[i].open_queue_count:,} deals abertos)",
        horizontal=True,
        index=1,
    )
    active_rep = queue_reports[selected_cut_idx]
    st.markdown(active_rep.to_markdown_table())

    wr = active_rep.within_rep_top20
    st.caption(
        f"**Decisão Intra-Vendedor (cada vendedor priorizando o Top 20% da própria fila em `{active_rep.split_date}`):** "
        f"`EV_90d` captura **US$ {wr['ev_90d_full']['captured_rev_usd']:,.0f} ({wr['ev_90d_full']['captured_rev_share_pct']:.1f}%)** "
        f"vs Preço Nominal **US$ {wr['nominal_price']['captured_rev_usd']:,.0f} ({wr['nominal_price']['captured_rev_share_pct']:.1f}%)** "
        f"e Frescor **US$ {wr['freshness']['captured_rev_usd']:,.0f} ({wr['freshness']['captured_rev_share_pct']:.1f}%)**."
    )

    st.markdown("---")
    st.markdown(
        "#### 2. Diagnóstico das Estratégias Avaliadas: Subpopulação Condicional Resolvida (`Won` vs `Lost`)\n"
        f" Em `30/06/2017`, das `{cond_report.open_total_at_split:,}` oportunidades abertas, `{cond_report.censored_excluded_count:,}` "
        f"permaneceram abertas até o fim do dataset e `{cond_report.resolved_deal_count:,}` fecharam como `Won` ou `Lost`. "
        "Quando avaliamos **apenas** os `970` casos já filtrados pelo desfecho futuro, as estratégias avaliadas ficam em "
        "**AUC ~0,49–0,51**. A vantagem na fila completa é compatível com triagem por idade "
        "ponderada pelo ticket. Isso não estabelece um teto para outros modelos nem demonstra impacto causal."
    )
    st.markdown(cond_report.to_markdown_table())

    st.markdown("---")
    c_gov_left, c_gov_right = st.columns(2)

    with c_gov_left:
        st.markdown(
            f"##### 🎯 Curva de Calibração Empírica (Corte `{active_rep.split_date}`, +90d)"
        )
        st.caption("Probabilidade prevista `P(Win 90d)` vs. taxa real observada por quintil.")
        df_calib = pd.DataFrame(active_rep.calibration_bins)
        fig_calib = go.Figure()
        fig_calib.add_trace(
            go.Scatter(
                x=df_calib["predicted_prob_mean"],
                y=df_calib["observed_win_rate"],
                mode="lines+markers",
                name="P_90d Empírico",
                line=dict(color="#0F52BA", width=3),
            )
        )
        fig_calib.add_trace(
            go.Scatter(
                x=[0.0, 0.55],
                y=[0.0, 0.55],
                mode="lines",
                name="Calibração Ideal (y = x)",
                line=dict(color="#94A3B8", dash="dash"),
            )
        )
        fig_calib.update_layout(
            xaxis_title="Probabilidade Prevista Média (90d)",
            yaxis_title="Taxa de Vitória Real em 90d",
            height=330,
            margin=dict(l=10, r=10, t=20, b=10),
        )
        st.plotly_chart(fig_calib, use_container_width=True)

    with c_gov_right:
        st.markdown("##### 📈 Proporção Histórica por Duração Observada (Descritivo)")
        st.caption(
            "Proporção bruta de negócios fechados vs. ainda abertos em 31/12/2017 por faixa de duração."
        )
        fig_surv = go.Figure()
        fig_surv.add_trace(
            go.Scatter(
                x=df_age_dist["age_threshold_days"],
                y=df_age_dist["closed_only_win_rate"] * 100,
                mode="lines+markers",
                name="Win Rate apenas entre Fechados (%)",
                line=dict(color="#EF4444", dash="dot"),
            )
        )
        fig_surv.add_trace(
            go.Scatter(
                x=df_age_dist["age_threshold_days"],
                y=df_age_dist["unconditional_won_share"] * 100,
                mode="lines+markers",
                name="Proporção Won sobre Total na Faixa (%)",
                line=dict(color="#10B981", width=3),
            )
        )
        fig_surv.update_layout(
            xaxis_title="Duração Observada Mínima (Dias)",
            yaxis_title="Proporção (%)",
            height=330,
            margin=dict(l=10, r=10, t=20, b=10),
        )
        st.plotly_chart(fig_surv, use_container_width=True)
