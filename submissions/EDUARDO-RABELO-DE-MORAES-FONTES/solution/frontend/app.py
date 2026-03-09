from __future__ import annotations

import math
import os
from datetime import UTC, date, datetime

import pandas as pd
import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
OPEN_STAGES = {"Prospecting", "Engaging"}

STAGE_LABELS = {
    "Prospecting": "Prospecção",
    "Engaging": "Engajamento",
    "Won": "Ganho",
    "Lost": "Perdido",
}


@st.cache_data(ttl=60)
def fetch_sales_teams() -> pd.DataFrame:
    response = requests.get(
        f"{API_BASE_URL}/sales-teams",
        params={"limit": 1000, "offset": 0},
        timeout=15,
    )
    response.raise_for_status()
    return pd.DataFrame(response.json())


@st.cache_data(ttl=60)
def fetch_opportunities(
    sales_agent: str | None,
    manager: str | None,
    regional_office: str | None,
    deal_stage: str | None,
    product: str | None,
    account: str | None,
) -> pd.DataFrame:
    params: dict[str, str | int] = {"limit": 2000, "offset": 0}
    if sales_agent and sales_agent != "Todos":
        params["sales_agent"] = sales_agent
    if manager and manager != "Todos":
        params["manager"] = manager
    if regional_office and regional_office != "Todas":
        params["regional_office"] = regional_office
    if deal_stage and deal_stage != "Todos":
        params["deal_stage"] = deal_stage
    if product and product != "Todos":
        params["product"] = product
    if account and account != "Todos":
        params["account"] = account

    response = requests.get(f"{API_BASE_URL}/opportunities", params=params, timeout=20)
    response.raise_for_status()
    return pd.DataFrame(response.json())


@st.cache_data(ttl=60)
def fetch_account_scores() -> pd.DataFrame:
    response = requests.get(
        f"{API_BASE_URL}/account-scores",
        params={"limit": 5000, "offset": 0},
        timeout=20,
    )
    response.raise_for_status()
    return pd.DataFrame(response.json())


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def calc_days_in_pipeline(engage_date: str | None) -> int:
    start_date = parse_date(engage_date)
    if not start_date:
        return 999
    return (datetime.now(UTC).date() - start_date).days


def calc_priority_score(row: pd.Series) -> float:
    components = get_score_components(row)
    total = sum(components.values())
    return round(max(0, min(total, 100)), 2)


def get_score_components(row: pd.Series) -> dict[str, float]:
    stage_weight = {
        "Prospecting": 35,
        "Engaging": 55,
        "Won": 0,
        "Lost": 0,
    }
    stage_points = float(stage_weight.get(row.get("deal_stage"), 0))

    deal_value = float(row.get("deal_value") or 0)
    value_points = min(deal_value / 200, 25)

    account_score = float(row.get("account_score") or 35)
    account_points = (account_score / 100) * 20

    days_in_pipeline = int(row.get("days_in_pipeline") or 999)
    urgency_points = 0.0
    if days_in_pipeline > 30:
        urgency_points = 15.0
    elif days_in_pipeline > 14:
        urgency_points = 8.0

    account_penalty = 0.0
    if not row.get("account"):
        account_penalty = -10.0

    product_penalty = 0.0
    if not row.get("product"):
        product_penalty = -8.0

    return {
        "stage_points": stage_points,
        "value_points": value_points,
        "account_history_points": account_points,
        "urgency_points": urgency_points,
        "account_penalty": account_penalty,
        "product_penalty": product_penalty,
    }


def build_reason(row: pd.Series) -> str:
    return "; ".join(build_reason_items(row))


def build_reason_items(row: pd.Series) -> list[str]:
    reasons: list[str] = []

    if row.get("deal_stage") == "Engaging":
        reasons.append("Está no estágio Engaging e pode converter mais rápido")
    if int(row.get("days_in_pipeline") or 0) > 30:
        reasons.append("Está esfriando no pipeline e exige ação imediata")
    if float(row.get("deal_value") or 0) > 3000:
        reasons.append("Tem alto potencial de receita")
    if not row.get("account"):
        reasons.append("Faltam dados da conta, risco operacional")

    account_score = float(row.get("account_score") or 35)
    if account_score >= 70:
        reasons.append("Histórico da conta é forte e favorece priorização")
    elif account_score < 40:
        reasons.append("Histórico da conta é fraco e exige qualificação melhor")

    if not reasons:
        reasons.append("Tem boa combinação de urgência e potencial")

    return reasons


