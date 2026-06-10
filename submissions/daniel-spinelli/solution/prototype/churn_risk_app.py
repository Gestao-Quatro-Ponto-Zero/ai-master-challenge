"""
RavenStack Churn Risk Analyzer
Protótipo operacional para priorização de contas em risco.
"""

import pandas as pd
import streamlit as st
import io

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="RavenStack Churn Risk Analyzer",
    page_icon="🦅",
    layout="wide",
)

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    """Carrega e processa todos os CSVs da pasta data/."""
    try:
        accounts = pd.read_csv("data/ravenstack_accounts.csv")
    except FileNotFoundError:
        st.error("Arquivo não encontrado: data/ravenstack_accounts.csv")
        st.stop()

    try:
        subscriptions = pd.read_csv("data/ravenstack_subscriptions.csv")
    except FileNotFoundError:
        subscriptions = pd.DataFrame()

    try:
        feature_usage = pd.read_csv("data/ravenstack_feature_usage.csv")
    except FileNotFoundError:
        feature_usage = pd.DataFrame()

    try:
        support_tickets = pd.read_csv("data/ravenstack_support_tickets.csv")
    except FileNotFoundError:
        support_tickets = pd.DataFrame()

    try:
        churn_events = pd.read_csv("data/ravenstack_churn_events.csv")
    except FileNotFoundError:
        churn_events = pd.DataFrame()

    return accounts, subscriptions, feature_usage, support_tickets, churn_events


# ─────────────────────────────────────────────
# BUILD ENRICHED ACCOUNT TABLE
# ─────────────────────────────────────────────
def build_account_features(accounts, subscriptions, feature_usage, support_tickets, churn_events):
    """
    Junta todas as fontes de dados em uma tabela por conta,
    mantendo apenas contas ativas (sem churn).
    """
    df = accounts.copy()

    # Normaliza colunas esperadas com fallback
    for col in ["account_id", "account_name", "industry", "country", "referral_source", "plan_tier"]:
        if col not in df.columns:
            df[col] = "unknown"

    # ── Subscriptions: MRR e is_trial ──────────────────────────────────
    if not subscriptions.empty and "account_id" in subscriptions.columns:
        sub = subscriptions.copy()

        # Filtra somente contas ativas (sem churn)
        churned_ids = set()
        if not churn_events.empty and "account_id" in churn_events.columns:
            churned_ids = set(churn_events["account_id"].dropna().unique())

        sub_active = sub[~sub["account_id"].isin(churned_ids)] if churned_ids else sub

        # MRR: soma por conta
        if "mrr_amount" in sub_active.columns:
            mrr = sub_active.groupby("account_id")["mrr_amount"].sum().reset_index()
            df = df.merge(mrr, on="account_id", how="left")
        else:
            df["mrr_amount"] = 0

        # is_trial: se qualquer assinatura for trial
        if "is_trial" in sub_active.columns:
            trial = sub_active.groupby("account_id")["is_trial"].max().reset_index()
            trial["is_trial"] = trial["is_trial"].fillna(False).astype(bool)
            df = df.merge(trial, on="account_id", how="left")
        else:
            df["is_trial"] = False
    else:
        df["mrr_amount"] = 0
        df["is_trial"] = False

    df["mrr_amount"] = pd.to_numeric(df["mrr_amount"], errors="coerce").fillna(0)
    df["is_trial"] = df["is_trial"].fillna(False).astype(bool)

    # ── Feature Usage ──────────────────────────────────────────────────
    if not feature_usage.empty and "account_id" in feature_usage.columns:
        usage_cols = {}
        if "event_id" in feature_usage.columns or "feature_name" in feature_usage.columns:
            usage_cols["usage_count"] = feature_usage.groupby("account_id").size()
        if "feature_name" in feature_usage.columns:
            usage_cols["unique_features_used"] = feature_usage.groupby("account_id")["feature_name"].nunique()

        if usage_cols:
            usage_df = pd.DataFrame(usage_cols).reset_index()
            df = df.merge(usage_df, on="account_id", how="left")
        else:
            df["usage_count"] = 0
            df["unique_features_used"] = 0
    else:
        df["usage_count"] = 0
        df["unique_features_used"] = 0

    df["usage_count"] = pd.to_numeric(df["usage_count"], errors="coerce").fillna(0)
    df["unique_features_used"] = pd.to_numeric(df["unique_features_used"], errors="coerce").fillna(0)

    # ── Support Tickets ────────────────────────────────────────────────
    if not support_tickets.empty and "account_id" in support_tickets.columns:
        tkt = support_tickets.copy()

        ticket_agg = {"tickets": tkt.groupby("account_id").size()}

        if "is_escalated" in tkt.columns:
            ticket_agg["escalations"] = tkt[tkt["is_escalated"].fillna(False).astype(bool)].groupby("account_id").size()
        elif "escalated" in tkt.columns:
            ticket_agg["escalations"] = tkt[tkt["escalated"].fillna(False).astype(bool)].groupby("account_id").size()

        if "satisfaction_score" in tkt.columns:
            ticket_agg["avg_satisfaction"] = tkt.groupby("account_id")["satisfaction_score"].mean()

        tkt_df = pd.DataFrame(ticket_agg).reset_index()
        df = df.merge(tkt_df, on="account_id", how="left")
    else:
        df["tickets"] = 0
        df["escalations"] = 0
        df["avg_satisfaction"] = None

    df["tickets"] = pd.to_numeric(df["tickets"], errors="coerce").fillna(0)
    df["escalations"] = pd.to_numeric(df["escalations"], errors="coerce").fillna(0)

    # ── Remove contas que já deram churn ──────────────────────────────
    if not churn_events.empty and "account_id" in churn_events.columns:
        churned_ids = set(churn_events["account_id"].dropna().unique())
        df = df[~df["account_id"].isin(churned_ids)].copy()

    return df


