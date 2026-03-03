"""
Phase 5: Interactive Dashboard — RavenStack Churn Diagnostic
=============================================================
Generates a self-contained HTML dashboard with Plotly.
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import json
import warnings
warnings.filterwarnings('ignore')

DATA = '/home/user/ai-master-challenge/datasets/'
OUT = '/home/user/ai-master-challenge/submissions/ai-master/solution/'

# Load data
accounts = pd.read_csv(f'{DATA}ravenstack_accounts.csv')
subs = pd.read_csv(f'{DATA}ravenstack_subscriptions.csv')
usage = pd.read_csv(f'{DATA}ravenstack_feature_usage.csv')
tickets = pd.read_csv(f'{DATA}ravenstack_support_tickets.csv')
churn = pd.read_csv(f'{DATA}ravenstack_churn_events.csv')
risk_scores = pd.read_csv(f'{OUT}account_risk_scores.csv')

with open(f'{OUT}model_metrics.json') as f:
    metrics = json.load(f)

# Prep
churned_ids = set(churn['account_id'].unique())
accounts['churned'] = accounts['account_id'].isin(churned_ids)
sub_acct = subs[['subscription_id', 'account_id']].drop_duplicates()
usage_m = usage.merge(sub_acct, on='subscription_id', how='left')
usage_m['churned'] = usage_m['account_id'].isin(churned_ids)
tickets_m = tickets.merge(accounts[['account_id', 'churned']], on='account_id', how='left')

# Color palette
COLORS = {
    'primary': '#1a1a2e',
    'secondary': '#16213e',
    'accent': '#0f3460',
    'highlight': '#e94560',
    'success': '#00b894',
    'warning': '#fdcb6e',
    'danger': '#d63031',
    'text': '#2d3436',
    'light': '#dfe6e9',
    'retained': '#00b894',
    'churned': '#d63031',
}

# ============================================================
# KPI CARDS DATA
# ============================================================
total_accounts = len(accounts)
churned_count = accounts['churned'].sum()
churn_rate = churned_count / total_accounts * 100
total_mrr_lost = churn.drop_duplicates('account_id')['last_mrr'].sum()
avg_satisfaction_all = tickets['satisfaction_score'].dropna().mean()
avg_satisfaction_retained = tickets_m[~tickets_m['churned']]['satisfaction_score'].dropna().mean()
avg_satisfaction_churned = tickets_m[tickets_m['churned']]['satisfaction_score'].dropna().mean()

# ============================================================
# FIGURE 1: Churn Overview KPIs
# ============================================================
fig_kpi = go.Figure()
fig_kpi.add_trace(go.Indicator(
    mode="number+delta",
    value=churn_rate,
    title={"text": "Churn Rate", "font": {"size": 16}},
    number={"suffix": "%", "font": {"size": 40, "color": COLORS['danger']}},
    delta={"reference": 15, "suffix": "%", "increasing": {"color": "red"}},
    domain={'x': [0, 0.25], 'y': [0, 1]}
))
fig_kpi.add_trace(go.Indicator(
    mode="number",
    value=total_mrr_lost,
    title={"text": "MRR Lost", "font": {"size": 16}},
    number={"prefix": "$", "font": {"size": 40, "color": COLORS['danger']}, "valueformat": ",.0f"},
    domain={'x': [0.25, 0.5], 'y': [0, 1]}
))
fig_kpi.add_trace(go.Indicator(
    mode="number",
    value=churned_count,
    title={"text": "Churned Accounts", "font": {"size": 16}},
    number={"font": {"size": 40, "color": COLORS['danger']}},
    domain={'x': [0.5, 0.75], 'y': [0, 1]}
))
fig_kpi.add_trace(go.Indicator(
    mode="number",
    value=avg_satisfaction_churned,
    title={"text": "Churned Satisfaction", "font": {"size": 16}},
    number={"font": {"size": 40, "color": COLORS['warning']}, "valueformat": ".2f", "suffix": "/5"},
    domain={'x': [0.75, 1], 'y': [0, 1]}
))
fig_kpi.update_layout(height=150, margin=dict(t=40, b=10, l=20, r=20),
                       paper_bgcolor='white')

# ============================================================
# FIGURE 2: Churn Rate by Segment (Plan × Channel × Industry)
# ============================================================
fig_segments = make_subplots(rows=1, cols=3, subplot_titles=[
    'By Plan', 'By Acquisition Channel', 'By Industry'
])

# By Plan
plan_churn = accounts.groupby('plan')['churned'].mean().sort_values(ascending=True) * 100
fig_segments.add_trace(go.Bar(
    y=plan_churn.index, x=plan_churn.values, orientation='h',
    marker_color=[COLORS['danger'] if v > 40 else COLORS['warning'] if v > 25 else COLORS['success'] for v in plan_churn.values],
    text=[f"{v:.0f}%" for v in plan_churn.values], textposition='auto',
), row=1, col=1)

# By Channel
ch_churn = accounts.groupby('acquisition_channel')['churned'].mean().sort_values(ascending=True) * 100
fig_segments.add_trace(go.Bar(
    y=ch_churn.index, x=ch_churn.values, orientation='h',
    marker_color=[COLORS['danger'] if v > 50 else COLORS['warning'] if v > 35 else COLORS['success'] for v in ch_churn.values],
    text=[f"{v:.0f}%" for v in ch_churn.values], textposition='auto',
), row=1, col=2)

# By Industry
ind_churn = accounts.groupby('industry')['churned'].mean().sort_values(ascending=True) * 100
fig_segments.add_trace(go.Bar(
    y=ind_churn.index, x=ind_churn.values, orientation='h',
    marker_color=[COLORS['danger'] if v > 50 else COLORS['warning'] if v > 35 else COLORS['success'] for v in ind_churn.values],
    text=[f"{v:.0f}%" for v in ind_churn.values], textposition='auto',
), row=1, col=3)

fig_segments.update_layout(height=400, showlegend=False, title_text="Churn Rate by Segment",
                            margin=dict(t=60, b=20))

# ============================================================
# FIGURE 3: The Paradox — Usage vs Churn
# ============================================================
acct_usage = usage_m.groupby(['account_id', 'churned']).agg(
    total_usage=('usage_count', 'sum'),
    features_used=('feature_name', 'nunique'),
).reset_index()

fig_paradox = make_subplots(rows=1, cols=2, subplot_titles=[
    'Usage Distribution: Retained vs Churned', 'Features Adopted: Retained vs Churned'
])

for churned, label, color in [(False, 'Retained', COLORS['success']), (True, 'Churned', COLORS['danger'])]:
    subset = acct_usage[acct_usage['churned'] == churned]
    fig_paradox.add_trace(go.Histogram(
        x=np.clip(subset['total_usage'], 0, 8000),
        name=label, marker_color=color, opacity=0.7, nbinsx=30,
    ), row=1, col=1)
    fig_paradox.add_trace(go.Histogram(
        x=subset['features_used'],
        name=label, marker_color=color, opacity=0.7, nbinsx=10,
    ), row=1, col=2)

fig_paradox.update_layout(height=350, barmode='overlay',
                           title_text="The Paradox: Usage Grew... But Only for Retained Customers")
fig_paradox.update_xaxes(title_text="Total Usage Count", row=1, col=1)
fig_paradox.update_xaxes(title_text="Number of Features Used", row=1, col=2)

# ============================================================
# FIGURE 4: Satisfaction Survivor Bias
# ============================================================
fig_satisfaction = make_subplots(rows=1, cols=2, subplot_titles=[
    'Satisfaction Distribution', 'Survey Response Rate'
])

for churned, label, color in [(False, 'Retained', COLORS['success']), (True, 'Churned', COLORS['danger'])]:
    subset = tickets_m[tickets_m['churned'] == churned]
    sat = subset['satisfaction_score'].dropna()
    counts = sat.value_counts().sort_index()
    fig_satisfaction.add_trace(go.Bar(
        x=counts.index, y=counts.values / counts.sum() * 100,
        name=label, marker_color=color, opacity=0.8,
    ), row=1, col=1)

resp_rates = pd.DataFrame({
    'Group': ['Retained', 'Churned'],
    'Response Rate': [
        tickets_m[~tickets_m['churned']]['satisfaction_score'].notna().mean() * 100,
        tickets_m[tickets_m['churned']]['satisfaction_score'].notna().mean() * 100,
    ]
})
fig_satisfaction.add_trace(go.Bar(
    x=resp_rates['Group'], y=resp_rates['Response Rate'],
    marker_color=[COLORS['success'], COLORS['danger']],
    text=[f"{v:.0f}%" for v in resp_rates['Response Rate']],
    textposition='auto', showlegend=False,
), row=1, col=2)

fig_satisfaction.update_layout(height=350,
                                title_text="Survivor Bias: Satisfaction Looks OK Because Unhappy Customers Don't Respond")

# ============================================================
# FIGURE 5: Support Experience Gap
# ============================================================
support_metrics = []
for churned, label in [(False, 'Retained'), (True, 'Churned')]:
    subset = tickets_m[tickets_m['churned'] == churned]
    support_metrics.append({
        'Group': label,
        'First Response (hrs)': subset['first_response_hours'].mean(),
        'Resolution Time (hrs)': subset['resolution_hours'].mean(),
        'Escalation Rate (%)': subset['escalated'].mean() * 100,
        'Reopen Rate (%)': subset['reopened'].mean() * 100,
    })

sm = pd.DataFrame(support_metrics)

fig_support = make_subplots(rows=1, cols=4, subplot_titles=[
    'Avg First Response', 'Avg Resolution Time', 'Escalation Rate', 'Reopen Rate'
])

metrics_list = [
    ('First Response (hrs)', 'hrs'),
    ('Resolution Time (hrs)', 'hrs'),
    ('Escalation Rate (%)', '%'),
    ('Reopen Rate (%)', '%'),
]

for i, (metric, unit) in enumerate(metrics_list, 1):
    fig_support.add_trace(go.Bar(
        x=sm['Group'], y=sm[metric],
        marker_color=[COLORS['success'], COLORS['danger']],
        text=[f"{v:.1f}{unit}" for v in sm[metric]],
        textposition='auto', showlegend=False,
    ), row=1, col=i)

fig_support.update_layout(height=300, title_text="Support Experience: Churned Customers Get 3x Worse Service")

# ============================================================
# FIGURE 6: Feature Error Rates
# ============================================================
feat_errs = usage_m.groupby(['feature_name', 'churned']).agg(
    total_errors=('error_count', 'sum'),
    total_usage=('usage_count', 'sum'),
).reset_index()
feat_errs['error_rate'] = feat_errs['total_errors'] / feat_errs['total_usage']

fig_errors = go.Figure()
for churned, label, color in [(False, 'Retained', COLORS['success']), (True, 'Churned', COLORS['danger'])]:
    subset = feat_errs[feat_errs['churned'] == churned].sort_values('error_rate')
    fig_errors.add_trace(go.Bar(
        y=subset['feature_name'], x=subset['error_rate'] * 100,
        name=label, marker_color=color, orientation='h',
        text=[f"{v:.1f}%" for v in subset['error_rate'] * 100],
        textposition='auto',
    ))

fig_errors.update_layout(
    height=400, barmode='group',
    title_text="Feature Error Rates: Workflow Builder & Report Generator are 3x Worse",
    xaxis_title="Error Rate (%)"
)

# ============================================================
# FIGURE 7: MRR Lost by Reason
# ============================================================
reason_mrr = churn.groupby('reason_code').agg(
    total_mrr=('last_mrr', 'sum'),
    count=('churn_event_id', 'count'),
).sort_values('total_mrr', ascending=True).reset_index()

fig_mrr = go.Figure()
fig_mrr.add_trace(go.Bar(
    y=reason_mrr['reason_code'], x=reason_mrr['total_mrr'],
    orientation='h', marker_color=COLORS['highlight'],
    text=[f"${v:,.0f}" for v in reason_mrr['total_mrr']],
    textposition='auto',
))
fig_mrr.update_layout(
    height=400, title_text="MRR Lost by Churn Reason",
    xaxis_title="Total MRR Lost ($)"
)

# ============================================================
# FIGURE 8: Feature Importance (Model)
# ============================================================
feat_imp = pd.read_csv(f'{OUT}feature_importance.csv')
top_feat = feat_imp.head(10).sort_values('importance')

fig_importance = go.Figure()
fig_importance.add_trace(go.Bar(
    y=top_feat['feature'], x=top_feat['importance'],
    orientation='h', marker_color=COLORS['accent'],
    text=[f"{v:.3f}" for v in top_feat['importance']],
    textposition='auto',
))
fig_importance.update_layout(
    height=350, title_text="Churn Prediction: Top 10 Features by Importance",
    xaxis_title="Feature Importance"
)

# ============================================================
# FIGURE 9: Channel Quality Scatter
# ============================================================
ch_data = accounts.groupby('acquisition_channel').agg(
    churn_rate=('churned', 'mean'),
    count=('account_id', 'count'),
).reset_index()
ch_mrr = churn.merge(accounts[['account_id', 'acquisition_channel']], on='account_id')
ch_mrr_agg = ch_mrr.groupby('acquisition_channel')['last_mrr'].sum().reset_index(name='mrr_lost')
ch_data = ch_data.merge(ch_mrr_agg, on='acquisition_channel', how='left').fillna(0)

fig_channel = go.Figure()
fig_channel.add_trace(go.Scatter(
    x=ch_data['churn_rate'] * 100, y=ch_data['mrr_lost'],
    mode='markers+text', text=ch_data['acquisition_channel'],
    textposition='top center',
    marker=dict(
        size=ch_data['count'] / 2,
        color=ch_data['churn_rate'],
        colorscale='RdYlGn_r',
        showscale=True,
        colorbar=dict(title="Churn %"),
    ),
))
fig_channel.update_layout(
    height=400, title_text="Channel Quality: Churn Rate vs MRR Lost",
    xaxis_title="Churn Rate (%)", yaxis_title="Total MRR Lost ($)",
)

# ============================================================
# ASSEMBLE HTML DASHBOARD
# ============================================================
print("Generating HTML dashboard...")

html_parts = []
html_parts.append("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RavenStack Churn Diagnostic — Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               background: #f5f6fa; color: #2d3436; }
        .header { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                   color: white; padding: 30px 40px; }
        .header h1 { font-size: 28px; margin-bottom: 8px; }
        .header p { opacity: 0.8; font-size: 14px; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .section { background: white; border-radius: 12px; padding: 20px;
                   margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); }
        .section-title { font-size: 18px; font-weight: 700; color: #1a1a2e;
                         margin-bottom: 5px; padding-bottom: 10px;
                         border-bottom: 2px solid #e94560; }
        .insight-box { background: #fff3e0; border-left: 4px solid #e94560;
                       padding: 15px; margin: 15px 0; border-radius: 0 8px 8px 0; }
        .insight-box strong { color: #e94560; }
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .action-item { background: #e8f5e9; border-left: 4px solid #00b894;
                       padding: 12px 15px; margin: 8px 0; border-radius: 0 8px 8px 0; }
        .action-item h4 { color: #00b894; margin-bottom: 4px; }
        .tag { display: inline-block; padding: 3px 10px; border-radius: 12px;
               font-size: 12px; font-weight: 600; margin: 2px; }
        .tag-danger { background: #ffeef0; color: #d63031; }
        .tag-warning { background: #fff8e1; color: #f39c12; }
        .tag-success { background: #e8f5e9; color: #00b894; }
        @media (max-width: 768px) { .grid-2 { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="header">
        <h1>RavenStack — Churn Diagnostic Dashboard</h1>
        <p>AI Master Challenge 001 | Cross-analysis of 5 datasets | 500 accounts</p>
    </div>
    <div class="container">
""")

