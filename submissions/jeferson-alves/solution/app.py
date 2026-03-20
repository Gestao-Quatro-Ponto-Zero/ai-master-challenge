from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from lead_scoring import (
    component_frame,
    format_currency,
    load_and_score,
    safe_ratio,
    score_summary,
)


st.set_page_config(
    page_title="Lead Scorer",
    page_icon="targets",
    layout="wide",
)


st.markdown(
    """
    <style>
    .stApp {
        color: var(--text-color);
        background:
            radial-gradient(circle at top right, rgba(13, 148, 136, 0.14), transparent 30%),
            radial-gradient(circle at left top, rgba(249, 115, 22, 0.12), transparent 28%),
            var(--background-color);
    }
    div[data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at top right, rgba(13, 148, 136, 0.14), transparent 30%),
            radial-gradient(circle at left top, rgba(249, 115, 22, 0.12), transparent 28%),
            var(--background-color);
    }
    div[data-testid="stMetric"] {
        background: color-mix(in srgb, var(--secondary-background-color) 88%, transparent);
        border: 1px solid color-mix(in srgb, var(--text-color) 10%, transparent);
        border-radius: 16px;
        padding: 14px;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.12);
    }
    .hero {
        background: linear-gradient(135deg, rgba(15,118,110,0.96), rgba(22,78,99,0.94));
        color: white;
        padding: 28px 30px;
        border-radius: 24px;
        margin-bottom: 18px;
        box-shadow: 0 18px 34px rgba(15, 23, 42, 0.15);
    }
    .hero h1 {
        margin: 0 0 8px 0;
        font-size: 2.2rem;
    }
    .hero p {
        margin: 0;
        max-width: 860px;
        opacity: 0.92;
    }
    div[data-testid="stSidebar"] {
        background: color-mix(in srgb, var(--secondary-background-color) 92%, transparent);
    }
    div[data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def get_scored_data(data_dir: str) -> tuple[pd.DataFrame, pd.DataFrame, object]:
    return load_and_score(data_dir)


solution_dir = Path(__file__).resolve().parent
data_dir = solution_dir / "data"
open_deals, team_summary, context = get_scored_data(str(data_dir))


st.markdown(
    f"""
    <div class="hero">
        <h1>Lead Scorer para priorizacao comercial</h1>
        <p>
            App para o vendedor abrir o pipeline, filtrar sua carteira e saber onde focar agora.
            O score combina etapa do deal, historico do vendedor, conta, produto, manager, regiao,
            frescor do pipeline e potencial financeiro. Baseline historico de ganho em deals fechados: {safe_ratio(context.global_win_rate)}.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


with st.sidebar:
    st.header("Filtros")
    selected_regions = st.multiselect(
        "Regional office",
        sorted(open_deals["regional_office"].dropna().unique()),
    )
    filtered_managers = open_deals.copy()
    if selected_regions:
        filtered_managers = filtered_managers[
            filtered_managers["regional_office"].isin(selected_regions)
        ]

    selected_managers = st.multiselect(
        "Manager",
        sorted(filtered_managers["manager"].dropna().unique()),
    )
    filtered_agents = filtered_managers.copy()
    if selected_managers:
        filtered_agents = filtered_agents[filtered_agents["manager"].isin(selected_managers)]

    selected_agents = st.multiselect(
        "Sales agent",
        sorted(filtered_agents["sales_agent"].dropna().unique()),
    )
    selected_stages = st.multiselect(
        "Deal stage",
        sorted(open_deals["deal_stage"].dropna().unique()),
        default=sorted(open_deals["deal_stage"].dropna().unique()),
    )
    min_score = st.slider("Score minimo", min_value=0, max_value=100, value=55)
    top_n = st.slider("Deals na tabela", min_value=10, max_value=100, value=25, step=5)


filtered = open_deals.copy()
if selected_regions:
    filtered = filtered[filtered["regional_office"].isin(selected_regions)]
if selected_managers:
    filtered = filtered[filtered["manager"].isin(selected_managers)]
if selected_agents:
    filtered = filtered[filtered["sales_agent"].isin(selected_agents)]
if selected_stages:
    filtered = filtered[filtered["deal_stage"].isin(selected_stages)]
filtered = filtered[filtered["priority_score"] >= min_score].copy()

summary = score_summary(filtered)
metric_cols = st.columns(5)
metric_cols[0].metric("Deals em foco", f"{summary['open_deals']:,}")
metric_cols[1].metric("Score medio", f"{summary['avg_score']:.1f}")
metric_cols[2].metric("Hot deals", f"{summary['hot_deals']:,}")
metric_cols[3].metric("Hot + Focus", f"{summary['focus_deals']:,}")
metric_cols[4].metric("Receita esperada", format_currency(summary["expected_revenue"]))

if filtered.empty:
    st.warning("Nenhum deal atende aos filtros atuais.")
    st.stop()

tab_priority, tab_team, tab_method = st.tabs(["Priorizar deals", "Visao de time", "Metodologia"])

with tab_priority:
    top_deals = filtered.head(top_n).copy()
    chart_cols = st.columns([1.25, 1])

    with chart_cols[0]:
        score_chart = px.bar(
            top_deals.head(12).sort_values("priority_score", ascending=True),
            x="priority_score",
            y="opportunity_id",
            orientation="h",
            color="priority_tier",
            color_discrete_map={
                "Hot": "#0f766e",
                "Focus": "#2563eb",
                "Watch": "#f59e0b",
                "Low": "#dc2626",
            },
            hover_data=["sales_agent", "account_label", "product_label", "expected_revenue"],
            title="Top deals por score",
        )
        score_chart.update_layout(height=420, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(score_chart, use_container_width=True)

    with chart_cols[1]:
        scatter = px.scatter(
            top_deals,
            x="priority_score",
            y="expected_revenue",
            color="deal_stage",
            size="expected_deal_value",
            hover_name="opportunity_id",
            hover_data=["sales_agent", "account_label", "product_label"],
            color_discrete_map={"Engaging": "#0f766e", "Prospecting": "#c2410c"},
            title="Score x receita esperada",
        )
        scatter.update_layout(height=420, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(scatter, use_container_width=True)

    display_columns = [
        "rank",
        "opportunity_id",
        "priority_score",
        "priority_tier",
        "sales_agent",
        "manager",
        "regional_office",
        "deal_stage",
        "account_label",
        "product_label",
        "expected_deal_value",
        "expected_revenue",
        "recommended_action",
        "explanation",
    ]
    display_frame = top_deals[display_columns].rename(
        columns={
            "rank": "Rank",
            "opportunity_id": "Opportunity",
            "priority_score": "Score",
            "priority_tier": "Tier",
            "sales_agent": "Sales agent",
            "manager": "Manager",
            "regional_office": "Region",
            "deal_stage": "Stage",
            "account_label": "Account",
            "product_label": "Product",
            "expected_deal_value": "Deal value",
            "expected_revenue": "Expected revenue",
            "recommended_action": "Next action",
            "explanation": "Why this score",
        }
    )

    st.dataframe(
        display_frame,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Score": st.column_config.NumberColumn(format="%.1f"),
            "Deal value": st.column_config.NumberColumn(format="$%.0f"),
            "Expected revenue": st.column_config.NumberColumn(format="$%.0f"),
        },
    )

    detail_options = top_deals["opportunity_id"].tolist()
    selected_id = st.selectbox("Explique um deal", detail_options, index=0)
    selected_deal = top_deals.loc[top_deals["opportunity_id"] == selected_id].iloc[0]

    detail_cols = st.columns([1.1, 1])
    with detail_cols[0]:
        st.subheader(f"Deal {selected_deal['opportunity_id']}")
        st.write(f"Vendedor: {selected_deal['sales_agent']}")
        st.write(f"Manager: {selected_deal['manager']} | Regiao: {selected_deal['regional_office']}")
        st.write(f"Conta: {selected_deal['account_label']}")
        st.write(f"Produto: {selected_deal['product_label']}")
        st.write(f"Etapa atual: {selected_deal['deal_stage']}")
        st.write(f"Score: {selected_deal['priority_score']:.1f} | Tier: {selected_deal['priority_tier']}")
        st.write(f"Probabilidade estimada de ganho: {safe_ratio(selected_deal['estimated_win_rate'])}")
        st.write(f"Receita esperada: {format_currency(selected_deal['expected_revenue'])}")
        st.write(f"Proxima acao sugerida: {selected_deal['recommended_action']}")

        st.markdown("**Principais motivos**")
        for reason in selected_deal["explanation"].split(" | "):
            st.write(f"- {reason}")

    with detail_cols[1]:
        contribution_chart = px.bar(
            component_frame(selected_deal),
            x="contribution",
            y="component",
            orientation="h",
            color="contribution",
            color_continuous_scale=["#c2410c", "#f59e0b", "#0f766e"],
            title="Contribuicao de cada componente no score",
        )
        contribution_chart.update_layout(
            showlegend=False,
            coloraxis_showscale=False,
            height=360,
            margin=dict(l=10, r=10, t=50, b=10),
        )
        st.plotly_chart(contribution_chart, use_container_width=True)

with tab_team:
    filtered_summary = team_summary.copy()
    if selected_regions:
        filtered_summary = filtered_summary[
            filtered_summary["regional_office"].isin(selected_regions)
        ]
    if selected_managers:
        filtered_summary = filtered_summary[filtered_summary["manager"].isin(selected_managers)]
    if selected_agents:
        filtered_summary = filtered_summary[filtered_summary["sales_agent"].isin(selected_agents)]

    team_cols = st.columns([1, 1])
    with team_cols[0]:
        team_chart = px.bar(
            filtered_summary.head(15).sort_values("focus_deals", ascending=True),
            x="focus_deals",
            y="sales_agent",
            orientation="h",
            color="manager",
            title="Quem tem mais deals para atacar agora",
            hover_data=["open_deals", "avg_score", "expected_revenue", "regional_office"],
        )
        team_chart.update_layout(height=450, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(team_chart, use_container_width=True)

    with team_cols[1]:
        region_chart = px.treemap(
            filtered_summary,
            path=[px.Constant("Pipeline"), "regional_office", "manager", "sales_agent"],
            values="expected_revenue",
            color="avg_score",
            color_continuous_scale=["#f59e0b", "#2563eb", "#0f766e"],
            title="Receita esperada por regiao, manager e vendedor",
        )
        region_chart.update_layout(height=450, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(region_chart, use_container_width=True)

    st.dataframe(
        filtered_summary.rename(
            columns={
                "manager": "Manager",
                "regional_office": "Region",
                "sales_agent": "Sales agent",
                "open_deals": "Open deals",
                "avg_score": "Avg score",
                "hot_deals": "Hot deals",
                "focus_deals": "Hot + Focus",
                "expected_revenue": "Expected revenue",
            }
        ),
        hide_index=True,
        use_container_width=True,
        column_config={
            "Avg score": st.column_config.NumberColumn(format="%.1f"),
            "Expected revenue": st.column_config.NumberColumn(format="$%.0f"),
        },
    )

with tab_method:
    st.subheader("Como o score foi montado")
    st.write(
        "O objetivo nao foi prever com machine learning pesado, e sim criar uma priorizacao que o vendedor consiga entender e usar."
    )
    st.write(
        "Cada deal aberto recebe uma estimativa de ganho combinando etapa atual, historico do vendedor, conta, produto, manager, regiao, frescor do deal e potencial financeiro."
    )

    methodology = pd.DataFrame(
        [
            ("Stage", "26%", "Deals em Engaging recebem prioridade maior que Prospecting"),
            ("Sales agent", "18%", "Historico individual do vendedor em deals fechados"),
            ("Account", "14%", "Empresas que historicamente fecham melhor puxam o score para cima"),
            ("Product", "12%", "Alguns produtos convertem melhor no historico"),
            ("Manager", "10%", "Captura disciplina comercial do time"),
            ("Region", "8%", "Ajusta diferencas regionais sem dominar o score"),
            ("Freshness", "7%", "Deals mais recentes sobem; deals envelhecidos caem"),
            ("Value", "5%", "Receita ajuda a desempatar, mas nao domina a priorizacao"),
        ],
        columns=["Componente", "Peso", "Por que importa"],
    )
    st.dataframe(methodology, hide_index=True, use_container_width=True)

    st.markdown("**Tratamento de qualidade do dado**")
    st.write("- Normalizei nomes de produto para resolver o conflito `GTXPro` x `GTX Pro` entre os arquivos.")
    st.write("- Usei smoothing bayesiano nas taxas historicas para evitar supervalorizar amostras pequenas.")
    st.write("- Quando a conta nao existe no CSV de contas, o score continua rodando, mas o deal perde confianca.")
    st.write("- Quando nao ha valor de fechamento no deal aberto, uso o preco de catalogo do produto como aproximacao.")

    st.markdown("**Leitura rapida dos tiers**")
    st.write("- Hot: deals que devem receber atencao imediata")
    st.write("- Focus: boas oportunidades para o ciclo atual")
    st.write("- Watch: monitorar e requalificar")
    st.write("- Low: baixo retorno esperado agora")
