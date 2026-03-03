"""Export all dashboard data as JSON for Lovable app."""
import pandas as pd
import numpy as np
import json
from scipy import stats
import os

DATA = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'challenges', 'data-001-churn', 'data')
accounts = pd.read_csv(os.path.join(DATA, 'ravenstack_accounts.csv'))
subs = pd.read_csv(os.path.join(DATA, 'ravenstack_subscriptions.csv'))
usage = pd.read_csv(os.path.join(DATA, 'ravenstack_feature_usage.csv'))
tickets = pd.read_csv(os.path.join(DATA, 'ravenstack_support_tickets.csv'))
churn = pd.read_csv(os.path.join(DATA, 'ravenstack_churn_events.csv'))

accounts['signup_date'] = pd.to_datetime(accounts['signup_date'])
subs['start_date'] = pd.to_datetime(subs['start_date'])
subs['end_date'] = pd.to_datetime(subs['end_date'])
usage['usage_date'] = pd.to_datetime(usage['usage_date'])
churn['churn_date'] = pd.to_datetime(churn['churn_date'])

# Segments
ever_churned = set(churn['account_id'])
accounts['segment'] = 'Nunca Churnou'
accounts.loc[accounts['account_id'].isin(ever_churned) & ~accounts['churn_flag'], 'segment'] = 'Porta Giratoria'
accounts.loc[accounts['account_id'].isin(ever_churned) & accounts['churn_flag'], 'segment'] = 'Perdido Permanente'
accounts.loc[~accounts['account_id'].isin(ever_churned) & accounts['churn_flag'], 'segment'] = 'Flag sem Evento'

events_per = churn.groupby('account_id').size()
accounts['num_churn_events'] = accounts['account_id'].map(events_per).fillna(0).astype(int)

last_sub = subs.sort_values('start_date').groupby('account_id').last().reset_index()
accts = accounts.merge(last_sub[['account_id','mrr_amount','billing_frequency','plan_tier','seats']],
                       on='account_id', suffixes=('_acct','_sub'))
lost = accts[accts['segment']=='Perdido Permanente']
total_lost_mrr = float(lost['mrr_amount'].sum())

data = {}

# Segments
data['segments'] = [
    {'name': 'Nunca Churnou', 'value': int(len(accts[accts['segment']=='Nunca Churnou'])), 'color': '#00d2a0'},
    {'name': 'Porta Giratoria', 'value': int(len(accts[accts['segment']=='Porta Giratoria'])), 'color': '#ffd700'},
    {'name': 'Perdido Permanente', 'value': int(len(accts[accts['segment']=='Perdido Permanente'])), 'color': '#e94560'},
    {'name': 'Flag sem Evento', 'value': int(len(accts[accts['segment']=='Flag sem Evento'])), 'color': '#ff8c42'},
]

# KPIs
active_subs = subs[subs['end_date'].isna() & ~subs['is_trial']]
data['kpis'] = {
    'total_accounts': 500,
    'total_mrr': round(float(active_subs['mrr_amount'].sum()), 0),
    'lost_mrr': round(total_lost_mrr, 0),
    'lost_arr': round(total_lost_mrr * 12, 0),
    'multi_churn': int(len(accounts[accounts['num_churn_events'] > 1])),
    'churn_events_total': 600,
    'unique_accounts_churned': 352,
    'ent_lost_mrr': round(float(lost[lost['plan_tier_sub']=='Enterprise']['mrr_amount'].sum()), 0),
    'ent_lost_pct': round(float(lost[lost['plan_tier_sub']=='Enterprise']['mrr_amount'].sum()) / total_lost_mrr * 100, 0),
}

# Revenue by plan tier (lost)
data['rev_by_tier'] = []
for tier in ['Basic','Pro','Enterprise']:
    t = lost[lost['plan_tier_sub']==tier]
    data['rev_by_tier'].append({
        'tier': tier, 'n': int(len(t)),
        'mrr': round(float(t['mrr_amount'].sum()), 0),
        'mrr_avg': round(float(t['mrr_amount'].mean()), 0) if len(t) > 0 else 0
    })