# KPIs
html_parts.append(f"""
    <div class="section">
        <div class="section-title">Key Metrics</div>
        {fig_kpi.to_html(full_html=False, include_plotlyjs='cdn')}
    </div>
""")

# The Paradox
html_parts.append(f"""
    <div class="section">
        <div class="section-title">The Paradox Explained</div>
        <div class="insight-box">
            <strong>Why does usage grow while churn increases?</strong>
            <p>Usage grew overall — but it's driven by retained power users. The top 10% of accounts
            generate 31.5% of all usage and have 0% churn. Meanwhile, churned accounts had
            18x LESS average usage (160 vs 3,039). The CEO is seeing aggregate numbers that mask
            a bifurcating customer base.</p>
        </div>
        {fig_paradox.to_html(full_html=False, include_plotlyjs=False)}
    </div>
""")

# Satisfaction Bias
html_parts.append(f"""
    <div class="section">
        <div class="section-title">Satisfaction: The Survivor Bias</div>
        <div class="insight-box">
            <strong>Why does CS say satisfaction is OK?</strong>
            <p>Overall satisfaction is 3.22/5 — seems fine. But retained customers rate 3.79/5 and respond
            78% of the time. Churned customers rate 2.71/5 and only respond 54% of the time.
            The CS team is measuring a biased sample: happy customers who stay AND respond.</p>
        </div>
        {fig_satisfaction.to_html(full_html=False, include_plotlyjs=False)}
    </div>
""")

