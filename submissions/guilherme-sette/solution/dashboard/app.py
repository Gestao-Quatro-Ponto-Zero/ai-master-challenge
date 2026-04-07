from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from analytics import format_currency, format_percent, load_dashboard_data


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CSS_PATH = Path(__file__).with_name("styles.css")

ACTION_COLOR_MAP = {
    "Completar CRM": "#f59e0b",
    "Prioridade comercial": "#2563eb",
    "Retomar ou encerrar": "#ef4444",
    "Acompanhar": "#94a3b8",
}


st.set_page_config(page_title="Revenue Radar", layout="wide")

PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}


@st.cache_data
def load_app_state() -> dict:
    return load_dashboard_data(DATA_DIR)


def load_css() -> None:
    st.markdown(f"<style>{CSS_PATH.read_text()}</style>", unsafe_allow_html=True)


def badge(label: str, tone: str = "default") -> str:
    return f"<span class='badge badge-{tone}'>{label}</span>"


def action_tone(action: str) -> str:
    if action == "Retomar ou encerrar":
        return "danger"
    if action == "Completar CRM":
        return "warn"
    if action == "Prioridade comercial":
        return "success"
    return "default"


def safe_text(value: object, fallback: str) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return fallback
    return str(value)


def render_metric_card(label: str, value: str, subtext: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-subtext">{subtext}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_deal_card(row: pd.Series) -> None:
    alignment_tone = "warn" if row["alignment_status"] == "Reassign" else "success"
    movement_note = ""
    if row["current_owner"] != row["suggested_owner"]:
        movement_note = (
            f"<div class='deal-transfer'>Antes com <strong>{row['current_owner']}</strong>. "
            f"Agora com voce porque seu fit ficou <strong>+{row['suggested_delta_pp']:.1f} pp</strong> acima.</div>"
        )
    reason_html = f"<div class='deal-reason'><strong>Proximo passo:</strong> {row['action_detail']}<br>{row['why_now']}</div>"

    st.markdown(
        f"""
        <div class="deal-card">
            <div class="deal-head">
                <div>
                    <div class="deal-title">{safe_text(row['account'], 'Conta nao vinculada')} • {row['product']}</div>
                    <div class="deal-meta">{row['opportunity_id']} • {row['deal_stage']} • {safe_text(row['sector'], 'Setor nao informado')}</div>
                </div>
                <div class="deal-badges">
                    {badge(row['recommended_action'], action_tone(row['recommended_action']))}
                    {badge(row['alignment_status'], alignment_tone)}
                    {badge(row['data_quality_status'], 'warn' if row['needs_data_completion'] else 'default')}
                </div>
            </div>
            <div class="deal-grid">
                <div>
                    <div class="deal-kpi-label">Prob. ganho</div>
                    <div class="deal-kpi-value">{format_percent(row['forecast_pct'])}</div>
                </div>
                <div>
                    <div class="deal-kpi-label">Valor esperado</div>
                    <div class="deal-kpi-value">{format_currency(row['expected_value_proxy'])}</div>
                </div>
                <div>
                    <div class="deal-kpi-label">Owner anterior</div>
                    <div class="deal-kpi-value">{row['current_owner']}</div>
                </div>
                <div>
                    <div class="deal-kpi-label">Status</div>
                    <div class="deal-kpi-value">{'Recebido agora' if row['current_owner'] != row['suggested_owner'] else 'Ja estava com voce'}</div>
                </div>
            </div>
            {movement_note}
            {reason_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_action_legend() -> None:
    st.markdown(
        """
        <div class="insight-card">
            <div class="insight-title">Como ler as acoes</div>
            <div class="insight-line"><strong>Prioridade comercial:</strong> falar com o cliente agora porque o deal tem sinal bom de captura.</div>
            <div class="insight-line"><strong>Completar CRM:</strong> preencher conta e/ou data de engajamento para recuperar contexto e retomar a negociacao.</div>
            <div class="insight-line"><strong>Retomar ou encerrar:</strong> deal envelhecido demais para continuar parado sem acao clara.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_seller_header(seller_row: pd.Series) -> None:
    badges = [
        badge(f"Top produto: {safe_text(seller_row.get('top_product'), 'n/d')}", "default"),
        badge(f"Top setor: {safe_text(seller_row.get('top_sector'), 'n/d')}", "default"),
    ]
    if bool(seller_row.get("yellow_flag", False)):
        badges.append(
            badge(
                f"YELLOW FLAG • {abs(float(seller_row.get('performance_vs_avg_pct', 0))):.1f}% pior que a media",
                "warn",
            )
        )

    st.markdown(
        f"""
        <div class="hero-card">
            <div>
                <div class="hero-title">Painel do vendedor</div>
                <div class="hero-subtitle">
                    Fila objetiva para agir agora, limpar CRM quando faltar contexto e evitar deals envelhecidos.
                </div>
            </div>
            <div class="hero-badges">
                {"".join(badges)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def vendor_tab(state: dict) -> None:
    open_deals = state["open_deals"]
    seller_summary = state["seller_summary"]

    sellers = sorted(seller_summary["seller"].dropna().tolist())
    selected_seller = st.selectbox("Escolha o vendedor", sellers)

    seller_row = seller_summary[seller_summary["seller"] == selected_seller].iloc[0]
    suggested_queue = open_deals[open_deals["suggested_owner"] == selected_seller].copy()
    current_queue = open_deals[open_deals["current_owner"] == selected_seller].copy()
    crm_alerts = current_queue[current_queue["needs_data_completion"]].copy()
    stale_alerts = current_queue[current_queue["recommended_action"] == "Retomar ou encerrar"].copy()
    incoming = suggested_queue[suggested_queue["current_owner"] != selected_seller].copy()
    selling_actions = ["Prioridade comercial", "Retomar ou encerrar"]
    seller_visible_queue = suggested_queue.copy()
    selling_queue = seller_visible_queue[seller_visible_queue["recommended_action"].isin(selling_actions)].copy()

    action_priority = {
        "Prioridade comercial": 0,
        "Retomar ou encerrar": 1,
        "Completar CRM": 2,
        "Acompanhar": 4,
    }
    seller_visible_queue["action_rank"] = seller_visible_queue["recommended_action"].map(action_priority).fillna(99)
    selling_queue["action_rank"] = selling_queue["recommended_action"].map(action_priority).fillna(99)
    focus_deals = selling_queue.sort_values(
        ["action_rank", "expected_value_proxy", "forecast_pct"],
        ascending=[True, False, False],
    ).head(8)

    render_seller_header(seller_row)

    metric_cols = st.columns(5)
    with metric_cols[0]:
        render_metric_card(
            "Acoes de venda",
            f"{int(len(selling_queue))}",
            "Deals agora na sua mao que pedem movimento comercial direto",
        )
    with metric_cols[1]:
        render_metric_card(
            "Valor esperado sugerido",
            format_currency(float(seller_visible_queue["expected_value_proxy"].sum())),
            "Potencial total da carteira que agora esta com voce",
        )
    with metric_cols[2]:
        render_metric_card(
            "Negocios recebidos",
            f"{int(len(incoming))}",
            "Clientes que nao estavam com voce e agora vieram para sua fila",
        )
    with metric_cols[3]:
        render_metric_card(
            "Alertas de CRM",
            f"{int(len(crm_alerts))}",
            "Higiene pendente que pode travar contexto do deal",
        )
    with metric_cols[4]:
        render_metric_card(
            "Retomar ou encerrar",
            f"{int(len(stale_alerts))}",
            "Deals envelhecidos acima do ritmo historico",
        )

    st.markdown("### Prioridades para agir")
    if focus_deals.empty:
        st.info("Nenhum deal de venda prioritario para este vendedor na configuracao atual.")
    else:
        for _, row in focus_deals.iterrows():
            render_deal_card(row)

    alert_cols = st.columns(2)
    with alert_cols[0]:
        st.markdown("### Higiene de CRM")
        crm_table = crm_alerts[
            [
                "opportunity_id",
                "account",
                "product",
                "deal_stage",
                "data_quality_status",
                "action_detail",
            ]
        ].rename(
            columns={
                "opportunity_id": "Deal",
                "account": "Conta",
                "product": "Produto",
                "deal_stage": "Etapa",
                "data_quality_status": "Lacuna",
                "action_detail": "Proximo passo",
            }
        )
        st.dataframe(crm_table, width="stretch", height=280, hide_index=True)

    with alert_cols[1]:
        st.markdown("### Retomar ou encerrar")
        stale_table = stale_alerts[
            [
                "opportunity_id",
                "account",
                "product",
                "age_ratio",
                "forecast_pct",
                "action_detail",
            ]
        ].rename(
            columns={
                "opportunity_id": "Deal",
                "account": "Conta",
                "product": "Produto",
                "age_ratio": "Ciclo vs historico",
                "forecast_pct": "Prob. ganho",
                "action_detail": "Proximo passo",
            }
        )
        st.dataframe(
            stale_table,
            width="stretch",
            height=280,
            hide_index=True,
            column_config={
                "Ciclo vs historico": st.column_config.NumberColumn("Ciclo vs historico", format="%.1fx"),
                "Prob. ganho": st.column_config.NumberColumn("Prob. ganho", format="%.1f%%"),
            },
        )

    with st.expander("Ver guia rapido das acoes"):
        render_action_legend()

    st.markdown("### Fila operacional")
    operational_queue = seller_visible_queue.sort_values(
        ["action_rank", "expected_value_proxy", "forecast_pct"],
        ascending=[True, False, False],
    )
    table = operational_queue[
        [
            "opportunity_id",
            "account",
            "product",
            "deal_stage",
            "recommended_action",
            "action_detail",
            "forecast_pct",
            "expected_value_proxy",
            "current_owner",
            "suggested_delta_pp",
            "data_quality_status",
        ]
    ].rename(
        columns={
            "opportunity_id": "Deal",
            "account": "Conta",
            "product": "Produto",
            "deal_stage": "Etapa",
            "recommended_action": "Acao",
            "action_detail": "Proximo passo",
            "forecast_pct": "Prob. ganho",
            "expected_value_proxy": "Valor esperado",
            "current_owner": "Owner anterior",
            "suggested_delta_pp": "Ganho de fit (pp)",
            "data_quality_status": "Qualidade CRM",
        }
    )

    st.dataframe(
        table,
        width="stretch",
        height=520,
        hide_index=True,
        column_config={
            "Prob. ganho": st.column_config.ProgressColumn(
                "Prob. ganho",
                min_value=0.0,
                max_value=100.0,
                format="%.0f%%",
            ),
            "Valor esperado": st.column_config.NumberColumn("Valor esperado", format="R$ %.0f"),
            "Ganho de fit (pp)": st.column_config.NumberColumn("Ganho de fit (pp)", format="%.1f"),
        },
    )


def head_tab(state: dict) -> None:
    open_deals = state["open_deals"]
    seller_summary = state["seller_summary"]
    head_summary = state["head_summary"]

    st.markdown(
        """
        <div class="hero-card">
            <div>
                <div class="hero-title">Painel da head</div>
                <div class="hero-subtitle">
                    Visao macro do pipeline, transferencias sugeridas com perda controlada e higiene de CRM que trava forecast.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_cols = st.columns(5)
    with metric_cols[0]:
        render_metric_card("Pipeline aberto", f"{len(open_deals):,}".replace(",", "."), "Deals ainda em jogo no CRM")
    with metric_cols[1]:
        render_metric_card(
            "Valor esperado total",
            format_currency(head_summary["expected_value_total"]),
            "Forecast proxy baseado em deal quality",
        )
    with metric_cols[2]:
        render_metric_card(
            "Transferencias sugeridas",
            f"{head_summary['transfer_candidates']}",
            "Deals com owner alternativo e ganho material de fit",
        )
    with metric_cols[3]:
        render_metric_card(
            "Completar CRM",
            f"{head_summary['crm_fix_candidates']}",
            "Deals com conta e/ou data de engajamento faltando",
        )
    with metric_cols[4]:
        render_metric_card(
            "Perda media no rebalance",
            f"{head_summary['mean_fit_loss_pp']:.1f} pp",
            "Queda media de fit para aliviar concentracao sem sacrificar muito resultado",
        )

    chart_cols = st.columns([1.1, 1])
    with chart_cols[0]:
        st.markdown("### Forecast por familia")
        family_chart = px.bar(
            head_summary["expected_by_family"],
            x="family",
            y="expected_value_proxy",
            color="family",
            color_discrete_sequence=["#ff7a59", "#425b76", "#00a4bd"],
        )
        family_chart.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            showlegend=False,
            yaxis_title=None,
            xaxis_title=None,
        )
        st.plotly_chart(family_chart, use_container_width=True, config=PLOTLY_CONFIG)

    with chart_cols[1]:
        st.markdown("### Acoes recomendadas")
        action_chart = px.bar(
            head_summary["actions_breakdown"],
            x="recommended_action",
            y="deals",
            color="recommended_action",
            color_discrete_map=ACTION_COLOR_MAP,
            category_orders={
                "recommended_action": [
                    "Prioridade comercial",
                    "Completar CRM",
                    "Transferir owner",
                    "Retomar ou encerrar",
                    "Acompanhar",
                ]
            },
        )
        action_chart.update_layout(margin=dict(l=0, r=0, t=10, b=0), xaxis_title=None, yaxis_title=None, showlegend=False)
        st.plotly_chart(action_chart, use_container_width=True, config=PLOTLY_CONFIG)

    st.markdown("### Macro insights")
    top_products = (
        open_deals.groupby("product")["expected_value_proxy"].sum().sort_values(ascending=False).head(3).index.tolist()
    )
    top_shift = seller_summary.sort_values("suggested_open_deals", ascending=False).head(3)
    macro = [
        f"O pipeline esperado continua puxado por {', '.join(top_products)}, entao a gestao deve manter foco nesses SKUs.",
        f"{head_summary['transfer_candidates']} deals mostram movimentacao potencial de owner com ganho material de fit.",
        f"Os vendedores com maior carteira sugerida agora sao {', '.join(top_shift['seller'].tolist())}.",
    ]
    for item in macro:
        st.markdown(f"- {item}")

    management_cols = st.columns([1.2, 1])
    with management_cols[0]:
        st.markdown("### Historico de movimentacao de owners")
        transfer_table = head_summary["movement_history"][
            [
                "opportunity_id",
                "account",
                "product",
                "movement_history",
                "forecast_pct",
                "expected_value_proxy",
                "movement_reason",
            ]
        ].rename(
            columns={
                "opportunity_id": "Deal",
                "account": "Conta",
                "product": "Produto",
                "movement_history": "Movimentacao",
                "forecast_pct": "Prob. ganho",
                "expected_value_proxy": "Valor esperado",
                "movement_reason": "Racional",
            }
        )
        st.dataframe(
            transfer_table,
            width="stretch",
            height=420,
            hide_index=True,
            column_config={
                "Prob. ganho": st.column_config.ProgressColumn("Prob. ganho", min_value=0.0, max_value=100.0, format="%.0f%%"),
                "Valor esperado": st.column_config.NumberColumn("Valor esperado", format="R$ %.0f"),
            },
        )

    with management_cols[1]:
        st.markdown("### Board de vendedores")
        seller_board = seller_summary[
            [
                "seller",
                "yellow_flag",
                "performance_vs_avg_pct",
                "current_open_deals",
                "suggested_open_deals",
                "current_expected_value",
                "suggested_expected_value",
                "data_gaps",
            ]
        ].copy()
        seller_board["status"] = seller_board.apply(
            lambda row: "YELLOW FLAG" if row["yellow_flag"] else "OK",
            axis=1,
        )
        seller_board = seller_board.rename(
            columns={
                "seller": "Vendedor",
                "status": "Status",
                "performance_vs_avg_pct": "Vs media",
                "current_open_deals": "Carteira atual",
                "suggested_open_deals": "Carteira sugerida",
                "current_expected_value": "Valor atual",
                "suggested_expected_value": "Valor sugerido",
                "data_gaps": "Completar CRM",
            }
        )
        st.dataframe(
            seller_board,
            width="stretch",
            height=420,
            hide_index=True,
            column_config={
                "Vs media": st.column_config.NumberColumn("Vs media", format="%.1f%%"),
                "Valor atual": st.column_config.NumberColumn("Valor atual", format="R$ %.0f"),
                "Valor sugerido": st.column_config.NumberColumn("Valor sugerido", format="R$ %.0f"),
            },
        )

    extra_cols = st.columns([1.2, 1])
    with extra_cols[0]:
        st.markdown("### Forecast por owner atual")
        owner_chart = px.bar(
            head_summary["expected_by_current_owner"].head(12),
            x="current_owner",
            y="expected_value_proxy",
            color="expected_value_proxy",
            color_continuous_scale=["#dbeafe", "#2563eb"],
        )
        owner_chart.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title=None,
            yaxis_title=None,
            coloraxis_showscale=False,
        )
        st.plotly_chart(owner_chart, use_container_width=True, config=PLOTLY_CONFIG)

    with extra_cols[1]:
        st.markdown("### Forecast por owner sugerido")
        suggested_chart = px.bar(
            head_summary["recommended_by_owner"].head(12),
            x="suggested_owner",
            y="expected_value_proxy",
            color="expected_value_proxy",
            color_continuous_scale=["#ede9fe", "#7c3aed"],
        )
        suggested_chart.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title=None,
            yaxis_title=None,
            coloraxis_showscale=False,
        )
        st.plotly_chart(suggested_chart, use_container_width=True, config=PLOTLY_CONFIG)


def main() -> None:
    load_css()
    state = load_app_state()

    st.markdown(
        """
        <div class="app-shell">
            <div class="app-kicker">Revenue Radar</div>
            <div class="app-title">Pipeline priorizado com Deal Forecast, hygiene coaching e rebalanceamento conservador</div>
            <div class="app-copy">
                Dashboard pensada para times acostumados a CRM comercial: leitura direta, acoes claras e redistribuicao sem sacrificar materialmente o resultado.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_vendor, tab_head = st.tabs(["VENDEDOR", "HEAD"])
    with tab_vendor:
        vendor_tab(state)
    with tab_head:
        head_tab(state)


if __name__ == "__main__":
    main()
