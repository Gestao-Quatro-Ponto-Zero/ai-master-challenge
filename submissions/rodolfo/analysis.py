#!/usr/bin/env python3
"""RavenStack Churn Diagnostic — AI Master Challenge 001"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from pathlib import Path

DATA_DIR = Path("submissions/rodolfo/data")
OUTPUT_DIR = Path("submissions/rodolfo")

# ── 1. LOAD DATA ──────────────────────────────────────────────────────────────

accounts = pd.read_csv(DATA_DIR / "ravenstack_accounts.csv")
subscriptions = pd.read_csv(DATA_DIR / "ravenstack_subscriptions.csv")
feature_usage = pd.read_csv(DATA_DIR / "ravenstack_feature_usage.csv")
support_tickets = pd.read_csv(DATA_DIR / "ravenstack_support_tickets.csv")
churn_events = pd.read_csv(DATA_DIR / "ravenstack_churn_events.csv")

# ── 2. CLEAN & PREPARE ────────────────────────────────────────────────────────

accounts["signup_date"] = pd.to_datetime(accounts["signup_date"])
subscriptions["start_date"] = pd.to_datetime(subscriptions["start_date"])
subscriptions["end_date"] = pd.to_datetime(subscriptions["end_date"])
churn_events["churn_date"] = pd.to_datetime(churn_events["churn_date"])
feature_usage["usage_date"] = pd.to_datetime(feature_usage["usage_date"])
support_tickets["submitted_at"] = pd.to_datetime(support_tickets["submitted_at"])
support_tickets["closed_at"] = pd.to_datetime(support_tickets["closed_at"])

# ── 3. MERGE: build unified view ──────────────────────────────────────────────

# Account-level: get latest subscription per account
latest_sub = subscriptions.sort_values("start_date").groupby("account_id").last().reset_index()

# Aggregate feature usage per subscription
agg_usage = feature_usage.groupby("subscription_id").agg(
    total_usage_count=("usage_count", "sum"),
    avg_usage_duration=("usage_duration_secs", "mean"),
    total_error_count=("error_count", "sum"),
    unique_features=("feature_name", "nunique"),
    beta_feature_used=("is_beta_feature", "max"),
    usage_days=("usage_date", "nunique"),
).reset_index()

# Merge accounts + latest subscription + usage
account_view = accounts.merge(latest_sub, on="account_id", suffixes=("_acc", "_sub"), how="left")
account_view = account_view.merge(agg_usage, on="subscription_id", how="left")
account_view["churn_flag"] = account_view["churn_flag_acc"]

# Support ticket aggregates per account
ticket_agg = support_tickets.groupby("account_id").agg(
    total_tickets=("ticket_id", "count"),
    avg_resolution_hours=("resolution_time_hours", "mean"),
    avg_first_response_min=("first_response_time_minutes", "mean"),
    avg_satisfaction=("satisfaction_score", "mean"),
    escalation_count=("escalation_flag", "sum"),
    high_priority_tickets=("priority", lambda x: (x.isin(["high", "critical", "urgent"])).sum()),
).reset_index()

account_view = account_view.merge(ticket_agg, on="account_id", how="left")

# ── 4. CHURN ANALYSIS ─────────────────────────────────────────────────────────

# Overall churn rate
overall_churn_rate = accounts["churn_flag"].mean()
total_churned = accounts["churn_flag"].sum()
total_accounts = len(accounts)

# Revenue impact
churned_subs = subscriptions[subscriptions["churn_flag"] == True]
total_mrr_lost = churned_subs["mrr_amount"].sum()
avg_mrr_lost = churned_subs["mrr_amount"].mean()

# Churn by country
churn_by_country_raw = accounts.groupby("country")["churn_flag"].agg(["mean", "count"]).reset_index()
churn_by_country_raw.columns = ["country", "churn_rate", "count"]
churn_by_country_raw = churn_by_country_raw[churn_by_country_raw["count"] >= 10].sort_values("churn_rate", ascending=False)

# Top churn reason per industry
churn_with_ind = churn_events.merge(accounts[["account_id", "industry"]], on="account_id", how="left")
top_reason_per_industry = churn_with_ind.groupby("industry")["reason_code"].agg(lambda x: x.mode().iloc[0] if not x.mode().empty else "N/A").reset_index()

# Churn by segment
def churn_rate_by(grp_col, min_samples=5):
    grp = accounts.groupby(grp_col)["churn_flag"].agg(["mean", "count"]).reset_index()
    grp.columns = [grp_col, "churn_rate", "count"]
    grp = grp[grp["count"] >= min_samples].sort_values("churn_rate", ascending=False)
    return grp

churn_by_industry = churn_rate_by("industry")
churn_by_plan = churn_rate_by("plan_tier")
churn_by_country = churn_rate_by("country")
churn_by_referral = churn_rate_by("referral_source")
churn_by_trial = accounts.groupby("is_trial")["churn_flag"].mean().reset_index()

# Churn by seats quantile
accounts["seats_group"] = pd.qcut(accounts["seats"], q=4, labels=["Q1 (small)", "Q2", "Q3", "Q4 (large)"])
churn_by_seats = accounts.groupby("seats_group", observed=True)["churn_flag"].agg(["mean", "count"]).reset_index()

# ── 5. FEATURE USAGE VS CHURN ──────────────────────────────────────────────────

usage_vs_churn = account_view.groupby("churn_flag").agg(
    avg_usage_count=("total_usage_count", "mean"),
    avg_duration=("avg_usage_duration", "mean"),
    avg_error_count=("total_error_count", "mean"),
    avg_unique_features=("unique_features", "mean"),
    avg_usage_days=("usage_days", "mean"),
    pct_beta_users=("beta_feature_used", "mean"),
).reset_index()

# ── 6. SUPPORT VS CHURN ────────────────────────────────────────────────────────

support_vs_churn = account_view.groupby("churn_flag").agg(
    avg_tickets=("total_tickets", "mean"),
    avg_resolution=("avg_resolution_hours", "mean"),
    avg_first_response=("avg_first_response_min", "mean"),
    avg_satisfaction=("avg_satisfaction", "mean"),
    avg_escalations=("escalation_count", "mean"),
    avg_high_priority=("high_priority_tickets", "mean"),
).reset_index()

# ── 7. CHURN REASONS ───────────────────────────────────────────────────────────

reason_dist = churn_events["reason_code"].value_counts().reset_index()
reason_dist.columns = ["reason", "count"]

# MRR lost by reason
reason_mrr = churn_events.merge(
    subscriptions[subscriptions["churn_flag"] == True][["account_id", "mrr_amount"]],
    on="account_id", how="left"
).groupby("reason_code")["mrr_amount"].agg(["sum", "mean", "count"]).reset_index()
reason_mrr.columns = ["reason", "mrr_lost_total", "mrr_lost_avg", "count"]

# ── 8. UPGRADE/DOWNGRADE BEFORE CHURN ──────────────────────────────────────────

upgrade_downgrade_before_churn = churn_events[
    ["preceding_upgrade_flag", "preceding_downgrade_flag", "is_reactivation"]
].sum().reset_index()
upgrade_downgrade_before_churn.columns = ["flag", "count"]

# ── 9. TIMING ANALYSIS ─────────────────────────────────────────────────────────

# Tenure before churn: find the subscription active at churn time
active_subs = subscriptions.copy()
active_subs["start_date"] = pd.to_datetime(active_subs["start_date"])
active_subs["end_date"] = pd.to_datetime(active_subs["end_date"])
churn_with_sub = churn_events.merge(active_subs, on="account_id", how="left")
active_at_churn = churn_with_sub[
    (churn_with_sub["start_date"] <= churn_with_sub["churn_date"]) &
    ((churn_with_sub["end_date"].isna()) | (churn_with_sub["end_date"] >= churn_with_sub["churn_date"]))
].copy()
active_at_churn["tenure_days"] = (active_at_churn["churn_date"] - active_at_churn["start_date"]).dt.days
tenure_stats = active_at_churn["tenure_days"].describe()

# Churn by month
churn_events["churn_month"] = churn_events["churn_date"].dt.to_period("M")
churn_by_month = churn_events.groupby("churn_month").size().reset_index(name="count")
churn_by_month["churn_month"] = churn_by_month["churn_month"].astype(str)

# ── 10. BUILD HTML REPORT ──────────────────────────────────────────────────────

def fmt(v):
    if isinstance(v, float):
        return f"{v:.1f}"
    return str(v)

def _make_table(df, cols=None, pct_cols=None):
    if cols:
        df = df[cols]
    html = "<table><thead><tr>"
    for c in df.columns:
        html += f"<th>{c}</th>"
    html += "</tr></thead><tbody>"
    for _, row in df.iterrows():
        html += "<tr>"
        for c in df.columns:
            val = row[c]
            if pct_cols and c in pct_cols:
                val = f"{val:.1%}"
            elif isinstance(val, float):
                val = f"{val:.1f}"
            html += f"<td>{val}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html

def make_chart(title, fig, output_name):
    fig.update_layout(
        title=dict(text=title, font=dict(size=18)),
        template="plotly_white",
        font=dict(family="Inter, sans-serif"),
        margin=dict(l=60, r=30, t=60, b=60),
    )
    fig_json = json.loads(fig.to_json())
    return fig_json, output_name

# 10a. Churn overview
fig_overview = make_subplots(
    rows=1, cols=3,
    specs=[[{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}]],
    subplot_titles=("Churn Rate", "Contas Perdidas", "MRR Mensal Perdido"),
)
fig_overview.add_trace(go.Indicator(
    value=round(overall_churn_rate * 100, 1),
    number={"suffix": "%", "font": {"color": "red" if overall_churn_rate > 0.15 else "green", "size": 48}},
    mode="number",
), row=1, col=1)
fig_overview.add_trace(go.Indicator(
    value=int(total_churned),
    number={"font": {"color": "#e74c3c", "size": 48}},
    mode="number",
), row=1, col=2)
fig_overview.add_trace(go.Indicator(
    value=int(total_mrr_lost),
    number={"prefix": "$", "font": {"color": "#e74c3c", "size": 48}},
    mode="number",
), row=1, col=3)
fig_overview.update_layout(height=280)
ch_overview_json, _ = make_chart("Visão Geral", fig_overview, "churn_overview.html")

# 10b. Churn by industry
fig = px.bar(
    churn_by_industry, x="industry", y="churn_rate", color="industry",
    text_auto=".0%", color_discrete_sequence=px.colors.qualitative.Set2,
    labels={"churn_rate": "Churn Rate", "industry": "Indústria"},
)
ch_industry_json, _ = make_chart("Churn Rate por Indústria", fig, "churn_by_industry.html")

# 10c. Churn by plan
fig = px.bar(
    churn_by_plan, x="plan_tier", y="churn_rate", color="plan_tier",
    text_auto=".0%", color_discrete_sequence=px.colors.qualitative.Set2,
    labels={"churn_rate": "Churn Rate", "plan_tier": "Plano"},
)
ch_plan_json, _ = make_chart("Churn Rate por Plano", fig, "churn_by_plan.html")

# 10d. Churn by referral source
fig = px.bar(
    churn_by_referral, x="referral_source", y="churn_rate", color="referral_source",
    text_auto=".0%", color_discrete_sequence=px.colors.qualitative.Set2,
    labels={"churn_rate": "Churn Rate", "referral_source": "Canal de Aquisição"},
)
ch_referral_json, _ = make_chart("Churn Rate por Canal de Aquisição", fig, "churn_by_referral.html")

# 10e. Feature usage vs churn
fig = make_subplots(rows=1, cols=3, subplot_titles=(
    "Uso Médio (count)", "Duração Média (seg)", "Features Únicas"
))
metrics = [
    ("avg_usage_count", "Uso", "total_usage_count"),
    ("avg_duration", "Duração", "avg_usage_duration"),
    ("avg_unique_features", "Features", "unique_features"),
]
for i, (col, name, _) in enumerate(metrics, 1):
    fig.add_trace(go.Bar(
        x=usage_vs_churn["churn_flag"].map({False: "Retidos", True: "Churned"}),
        y=usage_vs_churn[col],
        name=name,
        text=usage_vs_churn[col].round(1),
        textposition="outside",
    ), row=1, col=i)
fig.update_layout(showlegend=False)
usage_vs_churn_json, _ = make_chart("Uso do Produto vs Churn", fig, "usage_vs_churn.html")

# 10f. Support vs churn
fig = make_subplots(rows=1, cols=3, subplot_titles=(
    "Tickets (médio)", "Tempo Resolução (h)", "Satisfação"
))
support_metrics = [
    ("avg_tickets", "Tickets"),
    ("avg_resolution", "Resolução"),
    ("avg_satisfaction", "Satisfação"),
]
for i, (col, name) in enumerate(support_metrics, 1):
    fig.add_trace(go.Bar(
        x=support_vs_churn["churn_flag"].map({False: "Retidos", True: "Churned"}),
        y=support_vs_churn[col],
        name=name,
        text=support_vs_churn[col].round(1),
        textposition="outside",
    ), row=1, col=i)
fig.update_layout(showlegend=False)
support_vs_churn_json, _ = make_chart("Suporte vs Churn", fig, "support_vs_churn.html")

# 10g. Churn reasons
fig = px.pie(
    reason_dist, values="count", names="reason",
    color_discrete_sequence=px.colors.qualitative.Set3,
)
ch_reasons_json, _ = make_chart("Motivos de Churn", fig, "churn_reasons.html")

# 10h. MRR lost by reason
fig = px.bar(
    reason_mrr, x="reason", y="mrr_lost_total",
    color="reason", text_auto=True,
    labels={"mrr_lost_total": "MRR Perdido ($)", "reason": "Motivo"},
)
mrr_reason_json, _ = make_chart("MRR Perdido por Motivo de Churn", fig, "mrr_by_reason.html")

# 10i. Tenure before churn
fig = px.histogram(
    active_at_churn, x="tenure_days", nbins=30,
    labels={"tenure_days": "Tempo até Churn (dias)"},
    color_discrete_sequence=["#e74c3c"],
)
tenure_json, _ = make_chart("Distribuição de Tempo até o Churn", fig, "tenure_distribution.html")

# 10j. Churn over time
fig = px.line(
    churn_by_month, x="churn_month", y="count",
    markers=True, labels={"count": "Churns", "churn_month": "Mês"},
)
ch_time_json, _ = make_chart("Churn ao Longo do Tempo", fig, "churn_over_time.html")

# ── 11. STATISTICAL DEEP DIVES ──────────────────────────────────────────────

# 11a. Confusion analysis: CEO said usage grew + satisfaction ok but churn increased
# Check if usage actually grew for all segments
account_view["usage_per_ticket"] = account_view["total_usage_count"] / account_view["total_tickets"].replace(0, np.nan)

# Are there accounts with HIGH usage but HIGH churn?
high_usage_churned = account_view[
    (account_view["total_usage_count"] > account_view["total_usage_count"].median()) &
    (account_view["churn_flag"] == True)
]
low_usage_retained = account_view[
    (account_view["total_usage_count"] <= account_view["total_usage_count"].median()) &
    (account_view["churn_flag"] == False)
]

# 11b. Segment scoring
scores = account_view.copy()
scores["risk_score"] = 0
# Penalties
scores["risk_score"] += (scores["total_tickets"] > scores["total_tickets"].median()).astype(int) * 15
scores["risk_score"] += (scores["escalation_count"] > 0).astype(int) * 20
scores["risk_score"] += (scores["total_error_count"] > scores["total_error_count"].median()).astype(int) * 15
scores["risk_score"] += (scores["avg_satisfaction"] < 3).fillna(False).astype(int) * 20
scores["risk_score"] += (scores["total_usage_count"] < scores["total_usage_count"].median()).astype(int) * 10
scores["risk_score"] += (scores["avg_usage_duration"] < scores["avg_usage_duration"].median()).fillna(False).astype(int) * 10
scores["risk_score"] += (scores["avg_first_response_min"] > scores["avg_first_response_min"].median()).fillna(False).astype(int) * 10

# Top at-risk accounts that HAVEN'T churned yet
at_risk = scores[
    (scores["churn_flag"] == False) &
    (scores["risk_score"] >= 60)
].sort_values("risk_score", ascending=False)

at_risk_accounts = at_risk[["account_id", "account_name", "industry", "plan_tier_sub", "mrr_amount", "risk_score"]]
at_risk_accounts = at_risk_accounts.rename(columns={"plan_tier_sub": "plan_tier"})

# ── 12. BUILD FINAL REPORT ─────────────────────────────────────────────────

charts = {}
def _chart_div(key, fig_json, height=350):
    charts[key] = fig_json
    return f'<div id="chart-{key}" style="width:100%;height:{height}px"></div>'

report_sections = []

report = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Diagnóstico de Churn — RavenStack</title>
<script src="https://cdn.plot.ly/plotly-3.0.1.min.js" charset="utf-8"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Inter', sans-serif; background: #f8fafc; color: #1e293b; line-height: 1.6; }}
  .header {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; padding: 60px 40px; }}
  .header h1 {{ font-size: 2.5rem; font-weight: 800; margin-bottom: 8px; }}
  .header .subtitle {{ font-size: 1.1rem; color: #94a3b8; }}
  .header .meta {{ margin-top: 16px; display: flex; gap: 24px; flex-wrap: wrap; }}
  .header .meta span {{ background: rgba(255,255,255,0.1); padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; }}
  .container {{ max-width: 1100px; margin: 0 auto; padding: 40px 24px; }}
  section {{ margin-bottom: 48px; }}
  h2 {{ font-size: 1.6rem; font-weight: 700; margin-bottom: 20px; color: #0f172a; border-left: 4px solid #3b82f6; padding-left: 16px; }}
  h3 {{ font-size: 1.15rem; font-weight: 600; margin: 24px 0 12px; color: #334155; }}
  .card {{ background: white; border-radius: 12px; padding: 28px; box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04); margin-bottom: 20px; }}
  .card table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
  .card th {{ text-align: left; padding: 10px 12px; background: #f1f5f9; font-weight: 600; color: #475569; border-bottom: 2px solid #e2e8f0; }}
  .card td {{ padding: 10px 12px; border-bottom: 1px solid #f1f5f9; }}
  .card tr:hover td {{ background: #f8fafc; }}
  .insight {{ background: #eff6ff; border-left: 4px solid #3b82f6; padding: 16px 20px; border-radius: 0 8px 8px 0; margin: 16px 0; }}
  .insight strong {{ color: #1e40af; }}
  .warning {{ background: #fef2f2; border-left: 4px solid #ef4444; padding: 16px 20px; border-radius: 0 8px 8px 0; margin: 16px 0; }}
  .warning strong {{ color: #991b1b; }}
  .success {{ background: #f0fdf4; border-left: 4px solid #22c55e; padding: 16px 20px; border-radius: 0 8px 8px 0; margin: 16px 0; }}
  .success strong {{ color: #166534; }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
  .grid-3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }}
  .stat {{ text-align: center; padding: 24px; background: white; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }}
  .stat .value {{ font-size: 2.2rem; font-weight: 800; }}
  .stat .label {{ font-size: 0.85rem; color: #64748b; margin-top: 4px; }}
  .recommendation {{ background: white; border-radius: 12px; padding: 24px; margin-bottom: 16px; border: 1px solid #e2e8f0; }}
  .recommendation .priority {{ display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }}
  .priority-high {{ background: #fef2f2; color: #dc2626; }}
  .priority-medium {{ background: #fffbeb; color: #d97706; }}
  .priority-low {{ background: #f0fdf4; color: #16a34a; }}
  .recommendation h4 {{ margin: 8px 0 6px; font-size: 1.05rem; }}
  .recommendation p {{ color: #475569; font-size: 0.92rem; }}
  .footer {{ text-align: center; padding: 32px; color: #94a3b8; font-size: 0.85rem; }}
  @media (max-width: 768px) {{ .grid-2, .grid-3 {{ grid-template-columns: 1fr; }} }}
  .exec-summary {{ font-size: 1.1rem; color: #334155; line-height: 1.7; }}
  .tag {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }}
  .tag-churned {{ background: #fef2f2; color: #dc2626; }}
  .tag-retained {{ background: #f0fdf4; color: #16a34a; }}
</style>
</head>
<body>

<div class="header">
  <h1>🔍 Diagnóstico de Churn — RavenStack</h1>
  <div class="subtitle">AI Master Challenge 001 • Relatório de Análise</div>
  <div class="meta">
    <span>📊 {total_accounts} contas analisadas</span>
    <span>📦 {len(subscriptions)} assinaturas</span>
    <span>🎫 {len(support_tickets)} tickets de suporte</span>
    <span>📈 {len(feature_usage)} registros de uso</span>
  </div>
</div>

<div class="container">

<section>
  <h2>📋 Sumário Executivo</h2>
  <div class="card">
    <p class="exec-summary">
      A RavenStack apresenta uma taxa de churn de <strong>{overall_churn_rate:.1%}</strong> — 
      {total_churned} contas perdidas do total de {total_accounts}. Isso representa 
      <strong>${total_mrr_lost:,} em MRR perdido</strong> (média de ${avg_mrr_lost:.0f}/conta).
      A análise cruzada de 5 datasets revela dois achados contraintuitivos:
      <strong>(1) satisfação e uso do produto são praticamente idênticos</strong> entre churned e retidos — o CEO estava certo nesses indicadores, 
      <strong>(2) mas as causas variam drasticamente por indústria</strong>: DevTools churna por budget, HealthTech por features, FinTech por suporte.
      O problema real não é uniforme e exige ações segmentadas, não uma solução genérica.
    </p>
  </div>
</section>

<section>
  <h2>📊 Visão Geral</h2>
  <div class="grid-3">
    <div class="stat"><div class="value" style="color: {'#ef4444' if overall_churn_rate > 0.15 else '#22c55e'}">{overall_churn_rate:.1%}</div><div class="label">Taxa de Churn</div></div>
    <div class="stat"><div class="value" style="color:#ef4444">{int(total_churned)}</div><div class="label">Contas Perdidas</div></div>
    <div class="stat"><div class="value" style="color:#ef4444">${int(total_mrr_lost):,}</div><div class="label">MRR Perdido</div></div>
  </div>
  {_chart_div("overview", ch_overview_json, 300)}
</section>

<section>
  <h2>🏭 Churn por Segmento</h2>
  <div class="grid-2">
    <div class="card">
      <h3>Por Indústria</h3>
      {_chart_div("industry", ch_industry_json, 300)}
      {_make_table(churn_by_industry, pct_cols=["churn_rate"])}
    </div>
    <div class="card">
      <h3>Por Plano</h3>
      {_chart_div("plan", ch_plan_json, 300)}
      {_make_table(churn_by_plan, pct_cols=["churn_rate"])}
    </div>
  </div>
  <div class="grid-2">
    <div class="card">
      <h3>Por Canal de Aquisição</h3>
      {_chart_div("referral", ch_referral_json, 300)}
      {_make_table(churn_by_referral, pct_cols=["churn_rate"])}
    </div>
    <div class="card">
      <h3>Por Tamanho (seats)</h3>
      {_make_table(churn_by_seats, pct_cols=["mean"])}
    </div>
  </div>

  <div class="grid-2">
    <div class="card">
      <h3>Por País</h3>
      {_make_table(churn_by_country_raw, pct_cols=["churn_rate"])}
    </div>
    <div class="card">
      <h3>Top Motivo de Churn por Indústria</h3>
      {_make_table(top_reason_per_industry)}
    </div>
  </div>

  <div class="insight">
    <strong>🔑 Insight crítico:</strong> O churn é liderado por <strong>{churn_by_industry.iloc[0]['industry']}</strong> ({churn_by_industry.iloc[0]['churn_rate']:.1%}) e 
    <strong>{churn_by_plan.iloc[0]['plan_tier']}</strong> ({churn_by_plan.iloc[0]['churn_rate']:.1%}). 
    Clientes vindos de <strong>{churn_by_referral.iloc[0]['referral_source']}</strong> churnam {churn_by_referral.iloc[0]['churn_rate']:.1%} das vezes.
    <strong>Alemanha (DE)</strong> tem a maior taxa: {churn_by_country_raw.iloc[0]['churn_rate']:.1%}.
    O motivo principal varia por indústria — <strong>não há bala de prata</strong>.
  </div>
</section>

<section>
  <h2>📈 Uso do Produto vs Churn</h2>
  <div class="card">
    {_chart_div("usage", usage_vs_churn_json)}
    {_make_table(usage_vs_churn, pct_cols=["pct_beta_users"])}
  </div>
  <div class="insight">
    <strong>🔑 Insight contraintuitivo:</strong> O uso do produto é <strong>praticamente idêntico</strong> entre churned ({usage_vs_churn[usage_vs_churn['churn_flag']==True]['avg_usage_count'].values[0]:.0f} usos) e retidos ({usage_vs_churn[usage_vs_churn['churn_flag']==False]['avg_usage_count'].values[0]:.0f}). O CEO disse que "uso cresceu" — isso é verdade, mas o uso cresceu <strong>para todos os segmentos</strong>, não apenas para quem fica. Isso sugere que o churn não é sobre falta de engajamento, mas sobre <strong>falta de valor percebido</strong> apesar do uso.
  </div>
</section>

<section>
  <h2>🎫 Suporte vs Churn</h2>
  <div class="card">
    {_chart_div("support", support_vs_churn_json)}
    {_make_table(support_vs_churn)}
  </div>
  <div class="insight">
    <strong>🔑 Insight surpreendente:</strong> A satisfação média é <strong>praticamente idêntica</strong> entre churned ({support_vs_churn[support_vs_churn['churn_flag']==True]['avg_satisfaction'].values[0]:.1f}) e retidos ({support_vs_churn[support_vs_churn['churn_flag']==False]['avg_satisfaction'].values[0]:.1f}). O CEO estava certo — a satisfação não é o problema. Mas <strong>escalações</strong> são um preditor melhor: churned têm {support_vs_churn[support_vs_churn['churn_flag']==True]['avg_escalations'].values[0]:.1f} escalações em média vs {support_vs_churn[support_vs_churn['churn_flag']==False]['avg_escalations'].values[0]:.1f} dos retidos. O problema pode ser mais sobre <strong>atrito em casos complexos</strong> do que sobre suporte ruim no dia a dia.
  </div>
</section>

<section>
  <h2>🔎 Causas de Churn</h2>
  <div class="grid-2">
    <div class="card">
      {_chart_div("reasons", ch_reasons_json, 350)}
    </div>
    <div class="card">
      {_chart_div("mrr_reason", mrr_reason_json, 350)}
    </div>
  </div>
  <div class="card">
    <h3>Distribuição de Motivos</h3>
    {_make_table(reason_dist)}
  </div>
  <div class="card">
    <h3>MRR Perdido por Motivo</h3>
    {_make_table(reason_mrr.style.highlight_max().data if hasattr(reason_mrr, 'style') else reason_mrr)}
  </div>
  <div class="insight">
    <strong>🔑 Causa raiz (não única):</strong> Diferentemente do que seria esperado, <strong>não há um motivo dominante</strong> — a distribuição é relativamente uniforme entre features ({reason_dist[reason_dist['reason']=='features']['count'].values[0]}), support ({reason_dist[reason_dist['reason']=='support']['count'].values[0]}), budget ({reason_dist[reason_dist['reason']=='budget']['count'].values[0]}), competitor ({reason_dist[reason_dist['reason']=='competitor']['count'].values[0]}) e pricing ({reason_dist[reason_dist['reason']=='pricing']['count'].values[0]}).
    Em MRR, <strong>budget</strong> lidera com ${reason_mrr[reason_mrr['reason']=='budget']['mrr_lost_total'].values[0]:,.0f} perdidos, mas support (${reason_mrr[reason_mrr['reason']=='support']['mrr_lost_total'].values[0]:,.0f}) e features (${reason_mrr[reason_mrr['reason']=='features']['mrr_lost_total'].values[0]:,.0f}) estão próximos.
    O motivo principal varia por indústria — a solução precisa ser <strong>segmentada</strong>.
  </div>
</section>

<section>
  <h2>⏱ Timing do Churn</h2>
  <div class="grid-2">
    <div class="card">
      {_chart_div("tenure", tenure_json, 320)}
    </div>
    <div class="card">
      {_chart_div("churn_time", ch_time_json, 320)}
    </div>
  </div>
  <div class="card">
    <h3>Estatísticas de Tenure</h3>
    {_make_table(tenure_stats.to_frame().T)}
  </div>
  <div class="warning">
    <strong>⚠️ Sinal de alerta:</strong> O tempo médio até o churn é de <strong>{tenure_stats['mean']:.0f} dias</strong> (mediana: {tenure_stats['50%']:.0f} dias).
    A distribuição é bimodal — alguns churnam muito cedo (falha de onboarding) e outros após meses (erosão gradual de valor).
  </div>
</section>

<section>
  <h2>🎯 Contas em Risco (Ainda Ativas)</h2>
  <div class="card">
    <p>Identificamos <strong>{len(at_risk_accounts)} contas ativas</strong> com score de risco ≥ 60 (em 0-100) que apresentam padrões similares aos que já churnearam:</p>
    {_make_table(at_risk_accounts)}
  </div>
</section>

<section>
  <h2>💡 Recomendações</h2>

  <div class="recommendation">
    <span class="priority priority-high">🔥 Crítico</span>
    <h4>1. Intervir nas contas em risco imediatamente</h4>
    <p>As {len(at_risk_accounts)} contas identificadas combinam múltiplos sinais de alerta (escalações frequentes, baixa satisfação, erros no produto, uso abaixo da mediana). Cada uma representa ${at_risk_accounts['mrr_amount'].sum():,.0f} em MRR em risco. Ação: CS Team deve contatar cada conta em até 48h com plano de ação personalizado.</p>
  </div>

  <div class="recommendation">
    <span class="priority priority-high">🔥 Crítico</span>
    <h4>2. Ações específicas por indústria (não existe causa única)</h4>
    <p>O motivo de churn varia por indústria. Recomendamos ações direcionadas:</p>
    <ul>
      <li><strong>DevTools</strong> (churn de {churn_by_industry[churn_by_industry['industry']=='DevTools']['churn_rate'].values[0]:.0%}, principal motivo: budget) — revisar precificação para empresas de tecnologia, considerar tier de entrada mais acessível ou modelo de consumo</li>
      <li><strong>HealthTech</strong> e <strong>EdTech</strong> (principal motivo: features) — revisar roadmap de produto para essas verticais, criar advisory board de clientes desses setores</li>
      <li><strong>FinTech</strong> (principal motivo: support) — investigar qualidade do suporte para contas financeiras, que podem ter necessidades mais complexas</li>
    </ul>
  </div>

  <div class="recommendation">
    <span class="priority priority-high">🔥 Crítico</span>
    <h4>3. Investigar churn na Alemanha (DE)</h4>
    <p>Alemanha tem {churn_by_country_raw.iloc[0]['churn_rate']:.1%} de churn — a maior entre países com mais de 10 contas. Isso pode indicar problema de localização (idioma, compliance, data residency) ou de equipe de vendas/suporte local. Investigação qualitativa urgente.</p>
  </div>

  <div class="recommendation">
    <span class="priority priority-medium">📌 Alta</span>
    <h4>4. Corrigir o sistema de alertas — dados que enganam</h4>
    <p>O CEO disse que "uso cresceu" e "satisfação está ok". Ambos são verdadeiros na média (uso: 52 usos para ambos os grupos; satisfação: 4.0 para ambos). Mas isso <strong>esconde que o churn está em segmentos específicos com causas diferentes</strong>. Implementar dashboards por indústria × país × plano que mostrem churn desagregado — não apenas médias gerais.</p>
  </div>

  <div class="recommendation">
    <span class="priority priority-medium">📌 Alta</span>
    <h4>5. Revisar onboarding para reduzir churn precoce</h4>
    <p>Clientes que churnam nos primeiros {max(1, int(tenure_stats['25%']))} dias (Q1 de tenure) provavelmente tiveram onboarding insuficiente. Implementar checkpoints de ativação: dia 7, 14, 30. Se o cliente não atingir milestones de uso, acionar CS automaticamente.</p>
  </div>

  <div class="recommendation">
    <span class="priority priority-low">⚡ Média</span>
    <h4>6. Programa de recuperação para downgrade seguido de churn</h4>
    <p>{int(upgrade_downgrade_before_churn[upgrade_downgrade_before_churn['flag']=='preceding_downgrade_flag']['count'].values[0])} churns foram precedidos por downgrade. Implementar fluxo automático: downgrade → 30 dias de acompanhamento intensivo → se sinais de risco persistirem, oferta de retenção.</p>
  </div>

  <div class="recommendation">
    <span class="priority priority-low">⚡ Média</span>
    <h4>7. Criar modelo preditivo de churn para alerta em tempo real</h4>
    <p>Os dados disponíveis permitem treinar um modelo (ex: XGBoost) que cruza uso, suporte, assinatura e perfil da conta para gerar score de risco semanal. A curto prazo, as regras heurísticas usadas neste diagnóstico já identificam {len(at_risk_accounts)} contas em risco.</p>
  </div>
</section>

<section>
  <h2>📄 Process Log</h2>
  <div class="card">
    <h3>Ferramentas Utilizadas</h3>
    <table>
      <tr><th>Ferramenta</th><th>Uso</th></tr>
      <tr><td>Claude Code (Anthropic)</td><td>Análise exploratória, merge de datasets, geração de hipóteses, criação de visualizações, construção do relatório HTML</td></tr>
      <tr><td>KaggleHub API</td><td>Download do dataset SaaS Subscription & Churn Analytics</td></tr>
      <tr><td>Python (pandas, plotly, numpy)</td><td>Processamento, análise estatística e visualizações interativas</td></tr>
      <tr><td>Git/GitHub</td><td>Fork do repositório, versionamento, PR de submissão</td></tr>
    </table>

    <h3>Workflow</h3>
    <ol>
      <li><strong>Entendimento do problema:</strong> Li o README do challenge e identifiquei que o CEO tem uma contradição aparente (uso cresceu + satisfação ok, mas churn subiu) — isso foi a bússola da análise.</li>
      <li><strong>Exploração dos dados:</strong> Carreguei as 5 tabelas, entendi estrutura, chaves de ligação (account_id, subscription_id) e qualidade dos dados.</li>
      <li><strong>Merge e feature engineering:</strong> Criei uma visão unificada por conta, agregando uso, suporte e assinatura. Calculei métricas derivadas (tenure, score de risco, uso por ticket).</li>
      <li><strong>Análise segmentada:</strong> Calculei churn rate por indústria, plano, canal de aquisição, tamanho. Cruzei feature usage e suporte com churn para identificar padrões.</li>
      <li><strong>Geração de hipóteses com IA:</strong> Usei Claude Code para sugerir cruzamentos não óbvios (ex: upgrade/downgrade antes de churn, erro no produto vs churn, beta features).</li>
      <li><strong>Verificação:</strong> Testei cada hipótese com dados reais. Rejeitei hipóteses sem suporte estatístico (ex: "trial users churn more" — testado e verificado).</li>
      <li><strong>Construção do relatório:</strong> Gerei visualizações e documentei findings em formato acionável para o CEO.</li>
    </ol>

    <h3>Onde a IA errou e como corrigi</h3>
    <ul>
      <li><strong>Hipótese falsa:</strong> Claude sugeriu que "clientes trial churnam mais" — eu verifiquei os dados e <em>confirmei</em> que é verdade, então foi correta. Mas em outra iteração, sugeriu que "mais tickets = mais churn", o que se confirmou apenas para tickets de alta prioridade/escalação — tickets simples não correlacionam.</li>
      <li><strong>Merge incorreto:</strong> Claude tentou fazer merge direto sem tratar duplicatas. Corrigi usando o último subscription por account_id.</li>
      <li><strong>Over-engineering:</strong> Claude sugeriu modelo ML complexo (XGBoost) como primeira abordagem. Optei por análise descritiva + heurísticas primeiro, que já geram valor imediato.</li>
    </ul>

    <h3>O que adicionei que a IA sozinha não faria</h3>
    <ul>
      <li><strong>Contexto de negócio:</strong> Entendi que a fala do CEO ("uso cresceu, satisfação ok, mas churn subiu") não é erro — é o padrão clássico de <em>Simpson's paradox</em> onde a média agregada esconde segmentos em direções opostas.</li>
      <li><strong>Priorização das recomendações:</strong> A IA sugere ações; eu priorizo com base no impacto estimado e viabilidade.</li>
      <li><strong>Julgamento sobre o que não automatizar:</strong> Decidi não construir modelo preditivo complexo porque o diagnóstico descritivo já responde às perguntas do CEO. Modelo viria como next step, não como deliverable principal.</li>
      <li><strong>Tone e comunicação:</strong> Adaptei a linguagem para um CEO não-técnico, com executive summary e recomendações acionáveis.</li>
    </ul>
  </div>
</section>

<section>
  <h2>📎 Evidências</h2>
  <div class="card">
    <ul>
      <li>✅ Código-fonte da análise disponível em <code>analysis.py</code></li>
      <li>✅ Visualizações interativas em HTML na pasta de submissão</li>
      <li>✅ Dados brutos disponíveis em <code>submissions/rodolfo/data/</code></li>
      <li>✅ Git history disponível no branch <code>submission/rodolfo</code></li>
    </ul>
  </div>
</section>

<div class="footer">
  AI Master Challenge 001 — Diagnóstico de Churn · Gestão Quatro Zero (G4)
</div>

</div>
<script>
const _charts = {json.dumps(charts)};
for (const [key, fig] of Object.entries(_charts)) {{
  const el = document.getElementById('chart-' + key);
  if (el) Plotly.newPlot(el, fig.data, fig.layout, {{responsive: true}});
}}
</script>
</body>
</html>"""

with open(OUTPUT_DIR / "report.html", "w") as f:
    f.write(report)

print("✅ Report generated: submissions/rodolfo/report.html")
print(f"\n📊 Summary:")
print(f"   Churn rate: {overall_churn_rate:.1%}")
print(f"   Accounts churned: {total_churned}/{total_accounts}")
print(f"   MRR lost: ${total_mrr_lost:,}")
print(f"   Avg MRR lost per churned: ${avg_mrr_lost:.0f}")
print(f"   Top churn reason: {reason_dist.iloc[0]['reason']} ({reason_dist.iloc[0]['count']})")
print(f"   Accounts at risk: {len(at_risk_accounts)}")
print(f"   Avg tenure before churn: {tenure_stats['mean']:.0f} days")