def build_next_action(row: pd.Series) -> str:
    stage = row.get("deal_stage")
    days_in_pipeline = int(row.get("days_in_pipeline") or 999)
    deal_value = float(row.get("deal_value") or 0)
    account_score = float(row.get("account_score") or 35)

    if stage == "Engaging" and days_in_pipeline > 21:
        return "Ligar hoje e garantir reunião de fechamento em até 48h."
    if stage == "Engaging" and deal_value > 3000:
        return "Enviar proposta final hoje e envolver manager para destravar decisão."
    if stage == "Prospecting" and account_score >= 70:
        return "Priorizar contato hoje: conta com bom histórico tende a converter."
    if stage == "Prospecting" and days_in_pipeline > 14:
        return "Fazer follow-up com CTA objetivo para avançar ao Engaging."
    return "Realizar contato hoje e registrar próximo passo com data definida."


def calc_priority_band(score: float) -> str:
    if score >= 55:
        return "Alta"
    if score >= 38:
        return "Média"
    return "Baixa"


def to_stage_label(value: str | None) -> str:
    if not value:
        return "Não informado"
    return STAGE_LABELS.get(value, value)


def format_currency(value: float | None) -> str:
    numeric = float(value) if value is not None else 0.0
    if math.isnan(numeric):
        numeric = 0.0
    return f"USD {numeric:,.0f}"


def resolve_deal_value(row: pd.Series) -> float:
    close_value = float(row.get("close_value") or 0)
    if math.isnan(close_value):
        close_value = 0.0
    if close_value > 0:
        return close_value
    sales_price = float(row.get("sales_price") or 0)
    if math.isnan(sales_price):
        sales_price = 0.0
    return sales_price


def to_safe_int(value: object) -> int:
    if value is None:
        return 0
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0
    if math.isnan(numeric):
        return 0
    return int(numeric)


def get_account_score_components(row: pd.Series) -> dict[str, float]:
    win_rate = float(row.get("win_rate") or 0)
    avg_won_value = float(row.get("avg_won_value") or 0)
    closed_deals = float(row.get("closed_deals") or 0)

    win_rate_points = 45 * max(0, min(win_rate, 1))
    ticket_points = min(avg_won_value / 150, 35)
    volume_points = min(closed_deals, 20)
    total = max(0, min(win_rate_points + ticket_points + volume_points, 100))

    return {
        "win_rate_points": win_rate_points,
        "ticket_points": ticket_points,
        "volume_points": volume_points,
        "account_score_total": total,
    }