# Top 10 lost
data['top10_lost'] = []
for _, r in lost.nlargest(10, 'mrr_amount').iterrows():
    data['top10_lost'].append({
        'name': r['account_name'], 'industry': r['industry'],
        'plan': r['plan_tier_sub'], 'mrr': round(float(r['mrr_amount']), 0)
    })

# Statistical significance function
global_rate = len(lost) / len(accounts)
data['global_churn_rate'] = round(global_rate * 100, 1)

def calc_sig(name, grp):
    n = len(grp)
    l = int((grp['segment']=='Perdido Permanente').sum())
    rate = l/n if n > 0 else 0
    z = 1.96
    denom = 1 + z**2/n
    center = (rate + z**2/(2*n)) / denom
    margin = z * np.sqrt((rate*(1-rate) + z**2/(4*n)) / n) / denom
    exp_l = n * global_rate
    exp_n = n * (1-global_rate)
    if exp_l >= 5 and exp_n >= 5:
        _, p = stats.chisquare([l, n-l], [exp_l, exp_n])
        sig = 'sig' if p < 0.05 else 'marginal' if p < 0.1 else 'ns'
    else:
        p = None; sig = 'small_n'
    return {
        'name': name, 'n': n, 'lost': l, 'rate': round(rate*100, 1),
        'ci_lo': round(max(0, center-margin)*100, 1),
        'ci_hi': round(min(1, center+margin)*100, 1),
        'p': round(float(p), 4) if p is not None else None, 'sig': sig
    }

data['significance'] = {
    'by_industry': [calc_sig(name, grp) for name, grp in accounts.groupby('industry')],
    'by_country': [calc_sig(name, grp) for name, grp in accounts.groupby('country')],
    'by_referral': [calc_sig(name, grp) for name, grp in accounts.groupby('referral_source')],
}

# Billing frequency
data['billing'] = []
for freq in ['monthly', 'annual']:
    sub = accts[accts['billing_frequency']==freq]
    perm = sub[sub['segment']=='Perdido Permanente']
    data['billing'].append({
        'freq': freq, 'n': int(len(sub)), 'n_lost': int(len(perm)),
        'rate': round(len(perm)/len(sub)*100, 1),
        'mrr_total': round(float(sub['mrr_amount'].sum()), 0),
        'mrr_lost': round(float(perm['mrr_amount'].sum()), 0),
        'mrr_avg_lost': round(float(perm['mrr_amount'].mean()), 0) if len(perm) > 0 else 0
    })

# Usage by month
usage_with_sub = usage.merge(subs[['subscription_id','account_id']], on='subscription_id')
usage_with_sub['month'] = usage_with_sub['usage_date'].dt.to_period('M').astype(str)
ubm = usage_with_sub.groupby('month').agg(
    total_usage=('usage_count','sum'), unique_accts=('account_id','nunique')
).reset_index().sort_values('month')
data['usage_by_month'] = [{'month': r['month'], 'total': int(r['total_usage']), 'accounts': int(r['unique_accts'])} for _, r in ubm.iterrows()]

# Per-account average
pam = usage_with_sub.groupby(['month','account_id'])['usage_count'].sum().reset_index()
pam_avg = pam.groupby('month')['usage_count'].mean().reset_index().sort_values('month')
data['per_acct_avg'] = [{'month': r['month'], 'avg': round(float(r['usage_count']), 1)} for _, r in pam_avg.iterrows()]

# Churn reasons
data['churn_reasons'] = [{'reason': k, 'count': int(v)} for k, v in churn['reason_code'].value_counts().items()]

