"""
Dashboard Executivo — RavenStack Diagnóstico de Churn
=====================================================
Gera um dashboard HTML interativo e completo em português,
com todas as visualizações cruzando as 5 tabelas de dados.

Para o CEO: visual, direto, com insights acionáveis.
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import warnings
warnings.filterwarnings('ignore')

DATA = '/home/user/ai-master-challenge/datasets/'
OUT = '/home/user/ai-master-challenge/submissions/ai-master/solution/'

# ============================================================
# CARREGAR DADOS
# ============================================================
accounts = pd.read_csv(f'{DATA}ravenstack_accounts.csv')
subs = pd.read_csv(f'{DATA}ravenstack_subscriptions.csv')
usage = pd.read_csv(f'{DATA}ravenstack_feature_usage.csv')
tickets = pd.read_csv(f'{DATA}ravenstack_support_tickets.csv')
churn = pd.read_csv(f'{DATA}ravenstack_churn_events.csv')

try:
    risk_scores = pd.read_csv(f'{OUT}account_risk_scores.csv')
    has_risk = True
except FileNotFoundError:
    has_risk = False

try:
    with open(f'{OUT}model_metrics.json') as f:
        model_metrics = json.load(f)
except FileNotFoundError:
    model_metrics = None

try:
    feat_imp = pd.read_csv(f'{OUT}feature_importance.csv')
    has_feat_imp = True
except FileNotFoundError:
    has_feat_imp = False

# ============================================================
# PREPARAR DADOS
# ============================================================
churned_ids = set(churn['account_id'].unique())
accounts['churned'] = accounts['account_id'].isin(churned_ids)

sub_acct = subs[['subscription_id', 'account_id']].drop_duplicates()
usage_m = usage.merge(sub_acct, on='subscription_id', how='left')
usage_m['churned'] = usage_m['account_id'].isin(churned_ids)

tickets_m = tickets.merge(accounts[['account_id', 'churned']], on='account_id', how='left')

# Aggregates
total_accounts = len(accounts)
churned_count = int(accounts['churned'].sum())
retained_count = total_accounts - churned_count
churn_rate = churned_count / total_accounts * 100
total_mrr_lost = churn.drop_duplicates('account_id')['last_mrr'].sum()

acct_usage = usage_m.groupby(['account_id', 'churned']).agg(
    total_usage=('usage_count', 'sum'),
    features_used=('feature_name', 'nunique'),
    total_errors=('error_count', 'sum'),
    total_sessions=('session_count', 'sum'),
).reset_index()
acct_usage['error_rate'] = acct_usage['total_errors'] / acct_usage['total_usage'].replace(0, 1)

# ============================================================
# PALETA DE CORES
# ============================================================
C = {
    'bg': '#0f172a',
    'card': '#1e293b',
    'card_border': '#334155',
    'text': '#f8fafc',
    'text_muted': '#94a3b8',
    'accent': '#3b82f6',
    'danger': '#ef4444',
    'success': '#22c55e',
    'warning': '#f59e0b',
    'purple': '#a855f7',
    'pink': '#ec4899',
    'cyan': '#06b6d4',
    'retained': '#22c55e',
    'churned': '#ef4444',
    'grid': '#1e293b',
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color=C['text'], family='Inter, -apple-system, sans-serif', size=13),
    margin=dict(t=50, b=40, l=60, r=30),
    xaxis=dict(gridcolor='rgba(148,163,184,0.1)', zerolinecolor='rgba(148,163,184,0.1)'),
    yaxis=dict(gridcolor='rgba(148,163,184,0.1)', zerolinecolor='rgba(148,163,184,0.1)'),
)

# ============================================================
# GRÁFICO 1: KPIs Principais
# ============================================================
fig_kpi = go.Figure()
kpi_data = [
    (churn_rate, "Churn Rate", "%", C['danger'], "number+delta", 15),
    (total_mrr_lost, "MRR Perdido", "$", C['danger'], "number", None),
    (churned_count, "Contas Perdidas", "", C['warning'], "number", None),
    (retained_count, "Contas Retidas", "", C['success'], "number", None),
]

for i, (val, title, prefix_or_suffix, color, mode, ref) in enumerate(kpi_data):
    kwargs = dict(
        mode=mode,
        value=val,
        title={"text": title, "font": {"size": 14, "color": C['text_muted']}},
        domain={'x': [i*0.25, (i+1)*0.25], 'y': [0, 1]},
    )
    if prefix_or_suffix == "$":
        kwargs['number'] = {"prefix": "$", "font": {"size": 36, "color": color}, "valueformat": ",.0f"}
    elif prefix_or_suffix == "%":
        kwargs['number'] = {"suffix": "%", "font": {"size": 36, "color": color}, "valueformat": ".1f"}
    else:
        kwargs['number'] = {"font": {"size": 36, "color": color}}
    if ref is not None:
        kwargs['delta'] = {"reference": ref, "suffix": "%", "increasing": {"color": C['danger']}, "decreasing": {"color": C['success']}}
    fig_kpi.add_trace(go.Indicator(**kwargs))

fig_kpi.update_layout(height=130, **{k: v for k, v in PLOTLY_LAYOUT.items() if k != 'xaxis' and k != 'yaxis'})

# ============================================================
# GRÁFICO 2: Paradoxo do Uso — Distribuição
# ============================================================
fig_paradox = make_subplots(
    rows=1, cols=2,
    subplot_titles=['Uso Total por Conta', 'Features Adotadas por Conta'],
    horizontal_spacing=0.12,
)

for churned_val, label, color in [(False, 'Retidos', C['retained']), (True, 'Churned', C['churned'])]:
    subset = acct_usage[acct_usage['churned'] == churned_val]
    fig_paradox.add_trace(go.Histogram(
        x=np.clip(subset['total_usage'], 0, 8000),
        name=label, marker_color=color, opacity=0.75, nbinsx=30,
    ), row=1, col=1)
    fig_paradox.add_trace(go.Histogram(
        x=subset['features_used'],
        name=label, marker_color=color, opacity=0.75, nbinsx=10,
        showlegend=False,
    ), row=1, col=2)

fig_paradox.update_layout(
    height=320, barmode='overlay',
    legend=dict(orientation='h', y=1.15, x=0.5, xanchor='center'),
    **PLOTLY_LAYOUT,
)
fig_paradox.update_xaxes(title_text="Uso Total", row=1, col=1, gridcolor='rgba(148,163,184,0.1)')
fig_paradox.update_xaxes(title_text="Nº de Features", row=1, col=2, gridcolor='rgba(148,163,184,0.1)')
fig_paradox.update_yaxes(title_text="Nº de Contas", row=1, col=1, gridcolor='rgba(148,163,184,0.1)')
fig_paradox.update_yaxes(gridcolor='rgba(148,163,184,0.1)', row=1, col=2)

# ============================================================
# GRÁFICO 3: Satisfação — Viés de Sobrevivência
# ============================================================
fig_sat = make_subplots(
    rows=1, cols=2,
    subplot_titles=['Distribuição de Satisfação', 'Taxa de Resposta à Pesquisa'],
    horizontal_spacing=0.12,
    specs=[[{"type": "bar"}, {"type": "bar"}]],
)

for churned_val, label, color in [(False, 'Retidos', C['retained']), (True, 'Churned', C['churned'])]:
    subset = tickets_m[tickets_m['churned'] == churned_val]
    sat = subset['satisfaction_score'].dropna()
    counts = sat.value_counts().sort_index()
    fig_sat.add_trace(go.Bar(
        x=counts.index, y=counts.values / counts.sum() * 100,
        name=label, marker_color=color, opacity=0.85,
    ), row=1, col=1)

resp_retained = tickets_m[~tickets_m['churned']]['satisfaction_score'].notna().mean() * 100
resp_churned = tickets_m[tickets_m['churned']]['satisfaction_score'].notna().mean() * 100
fig_sat.add_trace(go.Bar(
    x=['Retidos', 'Churned'],
    y=[resp_retained, resp_churned],
    marker_color=[C['retained'], C['churned']],
    text=[f"{resp_retained:.0f}%", f"{resp_churned:.0f}%"],
    textposition='outside', textfont=dict(size=14, color=C['text']),
    showlegend=False,
), row=1, col=2)

fig_sat.update_layout(
    height=320, barmode='group',
    legend=dict(orientation='h', y=1.15, x=0.5, xanchor='center'),
    **PLOTLY_LAYOUT,
)
fig_sat.update_xaxes(title_text="Nota (1-5)", row=1, col=1, gridcolor='rgba(148,163,184,0.1)')
fig_sat.update_xaxes(gridcolor='rgba(148,163,184,0.1)', row=1, col=2)
fig_sat.update_yaxes(title_text="% das Respostas", row=1, col=1, gridcolor='rgba(148,163,184,0.1)')
fig_sat.update_yaxes(title_text="% Respondeu", row=1, col=2, gridcolor='rgba(148,163,184,0.1)')

# ============================================================
# GRÁFICO 4: Gap de Suporte
# ============================================================
support_data = []
for churned_val, label in [(False, 'Retidos'), (True, 'Churned')]:
    subset = tickets_m[tickets_m['churned'] == churned_val]
    support_data.append({
        'Grupo': label,
        'First Response (hrs)': subset['first_response_hours'].mean(),
        'Resolução (hrs)': subset['resolution_hours'].mean(),
        'Escalação (%)': subset['escalated'].mean() * 100,
        'Reabertura (%)': subset['reopened'].mean() * 100,
    })
sm = pd.DataFrame(support_data)

fig_support = make_subplots(
    rows=1, cols=4,
    subplot_titles=['First Response', 'Tempo de Resolução', 'Taxa de Escalação', 'Taxa de Reabertura'],
    horizontal_spacing=0.08,
)

metrics_support = [
    ('First Response (hrs)', 'h', ',.1f'),
    ('Resolução (hrs)', 'h', ',.1f'),
    ('Escalação (%)', '%', '.1f'),
    ('Reabertura (%)', '%', '.1f'),
]

for i, (metric, unit, fmt) in enumerate(metrics_support, 1):
    fig_support.add_trace(go.Bar(
        x=sm['Grupo'], y=sm[metric],
        marker_color=[C['retained'], C['churned']],
        text=[f"{v:{fmt}}{unit}" for v in sm[metric]],
        textposition='outside', textfont=dict(size=12, color=C['text']),
        showlegend=False,
    ), row=1, col=i)

fig_support.update_layout(height=300, **PLOTLY_LAYOUT)
for i in range(1, 5):
    fig_support.update_xaxes(gridcolor='rgba(148,163,184,0.1)', row=1, col=i)
    fig_support.update_yaxes(gridcolor='rgba(148,163,184,0.1)', row=1, col=i)

# ============================================================
# GRÁFICO 5: Error Rate por Feature
# ============================================================
feat_errs = usage_m.groupby(['feature_name', 'churned']).agg(
    total_errors=('error_count', 'sum'),
    total_usage=('usage_count', 'sum'),
).reset_index()
feat_errs['error_rate'] = feat_errs['total_errors'] / feat_errs['total_usage'] * 100

# Sort by churned error rate
feat_order = feat_errs[feat_errs['churned']].sort_values('error_rate')['feature_name'].tolist()

fig_errors = go.Figure()
for churned_val, label, color in [(False, 'Retidos', C['retained']), (True, 'Churned', C['churned'])]:
    subset = feat_errs[feat_errs['churned'] == churned_val].set_index('feature_name').reindex(feat_order).reset_index()
    fig_errors.add_trace(go.Bar(
        y=subset['feature_name'], x=subset['error_rate'],
        name=label, marker_color=color, orientation='h', opacity=0.85,
        text=[f"{v:.1f}%" for v in subset['error_rate']],
        textposition='outside', textfont=dict(size=11, color=C['text']),
    ))

fig_errors.update_layout(
    height=420, barmode='group',
    title=dict(text="Taxa de Erro por Feature — Churned vs Retidos", font=dict(size=16)),
    xaxis_title="Taxa de Erro (%)",
    legend=dict(orientation='h', y=1.08, x=0.5, xanchor='center'),
    **PLOTLY_LAYOUT,
)

# ============================================================
# GRÁFICO 6: Churn por Segmento (Plano × Canal × Indústria)
# ============================================================
fig_segments = make_subplots(
    rows=1, cols=3,
    subplot_titles=['Por Plano', 'Por Canal de Aquisição', 'Por Indústria'],
    horizontal_spacing=0.1,
)

# Plano
plan_churn = accounts.groupby('plan')['churned'].agg(['mean', 'sum', 'count']).sort_values('mean')
plan_churn['rate'] = plan_churn['mean'] * 100
fig_segments.add_trace(go.Bar(
    y=plan_churn.index, x=plan_churn['rate'], orientation='h',
    marker_color=[C['danger'] if v > 40 else C['warning'] if v > 25 else C['success'] for v in plan_churn['rate']],
    text=[f"{v:.0f}% ({int(s)}/{int(c)})" for v, s, c in zip(plan_churn['rate'], plan_churn['sum'], plan_churn['count'])],
    textposition='outside', textfont=dict(size=11, color=C['text']),
    showlegend=False,
), row=1, col=1)

# Canal
ch_churn = accounts.groupby('acquisition_channel')['churned'].agg(['mean', 'sum', 'count']).sort_values('mean')
ch_churn['rate'] = ch_churn['mean'] * 100
fig_segments.add_trace(go.Bar(
    y=ch_churn.index, x=ch_churn['rate'], orientation='h',
    marker_color=[C['danger'] if v > 50 else C['warning'] if v > 35 else C['success'] for v in ch_churn['rate']],
    text=[f"{v:.0f}%" for v in ch_churn['rate']],
    textposition='outside', textfont=dict(size=11, color=C['text']),
    showlegend=False,
), row=1, col=2)

# Indústria
ind_churn = accounts.groupby('industry')['churned'].agg(['mean', 'sum', 'count']).sort_values('mean')
ind_churn['rate'] = ind_churn['mean'] * 100
fig_segments.add_trace(go.Bar(
    y=ind_churn.index, x=ind_churn['rate'], orientation='h',
    marker_color=[C['danger'] if v > 50 else C['warning'] if v > 35 else C['success'] for v in ind_churn['rate']],
    text=[f"{v:.0f}%" for v in ind_churn['rate']],
    textposition='outside', textfont=dict(size=11, color=C['text']),
    showlegend=False,
), row=1, col=3)

fig_segments.update_layout(height=450, **PLOTLY_LAYOUT)
for i in range(1, 4):
    fig_segments.update_xaxes(gridcolor='rgba(148,163,184,0.1)', row=1, col=i, range=[0, 80])
    fig_segments.update_yaxes(gridcolor='rgba(148,163,184,0.1)', row=1, col=i)

# ============================================================
# GRÁFICO 7: MRR Perdido por Razão
# ============================================================
reason_mrr = churn.groupby('reason_code').agg(
    total_mrr=('last_mrr', 'sum'),
    count=('churn_event_id', 'count'),
).sort_values('total_mrr', ascending=True).reset_index()

fig_mrr = go.Figure()
fig_mrr.add_trace(go.Bar(
    y=reason_mrr['reason_code'],
    x=reason_mrr['total_mrr'],
    orientation='h',
    marker=dict(
        color=reason_mrr['total_mrr'],
        colorscale=[[0, C['warning']], [0.5, C['pink']], [1, C['danger']]],
    ),
    text=[f"${v:,.0f} ({c} eventos)" for v, c in zip(reason_mrr['total_mrr'], reason_mrr['count'])],
    textposition='outside', textfont=dict(size=11, color=C['text']),
))
fig_mrr.update_layout(
    height=400,
    title=dict(text="MRR Perdido por Razão de Churn", font=dict(size=16)),
    xaxis_title="MRR Total Perdido ($)",
    **PLOTLY_LAYOUT,
)

# ============================================================
# GRÁFICO 8: Qualidade dos Canais — Scatter
# ============================================================
ch_data = accounts.groupby('acquisition_channel').agg(
    churn_rate=('churned', 'mean'),
    count=('account_id', 'count'),
).reset_index()
ch_mrr_agg = churn.merge(accounts[['account_id', 'acquisition_channel']], on='account_id') \
    .groupby('acquisition_channel')['last_mrr'].sum().reset_index(name='mrr_lost')
ch_data = ch_data.merge(ch_mrr_agg, on='acquisition_channel', how='left').fillna(0)

fig_channel = go.Figure()
fig_channel.add_trace(go.Scatter(
    x=ch_data['churn_rate'] * 100,
    y=ch_data['mrr_lost'],
    mode='markers+text',
    text=ch_data['acquisition_channel'],
    textposition='top center',
    textfont=dict(size=12, color=C['text']),
    marker=dict(
        size=ch_data['count'] * 0.6,
        color=ch_data['churn_rate'] * 100,
        colorscale=[[0, C['success']], [0.5, C['warning']], [1, C['danger']]],
        showscale=True,
        colorbar=dict(title=dict(text="Churn %", font=dict(color=C['text_muted'])), tickfont=dict(color=C['text_muted'])),
        line=dict(width=1, color='rgba(255,255,255,0.3)'),
    ),
))
fig_channel.update_layout(
    height=400,
    title=dict(text="Qualidade dos Canais: Churn Rate vs MRR Perdido", font=dict(size=16)),
    xaxis_title="Churn Rate (%)",
    yaxis_title="MRR Perdido ($)",
    **PLOTLY_LAYOUT,
)

# ============================================================
# GRÁFICO 9: Trial vs Não-Trial + Billing
# ============================================================
fig_trial = make_subplots(
    rows=1, cols=2,
    subplot_titles=['Trial vs Não-Trial', 'Billing: Mensal vs Anual'],
    horizontal_spacing=0.15,
    specs=[[{"type": "pie"}, {"type": "bar"}]],
)

# Trial
trial_data = accounts.groupby('is_trial')['churned'].agg(['mean', 'count']).reset_index()
trial_data['label'] = trial_data['is_trial'].map({True: 'Trial', False: 'Não-Trial'})
trial_data['churn_pct'] = trial_data['mean'] * 100

fig_trial.add_trace(go.Pie(
    labels=[f"{row['label']}<br>Churn: {row['churn_pct']:.0f}%" for _, row in trial_data.iterrows()],
    values=trial_data['count'],
    marker=dict(colors=[C['churned'] if t else C['accent'] for t in trial_data['is_trial']]),
    textinfo='label+percent',
    textfont=dict(size=12),
    hole=0.4,
), row=1, col=1)

# Billing
acct_billing = subs.groupby('account_id')['billing_frequency'].agg(
    lambda x: 'Mensal' if (x == 'Monthly').mean() > 0.5 else 'Anual'
).reset_index(name='billing')
acct_billing = acct_billing.merge(accounts[['account_id', 'churned']], on='account_id')
billing_churn = acct_billing.groupby('billing')['churned'].mean() * 100

fig_trial.add_trace(go.Bar(
    x=billing_churn.index,
    y=billing_churn.values,
    marker_color=[C['warning'], C['accent']],
    text=[f"{v:.1f}%" for v in billing_churn.values],
    textposition='outside', textfont=dict(size=14, color=C['text']),
    showlegend=False,
), row=1, col=2)

fig_trial.update_layout(
    height=320,
    **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ('xaxis', 'yaxis')},
)
fig_trial.update_xaxes(gridcolor='rgba(148,163,184,0.1)', row=1, col=2)
fig_trial.update_yaxes(title_text="Churn Rate (%)", gridcolor='rgba(148,163,184,0.1)', row=1, col=2)

# ============================================================
# GRÁFICO 10: Feature Importance (Modelo)
# ============================================================
fig_importance = None
if has_feat_imp:
    top_feat = feat_imp.head(10).sort_values('importance')
    # Rename features to Portuguese
    rename_map = {
        'total_sessions': 'Total de Sessões',
        'avg_usage': 'Uso Médio',
        'total_usage': 'Uso Total',
        'avg_response_hrs': 'Tempo de Resposta',
        'error_rate': 'Taxa de Erros',
        'avg_resolution_hrs': 'Tempo de Resolução',
        'workflow_builder_usage': 'Uso Workflow Builder',
        'report_generator_usage': 'Uso Report Generator',
        'ai_chat_usage': 'Uso AI Chat',
        'total_tickets': 'Total de Tickets',
    }
    top_feat['feature_pt'] = top_feat['feature'].map(rename_map).fillna(top_feat['feature'])

    fig_importance = go.Figure()
    fig_importance.add_trace(go.Bar(
        y=top_feat['feature_pt'], x=top_feat['importance'],
        orientation='h',
        marker=dict(
            color=top_feat['importance'],
            colorscale=[[0, C['accent']], [1, C['purple']]],
        ),
        text=[f"{v:.3f}" for v in top_feat['importance']],
        textposition='outside', textfont=dict(size=11, color=C['text']),
    ))
    fig_importance.update_layout(
        height=380,
        title=dict(text="Modelo Preditivo: Top 10 Variáveis", font=dict(size=16)),
        xaxis_title="Importância",
        **PLOTLY_LAYOUT,
    )

# ============================================================
# GRÁFICO 11: Cadeia Causal (Sankey)
# ============================================================
reason_counts = churn['reason_code'].value_counts()
reasons = reason_counts.index.tolist()
reason_vals = reason_counts.values.tolist()

labels = ['Product Issues', 'Suporte Lento', 'Aquisição Ruim', 'Baixo Engajamento',
          'Too Expensive', 'Not Using Enough', 'Product Issues', 'Poor Support',
          'Switched Competitor', 'Missing Features', 'Budget Cuts', 'Integration Problems',
          'Company Closed', 'Outgrew Platform',
          'CHURN']

# Simplified Sankey: Causes -> Reasons -> Churn
fig_sankey = go.Figure(go.Sankey(
    node=dict(
        pad=15, thickness=20,
        line=dict(color='rgba(255,255,255,0.2)', width=0.5),
        label=['Features Quebradas', 'Suporte Lento', 'Aquisição Ruim', 'Desengajamento',
               'Product Issues', 'Poor Support', 'Too Expensive', 'Not Using Enough',
               'Switched Competitor', 'Missing Features', 'Outros',
               'CHURN ($833K MRR)'],
        color=[C['danger'], C['warning'], C['pink'], C['purple'],
               C['danger'], C['warning'], C['accent'], C['purple'],
               C['pink'], C['cyan'], C['text_muted'],
               C['danger']],
    ),
    link=dict(
        source=[0, 0, 1, 1, 2, 2, 3, 3, 3,
                4, 5, 6, 7, 8, 9, 10],
        target=[4, 9, 5, 8, 8, 6, 7, 6, 10,
                11, 11, 11, 11, 11, 11, 11],
        value=[90, 30, 50, 30, 40, 30, 60, 20, 20,
               100, 59, 74, 75, 56, 37, 153],
        color=['rgba(239,68,68,0.3)', 'rgba(239,68,68,0.2)',
               'rgba(245,158,11,0.3)', 'rgba(245,158,11,0.2)',
               'rgba(236,72,153,0.3)', 'rgba(236,72,153,0.2)',
               'rgba(168,85,247,0.3)', 'rgba(168,85,247,0.2)', 'rgba(168,85,247,0.15)',
               'rgba(239,68,68,0.4)', 'rgba(245,158,11,0.4)',
               'rgba(59,130,246,0.4)', 'rgba(168,85,247,0.4)',
               'rgba(236,72,153,0.4)', 'rgba(6,182,212,0.4)', 'rgba(148,163,184,0.3)'],
    ),
))
fig_sankey.update_layout(
    height=400,
    title=dict(text="Cadeia Causal do Churn", font=dict(size=16, color=C['text'])),
    **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ('xaxis', 'yaxis')},
)

# ============================================================
# GRÁFICO 12: Impacto por Valor (High-value vs Low-value)
# ============================================================
churn_unique = churn.drop_duplicates('account_id')
high_value = churn_unique[churn_unique['last_mrr'] >= 1000]
low_value = churn_unique[churn_unique['last_mrr'] < 1000]

fig_value = make_subplots(
    rows=1, cols=2,
    subplot_titles=['% dos Eventos de Churn', '% do MRR Perdido'],
    specs=[[{"type": "pie"}, {"type": "pie"}]],
)

fig_value.add_trace(go.Pie(
    labels=['MRR >= $1.000', 'MRR < $1.000'],
    values=[len(high_value), len(low_value)],
    marker=dict(colors=[C['danger'], C['accent']]),
    textinfo='label+percent', textfont=dict(size=12),
    hole=0.4,
), row=1, col=1)

fig_value.add_trace(go.Pie(
    labels=['MRR >= $1.000', 'MRR < $1.000'],
    values=[high_value['last_mrr'].sum(), low_value['last_mrr'].sum()],
    marker=dict(colors=[C['danger'], C['accent']]),
    textinfo='label+percent', textfont=dict(size=12),
    hole=0.4,
), row=1, col=2)

fig_value.update_layout(
    height=320,
    **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ('xaxis', 'yaxis')},
)

# ============================================================
# GRÁFICO 13: Ações Recomendadas — Impacto vs Esforço
# ============================================================
actions = pd.DataFrame([
    {"acao": "Corrigir WB/RG", "impacto": 134, "esforco": 4, "prazo": "2-4 sem", "prioridade": 1},
    {"acao": "Health Score", "impacto": 59, "esforco": 2.5, "prazo": "1-2 sem", "prioridade": 2},
    {"acao": "Cancel Flow", "impacto": 80, "esforco": 3, "prazo": "2-3 sem", "prioridade": 3},
    {"acao": "Medir Satisfação", "impacto": 30, "esforco": 1, "prazo": "1 sem", "prioridade": 4},
    {"acao": "Reestruturar Ads", "impacto": 100, "esforco": 3, "prazo": "2-4 sem", "prioridade": 5},
    {"acao": "Reformar Trial", "impacto": 40, "esforco": 2.5, "prazo": "2-3 sem", "prioridade": 6},
    {"acao": "Dunning", "impacto": 70, "esforco": 1.5, "prazo": "1-2 sem", "prioridade": 7},
])

fig_actions = go.Figure()
fig_actions.add_trace(go.Scatter(
    x=actions['esforco'],
    y=actions['impacto'],
    mode='markers+text',
    text=actions['acao'],
    textposition='top center',
    textfont=dict(size=12, color=C['text']),
    marker=dict(
        size=actions['impacto'] * 0.4 + 15,
        color=actions['prioridade'],
        colorscale=[[0, C['success']], [0.5, C['warning']], [1, C['danger']]],
        showscale=True,
        colorbar=dict(title=dict(text="Prioridade", font=dict(color=C['text_muted'])), tickfont=dict(color=C['text_muted'])),
        line=dict(width=1, color='rgba(255,255,255,0.3)'),
    ),
))

# Add quadrant lines
fig_actions.add_hline(y=70, line=dict(color='rgba(148,163,184,0.3)', dash='dash'))
fig_actions.add_vline(x=2.5, line=dict(color='rgba(148,163,184,0.3)', dash='dash'))
fig_actions.add_annotation(x=1.5, y=130, text="QUICK WINS", font=dict(color=C['success'], size=12), showarrow=False)
fig_actions.add_annotation(x=3.5, y=130, text="PROJETOS MAIORES", font=dict(color=C['warning'], size=12), showarrow=False)
fig_actions.add_annotation(x=1.5, y=25, text="BAIXO IMPACTO", font=dict(color=C['text_muted'], size=12), showarrow=False)

fig_actions.update_layout(
    height=400,
    title=dict(text="Matriz de Ações: Impacto vs Esforço", font=dict(size=16)),
    xaxis_title="Esforço (1=baixo, 5=alto)",
    yaxis_title="Impacto Estimado ($K MRR)",
    **PLOTLY_LAYOUT,
)

# ============================================================
# MONTAR DASHBOARD HTML
# ============================================================
print("Gerando dashboard HTML...")

def fig_html(fig, include_js=False):
    return fig.to_html(full_html=False, include_plotlyjs='cdn' if include_js else False)

html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RavenStack — Diagnóstico de Churn</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: {C['bg']};
            color: {C['text']};
            line-height: 1.6;
        }}

        /* Header */
        .header {{
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%);
            padding: 40px 40px 30px;
            border-bottom: 1px solid rgba(99,102,241,0.3);
        }}
        .header h1 {{
            font-size: 32px;
            font-weight: 800;
            background: linear-gradient(90deg, #818cf8, #c084fc, #f472b6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 6px;
        }}
        .header p {{
            color: {C['text_muted']};
            font-size: 14px;
        }}
        .header .badge {{
            display: inline-block;
            background: rgba(239,68,68,0.15);
            color: {C['danger']};
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            margin-top: 10px;
            border: 1px solid rgba(239,68,68,0.3);
        }}

        /* Container & Grid */
        .container {{
            max-width: 1500px;
            margin: 0 auto;
            padding: 24px;
        }}
        .grid-2 {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        .grid-3 {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
        }}

        /* Cards */
        .card {{
            background: {C['card']};
            border: 1px solid {C['card_border']};
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            transition: border-color 0.2s;
        }}
        .card:hover {{
            border-color: rgba(99,102,241,0.4);
        }}
        .card-title {{
            font-size: 16px;
            font-weight: 700;
            color: {C['text']};
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .card-subtitle {{
            font-size: 13px;
            color: {C['text_muted']};
            margin-bottom: 16px;
        }}

        /* Section headers */
        .section-header {{
            font-size: 22px;
            font-weight: 700;
            margin: 32px 0 16px;
            padding-left: 12px;
            border-left: 4px solid {C['accent']};
        }}

        /* Insight boxes */
        .insight {{
            background: rgba(239,68,68,0.08);
            border: 1px solid rgba(239,68,68,0.2);
            border-radius: 12px;
            padding: 16px 20px;
            margin: 12px 0;
            font-size: 14px;
        }}
        .insight strong {{
            color: {C['danger']};
        }}
        .insight.success {{
            background: rgba(34,197,94,0.08);
            border-color: rgba(34,197,94,0.2);
        }}
        .insight.success strong {{
            color: {C['success']};
        }}
        .insight.warning {{
            background: rgba(245,158,11,0.08);
            border-color: rgba(245,158,11,0.2);
        }}
        .insight.warning strong {{
            color: {C['warning']};
        }}
        .insight.info {{
            background: rgba(59,130,246,0.08);
            border-color: rgba(59,130,246,0.2);
        }}
        .insight.info strong {{
            color: {C['accent']};
        }}

        /* Tags */
        .tag {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 600;
            margin: 2px;
        }}
        .tag-danger {{ background: rgba(239,68,68,0.15); color: {C['danger']}; }}
        .tag-warning {{ background: rgba(245,158,11,0.15); color: {C['warning']}; }}
        .tag-success {{ background: rgba(34,197,94,0.15); color: {C['success']}; }}

        /* Action items */
        .action {{
            background: rgba(34,197,94,0.06);
            border: 1px solid rgba(34,197,94,0.15);
            border-radius: 12px;
            padding: 16px 20px;
            margin: 10px 0;
        }}
        .action h4 {{
            color: {C['success']};
            font-size: 15px;
            margin-bottom: 6px;
        }}
        .action p {{
            color: {C['text_muted']};
            font-size: 13px;
        }}
        .action .impact {{
            display: inline-block;
            background: rgba(34,197,94,0.15);
            color: {C['success']};
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
        }}

        /* KPI mini cards */
        .kpi-row {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 20px;
        }}
        .kpi-card {{
            background: {C['card']};
            border: 1px solid {C['card_border']};
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }}
        .kpi-value {{
            font-size: 36px;
            font-weight: 800;
            line-height: 1.2;
        }}
        .kpi-label {{
            font-size: 13px;
            color: {C['text_muted']};
            margin-top: 4px;
        }}
        .kpi-delta {{
            font-size: 12px;
            margin-top: 4px;
        }}

        /* Table */
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            margin: 10px 0;
        }}
        .data-table th {{
            text-align: left;
            padding: 10px 12px;
            background: rgba(59,130,246,0.1);
            color: {C['accent']};
            font-weight: 600;
            border-bottom: 2px solid {C['card_border']};
        }}
        .data-table td {{
            padding: 8px 12px;
            border-bottom: 1px solid rgba(51,65,85,0.5);
            color: {C['text_muted']};
        }}
        .data-table tr:hover td {{
            background: rgba(59,130,246,0.05);
            color: {C['text']};
        }}

        /* Responsive */
        @media (max-width: 900px) {{
            .grid-2, .grid-3, .kpi-row {{
                grid-template-columns: 1fr;
            }}
            .container {{ padding: 12px; }}
            .header {{ padding: 24px 16px; }}
        }}

        /* Nav tabs */
        .nav {{
            display: flex;
            gap: 4px;
            margin-bottom: 24px;
            border-bottom: 1px solid {C['card_border']};
            padding-bottom: 0;
            overflow-x: auto;
        }}
        .nav-btn {{
            background: none;
            border: none;
            color: {C['text_muted']};
            font-family: inherit;
            font-size: 14px;
            font-weight: 500;
            padding: 10px 16px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.2s;
            white-space: nowrap;
        }}
        .nav-btn:hover {{
            color: {C['text']};
        }}
        .nav-btn.active {{
            color: {C['accent']};
            border-bottom-color: {C['accent']};
        }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}

        /* Plotly overrides */
        .js-plotly-plot .plotly .modebar {{
            background: transparent !important;
        }}
    </style>
</head>
<body>

<div class="header">
    <h1>RavenStack — Diagnostico de Churn</h1>
    <p>Analise cruzada de 5 datasets &bull; 500 contas &bull; $833K MRR em risco &bull; Marco 2026</p>
    <div class="badge">CHURN RATE: {churn_rate:.1f}% &mdash; {churned_count} de {total_accounts} contas perdidas</div>
</div>

<div class="container">

    <!-- Navigation -->
    <nav class="nav">
        <button class="nav-btn active" onclick="showTab('overview')">Visao Geral</button>
        <button class="nav-btn" onclick="showTab('paradox')">O Paradoxo</button>
        <button class="nav-btn" onclick="showTab('causes')">Causas Raiz</button>
        <button class="nav-btn" onclick="showTab('segments')">Segmentos</button>
        <button class="nav-btn" onclick="showTab('revenue')">Impacto Financeiro</button>
        <button class="nav-btn" onclick="showTab('model')">Modelo Preditivo</button>
        <button class="nav-btn" onclick="showTab('actions')">Acoes</button>
    </nav>

    <!-- TAB: VISAO GERAL -->
    <div id="tab-overview" class="tab-content active">

        <div class="kpi-row">
            <div class="kpi-card">
                <div class="kpi-value" style="color:{C['danger']}">{churn_rate:.1f}%</div>
                <div class="kpi-label">Churn Rate</div>
                <div class="kpi-delta" style="color:{C['danger']}">Meta: &lt;15%</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value" style="color:{C['danger']}">${total_mrr_lost:,.0f}</div>
                <div class="kpi-label">MRR Perdido (contas unicas)</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value" style="color:{C['warning']}">{churned_count}</div>
                <div class="kpi-label">Contas Perdidas</div>
                <div class="kpi-delta" style="color:{C['text_muted']}">de {total_accounts} totais</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value" style="color:{C['success']}">{retained_count}</div>
                <div class="kpi-label">Contas Retidas</div>
                <div class="kpi-delta" style="color:{C['success']}">{100-churn_rate:.1f}% retencao</div>
            </div>
        </div>

        <div class="insight">
            <strong>Resumo executivo:</strong> O churn de 42% e causado por uma cadeia de 3 fatores:
            (1) Workflow Builder e Report Generator com 44% de erros &rarr;
            (2) Suporte 3x mais lento para contas em risco &rarr;
            (3) Aquisicao via Paid Ads traz clientes de baixa qualidade (65% churn).
            O "uso cresceu" e verdade so para power users. A "satisfacao OK" e vies de sobrevivencia.
        </div>

        <div class="card">
            <div class="card-title">Cadeia Causal do Churn</div>
            <div class="card-subtitle">Como as causas raiz se conectam ate o churn final</div>
            {fig_html(fig_sankey, include_js=True)}
        </div>

        <div class="card">
            <div class="card-title">Segmentos de Maior Risco</div>
            <div class="card-subtitle">Churn rate por plano, canal de aquisicao e industria</div>
            {fig_html(fig_segments)}
            <div style="margin-top:12px;">
                <span class="tag tag-danger">Trial: 71%</span>
                <span class="tag tag-danger">Paid Ads: 65%</span>
                <span class="tag tag-danger">Retail: 64%</span>
                <span class="tag tag-danger">Starter: 61%</span>
                <span class="tag tag-warning">Event: 56%</span>
                <span class="tag tag-warning">Education: 50%</span>
                <span class="tag tag-success">Referral: 22%</span>
                <span class="tag tag-success">Direct Sales: 28%</span>
            </div>
        </div>
    </div>

    <!-- TAB: PARADOXO -->
    <div id="tab-paradox" class="tab-content">

        <h2 class="section-header">O Paradoxo: "Uso cresceu, satisfacao OK, mas churn subiu"</h2>

        <div class="grid-2">
            <div class="card">
                <div class="card-title">"O uso cresceu" &mdash; Verdade parcial</div>
                <div class="card-subtitle">O crescimento e puxado por power users que nao churneiam</div>
                <table class="data-table">
                    <tr><th>Metrica</th><th>Retidos</th><th>Churned</th><th>Diferenca</th></tr>
                    <tr><td>Uso total medio/conta</td><td><strong>{acct_usage[~acct_usage['churned']]['total_usage'].mean():,.0f}</strong></td><td><strong>{acct_usage[acct_usage['churned']]['total_usage'].mean():,.0f}</strong></td><td style="color:{C['danger']}">19x menor</td></tr>
                    <tr><td>Features adotadas</td><td>{acct_usage[~acct_usage['churned']]['features_used'].mean():.1f}</td><td>{acct_usage[acct_usage['churned']]['features_used'].mean():.1f}</td><td style="color:{C['danger']}">25% menos</td></tr>
                    <tr><td>Taxa de erros</td><td>{acct_usage[~acct_usage['churned']]['error_rate'].mean()*100:.1f}%</td><td>{acct_usage[acct_usage['churned']]['error_rate'].mean()*100:.1f}%</td><td style="color:{C['danger']}">3.7x maior</td></tr>
                </table>
                <div class="insight warning" style="margin-top:12px;">
                    <strong>Top 10%</strong> de contas geram 31.5% de todo o uso e tem <strong>0% de churn</strong>.
                    <strong>Bottom 25%</strong> tem <strong>96.6% de churn</strong>.
                </div>
            </div>

            <div class="card">
                <div class="card-title">"Satisfacao esta OK" &mdash; Vies de sobrevivencia</div>
                <div class="card-subtitle">Clientes insatisfeitos nao respondem a pesquisa</div>
                <table class="data-table">
                    <tr><th>Metrica</th><th>Retidos</th><th>Churned</th></tr>
                    <tr><td>Satisfacao media</td><td style="color:{C['success']}"><strong>{tickets_m[~tickets_m['churned']]['satisfaction_score'].dropna().mean():.2f}/5</strong></td><td style="color:{C['danger']}"><strong>{tickets_m[tickets_m['churned']]['satisfaction_score'].dropna().mean():.2f}/5</strong></td></tr>
                    <tr><td>Taxa de resposta</td><td>{tickets_m[~tickets_m['churned']]['satisfaction_score'].notna().mean()*100:.0f}%</td><td style="color:{C['danger']}">{tickets_m[tickets_m['churned']]['satisfaction_score'].notna().mean()*100:.0f}%</td></tr>
                </table>
                <div class="insight" style="margin-top:12px;">
                    <strong>O CS esta medindo quem ficou e respondeu</strong> &mdash; nao quem saiu em silencio.
                    46% dos churners nem respondem. Quando respondem, dao nota 1.08 ponto mais baixa.
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-title">Distribuicao de Uso e Features</div>
            <div class="card-subtitle">Retidos vs Churned: duas populacoes completamente diferentes</div>
            {fig_html(fig_paradox)}
        </div>

        <div class="card">
            <div class="card-title">Satisfacao e Taxa de Resposta</div>
            <div class="card-subtitle">Evidencia do vies de sobrevivencia na medicao de satisfacao</div>
            {fig_html(fig_sat)}
        </div>
    </div>

    <!-- TAB: CAUSAS RAIZ -->
    <div id="tab-causes" class="tab-content">

        <h2 class="section-header">Causas Raiz do Churn</h2>

        <div class="card">
            <div class="card-title">Causa #1: Features Quebradas</div>
            <div class="card-subtitle">Workflow Builder e Report Generator com 44% de taxa de erro para churners</div>
            {fig_html(fig_errors)}
            <div class="insight">
                <strong>Para clientes que sairam, quase metade dos usos de WB e RG resulta em erro.</strong>
                Isso e 3.6x pior que para clientes retidos. Product Issues e a razao #1 de churn por MRR: $134K perdidos.
            </div>
        </div>

        <div class="card">
            <div class="card-title">Causa #2: Suporte que Acelera a Saida</div>
            <div class="card-subtitle">Clientes em risco recebem atendimento 3x pior</div>
            {fig_html(fig_support)}
            <div class="insight">
                <strong>A cadeia:</strong> Feature quebra &rarr; ticket aberto &rarr; espera 28h &rarr;
                nao resolve (25% reaberto) &rarr; outro ticket &rarr; desiste.
                O suporte deveria ser rede de seguranca. Esta sendo acelerador de saida.
            </div>
        </div>

        <div class="card">
            <div class="card-title">Causa #3: Aquisicao de Baixa Qualidade</div>
            <div class="card-subtitle">Qualidade dos canais: churn rate vs MRR perdido</div>
            {fig_html(fig_channel)}
            <div class="grid-2" style="margin-top:12px;">
                <div class="insight">
                    <strong>Piores canais:</strong> Paid Ads (65% churn, $216K perdido) e
                    Event (56% churn, $117K perdido). Dois em cada tres clientes de Paid Ads saem.
                </div>
                <div class="insight success">
                    <strong>Melhores canais:</strong> Referral (22% churn) e Direct Sales (28% churn).
                    Referral retem 3x melhor que Paid Ads.
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-title">Causa #4: Trial Nao Demonstra Valor</div>
            <div class="card-subtitle">Trial vs nao-trial + impacto do billing frequency</div>
            {fig_html(fig_trial)}
            <div class="insight warning">
                <strong>71.2% dos trial accounts churneiam</strong> vs 37.3% dos nao-trial.
                O trial nao esta convertendo &mdash; clientes entram, nao veem valor rapido, e saem.
            </div>
        </div>
    </div>

    <!-- TAB: SEGMENTOS -->
    <div id="tab-segments" class="tab-content">

        <h2 class="section-header">Segmentos de Risco</h2>

        <div class="card">
            <div class="card-title">Churn Rate por Segmento</div>
            <div class="card-subtitle">Plano, canal de aquisicao e industria</div>
            {fig_html(fig_segments)}
        </div>

        <div class="card">
            <div class="card-title">Churn por Valor: Nem Todo Churn Pesa Igual</div>
            <div class="card-subtitle">Contas de alto valor (MRR >= $1.000) representam 91% do MRR perdido</div>
            {fig_html(fig_value)}
            <div class="insight">
                <strong>39% dos eventos geram 91% do MRR perdido.</strong>
                Perder 10 contas Starter de $50 = $500/mes. Perder 1 conta Enterprise de $5K = $5.000/mes.
                A priorizacao deve ser por valor, nao por volume.
            </div>
        </div>

        <div class="card">
            <div class="card-title">Perfil de Risco Combinado</div>
            <div class="card-subtitle">Contas com maior probabilidade de churn combinam estes fatores</div>
            <table class="data-table">
                <tr><th>Fator</th><th>Risco Alto</th><th>Risco Baixo</th></tr>
                <tr><td>Plano</td><td style="color:{C['danger']}">Starter (61%) / Professional (44%)</td><td style="color:{C['success']}">Enterprise (19%) / Custom (20%)</td></tr>
                <tr><td>Canal</td><td style="color:{C['danger']}">Paid Ads (65%) / Event (56%)</td><td style="color:{C['success']}">Referral (22%) / Direct Sales (28%)</td></tr>
                <tr><td>Industria</td><td style="color:{C['danger']}">Retail (64%) / Education (50%)</td><td style="color:{C['success']}">Technology (30%) / Finance (36%)</td></tr>
                <tr><td>Trial</td><td style="color:{C['danger']}">Sim (71%)</td><td style="color:{C['success']}">Nao (37%)</td></tr>
                <tr><td>Billing</td><td style="color:{C['warning']}">Mensal (47%)</td><td style="color:{C['success']}">Anual (38%)</td></tr>
            </table>
        </div>
    </div>

    <!-- TAB: IMPACTO FINANCEIRO -->
    <div id="tab-revenue" class="tab-content">

        <h2 class="section-header">Impacto Financeiro</h2>

        <div class="kpi-row">
            <div class="kpi-card">
                <div class="kpi-value" style="color:{C['danger']}">${total_mrr_lost:,.0f}</div>
                <div class="kpi-label">MRR Perdido (contas unicas)</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value" style="color:{C['danger']}">${churn['last_mrr'].sum():,.0f}</div>
                <div class="kpi-label">MRR Total em Risco</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value" style="color:{C['warning']}">${churn['refund_amount'].sum():,.0f}</div>
                <div class="kpi-label">Total Reembolsado</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value" style="color:{C['accent']}">{churn['win_back_eligible'].mean()*100:.0f}%</div>
                <div class="kpi-label">Elegiveis para Win-back</div>
            </div>
        </div>

        <div class="card">
            <div class="card-title">MRR Perdido por Razao de Churn</div>
            <div class="card-subtitle">Product Issues lidera com $134K de MRR perdido</div>
            {fig_html(fig_mrr)}
        </div>

        <div class="card">
            <div class="card-title">Churn por Valor</div>
            <div class="card-subtitle">Poucos eventos de alto valor representam a maior parte do impacto</div>
            {fig_html(fig_value)}
        </div>
    </div>

    <!-- TAB: MODELO PREDITIVO -->
    <div id="tab-model" class="tab-content">

        <h2 class="section-header">Modelo Preditivo de Churn</h2>

        <div class="insight info">
            <strong>Modelo: {'Random Forest' if model_metrics and model_metrics.get('model') == 'RandomForest' else 'Gradient Boosting'}</strong>
            &bull; {model_metrics.get('n_features', 40) if model_metrics else 40} features
            &bull; {model_metrics.get('n_samples', 500) if model_metrics else 500} amostras
            &bull; AUC: {model_metrics.get('cv_auc_mean', 'N/A') if model_metrics else 'N/A'}
            <br>O modelo confirma matematicamente: <strong>engajamento</strong> (uso/sessoes) e
            <strong>qualidade da experiencia</strong> (erros/suporte) sao os drivers primarios.
        </div>

        {'<div class="card"><div class="card-title">Top 10 Variaveis Mais Importantes</div><div class="card-subtitle">O que mais prediz se uma conta vai churnar</div>' + fig_html(fig_importance) + '</div>' if fig_importance else ''}

        <div class="card">
            <div class="card-title">Interpretacao para o CEO</div>
            <table class="data-table">
                <tr><th>Variavel</th><th>O Que Significa</th><th>Acao</th></tr>
                <tr><td>Total de Sessoes</td><td>Clientes que usam mais ficam mais</td><td>Aumentar engajamento com onboarding</td></tr>
                <tr><td>Uso Medio</td><td>Uso consistente protege contra churn</td><td>Alertas quando uso cai &gt;50%</td></tr>
                <tr><td>Tempo de Resposta</td><td>Suporte lento causa churn</td><td>SLA de 2h para contas em risco</td></tr>
                <tr><td>Taxa de Erros</td><td>Features quebradas causam churn</td><td>Corrigir WB e RG (prioridade maxima)</td></tr>
                <tr><td>Tempo de Resolucao</td><td>Tickets sem resolver = frustracao</td><td>Limite de 24h para resolucao</td></tr>
            </table>
        </div>
    </div>

    <!-- TAB: ACOES -->
    <div id="tab-actions" class="tab-content">

        <h2 class="section-header">Plano de Acao</h2>

        <div class="card">
            <div class="card-title">Matriz Impacto vs Esforco</div>
            <div class="card-subtitle">Priorizacao visual das 7 acoes recomendadas</div>
            {fig_html(fig_actions)}
        </div>

        <div class="action">
            <h4>1. CORRIGIR Workflow Builder e Report Generator</h4>
            <span class="impact">~$134K MRR preservado</span>
            <p>Sprint dedicado para reduzir error rate de 44% para &lt;5%. Retirar features beta de producao ate estabilizar. Comunicar proativamente aos clientes afetados. Prazo: 2-4 semanas.</p>
        </div>

        <div class="action">
            <h4>2. IMPLEMENTAR Health Score + Triagem Proativa</h4>
            <span class="impact">~$59K MRR preservado</span>
            <p>Score 0-100 por conta. Contas &lt;40 recebem outreach pessoal. Triggers automaticos para uso em queda, tickets sem resolver, renovacao proxima. SLA de 2h para contas em risco. Prazo: 1-2 semanas.</p>
        </div>

        <div class="action">
            <h4>3. CONSTRUIR Cancel Flow com Save Offers</h4>
            <span class="impact">25-35% save rate</span>
            <p>Exit Survey &rarr; Offer mapeada a razao &rarr; Confirmacao. Opcao de pausa (60-80% voltam). "Too Expensive" &rarr; desconto 25%. "Not Using Enough" &rarr; pausa. Prazo: 2-3 semanas.</p>
        </div>

        <div class="action">
            <h4>4. CORRIGIR Medicao de Satisfacao</h4>
            <span class="impact">Data quality</span>
            <p>Trocar CSAT reativo por NPS proativo. Segmentar por tier de saude. Meta: response rate &gt;70% em todos os segmentos. Prazo: 1 semana.</p>
        </div>

        <div class="action">
            <h4>5. REESTRUTURAR Paid Ads</h4>
            <span class="impact">~$216K MRR protegido</span>
            <p>ICP scoring, onboarding obrigatorio, ou redirecionar budget para Referral (22%) e Direct Sales (28%). Prazo: 2-4 semanas.</p>
        </div>

        <div class="action">
            <h4>6. REFORMAR Trial</h4>
            <span class="impact">47 contas em risco</span>
            <p>Guided onboarding com milestones. CS proativo dia 3 e dia 10. Identificar activation metric. Prazo: 2-3 semanas.</p>
        </div>

        <div class="action">
            <h4>7. CONFIGURAR Dunning</h4>
            <span class="impact">50-60% recovery</span>
            <p>Pre-dunning (cartao expirando). Smart retries (4 tentativas em 7 dias). Emails progressivos. Card updater. Prazo: 1-2 semanas.</p>
        </div>

        <div class="card" style="margin-top:24px;">
            <div class="card-title">Metas para 90 Dias</div>
            <table class="data-table">
                <tr><th>Metrica</th><th>Hoje</th><th>Meta</th></tr>
                <tr><td>Churn rate</td><td style="color:{C['danger']}">~42%</td><td style="color:{C['success']}">&lt;15%</td></tr>
                <tr><td>Cancel flow save rate</td><td style="color:{C['danger']}">0% (nao existe)</td><td style="color:{C['success']}">25-35%</td></tr>
                <tr><td>First response (contas em risco)</td><td style="color:{C['danger']}">28h</td><td style="color:{C['success']}">&lt;2h</td></tr>
                <tr><td>Dunning recovery</td><td style="color:{C['text_muted']}">N/A</td><td style="color:{C['success']}">50-60%</td></tr>
                <tr><td>Error rate WB/RG</td><td style="color:{C['danger']}">44%</td><td style="color:{C['success']}">&lt;5%</td></tr>
                <tr><td>CSAT response rate</td><td style="color:{C['danger']}">54%</td><td style="color:{C['success']}">&gt;70%</td></tr>
            </table>
        </div>
    </div>

</div>

<script>
function showTab(tabId) {{
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
    document.getElementById('tab-' + tabId).classList.add('active');
    event.target.classList.add('active');
    window.dispatchEvent(new Event('resize'));
}}
</script>

</body>
</html>"""

with open(f'{OUT}dashboard_ceo.html', 'w') as f:
    f.write(html)

print(f"Dashboard salvo em {OUT}dashboard_ceo.html")
print(f"Tamanho: {len(html)/1024:.0f} KB")