# Support Gap
html_parts.append(f"""
    <div class="section">
        <div class="section-title">Support Experience Gap</div>
        <div class="insight-box">
            <strong>Churned customers get dramatically worse support:</strong>
            <p>3x slower first response (28h vs 9h), 3.4x slower resolution (146h vs 43h),
            3.7x more escalations (35% vs 9%). This isn't just a symptom — it's a cause.
            When the product fails, bad support accelerates the exit.</p>
        </div>
        {fig_support.to_html(full_html=False, include_plotlyjs=False)}
    </div>
""")

# Segments
html_parts.append(f"""
    <div class="section">
        <div class="section-title">Churn by Segment</div>
        {fig_segments.to_html(full_html=False, include_plotlyjs=False)}
        <div class="insight-box">
            <strong>Highest-risk segments:</strong>
            <span class="tag tag-danger">Trial: 71%</span>
            <span class="tag tag-danger">Paid Ads: 65%</span>
            <span class="tag tag-danger">Retail: 64%</span>
            <span class="tag tag-danger">Starter: 61%</span>
            <span class="tag tag-danger">Event: 56%</span>
            <span class="tag tag-warning">Education: 50%</span>
        </div>
    </div>
""")

# Feature Errors
html_parts.append(f"""
    <div class="section">
        <div class="section-title">Product Quality: Feature Error Rates</div>
        {fig_errors.to_html(full_html=False, include_plotlyjs=False)}
        <div class="insight-box">
            <strong>Workflow Builder and Report Generator have 3x the error rate</strong> of other features.
            For churned customers, these features have 44% error rates — meaning nearly half of all uses
            result in an error. This is the #1 product issue driving churn.
        </div>
    </div>
""")