# ─────────────────────────────────────────────
# SCORING ENGINE
# ─────────────────────────────────────────────
def compute_risk_score(row, mrr_p75, features_median):
    """
    Calcula o risk_score (0–100) e retorna os principais drivers.
    Lógica baseada em heurística explicável, derivada da análise de churn.
    """
    score = 20  # base
    drivers = []

    industry = str(row.get("industry", "")).strip()
    referral = str(row.get("referral_source", "")).strip()
    country = str(row.get("country", "")).strip()
    mrr = float(row.get("mrr_amount", 0) or 0)
    is_trial = bool(row.get("is_trial", False))
    features_used = float(row.get("unique_features_used", 0) or 0)
    escalations = float(row.get("escalations", 0) or 0)

    # Industry
    if industry == "DevTools":
        score += 20
        drivers.append("DevTools")
    elif industry == "FinTech":
        score += 12
        drivers.append("FinTech")

    # Referral source
    if referral == "event":
        score += 20
        drivers.append("Event channel")
    elif referral == "ads":
        score += 10
        drivers.append("Ads channel")
    elif referral == "partner":
        score -= 10

    # Country
    if country == "US":
        score += 10
        drivers.append("US")
    elif country == "DE":
        score += 8
        drivers.append("DE")

    # Trial
    if is_trial:
        score += 8
        drivers.append("Trial account")

    # Feature usage below median → higher risk? (inverse: acima da mediana = menos risco)
    # O prompt pede +5 se ACIMA da mediana (o modelo preditivo achou essa var importante)
    if features_used > features_median:
        score += 5
        drivers.append("High feature usage")

    # Escalations
    if escalations > 0:
        score += 8
        drivers.append("Escalated tickets")

    # High MRR (financial priority, não churn direto)
    if mrr >= mrr_p75:
        score += 10
        drivers.append("High MRR")

    # Clamp 0–100
    score = max(0, min(100, score))
    return score, drivers


def risk_level(score):
    if score >= 80:
        return "Critical"
    elif score >= 60:
        return "High"
    elif score >= 40:
        return "Medium"
    return "Low"


# ─────────────────────────────────────────────
# RECOMMENDATIONS
# ─────────────────────────────────────────────
RECOMMENDATIONS = {
    "DevTools": "Conduzir conversa de produto focada em missing features, roadmap e comparação competitiva.",
    "FinTech": "Priorizar playbook de retenção por impacto financeiro. Envolver CS sênior e liderança comercial.",
    "Event channel": "Revisar fit de aquisição e qualificação do lead. Agendar check-in de valor nos primeiros 30 dias.",
    "Trial account": "Ativar onboarding dedicado e demonstrar valor concreto antes do fim do trial.",
    "High MRR": "Conta de alto impacto financeiro. Criar plano de retenção individual.",
    "US": "Investigar padrões regionais de churn e comparação competitiva local (mercado US).",
    "DE": "Investigar padrões regionais de churn e comparação competitiva local (mercado DE).",
    "Escalated tickets": "Revisar histórico de suporte escalado antes da próxima renovação.",
    "Ads channel": "Avaliar qualidade do lead e expectativas de produto. Revisar fit.",
    "High feature usage": "Conta engajada — verificar se há gaps de valor não atendidos ou interesse em upgrade.",
}