def render_style() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap');
        html, body, [class*="css"] {
            font-family: 'Space Grotesk', sans-serif;
            color: #14232b;
        }
        .stApp {
            background: radial-gradient(
                circle at 20% 10%,
                #f2efe6 0%,
                #f7f4ec 30%,
                #f9f8f4 100%
            );
        }
        .stApp [data-testid="stAppViewContainer"] {
            color: #14232b;
        }
        .stApp [data-testid="stAppViewContainer"] .block-container {
            padding-top: 0.6rem !important;
        }
        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
        .stApp p, .stApp li, .stApp label, .stApp span, .stApp small,
        .stApp div {
            color: #14232b;
        }
        .stApp [data-testid="stMetricValue"],
        .stApp [data-testid="stMetricLabel"],
        .stApp [data-testid="stMetricDelta"] {
            color: #14232b;
        }
        .stApp [data-baseweb="select"] > div,
        .stApp [data-testid="stTextInput"] input {
            background-color: #ffffff;
            color: #14232b;
            border: 1px solid #c8d3d7;
        }
        .stApp [data-testid="stDataFrame"] {
            border: 1px solid #dbe4e7;
            border-radius: 10px;
            background: #ffffff;
        }
        .stApp [data-testid="stToolbar"],
        .stApp [data-testid="stAppDeployButton"],
        .stApp [data-testid="stMainMenu"],
        .stApp [data-testid="stToolbarActions"],
        .stApp header {
            display: none !important;
        }
        .hero-card {
            background: #000000;
            color: #f8f5ee;
            border-radius: 14px;
            padding: 1rem 1.2rem;
            margin-bottom: 1rem;
        }
        .hero-card * {
            color: #f8f5ee !important;
        }
        .hero-title {
            font-size: 1.75rem;
            font-weight: 700;
            letter-spacing: 0.2px;
            margin: 0;
        }
        .hero-subtitle {
            margin: 0.4rem 0 0 0;
            font-weight: 500;
            opacity: 0.95;
        }
        .pill {
            display: inline-block;
            padding: 0.2rem 0.65rem;
            border-radius: 999px;
            font-size: 0.85rem;
            margin-right: 0.4rem;
            color: #08333a;
            background-color: #bde8df;
        }
        .stApp [data-testid="stExpander"] {
            border: 1px solid #d8e2e6;
            border-radius: 10px;
            background: #ffffff;
        }
        .stApp [data-testid="stExpander"] details,
        .stApp [data-testid="stExpander"] summary,
        .stApp [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
            background: #ffffff !important;
            color: #14232b !important;
        }
        .stApp [data-testid="stExpander"] summary {
            border-radius: 10px;
            padding: 0.35rem 0.5rem;
        }
        .stApp [data-testid="stExpander"] summary:hover,
        .stApp [data-testid="stExpander"] summary:focus,
        .stApp [data-testid="stExpander"] summary:focus-visible {
            background: #f4f8fa !important;
            color: #14232b !important;
            outline: none;
        }
        .stApp [data-testid="stExpander"] summary svg,
        .stApp [data-testid="stExpander"] summary path {
            fill: #14232b !important;
            stroke: #14232b !important;
            color: #14232b !important;
        }
        .stApp [data-testid="stExpander"] summary,
        .stApp [data-testid="stExpander"] summary p,
        .stApp [data-testid="stExpander"] p,
        .stApp [data-testid="stExpander"] li,
        .stApp [data-testid="stExpander"] span,
        .stApp [data-testid="stExpander"] div {
            color: #14232b !important;
        }
        .stApp [data-testid="stExpander"] code {
            color: #14232b !important;
            background: #edf2f4;
            border-radius: 4px;
            padding: 0.1rem 0.3rem;
        }
        .deal-card {
            background: #ffffff;
            border: 1px solid #d8e2e6;
            border-radius: 12px;
            padding: 0.9rem 1rem;
            margin-bottom: 0.8rem;
            box-shadow: 0 2px 8px rgba(10, 30, 40, 0.05);
        }
        .deal-title {
            margin: 0;
            font-size: 1rem;
            font-weight: 700;
            color: #0f2a36;
        }
        .deal-meta {
            margin: 0.35rem 0 0.5rem 0;
            font-size: 0.9rem;
            color: #29414c;
            line-height: 1.35;
        }
        .deal-tag {
            display: inline-block;
            margin: 0 0.35rem 0.4rem 0;
            padding: 0.15rem 0.55rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 600;
            color: #11313f;
            background: #d8f0ea;
        }
        .deal-why {
            margin: 0.3rem 0 0 0;
            font-size: 0.92rem;
            color: #223943;
        }
        .reason-checklist {
            margin: 0.35rem 0 0 0;
            padding: 0;
        }
        .reason-checklist li {
            list-style: none;
            margin: 0.28rem 0;
            color: #203841;
            font-size: 0.9rem;
            background: #f3faf8;
            border: 1px solid #d3ebe5;
            border-radius: 8px;
            padding: 0.35rem 0.55rem;
        }
        .reason-checklist li::before {
            content: "✓";
            margin-right: 0.4rem;
            color: #1f6f6f;
            font-weight: 700;
        }
        .deal-next {
            margin: 0.45rem 0 0 0;
            font-size: 0.92rem;
            color: #0f2a36;
            font-weight: 600;
        }
        .score-memory {
            margin-top: 0.55rem;
            border-top: 1px dashed #d4e0e5;
            padding-top: 0.45rem;
        }
        .score-memory-title {
            margin: 0;
            font-size: 0.88rem;
            font-weight: 700;
            color: #1a3a46;
        }
        .score-memory-list {
            margin: 0.3rem 0 0 0;
            padding-left: 0;
        }
        .score-memory-list li {
            list-style: none;
            margin: 0.15rem 0;
            font-size: 0.84rem;
            color: #29414c;
        }
        .score-memory-total {
            margin-top: 0.35rem;
            font-size: 0.88rem;
            font-weight: 700;
            color: #0f2a36;
        }
        .account-memory {
            margin-top: 0.55rem;
            border-top: 1px dashed #d4e0e5;
            padding-top: 0.45rem;
        }
        .account-memory-title {
            margin: 0;
            font-size: 0.88rem;
            font-weight: 700;
            color: #1a3a46;
        }
        .account-memory-list {
            margin: 0.3rem 0 0 0;
            padding-left: 0;
        }
        .account-memory-list li {
            list-style: none;
            margin: 0.15rem 0;
            font-size: 0.84rem;
            color: #29414c;
        }
        .account-memory-total {
            margin-top: 0.35rem;
            font-size: 0.88rem;
            font-weight: 700;
            color: #0f2a36;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="G4 Sales: Priority Desk", layout="wide")
    render_style()

    st.markdown(
        """
        <div class="hero-card">
            <h1 class="hero-title">G4 Sales: Priority Desk</h1>
            <p class="hero-subtitle">
                Abra o pipeline e saiba onde focar hoje.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Como o score do deal funciona", expanded=False):
        st.markdown(
            """
            - Base por estágio: `Prospecção = 35`, `Engajamento = 55`
            - Valor potencial: até `+25` pontos
            - Regra de valor: usa `close_value` quando existe; senão `sales_price`
            - Histórico da conta: até `+20` pontos (score histórico de Won/Lost)
            - Urgência por tempo no pipeline: `+8` ou `+15`
            - Penalidades: dados faltantes de conta/produto
            - Escala final: `0 a 100`
            """
        )

    with st.expander("Como o score da conta funciona", expanded=False):
        st.markdown(
            """
            - Considera apenas histórico fechado da conta (`Won` e `Lost`)
            - Componentes do score da conta:
            - `Win rate` histórico
            - `Ticket médio` dos deals ganhos
            - `Volume de histórico` (quantidade de deals fechados)
            - Escala final do score da conta: `0 a 100`
            - Se a conta não tem histórico suficiente, usamos valor padrão
            - Assim, o deal não é punido injustamente
            """
        )

    teams_df = fetch_sales_teams()
    agent_options = ["Todos"]
    manager_options = ["Todos"]
    region_options = ["Todas"]
    if not teams_df.empty and "sales_agent" in teams_df:
        agent_options.extend(sorted(teams_df["sales_agent"].dropna().unique().tolist()))
    if not teams_df.empty and "manager" in teams_df:
        manager_options.extend(sorted(teams_df["manager"].dropna().unique().tolist()))
    if not teams_df.empty and "regional_office" in teams_df:
        region_options.extend(
            sorted(teams_df["regional_office"].dropna().unique().tolist())
        )

    (
        filter_col_1,
        filter_col_2,
        filter_col_3,
        filter_col_4,
        filter_col_5,
        filter_col_6,
    ) = st.columns(6)
    with filter_col_1:
        selected_agent = st.selectbox("Vendedor", options=agent_options)
    with filter_col_2:
        selected_manager = st.selectbox("Manager", options=manager_options)
    with filter_col_3:
        selected_region = st.selectbox("Região", options=region_options)
    with filter_col_4:
        selected_stage = st.selectbox(
            "Estágio",
            options=["Todos", "Prospecting", "Engaging", "Won", "Lost"],
        )
    with filter_col_5:
        selected_product = st.text_input("Produto (opcional)", value="")
    with filter_col_6:
        selected_account = st.text_input("Conta (opcional)", value="")

    score_filter_col_1, score_filter_col_2 = st.columns(2)
    with score_filter_col_1:
        opportunity_score_range = st.slider(
            "Score da Oportunidade (mín. e máx.)",
            min_value=0,
            max_value=100,
            value=(0, 100),
            step=1,
        )
    with score_filter_col_2:
        account_score_range = st.slider(
            "Score da Conta (mín. e máx.)",
            min_value=0,
            max_value=100,
            value=(0, 100),
            step=1,
        )

    opportunities_df = fetch_opportunities(
        sales_agent=selected_agent,
        manager=selected_manager,
        regional_office=selected_region,
        deal_stage=selected_stage,
        product=selected_product if selected_product else None,
        account=selected_account if selected_account else None,
    )

    if opportunities_df.empty:
        st.warning("Nenhuma oportunidade encontrada para os filtros escolhidos.")
        return

    df = opportunities_df.copy()
    df = df[df["deal_stage"].isin(OPEN_STAGES)].copy()

    if df.empty:
        st.info("Não há deals abertos (Prospecting/Engaging) para os filtros atuais.")
        return

    account_scores_df = fetch_account_scores()
    if not account_scores_df.empty:
        score_cols = [
            "account",
            "account_score",
            "win_rate",
            "closed_deals",
            "avg_won_value",
        ]
        df = df.merge(account_scores_df[score_cols], on="account", how="left")
    else:
        df["account_score"] = None
        df["win_rate"] = None
        df["closed_deals"] = None
        df["avg_won_value"] = None

    df["account_score"] = df["account_score"].fillna(35)

    df["days_in_pipeline"] = df["engage_date"].apply(calc_days_in_pipeline)
    df["deal_value"] = df.apply(resolve_deal_value, axis=1)
    df["priority_score"] = df.apply(calc_priority_score, axis=1)
    df["priority_band"] = df["priority_score"].apply(calc_priority_band)
    df["deal_stage_label"] = df["deal_stage"].apply(to_stage_label)
    df["why"] = df.apply(build_reason, axis=1)
    df["next_action"] = df.apply(build_next_action, axis=1)

    df = df[
        (df["priority_score"] >= float(opportunity_score_range[0]))
        & (df["priority_score"] <= float(opportunity_score_range[1]))
        & (df["account_score"] >= float(account_score_range[0]))
        & (df["account_score"] <= float(account_score_range[1]))
    ].copy()

    if df.empty:
        st.info(
            "Nenhum deal atende aos filtros de score selecionados."
            " Ajuste os intervalos mínimo e máximo para ver mais resultados."
        )
        return

    ranked_df = df.sort_values("priority_score", ascending=False).head(12)

    kpi_col_1, kpi_col_2, kpi_col_3 = st.columns(3)
    kpi_col_1.metric("Deals abertos", f"{len(df)}")
    kpi_col_2.metric(
        "Valor potencial aberto",
        f"USD {df['deal_value'].fillna(0).sum():,.0f}",
    )
    kpi_col_3.metric(
        "Deals alta prioridade",
        f"{(df['priority_band'] == 'Alta').sum()}",
    )

    st.subheader("Por que esses deals?")
    for _, row in ranked_df.iterrows():
        opportunity_id = row["opportunity_id"]
        sales_agent = row["sales_agent"]
        deal_stage = to_stage_label(row["deal_stage"])
        priority_band = row["priority_band"]
        priority_score = row["priority_score"]
        close_value = format_currency(row["close_value"])
        potential_value = format_currency(row["deal_value"])
        account_score = round(float(row["account_score"] or 0), 1)
        win_rate = float(row.get("win_rate") or 0)
        closed_deals = to_safe_int(row.get("closed_deals"))
        avg_won_value = float(row.get("avg_won_value") or 0)
        reasons = build_reason_items(row)
        reasons_html = "".join(f"<li>{reason}</li>" for reason in reasons)
        next_action = row["next_action"]
        components = get_score_components(row)
        component_labels = {
            "stage_points": "Estágio",
            "value_points": "Valor potencial",
            "account_history_points": "Histórico da conta",
            "urgency_points": "Urgência (tempo no pipeline)",
            "account_penalty": "Penalidade por conta ausente",
            "product_penalty": "Penalidade por produto ausente",
        }
        memory_rows = []
        for key, label in component_labels.items():
            points = float(components[key])
            sign = "+" if points >= 0 else ""
            memory_rows.append(f"<li>{label}: <strong>{sign}{points:.1f}</strong></li>")
        memory_html = "".join(memory_rows)

        account_components = get_account_score_components(row)
        account_memory_html = "".join(
            [
                "<li>Win rate histórico: "
                f"<strong>+{account_components['win_rate_points']:.1f}</strong></li>",
                "<li>Ticket médio ganho: "
                f"<strong>+{account_components['ticket_points']:.1f}</strong></li>",
                "<li>Volume de deals fechados: "
                f"<strong>+{account_components['volume_points']:.1f}</strong></li>",
                f"<li>Win rate atual da conta: <strong>{win_rate:.0%}</strong></li>",
                "<li>Ticket médio atual da conta: "
                f"<strong>{format_currency(avg_won_value)}</strong></li>",
                "<li>Deals fechados no histórico: "
                f"<strong>{closed_deals}</strong></li>",
            ]
        )
        account_label = row["account"] or "Conta não informada"
        product_label = row["product"] or "Produto não informado"
        days_label = f"{int(row['days_in_pipeline'])} dias"
        st.markdown(
            f"""
            <div class="deal-card">
                <p class="deal-title">Deal {opportunity_id} - {account_label}</p>
                <p class="deal-meta">
                    Vendedor: <strong>{sales_agent}</strong><br>
                    Produto: <strong>{product_label}</strong>
                </p>
                <span class="deal-tag">Estágio: {deal_stage}</span>
                <span class="deal-tag">Prioridade: {priority_band}</span>
                <span class="deal-tag">Score: {priority_score}</span>
                <span class="deal-tag">Score da conta: {account_score}</span>
                <span class="deal-tag">Win rate conta: {win_rate:.0%}</span>
                <span class="deal-tag">Histórico conta: {closed_deals} deals</span>
                <span class="deal-tag">Dias no pipeline: {days_label}</span>
                <span class="deal-tag">Valor fechado: {close_value}</span>
                <span class="deal-tag">Valor potencial: {potential_value}</span>
                <p class="deal-why"><strong>Por quê:</strong></p>
                <ul class="reason-checklist">{reasons_html}</ul>
                <p class="deal-next"><strong>Próxima ação:</strong> {next_action}</p>
                <div class="score-memory">
                    <p class="score-memory-title">Memória do cálculo do score</p>
                    <ul class="score-memory-list">{memory_html}</ul>
                    <p class="score-memory-total">Score final: {priority_score:.1f}</p>
                </div>
                <div class="account-memory">
                    <p class="account-memory-title">Memória do cálculo da conta</p>
                    <ul class="account-memory-list">{account_memory_html}</ul>
                    <p class="account-memory-total">
                        Score da conta: {account_score:.1f}
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.subheader("Quais deals atacar hoje?")
    table_df = ranked_df[
        [
            "opportunity_id",
            "sales_agent",
            "account",
            "product",
            "deal_stage_label",
            "days_in_pipeline",
            "priority_band",
            "priority_score",
            "account_score",
            "deal_value",
        ]
    ].rename(
        columns={
            "opportunity_id": "Deal",
            "sales_agent": "Vendedor",
            "account": "Conta",
            "product": "Produto",
            "deal_stage_label": "Estágio",
            "days_in_pipeline": "Dias no pipeline",
            "priority_band": "Prioridade",
            "priority_score": "Score",
            "account_score": "Score da conta",
            "deal_value": "Valor potencial",
        }
    )
    st.dataframe(table_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