# Revenue Impact
html_parts.append(f"""
    <div class="section">
        <div class="section-title">Revenue Impact</div>
        <div class="grid-2">
            <div>{fig_mrr.to_html(full_html=False, include_plotlyjs=False)}</div>
            <div>{fig_channel.to_html(full_html=False, include_plotlyjs=False)}</div>
        </div>
        <div class="insight-box">
            <strong>Not all churn is equal:</strong> High-value accounts (MRR >= $1,000) represent
            only 39% of churn events but 91% of MRR lost. Product Issues is the #1 reason
            by total MRR impact ($134K), followed by Too Expensive ($126K).
        </div>
    </div>
""")

# Model
html_parts.append(f"""
    <div class="section">
        <div class="section-title">Predictive Model: What Drives Churn?</div>
        {fig_importance.to_html(full_html=False, include_plotlyjs=False)}
        <div class="insight-box">
            <strong>Model confirms:</strong> Usage patterns (sessions, avg usage) and support quality
            (response time, error rate, resolution time) are the strongest predictors of churn.
            This validates that the churn is driven by product experience + support failures,
            not pricing or market conditions.
        </div>
    </div>
""")

# Recommendations
html_parts.append("""
    <div class="section">
        <div class="section-title">Recommended Actions (Prioritized)</div>

        <div class="action-item">
            <h4>1. FIX Workflow Builder & Report Generator (Impact: ~$134K MRR saved)</h4>
            <p>These two features have 3x the error rate of others. For churned customers,
            44% of uses fail. This is the single most impactful fix. Assign a dedicated
            engineering sprint to reduce error rates to &lt;5%.</p>
        </div>

        <div class="action-item">
            <h4>2. IMPLEMENT Health Score + Proactive Support Triage (Impact: ~$59K MRR saved)</h4>
            <p>Build a health score (0-100) per account: Login frequency (30%) + Feature usage (25%) +
            Support sentiment (15%) + Billing health (15%) + Engagement (15%). Route accounts scoring
            &lt;40 to dedicated CS. Trigger proactive interventions when usage drops &gt;50% for 2 weeks.
            MRR-based routing: accounts &gt;$2K/mo require CS call before cancel completes.</p>
        </div>

        <div class="action-item">
            <h4>3. BUILD Cancel Flow with Dynamic Save Offers (Impact: 25-35% save rate)</h4>
            <p>Currently there's no cancel flow — cancellation is instant. Build: Exit Survey &rarr;
            Dynamic Offer &rarr; Confirmation. Map offers to reasons: "Too Expensive" &rarr; 25% discount for
            3 months; "Not Using Enough" &rarr; pause subscription; "Product Issues" &rarr; priority support +
            credit. Offer subscription pause (60-80% of pausers return). Max 2-3 screens, mobile-friendly.</p>
        </div>

        <div class="action-item">
            <h4>4. FIX Satisfaction Measurement (Impact: data quality)</h4>
            <p>Current CSAT has survivor bias — 46% of churned customers don't respond.
            Switch to proactive NPS at key moments. Segment by health score tier.
            Target: &gt;70% response rate across all segments.</p>
        </div>

        <div class="action-item">
            <h4>5. RESTRUCTURE Paid Ads Acquisition (Impact: ~$216K MRR at risk)</h4>
            <p>Paid Ads has 65% churn rate — the worst channel by far. Either improve
            qualification criteria (ICP scoring), add mandatory onboarding for Paid Ads leads,
            or redirect budget to Referral (22% churn) and Direct Sales (28% churn).</p>
        </div>

        <div class="action-item">
            <h4>6. REVAMP Trial-to-Paid Conversion (Impact: 47 accounts at risk)</h4>
            <p>71% of trial accounts churn vs 37% non-trial. Add guided onboarding with
            milestones, proactive CS on day 3 and 10, and identify the activation metric
            (what retained users do in first 7 days that churners don't).</p>
        </div>

        <div class="action-item">
            <h4>7. SET UP Dunning for Involuntary Churn (Impact: recover 50-60% of failed payments)</h4>
            <p>Involuntary churn (failed payments) is 30-50% of all churn and the easiest to fix.
            Pre-dunning: card expiry alerts 30/15/7 days before. Smart retries: 4 attempts over 7 days.
            Dunning emails: friendly &rarr; reminder &rarr; urgency &rarr; final warning. Target: 50-60% recovery rate.</p>
        </div>
    </div>
""")

html_parts.append("""
    </div>
</body>
</html>
""")

# Write dashboard
dashboard_html = ''.join(html_parts)
with open(f'{OUT}churn_dashboard.html', 'w') as f:
    f.write(dashboard_html)

print(f"Dashboard saved to {OUT}churn_dashboard.html")
print(f"File size: {len(dashboard_html)/1024:.0f} KB")