# Satisfaction broken
sat = tickets['satisfaction_score'].dropna()
tix_seg = tickets.merge(accounts[['account_id','segment']], on='account_id')
data['satisfaction'] = {
    'distribution': [{'score': str(int(k)), 'count': int(v)} for k, v in sat.value_counts().sort_index().items()],
    'null_pct': round(float(tickets['satisfaction_score'].isna().mean()*100), 0),
    'avg_never': round(float(tix_seg[tix_seg['segment']=='Nunca Churnou']['satisfaction_score'].mean()), 2),
    'avg_lost': round(float(tix_seg[tix_seg['segment']=='Perdido Permanente']['satisfaction_score'].mean()), 2),
}

# Multi-churn distribution
data['multi_churn_dist'] = [{'churns': str(int(k)), 'accounts': int(v)}
                            for k, v in accounts['num_churn_events'].value_counts().sort_index().items()]

# Reason changes in multi-churn
multi_ids = events_per[events_per > 1].index
multi_events = churn[churn['account_id'].isin(multi_ids)].sort_values(['account_id','churn_date'])
changes, same = 0, 0
for acct, grp in multi_events.groupby('account_id'):
    reasons = grp['reason_code'].tolist()
    for i in range(1, len(reasons)):
        if reasons[i] != reasons[i-1]: changes += 1
        else: same += 1
data['reason_changes'] = changes
data['reason_same'] = same

# Strategies
ent_mrr = float(lost[lost['plan_tier_sub']=='Enterprise']['mrr_amount'].sum())
top5_mrr = float(lost[lost['plan_tier_sub']=='Enterprise'].nlargest(5,'mrr_amount')['mrr_amount'].sum())
data['strategies'] = [
    {'name': 'Enterprise Save Program', 'description': '1 CSM dedicado para 25 Enterprise', 'cost_monthly': 8000, 'recovery_monthly': round(top5_mrr, 0), 'recovery_annual': round(top5_mrr*12, 0), 'roi': f'{top5_mrr/8000:.0f}x'},
    {'name': 'Desconto Anual 15%', 'description': 'Lock-in para contas mensais >$2k', 'cost_monthly': 5600, 'recovery_monthly': 11300, 'recovery_annual': 67700, 'roi': '2x'},
    {'name': 'DevTools PMF Audit', 'description': 'Investigar unico segmento significativo', 'cost_monthly': 0, 'recovery_monthly': 22800, 'recovery_annual': 274000, 'roi': 'Alto'},
    {'name': 'Programa 90-Day Success', 'description': 'Milestones para Porta Giratoria', 'cost_monthly': 0, 'recovery_monthly': 80900, 'recovery_annual': round(80900*12, 0), 'roi': 'Alto'},
    {'name': 'Qualificar Canal Events', 'description': 'Alterar pitch e onboarding', 'cost_monthly': 0, 'recovery_monthly': 0, 'recovery_annual': 0, 'roi': 'Qualitativo'},
]

# Heatmap: plan x industry
data['heatmap'] = []
for plan in ['Basic','Pro','Enterprise']:
    for ind in sorted(accounts['industry'].unique()):
        sub = accounts[(accounts['plan_tier']==plan) & (accounts['industry']==ind)]
        rate = round(float((sub['segment']=='Perdido Permanente').sum() / len(sub) * 100), 1) if len(sub) > 0 else 0
        data['heatmap'].append({'plan': plan, 'industry': ind, 'rate': rate, 'n': int(len(sub))})

# Usage by segment over time
usage_seg = usage_with_sub.merge(accounts[['account_id','segment']], on='account_id')
data['usage_by_seg_month'] = []
for seg in ['Nunca Churnou', 'Porta Giratoria', 'Perdido Permanente']:
    sub = usage_seg[usage_seg['segment']==seg]
    monthly = sub.groupby('month')['usage_count'].sum().reset_index().sort_values('month')
    for _, r in monthly.iterrows():
        data['usage_by_seg_month'].append({'month': r['month'], 'segment': seg, 'total': int(r['usage_count'])})

out_path = os.path.join(os.path.dirname(__file__), 'lovable_data.json')
with open(out_path, 'w') as f:
    json.dump(data, f, indent=2, default=str)
print(f"Exported: {out_path} ({os.path.getsize(out_path)/1024:.0f} KB)")