DEFAULT_REC = "Agendar QBR ou check-in de saúde da conta. Avaliar satisfação e próximo passo no ciclo de renovação."


def build_recommendation(drivers):
    recs = []
    for d in drivers:
        if d in RECOMMENDATIONS:
            recs.append(RECOMMENDATIONS[d])
    if not recs:
        return DEFAULT_REC
    return " | ".join(recs)


# ─────────────────────────────────────────────
# LEVEL BADGE COLORS
# ─────────────────────────────────────────────
LEVEL_COLOR = {
    "Critical": "🔴",
    "High": "🟠",
    "Medium": "🟡",
    "Low": "🟢",
}


# ─────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────
def main():
    st.title("🦅 RavenStack Churn Risk Analyzer")
    st.caption("Priorização operacional de contas em risco · Challenge 001")

    # ── Load ──────────────────────────────────────────────────────────
    with st.spinner("Carregando dados..."):
        accounts, subscriptions, feature_usage, support_tickets, churn_events = load_data()
        df = build_account_features(accounts, subscriptions, feature_usage, support_tickets, churn_events)

    if df.empty:
        st.error("Nenhuma conta ativa encontrada.")
        st.stop()

    # ── Compute percentiles ──────────────────────────────────────────
    mrr_p75 = df["mrr_amount"].quantile(0.75) if df["mrr_amount"].sum() > 0 else 0
    features_median = df["unique_features_used"].median() if df["unique_features_used"].sum() > 0 else 0

    # ── Score all accounts ────────────────────────────────────────────
    results = []
    for _, row in df.iterrows():
        score, drivers = compute_risk_score(row, mrr_p75, features_median)
        level = risk_level(score)
        rec = build_recommendation(drivers)
        results.append({
            "account_id": row.get("account_id", ""),
            "account_name": row.get("account_name", row.get("account_id", "")),
            "industry": row.get("industry", ""),
            "country": row.get("country", ""),
            "referral_source": row.get("referral_source", ""),
            "plan_tier": row.get("plan_tier", ""),
            "mrr_amount": round(float(row.get("mrr_amount", 0) or 0), 2),
            "risk_score": score,
            "risk_level": level,
            "risk_drivers": ", ".join(drivers) if drivers else "—",
            "recommendation": rec,
            # Detail fields
            "usage_count": int(row.get("usage_count", 0) or 0),
            "unique_features_used": int(row.get("unique_features_used", 0) or 0),
            "tickets": int(row.get("tickets", 0) or 0),
            "escalations": int(row.get("escalations", 0) or 0),
            "avg_satisfaction": row.get("avg_satisfaction", None),
            "is_trial": bool(row.get("is_trial", False)),
        })

    scored = pd.DataFrame(results)
    scored = scored.sort_values(["risk_score", "mrr_amount"], ascending=[False, False]).reset_index(drop=True)

    # ── Sidebar Filters ───────────────────────────────────────────────
    st.sidebar.header("Filtros")

    def multiselect_filter(label, col):
        opts = sorted(scored[col].dropna().unique().tolist())
        return st.sidebar.multiselect(label, opts, default=[])

    f_industry = multiselect_filter("Industry", "industry")
    f_referral = multiselect_filter("Referral Source", "referral_source")
    f_country = multiselect_filter("Country", "country")
    f_plan = multiselect_filter("Plan Tier", "plan_tier")
    f_level = st.sidebar.multiselect(
        "Risk Level",
        ["Critical", "High", "Medium", "Low"],
        default=[],
    )

    filtered = scored.copy()
    if f_industry:
        filtered = filtered[filtered["industry"].isin(f_industry)]
    if f_referral:
        filtered = filtered[filtered["referral_source"].isin(f_referral)]
    if f_country:
        filtered = filtered[filtered["country"].isin(f_country)]
    if f_plan:
        filtered = filtered[filtered["plan_tier"].isin(f_plan)]
    if f_level:
        filtered = filtered[filtered["risk_level"].isin(f_level)]

    # ── Executive Summary ─────────────────────────────────────────────
    high_critical = filtered[filtered["risk_level"].isin(["High", "Critical"])]
    mrr_at_risk = high_critical["mrr_amount"].sum()

    # Top 3 drivers
    all_drivers = []
    for d in filtered["risk_drivers"]:
        if d and d != "—":
            all_drivers.extend([x.strip() for x in d.split(",")])
    driver_counts = pd.Series(all_drivers).value_counts()
    top_drivers = driver_counts.head(3).index.tolist()

    st.subheader("Resumo Executivo")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Contas ativas analisadas", len(filtered))
    c2.metric("High / Critical", len(high_critical))
    c3.metric("MRR em risco (High+Critical)", f"${mrr_at_risk:,.0f}")
    c4.metric("Top driver", top_drivers[0] if top_drivers else "—")

    if top_drivers:
        st.caption(f"**Top 3 drivers:** {' · '.join(top_drivers)}")

    st.divider()

    # ── Main Table ────────────────────────────────────────────────────
    st.subheader(f"Contas priorizadas por risco ({len(filtered)} contas)")

    display_cols = [
        "risk_level", "risk_score", "account_name", "industry",
        "country", "referral_source", "plan_tier", "mrr_amount", "risk_drivers",
    ]
    display_cols = [c for c in display_cols if c in filtered.columns]

    # Add emoji to risk level for readability
    show_df = filtered[display_cols].copy()
    show_df["risk_level"] = show_df["risk_level"].apply(lambda x: f"{LEVEL_COLOR.get(x, '')} {x}")

    st.dataframe(
        show_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "risk_score": st.column_config.ProgressColumn(
                "Risk Score", min_value=0, max_value=100, format="%d"
            ),
            "mrr_amount": st.column_config.NumberColumn("MRR (USD)", format="$%.0f"),
        },
    )

    # ── Account Detail ────────────────────────────────────────────────
    st.divider()
    st.subheader("Detalhe da conta")

    account_options = filtered["account_name"].fillna(filtered["account_id"]).tolist()
    if account_options:
        selected_name = st.selectbox("Selecione uma conta para detalhar:", account_options)
        sel = filtered[filtered["account_name"] == selected_name].iloc[0]

        d1, d2 = st.columns([1, 2])
        with d1:
            level = sel["risk_level"]
            st.markdown(f"### {LEVEL_COLOR.get(level, '')} {sel['account_name']}")
            st.markdown(f"**Risk Score:** `{sel['risk_score']}/100` — **{level}**")
            st.markdown(f"**Industry:** {sel['industry']}  |  **Country:** {sel['country']}")
            st.markdown(f"**Referral:** {sel['referral_source']}  |  **Plan:** {sel['plan_tier']}")
            st.markdown(f"**MRR:** ${sel['mrr_amount']:,.2f}")
            st.markdown(f"**Trial:** {'Sim' if sel['is_trial'] else 'Não'}")

        with d2:
            st.markdown("**Risk Drivers**")
            st.info(sel["risk_drivers"])
            st.markdown("**Recomendação de ação**")
            st.success(sel["recommendation"])

        # Usage & support summary
        st.markdown("**Histórico resumido**")
        h1, h2, h3, h4, h5 = st.columns(5)
        h1.metric("Eventos de uso", int(sel["usage_count"]))
        h2.metric("Features únicas", int(sel["unique_features_used"]))
        h3.metric("Tickets", int(sel["tickets"]))
        h4.metric("Escalations", int(sel["escalations"]))
        avg_sat = sel.get("avg_satisfaction")
        h5.metric("Satisfação média", f"{avg_sat:.1f}" if pd.notna(avg_sat) else "N/A")

    # ── Export ────────────────────────────────────────────────────────
    st.divider()
    export_cols = [
        "account_id", "account_name", "industry", "country", "referral_source",
        "plan_tier", "mrr_amount", "risk_score", "risk_level", "risk_drivers", "recommendation",
    ]
    export_df = filtered[[c for c in export_cols if c in filtered.columns]]

    csv_buffer = io.StringIO()
    export_df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="⬇️ Download prioritized accounts CSV",
        data=csv_buffer.getvalue(),
        file_name="churn_risk_prioritized.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
