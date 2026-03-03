"""
RavenStack Churn Diagnostic Dashboard Generator v2
Unified account classification, corrected churn semantics.
"""
import pandas as pd
import json
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'challenges', 'data-001-churn', 'data')
OUTPUT = os.path.join(os.path.dirname(__file__), 'dashboard_churn.html')

# ── Load data ──────────────────────────────────────────────────────────────
print("Loading data...")
accounts = pd.read_csv(os.path.join(DATA_DIR, 'ravenstack_accounts.csv'))
subs = pd.read_csv(os.path.join(DATA_DIR, 'ravenstack_subscriptions.csv'))
usage = pd.read_csv(os.path.join(DATA_DIR, 'ravenstack_feature_usage.csv'))
tickets = pd.read_csv(os.path.join(DATA_DIR, 'ravenstack_support_tickets.csv'))
churn = pd.read_csv(os.path.join(DATA_DIR, 'ravenstack_churn_events.csv'))

accounts['signup_date'] = pd.to_datetime(accounts['signup_date'])
subs['start_date'] = pd.to_datetime(subs['start_date'])
subs['end_date'] = pd.to_datetime(subs['end_date'])
usage['usage_date'] = pd.to_datetime(usage['usage_date'])
tickets['submitted_at'] = pd.to_datetime(tickets['submitted_at'])
tickets['closed_at'] = pd.to_datetime(tickets['closed_at'])
churn['churn_date'] = pd.to_datetime(churn['churn_date'])

print("Computing metrics...")

# ═══════════════════════════════════════════════════════════════════════════
# UNIFIED ACCOUNT CLASSIFICATION
# churn_flag = CURRENTLY churned (not active)
# churn_events = historical events (a conta pode ter voltado)
# ═══════════════════════════════════════════════════════════════════════════
events_per_acct = churn.groupby('account_id').size()
ever_churned_ids = set(churn['account_id'])
currently_churned_ids = set(accounts[accounts['churn_flag']]['account_id'])

accounts['ever_churned'] = accounts['account_id'].isin(ever_churned_ids)
accounts['num_churn_events'] = accounts['account_id'].map(events_per_acct).fillna(0).astype(int)
accounts['currently_active'] = ~accounts['churn_flag']

# 4 segments
accounts['segment'] = 'Nunca Churnou'
accounts.loc[accounts['ever_churned'] & accounts['currently_active'], 'segment'] = 'Porta Giratoria'
accounts.loc[accounts['ever_churned'] & ~accounts['currently_active'] & accounts['account_id'].isin(ever_churned_ids), 'segment'] = 'Perdido Permanente'
accounts.loc[~accounts['ever_churned'] & ~accounts['currently_active'], 'segment'] = 'Flag sem Evento'

seg_counts = accounts['segment'].value_counts().to_dict()
n_never = seg_counts.get('Nunca Churnou', 0)
n_revolving = seg_counts.get('Porta Giratoria', 0)
n_lost = seg_counts.get('Perdido Permanente', 0)
n_flag_only = seg_counts.get('Flag sem Evento', 0)

total_accounts = len(accounts)

# Multi-churn
n_multi_churn = len(accounts[accounts['num_churn_events'] > 1])
n_single_churn = len(accounts[accounts['num_churn_events'] == 1])

# ── Revenue metrics ───────────────────────────────────────────────────────
active_subs = subs[subs['end_date'].isna() & ~subs['is_trial']]
total_mrr = active_subs['mrr_amount'].sum()
avg_mrr = active_subs['mrr_amount'].mean() if len(active_subs) > 0 else 0

# Lost MRR (permanently churned only)
lost_subs = subs[subs['account_id'].isin(currently_churned_ids & ever_churned_ids)]
lost_mrr = lost_subs.groupby('account_id')['mrr_amount'].last().sum()

# Recovered MRR
recovered_ids = ever_churned_ids - currently_churned_ids
rec_subs = subs[subs['account_id'].isin(recovered_ids) & subs['end_date'].isna()]
recovered_mrr = rec_subs.groupby('account_id')['mrr_amount'].last().sum() if len(rec_subs) > 0 else 0

# ── Churn reasons ─────────────────────────────────────────────────────────
churn_reasons = churn['reason_code'].value_counts().to_dict()

# Reasons for permanently lost vs revolving
perm_churn = churn[churn['account_id'].isin(currently_churned_ids & ever_churned_ids)]
revolving_churn = churn[churn['account_id'].isin(recovered_ids)]
perm_reasons = perm_churn['reason_code'].value_counts().to_dict()
revolv_reasons = revolving_churn['reason_code'].value_counts().to_dict()

# ── Segmentation by industry/plan/country/referral ────────────────────────
def seg_analysis(col):
    result = accounts.groupby(col).agg(
        total=('account_id', 'count'),
        never=('segment', lambda x: (x == 'Nunca Churnou').sum()),
        revolving=('segment', lambda x: (x == 'Porta Giratoria').sum()),
        lost=('segment', lambda x: (x == 'Perdido Permanente').sum()),
    ).reset_index()
    result['churn_rate'] = ((result['lost'] / result['total']) * 100).round(1)
    result['ever_churned_rate'] = (((result['revolving'] + result['lost']) / result['total']) * 100).round(1)
    return result

by_industry = seg_analysis('industry')
by_plan = seg_analysis('plan_tier')
by_country = seg_analysis('country').sort_values('total', ascending=False)
by_referral = seg_analysis('referral_source')

# ── Heatmap: plan x industry (permanent churn rate) ──────────────────────
plans_list = ['Basic', 'Pro', 'Enterprise']
industries_list = sorted(accounts['industry'].unique())
heatmap_perm = []
heatmap_ever = []
for plan in plans_list:
    row_p, row_e = [], []
    for ind in industries_list:
        sub = accounts[(accounts['plan_tier'] == plan) & (accounts['industry'] == ind)]
        if len(sub) == 0:
            row_p.append(0)
            row_e.append(0)
        else:
            row_p.append(round((sub['segment'] == 'Perdido Permanente').sum() / len(sub) * 100, 1))
            row_e.append(round(sub['ever_churned'].sum() / len(sub) * 100, 1))
    heatmap_perm.append(row_p)
    heatmap_ever.append(row_e)

# ── Revenue impact ────────────────────────────────────────────────────────
# By segment
seg_revenue = {}
for seg_name, seg_ids in [('Perdido Permanente', currently_churned_ids & ever_churned_ids),
                           ('Porta Giratoria', recovered_ids)]:
    seg_subs = subs[subs['account_id'].isin(seg_ids)]
    seg_revenue[seg_name] = seg_subs.groupby('account_id')['mrr_amount'].last().sum()

# Lost by plan and industry
lost_with_acct = lost_subs.merge(accounts[['account_id', 'plan_tier', 'industry']], on='account_id', suffixes=('_sub', ''))
rev_by_plan = lost_with_acct.groupby('plan_tier')['mrr_amount'].sum().to_dict()
rev_by_industry = lost_with_acct.groupby('industry')['mrr_amount'].sum().to_dict()

# MRR distribution
mrr_lost_list = lost_subs.groupby('account_id')['mrr_amount'].last().tolist()
mrr_active_list = active_subs.groupby('account_id')['mrr_amount'].last().dropna().tolist()

# Refunds
refund_stats = churn.groupby('reason_code')['refund_amount_usd'].agg(['mean', 'sum', 'count']).round(2)
total_refunds = churn['refund_amount_usd'].sum()

# ── Feature Usage Analysis ────────────────────────────────────────────────
usage_with_acct = usage.merge(subs[['subscription_id', 'account_id']], on='subscription_id')
usage_with_acct = usage_with_acct.merge(accounts[['account_id', 'segment']], on='account_id')

# Compare 3 groups: Never, Revolving, Lost
usage_by_seg = {}
for seg in ['Nunca Churnou', 'Porta Giratoria', 'Perdido Permanente']:
    sub = usage_with_acct[usage_with_acct['segment'] == seg]
    n_accts = accounts[accounts['segment'] == seg]['account_id'].nunique()
    feat_per_acct = sub.groupby('account_id')['feature_name'].nunique().mean() if len(sub) > 0 else 0
    usage_by_seg[seg] = {
        'avg_usage_count': round(sub['usage_count'].mean(), 2) if len(sub) > 0 else 0,
        'avg_duration': round(sub['usage_duration_secs'].mean(), 0) if len(sub) > 0 else 0,
        'avg_errors': round(sub['error_count'].mean(), 3) if len(sub) > 0 else 0,
        'total_events': len(sub),
        'features_per_acct': round(feat_per_acct, 1),
        'beta_pct': round(sub['is_beta_feature'].mean() * 100, 1) if len(sub) > 0 else 0,
        'events_per_acct': round(len(sub) / n_accts, 1) if n_accts > 0 else 0,
    }

# Top features by segment
top_feat = {}
for seg in ['Nunca Churnou', 'Porta Giratoria', 'Perdido Permanente']:
    sub = usage_with_acct[usage_with_acct['segment'] == seg]
    top_feat[seg] = sub.groupby('feature_name')['usage_count'].sum().nlargest(10).to_dict()

# Error-prone features for lost accounts
err_lost = usage_with_acct[usage_with_acct['segment'] == 'Perdido Permanente']
err_by_feat = err_lost.groupby('feature_name').agg(
    total_errors=('error_count', 'sum'),
    avg_errors=('error_count', 'mean'),
    total_usage=('usage_count', 'sum')
).sort_values('total_errors', ascending=False).head(10)

# ── Support Analysis ──────────────────────────────────────────────────────
tickets_with_seg = tickets.merge(accounts[['account_id', 'segment']], on='account_id')

support_by_seg = {}
for seg in ['Nunca Churnou', 'Porta Giratoria', 'Perdido Permanente']:
    sub = tickets_with_seg[tickets_with_seg['segment'] == seg]
    n_accts = accounts[accounts['segment'] == seg]['account_id'].nunique()
    tpa = sub.groupby('account_id')['ticket_id'].count()
    support_by_seg[seg] = {
        'tickets_per_acct': round(tpa.mean(), 1) if len(tpa) > 0 else 0,
        'avg_resolution': round(sub['resolution_time_hours'].mean(), 1) if len(sub) > 0 else 0,
        'avg_first_response': round(sub['first_response_time_minutes'].mean(), 0) if len(sub) > 0 else 0,
        'avg_satisfaction': round(sub['satisfaction_score'].mean(), 2) if len(sub) > 0 else 0,
        'null_satisfaction_pct': round(sub['satisfaction_score'].isna().mean() * 100, 0) if len(sub) > 0 else 0,
        'escalation_rate': round(sub['escalation_flag'].mean() * 100, 1) if len(sub) > 0 else 0,
        'total_tickets': len(sub),
    }

# Satisfaction distribution
sat_scores = tickets['satisfaction_score'].dropna().value_counts().sort_index().to_dict()
sat_scores = {str(int(k)): v for k, v in sat_scores.items()}

# Priority by segment
priority_by_seg = {}
for seg in ['Nunca Churnou', 'Porta Giratoria', 'Perdido Permanente']:
    sub = tickets_with_seg[tickets_with_seg['segment'] == seg]
    priority_by_seg[seg] = sub['priority'].value_counts().to_dict()

# ── Timeline & Cohort ─────────────────────────────────────────────────────
churn['churn_month'] = churn['churn_date'].dt.to_period('M').astype(str)
churn_timeline = churn.groupby('churn_month')['churn_event_id'].count().to_dict()

# Separate timeline for permanent vs revolving
perm_timeline = perm_churn.copy()
perm_timeline['churn_month'] = perm_timeline['churn_date'].dt.to_period('M').astype(str)
perm_tl = perm_timeline.groupby('churn_month')['churn_event_id'].count().to_dict()

revolv_timeline = revolving_churn.copy()
revolv_timeline['churn_month'] = revolv_timeline['churn_date'].dt.to_period('M').astype(str)
revolv_tl = revolv_timeline.groupby('churn_month')['churn_event_id'].count().to_dict()

all_months = sorted(set(list(churn_timeline.keys())))

# Cohort analysis
accounts['signup_month'] = accounts['signup_date'].dt.to_period('M').astype(str)
cohort = accounts.groupby('signup_month').agg(
    total=('account_id', 'count'),
    ever_churned=('ever_churned', 'sum'),
    perm_lost=('segment', lambda x: (x == 'Perdido Permanente').sum()),
).reset_index()
cohort['ever_rate'] = (cohort['ever_churned'] / cohort['total'] * 100).round(1)
cohort['perm_rate'] = (cohort['perm_lost'] / cohort['total'] * 100).round(1)

# Days to churn
churn_with_signup = churn.merge(accounts[['account_id', 'signup_date']], on='account_id')
churn_with_signup['days_to_churn'] = (churn_with_signup['churn_date'] - churn_with_signup['signup_date']).dt.days
dtc_stats = churn_with_signup['days_to_churn'].describe().round(1).to_dict()

bins = [0, 30, 60, 90, 180, 365, 9999]
labels = ['0-30d', '31-60d', '61-90d', '91-180d', '181-365d', '365d+']
churn_with_signup['bucket'] = pd.cut(churn_with_signup['days_to_churn'], bins=bins, labels=labels)
bucket_counts = churn_with_signup['bucket'].value_counts().sort_index().to_dict()
bucket_counts = {str(k): int(v) for k, v in bucket_counts.items()}

# ── Lifecycle ─────────────────────────────────────────────────────────────
upgrade_before = churn['preceding_upgrade_flag'].sum()
downgrade_before = churn['preceding_downgrade_flag'].sum()
reactivations = churn['is_reactivation'].sum()

# Upgrade before churn by segment
up_perm = perm_churn['preceding_upgrade_flag'].sum()
up_revolv = revolving_churn['preceding_upgrade_flag'].sum()

# Billing frequency
subs_with_seg = subs.merge(accounts[['account_id', 'segment']], on='account_id')
billing_seg = subs_with_seg.groupby(['billing_frequency', 'segment'])['subscription_id'].count().unstack(fill_value=0)

# Trial analysis
trial_seg = accounts.groupby(['is_trial', 'segment']).size().unstack(fill_value=0)

# Seats by segment
seats_by_seg = accounts.groupby('segment')['seats'].describe().round(1)

# ── Feedback Analysis ─────────────────────────────────────────────────────
feedback_all = churn[churn['feedback_text'].notna()]['feedback_text'].value_counts().head(15).to_dict()
n_with_feedback = churn['feedback_text'].notna().sum()
n_no_feedback = churn['feedback_text'].isna().sum()

# Feedback for permanent only
perm_fb = perm_churn[perm_churn['feedback_text'].notna()]['feedback_text'].value_counts().head(10).to_dict()

# ── Multi-churn pattern analysis ──────────────────────────────────────────
multi_churn_accts = accounts[accounts['num_churn_events'] > 1]
multi_dist = accounts['num_churn_events'].value_counts().sort_index().to_dict()
multi_dist = {str(k): v for k, v in multi_dist.items()}

# Time between churns for multi-churn accounts
multi_ids = events_per_acct[events_per_acct > 1].index
multi_events = churn[churn['account_id'].isin(multi_ids)].sort_values(['account_id', 'churn_date'])
gaps = []
for acct, grp in multi_events.groupby('account_id'):
    dates = grp['churn_date'].tolist()
    for i in range(1, len(dates)):
        gaps.append((dates[i] - dates[i-1]).days)
avg_gap = round(sum(gaps) / len(gaps), 0) if gaps else 0
median_gap = sorted(gaps)[len(gaps)//2] if gaps else 0

# Reason changes in multi-churn
reason_changes = 0
reason_same = 0
for acct, grp in multi_events.groupby('account_id'):
    reasons = grp['reason_code'].tolist()
    for i in range(1, len(reasons)):
        if reasons[i] != reasons[i-1]:
            reason_changes += 1
        else:
            reason_same += 1

# ── CEO QUESTION: Did usage grow? ─────────────────────────────────────────
usage_with_acct['month'] = usage_with_acct['usage_date'].dt.to_period('M').astype(str)

# Total usage by month (what Product sees)
usage_by_month = usage_with_acct.groupby('month').agg(
    events=('usage_id', 'count'),
    total_usage=('usage_count', 'sum'),
    total_duration=('usage_duration_secs', 'sum'),
    unique_accounts=('account_id', 'nunique'),
).reset_index().sort_values('month')
usage_months = usage_by_month['month'].tolist()

# Per-account averages by month
per_acct_month = usage_with_acct.groupby(['month', 'account_id']).agg(
    usage_sum=('usage_count', 'sum'),
    duration_sum=('usage_duration_secs', 'sum'),
    events=('usage_id', 'count')
).reset_index()
per_acct_avg = per_acct_month.groupby('month').agg(
    avg_usage=('usage_sum', 'mean'),
    avg_events=('events', 'mean'),
    n_accounts=('account_id', 'nunique')
).round(1).reset_index().sort_values('month')

# Usage by segment over time
seg_usage_monthly = {}
for seg in ['Nunca Churnou', 'Porta Giratoria', 'Perdido Permanente']:
    sub = usage_with_acct[usage_with_acct['segment'] == seg]
    monthly = sub.groupby('month')['usage_count'].sum().reindex(usage_months, fill_value=0)
    seg_usage_monthly[seg] = monthly.tolist()

# New signups per month
accounts['signup_month'] = accounts['signup_date'].dt.to_period('M').astype(str)
new_signups = accounts.groupby('signup_month')['account_id'].count().reindex(usage_months, fill_value=0).tolist()

# ── MATRICES: Health Score, RFD, Value x Risk ────────────────────────────
import numpy as np

# Build account-level master
usage_acct = usage_with_acct.groupby('account_id').agg(
    last_usage=('usage_date', 'max'),
    total_events=('usage_id', 'count'),
    total_usage_count=('usage_count', 'sum'),
    unique_features=('feature_name', 'nunique'),
    total_errors=('error_count', 'sum'),
    beta_usage=('is_beta_feature', 'sum'),
).reset_index()
ref_date = pd.Timestamp('2025-01-01')
usage_acct['recency_days'] = (ref_date - usage_acct['last_usage']).dt.days

acct_tix = tickets.merge(accounts[['account_id', 'segment']], on='account_id')
acct_tix_agg = acct_tix.groupby('account_id').agg(
    total_tickets=('ticket_id', 'count'),
    escalations=('escalation_flag', 'sum'),
).reset_index()

last_sub = subs.sort_values('start_date').groupby('account_id').last().reset_index()
acct_rev = last_sub[['account_id', 'mrr_amount', 'plan_tier']].copy()

mx = accounts[['account_id', 'segment', 'num_churn_events']].copy()
mx = mx.merge(usage_acct, on='account_id', how='left')
mx = mx.merge(acct_tix_agg, on='account_id', how='left')
mx = mx.merge(acct_rev, on='account_id', how='left')
for c in ['total_tickets', 'escalations', 'total_events']:
    mx[c] = mx[c].fillna(0)

mx_valid = mx[mx['total_events'] > 0].copy()

# Health Score
def norm(s):
    mn, mx_v = s.min(), s.max()
    return ((s - mn) / (mx_v - mn) * 100).round(1) if mx_v > mn else pd.Series(50.0, index=s.index)

mx_valid['health_score'] = (
    norm(mx_valid['total_usage_count']) * 0.25 +
    norm(mx_valid['unique_features']) * 0.20 +
    norm(mx_valid['recency_days'].max() - mx_valid['recency_days']) * 0.25 +
    norm(mx_valid['total_errors'].max() - mx_valid['total_errors']) * 0.15 +
    norm(mx_valid['total_tickets'].max() - mx_valid['total_tickets']) * 0.15
).round(1)

mx_valid['health_zone'] = pd.cut(mx_valid['health_score'], bins=[-1,30,50,70,100],
                                  labels=['Critical','Warning','Good','Excellent'])

# Health by segment
health_seg = mx_valid.groupby('segment')['health_score'].agg(['mean','median','std']).round(1)

# Health zone counts
hz_data = mx_valid.groupby(['segment', 'health_zone'], observed=False).size().unstack(fill_value=0)

# Value x Risk
mx_valid['value_tier'] = pd.qcut(mx_valid['mrr_amount'].rank(method='first'), 3,
                                  labels=['Low','Mid','High'])
mx_valid['risk_tier'] = pd.cut(mx_valid['health_score'], bins=[-1,40,65,100],
                                labels=['High Risk','Med Risk','Low Risk'])

vr = mx_valid.groupby(['value_tier', 'risk_tier'], observed=False).agg(
    count=('account_id', 'count'),
    mrr=('mrr_amount', 'sum'),
    lost=('segment', lambda x: (x == 'Perdido Permanente').sum()),
).reset_index()

# Build 3x3 matrix for heatmap
vr_labels = ['Low','Mid','High']
vr_risk_labels = ['High Risk','Med Risk','Low Risk']
vr_counts = []
vr_lost = []
vr_mrr = []
for v in vr_labels:
    row_c, row_l, row_m = [], [], []
    for r in vr_risk_labels:
        match = vr[(vr['value_tier'] == v) & (vr['risk_tier'] == r)]
        row_c.append(int(match['count'].values[0]) if len(match) > 0 else 0)
        row_l.append(int(match['lost'].values[0]) if len(match) > 0 else 0)
        row_m.append(float(match['mrr'].values[0]) if len(match) > 0 else 0)
    vr_counts.append(row_c)
    vr_lost.append(row_l)
    vr_mrr.append(row_m)

# Health score distributions for scatter
health_scatter = mx_valid[['account_id', 'segment', 'health_score', 'mrr_amount',
                            'total_events', 'unique_features', 'total_tickets']].copy()

# Pre-compute JSON strings for complex JS data
segs3 = ['Nunca Churnou', 'Porta Giratoria', 'Perdido Permanente']
_health_lists = {seg: mx_valid[mx_valid['segment']==seg]['health_score'].tolist() for seg in segs3}
health_lists_json = json.dumps(_health_lists)

_hz_dict = {}
for zone in ['Critical', 'Warning', 'Good', 'Excellent']:
    _hz_dict[zone] = {}
    for seg in segs3:
        val = int(hz_data.loc[seg, zone]) if seg in hz_data.index and zone in hz_data.columns else 0
        _hz_dict[zone][seg] = val
hz_dict_json = json.dumps(_hz_dict)

_scatter_data = {}
for seg in segs3:
    sub = health_scatter[health_scatter['segment']==seg]
    _scatter_data[seg] = sub[['health_score','mrr_amount','account_id','total_events']].to_dict('records')
scatter_json = json.dumps(_scatter_data, default=str)

# ── REVENUE-WEIGHTED ANALYSIS & STATISTICAL SIGNIFICANCE ─────────────
from scipy import stats as scipy_stats

last_sub_full = subs.sort_values('start_date').groupby('account_id').last().reset_index()
accts_full = accounts.merge(last_sub_full[['account_id', 'mrr_amount', 'billing_frequency', 'auto_renew_flag', 'plan_tier', 'seats']],
                            on='account_id', suffixes=('_acct', '_sub'))

# Revenue by segment
rev_by_segment = {}
for seg in ['Nunca Churnou', 'Porta Giratoria', 'Perdido Permanente', 'Flag sem Evento']:
    sub = accts_full[accts_full['segment'] == seg]
    rev_by_segment[seg] = {
        'n': len(sub), 'mrr_total': round(sub['mrr_amount'].sum(), 0),
        'mrr_avg': round(sub['mrr_amount'].mean(), 0), 'mrr_median': round(sub['mrr_amount'].median(), 0)
    }

# Lost by plan tier (revenue-weighted)
lost_accts = accts_full[accts_full['segment'] == 'Perdido Permanente']
rev_lost_by_tier = {}
for tier in ['Basic', 'Pro', 'Enterprise']:
    t = lost_accts[lost_accts['plan_tier_sub'] == tier]
    rev_lost_by_tier[tier] = {'n': len(t), 'mrr': round(t['mrr_amount'].sum(), 0), 'mrr_avg': round(t['mrr_amount'].mean(), 0) if len(t) > 0 else 0}

# Top 10 lost by MRR
top10_lost = lost_accts.nlargest(10, 'mrr_amount')[['account_id', 'account_name', 'industry', 'mrr_amount', 'plan_tier_sub']].to_dict('records')

# Enterprise lost details
ent_lost = lost_accts[lost_accts['plan_tier_sub'] == 'Enterprise']
ent_lost_mrr = ent_lost['mrr_amount'].sum()
total_lost_mrr = lost_accts['mrr_amount'].sum()
ent_lost_pct = round(ent_lost_mrr / total_lost_mrr * 100, 0) if total_lost_mrr > 0 else 0
top5_ent_mrr = ent_lost.nlargest(5, 'mrr_amount')['mrr_amount'].sum()

# Billing frequency vs churn
billing_stats = {}
for freq in ['monthly', 'annual']:
    sub = accts_full[accts_full['billing_frequency'] == freq]
    perm = sub[sub['segment'] == 'Perdido Permanente']
    billing_stats[freq] = {
        'n': len(sub), 'n_lost': len(perm),
        'rate': round(len(perm) / len(sub) * 100, 1),
        'mrr_total': round(sub['mrr_amount'].sum(), 0),
        'mrr_lost': round(perm['mrr_amount'].sum(), 0),
        'mrr_lost_pct': round(perm['mrr_amount'].sum() / sub['mrr_amount'].sum() * 100, 1) if sub['mrr_amount'].sum() > 0 else 0,
        'mrr_avg_lost': round(perm['mrr_amount'].mean(), 0) if len(perm) > 0 else 0,
    }

# Statistical significance
global_lost_rate = len(lost_accts) / len(accounts)

def calc_significance(grp_col, grp_name, grp_df):
    n = len(grp_df)
    lost_count = (grp_df['segment'] == 'Perdido Permanente').sum()
    rate = lost_count / n if n > 0 else 0
    z = 1.96
    denom = 1 + z**2/n
    center = (rate + z**2/(2*n)) / denom
    margin = z * np.sqrt((rate*(1-rate) + z**2/(4*n)) / n) / denom
    ci_lo, ci_hi = max(0, center-margin), min(1, center+margin)
    expected_lost = n * global_lost_rate
    expected_not = n * (1 - global_lost_rate)
    if expected_lost >= 5 and expected_not >= 5:
        chi2, p = scipy_stats.chisquare([lost_count, n-lost_count], [expected_lost, expected_not])
        sig = 'p<0.01' if p < 0.01 else 'p<0.05' if p < 0.05 else 'p<0.10' if p < 0.1 else 'n.s.'
        sig_tag = 'tag-red' if p < 0.05 else 'tag-yellow' if p < 0.1 else 'tag-green'
    else:
        p, sig, sig_tag = None, 'n insuf.', 'tag-orange'
    return {'col': grp_col, 'name': grp_name, 'n': n, 'lost': lost_count, 'rate': round(rate*100, 1),
            'ci_lo': round(ci_lo*100, 1), 'ci_hi': round(ci_hi*100, 1),
            'p': round(p, 4) if p is not None else None, 'sig': sig, 'sig_tag': sig_tag}

sig_results = []
for col, label in [('industry', 'Industria'), ('country', 'Pais'), ('referral_source', 'Canal')]:
    for name, grp in accounts.groupby(col):
        sig_results.append(calc_significance(label, name, grp))

# Seats analysis
accts_full['seat_bucket'] = pd.cut(accts_full['seats_acct'], bins=[0,5,15,50,200], labels=['1-5','6-15','16-50','51+'])
seats_stats = []
for bucket in ['1-5', '6-15', '16-50', '51+']:
    sub = accts_full[accts_full['seat_bucket'] == bucket]
    if len(sub) == 0:
        continue
    perm = sub[sub['segment'] == 'Perdido Permanente']
    seats_stats.append({
        'bucket': bucket, 'n': int(len(sub)), 'n_lost': int(len(perm)),
        'rate': round(len(perm)/len(sub)*100, 1),
        'mrr_total': float(round(sub['mrr_amount'].sum(), 0)),
        'mrr_lost': float(round(perm['mrr_amount'].sum(), 0)),
        'mrr_lost_pct': round(float(perm['mrr_amount'].sum())/total_lost_mrr*100, 1) if total_lost_mrr > 0 else 0
    })

# Strategy simulation numbers
csm_cost = 8000
strat_ent_roi = round(top5_ent_mrr / csm_cost, 0)

# ── Raw table samples (larger) ────────────────────────────────────────────
sample_accounts = accounts.sort_values('num_churn_events', ascending=False).head(50)
sample_subs = subs.sort_values('start_date', ascending=False).head(50)
sample_usage = usage.sort_values('usage_date', ascending=False).head(50)
sample_tickets = tickets.sort_values('submitted_at', ascending=False).head(50)
sample_churn = churn.sort_values('churn_date', ascending=False).head(50)

print("Building HTML...")

# ═══════════════════════════════════════════════════════════════════════════
# HTML GENERATION
# ═══════════════════════════════════════════════════════════════════════════
html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RavenStack - Churn Diagnostic Dashboard v2</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #0f1117; color: #e0e0e0; }}
.header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 30px 40px; border-bottom: 2px solid #e94560; }}
.header h1 {{ font-size: 28px; color: #fff; }}
.header p {{ color: #a0a0a0; margin-top: 5px; font-size: 14px; }}
.nav {{ background: #1a1a2e; padding: 10px 40px; display: flex; gap: 8px; flex-wrap: wrap; border-bottom: 1px solid #333; position: sticky; top: 0; z-index: 100; }}
.nav button {{ background: #252535; border: 1px solid #444; color: #ccc; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; transition: all 0.2s; }}
.nav button:hover, .nav button.active {{ background: #e94560; color: #fff; border-color: #e94560; }}
.container {{ max-width: 1600px; margin: 0 auto; padding: 20px 40px; }}
.section {{ display: none; }}
.section.active {{ display: block; }}
.kpi-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin: 20px 0; }}
.kpi {{ background: #1a1a2e; border-radius: 10px; padding: 20px; border-left: 4px solid #e94560; }}
.kpi .value {{ font-size: 28px; font-weight: 700; color: #fff; }}
.kpi .label {{ font-size: 13px; color: #888; margin-top: 4px; }}
.kpi .sub {{ font-size: 12px; color: #e94560; margin-top: 2px; }}
.kpi.green {{ border-left-color: #00d2a0; }} .kpi.green .sub {{ color: #00d2a0; }}
.kpi.blue {{ border-left-color: #4da6ff; }} .kpi.blue .sub {{ color: #4da6ff; }}
.kpi.yellow {{ border-left-color: #ffd700; }} .kpi.yellow .sub {{ color: #ffd700; }}
.kpi.purple {{ border-left-color: #b366ff; }} .kpi.purple .sub {{ color: #b366ff; }}
.kpi.orange {{ border-left-color: #ff8c42; }} .kpi.orange .sub {{ color: #ff8c42; }}
.chart-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(480px, 1fr)); gap: 20px; margin: 20px 0; }}
.chart-box {{ background: #1a1a2e; border-radius: 10px; padding: 20px; }}
.chart-box h3 {{ font-size: 15px; color: #ccc; margin-bottom: 10px; border-bottom: 1px solid #333; padding-bottom: 8px; }}
.chart-full {{ grid-column: 1 / -1; }}
.insight {{ background: #1a1a2e; border-radius: 10px; padding: 20px; margin: 20px 0; border-left: 4px solid #ffd700; }}
.insight h3 {{ color: #ffd700; margin-bottom: 10px; }}
.insight ul {{ padding-left: 20px; }} .insight li {{ margin: 6px 0; color: #ccc; line-height: 1.6; }}
.insight li strong {{ color: #fff; }}
.insight.red {{ border-left-color: #e94560; }} .insight.red h3 {{ color: #e94560; }}
.insight.green {{ border-left-color: #00d2a0; }} .insight.green h3 {{ color: #00d2a0; }}
table {{ width: 100%; border-collapse: collapse; }} th, td {{ text-align: left; padding: 10px 12px; border-bottom: 1px solid #2a2a3e; font-size: 13px; }}
th {{ background: #252535; color: #aaa; font-weight: 600; text-transform: uppercase; font-size: 11px; }}
tr:hover td {{ background: #252535; }}
.tag {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
.tag-red {{ background: #e9456033; color: #e94560; }}
.tag-green {{ background: #00d2a033; color: #00d2a0; }}
.tag-blue {{ background: #4da6ff33; color: #4da6ff; }}
.tag-yellow {{ background: #ffd70033; color: #ffd700; }}
.tag-orange {{ background: #ff8c4233; color: #ff8c42; }}
.compare-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 20px 0; }}
.compare-card {{ background: #1a1a2e; border-radius: 10px; padding: 18px; }}
.compare-card h3 {{ font-size: 14px; margin-bottom: 12px; }}
.compare-card.seg-never {{ border-top: 3px solid #00d2a0; }} .compare-card.seg-never h3 {{ color: #00d2a0; }}
.compare-card.seg-revolv {{ border-top: 3px solid #ffd700; }} .compare-card.seg-revolv h3 {{ color: #ffd700; }}
.compare-card.seg-lost {{ border-top: 3px solid #e94560; }} .compare-card.seg-lost h3 {{ color: #e94560; }}
.stat-row {{ display: flex; justify-content: space-between; padding: 7px 0; border-bottom: 1px solid #2a2a3e; }}
.stat-row .stat-label {{ color: #888; font-size: 13px; }}
.stat-row .stat-value {{ color: #fff; font-weight: 600; font-size: 13px; }}
.feedback-item {{ background: #252535; padding: 10px 14px; border-radius: 6px; margin: 6px 0; font-style: italic; color: #ccc; }}
.feedback-count {{ float: right; color: #888; font-style: normal; font-size: 12px; }}
.section-title {{ font-size: 22px; color: #fff; margin: 20px 0 10px; padding-bottom: 8px; border-bottom: 1px solid #333; }}
.legend-row {{ display: flex; gap: 20px; margin: 10px 0; flex-wrap: wrap; }}
.legend-item {{ display: flex; align-items: center; gap: 6px; font-size: 13px; color: #ccc; }}
.legend-dot {{ width: 12px; height: 12px; border-radius: 50%; }}
</style>
</head>
<body>

<div class="header">
    <h1>RavenStack — Churn Diagnostic Dashboard v2</h1>
    <p>Visao Unificada | 5 datasets, {total_accounts} accounts, {len(churn)} churn events, 352 contas afetadas | Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
</div>

<div class="nav">
    <button class="active" onclick="showSection('overview')">Visao Unificada</button>
    <button onclick="showSection('ceo')" style="border-color:#ffd700;color:#ffd700">Pergunta do CEO</button>
    <button onclick="showSection('segments')">Segmentacao</button>
    <button onclick="showSection('revenue')">Revenue Impact</button>
    <button onclick="showSection('usage')">Feature Usage</button>
    <button onclick="showSection('support')">Suporte & Satisfacao</button>
    <button onclick="showSection('timeline')">Timeline & Cohorts</button>
    <button onclick="showSection('multichurn')">Multi-Churn</button>
    <button onclick="showSection('matrices')" style="border-color:#b366ff;color:#b366ff">Matrizes & Health Score</button>
    <button onclick="showSection('strategy')" style="border-color:#ff6b9d;color:#ff6b9d">Estrategia & ROI</button>
    <button onclick="showSection('diagnostic')" style="border-color:#00d2a0;color:#00d2a0">Diagnostico Final</button>
    <button onclick="showSection('feedback')">Feedback</button>
    <button onclick="showSection('tables')">5 Tabelas Completas</button>
</div>

<div class="container">

<!-- ═══════════════ OVERVIEW ═══════════════ -->
<div id="overview" class="section active">
    <h2 class="section-title">Visao Unificada — Classificacao Real das Contas</h2>

    <div class="insight red">
        <h3>Correcao Critica: O churn NAO e 22%</h3>
        <ul>
            <li><strong>600 eventos de churn para 352 contas unicas</strong> — muitas contas churnaram multiplas vezes</li>
            <li><strong>churn_flag = estado ATUAL</strong> (ativo/inativo), NAO historico. 277 contas churnaram mas VOLTARAM e estao ativas</li>
            <li><strong>Churn permanente real: {n_lost} contas ({n_lost/total_accounts*100:.1f}%)</strong> — essas sairam e NAO voltaram</li>
            <li><strong>Porta giratoria: {n_revolving} contas ({n_revolving/total_accounts*100:.1f}%)</strong> — cancelam, voltam, cancelam de novo. Problema diferente de churn terminal</li>
        </ul>
    </div>

    <div class="kpi-row">
        <div class="kpi green">
            <div class="value">{n_never}</div>
            <div class="label">Nunca Churnaram</div>
            <div class="sub">{n_never/total_accounts*100:.0f}% — base saudavel</div>
        </div>
        <div class="kpi yellow">
            <div class="value">{n_revolving}</div>
            <div class="label">Porta Giratoria</div>
            <div class="sub">{n_revolving/total_accounts*100:.0f}% — churnaram mas voltaram</div>
        </div>
        <div class="kpi">
            <div class="value">{n_lost}</div>
            <div class="label">Perdidos Permanente</div>
            <div class="sub">{n_lost/total_accounts*100:.0f}% — churn REAL</div>
        </div>
        <div class="kpi orange">
            <div class="value">{n_flag_only}</div>
            <div class="label">Flag sem Evento</div>
            <div class="sub">Dados incompletos</div>
        </div>
    </div>

    <div class="kpi-row">
        <div class="kpi green">
            <div class="value">${total_mrr:,.0f}</div>
            <div class="label">MRR Ativo Total</div>
            <div class="sub">Media ${avg_mrr:,.0f}/conta</div>
        </div>
        <div class="kpi">
            <div class="value">${lost_mrr:,.0f}</div>
            <div class="label">MRR Perdido (Permanente)</div>
            <div class="sub">${lost_mrr*12:,.0f}/ano</div>
        </div>
        <div class="kpi blue">
            <div class="value">${recovered_mrr:,.0f}</div>
            <div class="label">MRR Recuperado (Porta Giratoria)</div>
            <div class="sub">Clientes que voltaram</div>
        </div>
        <div class="kpi yellow">
            <div class="value">{n_multi_churn}</div>
            <div class="label">Contas Multi-Churn (2+)</div>
            <div class="sub">{n_multi_churn} reincidentes</div>
        </div>
    </div>

    <div class="chart-grid">
        <div class="chart-box">
            <h3>Composicao das 500 Contas</h3>
            <div id="chart_segments_pie"></div>
        </div>
        <div class="chart-box">
            <h3>Motivos de Churn: Perdidos vs Porta Giratoria</h3>
            <div id="chart_reasons_compare"></div>
        </div>
    </div>

    <div class="chart-grid">
        <div class="chart-box chart-full">
            <h3>Distribuicao de Eventos por Conta</h3>
            <div id="chart_events_dist"></div>
        </div>
    </div>
</div>

<!-- ═══════════════ CEO QUESTION ═══════════════ -->
<div id="ceo" class="section">
    <h2 class="section-title">Resposta ao CEO: "Produto diz que uso cresceu. Algo nao bate."</h2>

    <div class="insight red">
        <h3>Veredicto: O uso da plataforma NAO cresceu</h3>
        <ul>
            <li><strong>Uso total FLAT</strong>: ~10.000-11.000 unidades/mes ao longo de 24 meses. Sem tendencia de crescimento</li>
            <li><strong>Uso por conta FLAT</strong>: media de ~24-26 por conta/mes. Nenhuma variacao significativa</li>
            <li><strong>Contas ativas FLAT</strong>: ~410-440 contas usando a plataforma/mes, apesar de ~20 novas contas/mes</li>
            <li><strong>Novas contas compensam churns</strong>: a base nao cresce porque o churn come os novos signups</li>
            <li><strong>O time de Produto pode estar olhando metricas cumulativas</strong> (total de signups, total de features lancadas) em vez de uso real</li>
        </ul>
    </div>

    <div class="chart-grid">
        <div class="chart-box chart-full">
            <h3>Uso Total por Mes (o que o time de Produto provavelmente mostra)</h3>
            <div id="chart_ceo_total"></div>
        </div>
        <div class="chart-box chart-full">
            <h3>Uso MEDIO por Conta por Mes (a metrica que importa)</h3>
            <div id="chart_ceo_per_acct"></div>
        </div>
        <div class="chart-box chart-full">
            <h3>Uso Total por Segmento (quem esta usando?)</h3>
            <div id="chart_ceo_by_seg"></div>
        </div>
        <div class="chart-box chart-full">
            <h3>Contas Ativas vs Novas Contas por Mes</h3>
            <div id="chart_ceo_accounts"></div>
        </div>
    </div>

    <div class="insight green">
        <h3>O que dizer ao CEO</h3>
        <ul>
            <li><strong>"O uso total nao cresceu."</strong> Estavel em ~10.500/mes nos ultimos 24 meses</li>
            <li><strong>"O uso por conta tambem nao."</strong> Media de ~25 por conta — igual em jan/2023 e dez/2024</li>
            <li><strong>"A base de usuarios nao esta crescendo."</strong> ~20 signups/mes sao anulados pelo churn</li>
            <li><strong>"CS diz satisfacao ok"</strong> — verdade, mas o instrumento de satisfacao so mede 3-5 (nunca 1-2). E inutil como alerta</li>
            <li><strong>Conclusao</strong>: O problema nao e de uso, e de RETENCAO. 55% das contas ja cancelaram pelo menos 1x (porta giratoria)</li>
        </ul>
    </div>
</div>

<!-- ═══════════════ SEGMENTS ═══════════════ -->
<div id="segments" class="section">
    <h2 class="section-title">Segmentacao — Onde esta o Churn?</h2>

    <div class="legend-row">
        <div class="legend-item"><div class="legend-dot" style="background:#00d2a0"></div>Nunca Churnou</div>
        <div class="legend-item"><div class="legend-dot" style="background:#ffd700"></div>Porta Giratoria</div>
        <div class="legend-item"><div class="legend-dot" style="background:#e94560"></div>Perdido Permanente</div>
    </div>

    <div class="chart-grid">
        <div class="chart-box">
            <h3>Por Industria</h3>
            <div id="chart_ind_stack"></div>
        </div>
        <div class="chart-box">
            <h3>Por Plano</h3>
            <div id="chart_plan_stack"></div>
        </div>
        <div class="chart-box">
            <h3>Por Canal de Aquisicao</h3>
            <div id="chart_ref_stack"></div>
        </div>
        <div class="chart-box">
            <h3>Por Pais</h3>
            <div id="chart_country_stack"></div>
        </div>
    </div>

    <div class="chart-grid">
        <div class="chart-box">
            <h3>Heatmap: Churn Permanente % (Plano x Industria)</h3>
            <div id="chart_heatmap_perm"></div>
        </div>
        <div class="chart-box">
            <h3>Heatmap: Ja Churnou (qualquer) % (Plano x Industria)</h3>
            <div id="chart_heatmap_ever"></div>
        </div>
    </div>

    <div class="chart-grid">
        <div class="chart-box chart-full">
            <h3>Tabela Detalhada por Industria</h3>
            <table>
                <tr><th>Industria</th><th>Total</th><th>Nunca</th><th>Porta Giratoria</th><th>Perdido</th><th>Churn Perm %</th><th>Ja Churnou %</th></tr>
                {"".join(f"<tr><td>{r['industry']}</td><td>{r['total']}</td><td>{r['never']}</td><td>{r['revolving']}</td><td>{r['lost']}</td><td><strong>{r['churn_rate']}%</strong></td><td>{r['ever_churned_rate']}%</td></tr>" for _, r in by_industry.iterrows())}
            </table>
        </div>
    </div>
</div>

<!-- ═══════════════ REVENUE ═══════════════ -->
<div id="revenue" class="section">
    <h2 class="section-title">Impacto em Receita</h2>
    <div class="kpi-row">
        <div class="kpi">
            <div class="value">${lost_mrr:,.0f}/mes</div>
            <div class="label">MRR Perdido Permanente</div>
            <div class="sub">${lost_mrr*12:,.0f}/ano</div>
        </div>
        <div class="kpi blue">
            <div class="value">${recovered_mrr:,.0f}/mes</div>
            <div class="label">MRR Recuperado</div>
            <div class="sub">Porta giratoria ativas agora</div>
        </div>
        <div class="kpi yellow">
            <div class="value">${total_refunds:,.0f}</div>
            <div class="label">Total Refunds</div>
            <div class="sub">Media ${churn['refund_amount_usd'].mean():,.0f}/evento</div>
        </div>
    </div>
    <div class="chart-grid">
        <div class="chart-box">
            <h3>MRR Perdido por Plano</h3>
            <div id="chart_rev_plan"></div>
        </div>
        <div class="chart-box">
            <h3>MRR Perdido por Industria</h3>
            <div id="chart_rev_industry"></div>
        </div>
        <div class="chart-box">
            <h3>Distribuicao MRR: Perdidos vs Ativos</h3>
            <div id="chart_mrr_dist"></div>
        </div>
        <div class="chart-box">
            <h3>Refund Total por Motivo</h3>
            <div id="chart_refund"></div>
        </div>
    </div>
</div>

<!-- ═══════════════ USAGE ═══════════════ -->
<div id="usage" class="section">
    <h2 class="section-title">Feature Usage — 3 Segmentos Comparados</h2>

    <div class="compare-grid">
        <div class="compare-card seg-never">
            <h3>Nunca Churnou ({n_never})</h3>
            <div class="stat-row"><span class="stat-label">Features unicas/conta</span><span class="stat-value">{usage_by_seg['Nunca Churnou']['features_per_acct']}</span></div>
            <div class="stat-row"><span class="stat-label">Eventos/conta</span><span class="stat-value">{usage_by_seg['Nunca Churnou']['events_per_acct']}</span></div>
            <div class="stat-row"><span class="stat-label">Uso medio (count)</span><span class="stat-value">{usage_by_seg['Nunca Churnou']['avg_usage_count']}</span></div>
            <div class="stat-row"><span class="stat-label">Duracao media (seg)</span><span class="stat-value">{usage_by_seg['Nunca Churnou']['avg_duration']:,.0f}</span></div>
            <div class="stat-row"><span class="stat-label">Erros medios</span><span class="stat-value">{usage_by_seg['Nunca Churnou']['avg_errors']}</span></div>
            <div class="stat-row"><span class="stat-label">% beta features</span><span class="stat-value">{usage_by_seg['Nunca Churnou']['beta_pct']}%</span></div>
        </div>
        <div class="compare-card seg-revolv">
            <h3>Porta Giratoria ({n_revolving})</h3>
            <div class="stat-row"><span class="stat-label">Features unicas/conta</span><span class="stat-value">{usage_by_seg['Porta Giratoria']['features_per_acct']}</span></div>
            <div class="stat-row"><span class="stat-label">Eventos/conta</span><span class="stat-value">{usage_by_seg['Porta Giratoria']['events_per_acct']}</span></div>
            <div class="stat-row"><span class="stat-label">Uso medio (count)</span><span class="stat-value">{usage_by_seg['Porta Giratoria']['avg_usage_count']}</span></div>
            <div class="stat-row"><span class="stat-label">Duracao media (seg)</span><span class="stat-value">{usage_by_seg['Porta Giratoria']['avg_duration']:,.0f}</span></div>
            <div class="stat-row"><span class="stat-label">Erros medios</span><span class="stat-value">{usage_by_seg['Porta Giratoria']['avg_errors']}</span></div>
            <div class="stat-row"><span class="stat-label">% beta features</span><span class="stat-value">{usage_by_seg['Porta Giratoria']['beta_pct']}%</span></div>
        </div>
        <div class="compare-card seg-lost">
            <h3>Perdido Permanente ({n_lost})</h3>
            <div class="stat-row"><span class="stat-label">Features unicas/conta</span><span class="stat-value">{usage_by_seg['Perdido Permanente']['features_per_acct']}</span></div>
            <div class="stat-row"><span class="stat-label">Eventos/conta</span><span class="stat-value">{usage_by_seg['Perdido Permanente']['events_per_acct']}</span></div>
            <div class="stat-row"><span class="stat-label">Uso medio (count)</span><span class="stat-value">{usage_by_seg['Perdido Permanente']['avg_usage_count']}</span></div>
            <div class="stat-row"><span class="stat-label">Duracao media (seg)</span><span class="stat-value">{usage_by_seg['Perdido Permanente']['avg_duration']:,.0f}</span></div>
            <div class="stat-row"><span class="stat-label">Erros medios</span><span class="stat-value">{usage_by_seg['Perdido Permanente']['avg_errors']}</span></div>
            <div class="stat-row"><span class="stat-label">% beta features</span><span class="stat-value">{usage_by_seg['Perdido Permanente']['beta_pct']}%</span></div>
        </div>
    </div>

    <div class="chart-grid">
        <div class="chart-box">
            <h3>Top Features: Nunca Churnou</h3>
            <div id="chart_feat_never"></div>
        </div>
        <div class="chart-box">
            <h3>Top Features: Perdido Permanente</h3>
            <div id="chart_feat_lost"></div>
        </div>
        <div class="chart-box chart-full">
            <h3>Features com Mais Erros (Perdidos Permanentes)</h3>
            <div id="chart_errors_lost"></div>
        </div>
    </div>
</div>

<!-- ═══════════════ SUPPORT ═══════════════ -->
<div id="support" class="section">
    <h2 class="section-title">Suporte & Satisfacao</h2>

    <div class="insight">
        <h3>Conclusao sobre Satisfacao</h3>
        <ul>
            <li><strong>Scores so existem em 3, 4 e 5</strong> — nenhum score 1 ou 2 em 2000 tickets. O instrumento NAO captura insatisfacao real</li>
            <li><strong>Medias identicas</strong> entre churned/retained, por prioridade, por escalacao, por tempo de resolucao</li>
            <li><strong>41% sem resposta</strong> — silenciosos podem ser os mais insatisfeitos (viés de nao-resposta)</li>
            <li><strong>Validacao do CEO</strong>: "CS diz satisfacao ok" e VERDADE nos dados — mas o score e inutil como indicador de risco</li>
        </ul>
    </div>

    <div class="compare-grid">
        <div class="compare-card seg-never">
            <h3>Nunca Churnou</h3>
            <div class="stat-row"><span class="stat-label">Tickets/conta</span><span class="stat-value">{support_by_seg['Nunca Churnou']['tickets_per_acct']}</span></div>
            <div class="stat-row"><span class="stat-label">Tempo resolucao (h)</span><span class="stat-value">{support_by_seg['Nunca Churnou']['avg_resolution']}</span></div>
            <div class="stat-row"><span class="stat-label">1a resposta (min)</span><span class="stat-value">{support_by_seg['Nunca Churnou']['avg_first_response']:.0f}</span></div>
            <div class="stat-row"><span class="stat-label">Satisfacao media</span><span class="stat-value">{support_by_seg['Nunca Churnou']['avg_satisfaction']}</span></div>
            <div class="stat-row"><span class="stat-label">% sem score</span><span class="stat-value">{support_by_seg['Nunca Churnou']['null_satisfaction_pct']:.0f}%</span></div>
            <div class="stat-row"><span class="stat-label">Taxa escalacao</span><span class="stat-value">{support_by_seg['Nunca Churnou']['escalation_rate']}%</span></div>
        </div>
        <div class="compare-card seg-revolv">
            <h3>Porta Giratoria</h3>
            <div class="stat-row"><span class="stat-label">Tickets/conta</span><span class="stat-value">{support_by_seg['Porta Giratoria']['tickets_per_acct']}</span></div>
            <div class="stat-row"><span class="stat-label">Tempo resolucao (h)</span><span class="stat-value">{support_by_seg['Porta Giratoria']['avg_resolution']}</span></div>
            <div class="stat-row"><span class="stat-label">1a resposta (min)</span><span class="stat-value">{support_by_seg['Porta Giratoria']['avg_first_response']:.0f}</span></div>
            <div class="stat-row"><span class="stat-label">Satisfacao media</span><span class="stat-value">{support_by_seg['Porta Giratoria']['avg_satisfaction']}</span></div>
            <div class="stat-row"><span class="stat-label">% sem score</span><span class="stat-value">{support_by_seg['Porta Giratoria']['null_satisfaction_pct']:.0f}%</span></div>
            <div class="stat-row"><span class="stat-label">Taxa escalacao</span><span class="stat-value">{support_by_seg['Porta Giratoria']['escalation_rate']}%</span></div>
        </div>
        <div class="compare-card seg-lost">
            <h3>Perdido Permanente</h3>
            <div class="stat-row"><span class="stat-label">Tickets/conta</span><span class="stat-value">{support_by_seg['Perdido Permanente']['tickets_per_acct']}</span></div>
            <div class="stat-row"><span class="stat-label">Tempo resolucao (h)</span><span class="stat-value">{support_by_seg['Perdido Permanente']['avg_resolution']}</span></div>
            <div class="stat-row"><span class="stat-label">1a resposta (min)</span><span class="stat-value">{support_by_seg['Perdido Permanente']['avg_first_response']:.0f}</span></div>
            <div class="stat-row"><span class="stat-label">Satisfacao media</span><span class="stat-value">{support_by_seg['Perdido Permanente']['avg_satisfaction']}</span></div>
            <div class="stat-row"><span class="stat-label">% sem score</span><span class="stat-value">{support_by_seg['Perdido Permanente']['null_satisfaction_pct']:.0f}%</span></div>
            <div class="stat-row"><span class="stat-label">Taxa escalacao</span><span class="stat-value">{support_by_seg['Perdido Permanente']['escalation_rate']}%</span></div>
        </div>
    </div>

    <div class="chart-grid">
        <div class="chart-box">
            <h3>Distribuicao de Scores de Satisfacao (TODOS)</h3>
            <div id="chart_sat_dist"></div>
        </div>
        <div class="chart-box">
            <h3>Problema: So scores 3-5, nenhum 1-2</h3>
            <div style="padding: 40px; text-align: center;">
                <div style="font-size: 60px; margin-bottom: 20px;">&#9888;</div>
                <p style="font-size: 16px; color: #ffd700; margin-bottom: 10px;">Instrumento de Satisfacao Quebrado</p>
                <table style="margin: 0 auto; text-align: left;">
                    <tr><th>Score</th><th>Tickets</th><th>%</th></tr>
                    {"".join(f"<tr><td>Score {k}</td><td>{v}</td><td>{v/sum(sat_scores.values())*100:.0f}%</td></tr>" for k, v in sat_scores.items())}
                    <tr style="border-top: 2px solid #ffd700"><td><strong>Null (sem resposta)</strong></td><td><strong>{tickets['satisfaction_score'].isna().sum()}</strong></td><td><strong>{tickets['satisfaction_score'].isna().mean()*100:.0f}%</strong></td></tr>
                </table>
                <p style="color: #888; margin-top: 15px; font-size: 13px;">Sem scores 1 ou 2, o indicador nao diferencia clientes satisfeitos de insatisfeitos.<br>Recomendacao: redesenhar pesquisa de satisfacao ou usar NPS.</p>
            </div>
        </div>
    </div>
</div>

<!-- ═══════════════ TIMELINE ═══════════════ -->
<div id="timeline" class="section">
    <h2 class="section-title">Timeline & Cohort Analysis</h2>
    <div class="chart-grid">
        <div class="chart-box chart-full">
            <h3>Eventos de Churn por Mes — Permanente vs Porta Giratoria</h3>
            <div id="chart_timeline"></div>
        </div>
        <div class="chart-box chart-full">
            <h3>Cohort de Signup: Taxa de Churn por Mes de Cadastro</h3>
            <div id="chart_cohort"></div>
        </div>
        <div class="chart-box">
            <h3>Dias entre Signup e Primeiro Churn</h3>
            <div id="chart_days_churn"></div>
        </div>
        <div class="chart-box">
            <h3>Estatisticas: Tempo ate Churn</h3>
            <table>
                <tr><th>Metrica</th><th>Dias</th></tr>
                <tr><td>Media</td><td>{dtc_stats.get('mean', 'N/A')}</td></tr>
                <tr><td>Mediana</td><td>{dtc_stats.get('50%', 'N/A')}</td></tr>
                <tr><td>Minimo</td><td>{dtc_stats.get('min', 'N/A')}</td></tr>
                <tr><td>Maximo</td><td>{dtc_stats.get('max', 'N/A')}</td></tr>
                <tr><td>Desvio Padrao</td><td>{dtc_stats.get('std', 'N/A')}</td></tr>
            </table>
        </div>
    </div>
</div>

<!-- ═══════════════ MULTI-CHURN ═══════════════ -->
<div id="multichurn" class="section">
    <h2 class="section-title">Multi-Churn — O Fenomeno da Porta Giratoria</h2>

    <div class="kpi-row">
        <div class="kpi yellow">
            <div class="value">{n_multi_churn}</div>
            <div class="label">Contas com 2+ Churns</div>
            <div class="sub">{n_multi_churn/total_accounts*100:.0f}% de todas as contas</div>
        </div>
        <div class="kpi blue">
            <div class="value">{avg_gap:.0f} dias</div>
            <div class="label">Gap Medio entre Churns</div>
            <div class="sub">Mediana: {median_gap} dias</div>
        </div>
        <div class="kpi orange">
            <div class="value">{reason_changes}</div>
            <div class="label">Mudaram de Motivo</div>
            <div class="sub">entre churns consecutivos</div>
        </div>
        <div class="kpi purple">
            <div class="value">{reason_same}</div>
            <div class="label">Mesmo Motivo Repetido</div>
            <div class="sub">problema nao resolvido</div>
        </div>
    </div>

    <div class="chart-grid">
        <div class="chart-box">
            <h3>Distribuicao: Quantos Churns por Conta</h3>
            <div id="chart_multi_dist"></div>
        </div>
        <div class="chart-box">
            <h3>Upgrade antes de Churn: Permanente vs Revolving</h3>
            <div id="chart_upgrade_seg"></div>
        </div>
    </div>

    <div class="insight">
        <h3>Analise Multi-Churn</h3>
        <ul>
            <li><strong>{n_multi_churn} contas churnaram 2+ vezes</strong> — gap medio de {avg_gap:.0f} dias entre saida e proxima saida</li>
            <li><strong>{reason_changes} vezes mudaram de motivo</strong> entre churns consecutivos vs {reason_same} vezes repetiram — sugere que o motivo declarado e pouco confiavel</li>
            <li><strong>{reactivations} marcados como reativacao</strong> mas 175 contas tem multiplos churns — flag is_reactivation subreporta o fenomeno</li>
            <li><strong>Padrao</strong>: cliente cancela, volta, descobre que o problema persiste, cancela de novo com motivo diferente</li>
        </ul>
    </div>
</div>

<!-- ═══════════════ MATRICES ═══════════════ -->
<div id="matrices" class="section">
    <h2 class="section-title">Matrizes de Analise & Customer Health Score</h2>

    <div class="insight red">
        <h3>Descoberta Critica: Health Score NAO diferencia os segmentos</h3>
        <ul>
            <li><strong>Nunca Churnou: {health_seg.loc['Nunca Churnou', 'mean']}</strong> media</li>
            <li><strong>Porta Giratoria: {health_seg.loc['Porta Giratoria', 'mean']}</strong> media</li>
            <li><strong>Perdido Permanente: {health_seg.loc['Perdido Permanente', 'mean']}</strong> media ← MAIOR que os saudaveis!</li>
            <li>Metricas tradicionais de Customer Success (uso, features, erros, tickets) <strong>NAO predizem churn</strong> neste cenario</li>
            <li>O churn e <strong>ESTRUTURAL</strong> (modelo de negocio / porta giratoria), nao comportamental</li>
        </ul>
    </div>

    <div class="chart-grid">
        <div class="chart-box">
            <h3>Health Score por Segmento (0-100)</h3>
            <div id="chart_health_box"></div>
        </div>
        <div class="chart-box">
            <h3>Zonas de Saude por Segmento</h3>
            <div id="chart_health_zones"></div>
        </div>
    </div>

    <div class="chart-grid">
        <div class="chart-box">
            <h3>Matriz Valor x Risco — Contas por Celula</h3>
            <div id="chart_vr_counts"></div>
        </div>
        <div class="chart-box">
            <h3>Matriz Valor x Risco — Perdidos Permanentes por Celula</h3>
            <div id="chart_vr_lost"></div>
        </div>
    </div>

    <div class="insight">
        <h3>Leitura da Matriz Valor x Risco</h3>
        <ul>
            <li><strong>High Value + Low Risk: 18 perdidos</strong> — a empresa perde seus MELHORES clientes sem saber. Health score dizia "tudo bem"</li>
            <li><strong>Low Value + Med Risk: 14 perdidos</strong> — esperado, mas menor impacto financeiro</li>
            <li><strong>O score de risco NAO funciona como preditor</strong> — perdas distribuidas quase uniformemente, independente do risco calculado</li>
        </ul>
    </div>

    <div class="chart-grid">
        <div class="chart-box chart-full">
            <h3>Scatter: Health Score vs MRR (cada ponto = 1 conta)</h3>
            <div id="chart_health_scatter"></div>
        </div>
    </div>

    <div class="chart-box" style="margin: 20px 0;">
        <h3>Componentes do Health Score</h3>
        <table>
            <tr><th>Componente</th><th>Peso</th><th>O que mede</th><th>Resultado</th></tr>
            <tr><td>Uso Total</td><td>25%</td><td>Volume de interacoes</td><td><span class="tag tag-yellow">Nao diferencia</span></td></tr>
            <tr><td>Features Unicas</td><td>20%</td><td>Amplitude de adocao</td><td><span class="tag tag-yellow">Nao diferencia</span></td></tr>
            <tr><td>Recencia</td><td>25%</td><td>Ultima vez que usou</td><td><span class="tag tag-yellow">Nao diferencia</span></td></tr>
            <tr><td>Erros</td><td>15%</td><td>Problemas tecnicos</td><td><span class="tag tag-yellow">Nao diferencia</span></td></tr>
            <tr><td>Tickets</td><td>15%</td><td>Carga de suporte</td><td><span class="tag tag-yellow">Nao diferencia</span></td></tr>
            <tr><td colspan="3"><strong>Conclusao</strong></td><td><span class="tag tag-red">Health Score INUTIL como preditor de churn</span></td></tr>
        </table>
    </div>
</div>

<!-- ═══════════════ STRATEGY & ROI ═══════════════ -->
<div id="strategy" class="section">
    <h2 class="section-title">Estrategia & ROI — Analise Ponderada por Receita</h2>

    <div class="insight red">
        <h3>Descoberta: Enterprise = 73% do MRR Perdido</h3>
        <ul>
            <li><strong>25 contas Enterprise perdidas = ${ent_lost_mrr:,.0f}/mes</strong> (${ent_lost_mrr*12:,.0f}/ano) — {ent_lost_pct:.0f}% de TODO o MRR perdido</li>
            <li><strong>MRR medio Enterprise perdido: ${rev_lost_by_tier['Enterprise']['mrr_avg']:,.0f}/mo</strong> vs Basic ${rev_lost_by_tier['Basic']['mrr_avg']:,.0f}/mo — cada Enterprise perdido vale 10x um Basic</li>
            <li><strong>Top 10 contas perdidas = ${sum(r['mrr_amount'] for r in top10_lost):,.0f}/mes</strong> — apenas 10 contas representam {sum(r['mrr_amount'] for r in top10_lost)/total_lost_mrr*100:.0f}% do MRR perdido</li>
        </ul>
    </div>

    <div class="kpi-row">
        <div class="kpi">
            <div class="value">${total_lost_mrr:,.0f}/mes</div>
            <div class="label">MRR Perdido Total</div>
            <div class="sub">${total_lost_mrr*12:,.0f}/ano</div>
        </div>
        <div class="kpi" style="border-left-color:#ff6b9d">
            <div class="value">${ent_lost_mrr:,.0f}/mes</div>
            <div class="label">MRR Perdido Enterprise</div>
            <div class="sub">{ent_lost_pct:.0f}% do total perdido</div>
        </div>
        <div class="kpi blue">
            <div class="value">${rev_lost_by_tier['Basic']['mrr']:,.0f}/mes</div>
            <div class="label">MRR Perdido Basic ({rev_lost_by_tier['Basic']['n']})</div>
            <div class="sub">Media ${rev_lost_by_tier['Basic']['mrr_avg']:,.0f}/conta</div>
        </div>
        <div class="kpi yellow">
            <div class="value">${rev_lost_by_tier['Pro']['mrr']:,.0f}/mes</div>
            <div class="label">MRR Perdido Pro ({rev_lost_by_tier['Pro']['n']})</div>
            <div class="sub">Media ${rev_lost_by_tier['Pro']['mrr_avg']:,.0f}/conta</div>
        </div>
    </div>

    <div class="chart-box" style="margin:20px 0; overflow-x:auto;">
        <h3>Top 10 Contas Perdidas por MRR (cada uma dessas merece um telefonema do CEO)</h3>
        <table>
            <tr><th>#</th><th>Conta</th><th>Industria</th><th>Plano</th><th>MRR</th><th>ARR Equivalente</th></tr>
            {"".join(f"<tr><td>{i+1}</td><td>{r['account_name']}</td><td>{r['industry']}</td><td><span class='tag tag-red'>{r['plan_tier_sub']}</span></td><td><strong>${r['mrr_amount']:,.0f}</strong></td><td>${r['mrr_amount']*12:,.0f}</td></tr>" for i, r in enumerate(top10_lost))}
        </table>
    </div>

    <h3 style="color:#ff6b9d;margin:30px 0 15px;">Significancia Estatistica — O que e real vs ruido</h3>

    <div class="insight">
        <h3>Por que isso importa</h3>
        <ul>
            <li><strong>Nem toda variacao e significativa.</strong> Alemanha tem 24% de churn vs 15% global, mas com n=25, o intervalo de confianca vai de 11.5% a 43.4%. Pode ser acaso.</li>
            <li><strong>DevTools e o UNICO segmento estatisticamente significativo</strong> (p=0.004). Os 24.8% de churn NAO sao acaso — e um problema real do produto para esse vertical.</li>
            <li><strong>Canal "events" e marginalmente significativo</strong> (p=0.059). Vale investigar, mas com cautela.</li>
            <li><strong>Correlacao ≠ Causalidade:</strong> DevTools churna mais — mas e pelo produto? pelo mercado? pela concorrencia? Significancia estatistica so diz que o padrao e REAL, nao a causa.</li>
        </ul>
    </div>

    <div class="chart-box" style="margin:20px 0; overflow-x:auto;">
        <h3>Teste de Significancia: Churn por Segmentacao vs Media Global ({global_lost_rate*100:.1f}%)</h3>
        <table>
            <tr><th>Tipo</th><th>Segmento</th><th>n</th><th>Perdidos</th><th>Taxa</th><th>IC 95%</th><th>p-valor</th><th>Significancia</th></tr>
            {"".join(f"<tr><td>{r['col']}</td><td>{r['name']}</td><td>{r['n']}</td><td>{r['lost']}</td><td><strong>{r['rate']}%</strong></td><td>[{r['ci_lo']}% - {r['ci_hi']}%]</td><td>{r['p'] if r['p'] is not None else 'N/A'}</td><td><span class='tag {r['sig_tag']}'>{r['sig']}</span></td></tr>" for r in sig_results)}
        </table>
    </div>

    <h3 style="color:#ff6b9d;margin:30px 0 15px;">Billing: Mensal vs Anual</h3>

    <div class="insight">
        <h3>Descoberta Contra-Intuitiva: Mensal perde MENOS contas mas MAIS receita</h3>
        <ul>
            <li><strong>Mensal: {billing_stats['monthly']['n_lost']} perdidos ({billing_stats['monthly']['rate']}%)</strong>, MRR perdido: ${billing_stats['monthly']['mrr_lost']:,.0f} ({billing_stats['monthly']['mrr_lost_pct']}% do MRR mensal)</li>
            <li><strong>Anual: {billing_stats['annual']['n_lost']} perdidos ({billing_stats['annual']['rate']}%)</strong>, MRR perdido: ${billing_stats['annual']['mrr_lost']:,.0f} ({billing_stats['annual']['mrr_lost_pct']}% do MRR anual)</li>
            <li><strong>MRR medio perdido mensal: ${billing_stats['monthly']['mrr_avg_lost']:,.0f}</strong> vs anual: ${billing_stats['annual']['mrr_avg_lost']:,.0f} — mensal perde contas de MAIOR valor</li>
            <li><strong>Implicacao:</strong> Desconto para plano anual beneficia mais a retencao de receita do que de contas. Contas grandes no mensal sao as mais vulneraveis.</li>
        </ul>
    </div>

    <div class="chart-grid">
        <div class="chart-box">
            <h3>MRR Perdido: Mensal vs Anual</h3>
            <div id="chart_billing_mrr"></div>
        </div>
        <div class="chart-box">
            <h3>Contas por Faixa de Seats (e % perdido)</h3>
            <div id="chart_seats_analysis"></div>
        </div>
    </div>

    <h3 style="color:#ff6b9d;margin:30px 0 15px;">5 Estrategias com ROI Estimado</h3>

    <div class="chart-grid">
        <div class="chart-box chart-full">
            <h3>Simulacao de Impacto</h3>
            <div id="chart_strategy_impact"></div>
        </div>
    </div>

    <div class="insight green">
        <h3>1. Enterprise Save Program (ROI: {strat_ent_roi:.0f}x)</h3>
        <ul>
            <li><strong>Problema:</strong> 25 contas Enterprise = ${ent_lost_mrr:,.0f}/mes = {ent_lost_pct:.0f}% de todo MRR perdido</li>
            <li><strong>Acao:</strong> 1 CSM dedicado (~$8.000/mes) com QBR trimestral, onboarding personalizado, executive sponsor</li>
            <li><strong>Se salvar 5 de 25 (20%):</strong> recupera ${top5_ent_mrr:,.0f}/mes = ${top5_ent_mrr*12:,.0f}/ano</li>
            <li><strong>ROI:</strong> {strat_ent_roi:.0f}x o custo do CSM. Payback em &lt;1 mes</li>
        </ul>
    </div>

    <div class="insight green">
        <h3>2. Desconto Anual para Contas Mensais de Alto Valor</h3>
        <ul>
            <li><strong>Problema:</strong> Mensal perde ${billing_stats['monthly']['mrr_lost']:,.0f}/mes — contas de alto valor sem lock-in</li>
            <li><strong>Acao:</strong> Oferecer 15% de desconto para migrar mensal → anual para contas com MRR > $2.000</li>
            <li><strong>Mecanismo:</strong> Pagamento anual = 12 meses de compromisso = cliente nao pode sair impulsivamente</li>
            <li><strong>Estimativa conservadora (40% conversao, 30% retencao incremental):</strong></li>
            <li>Custo desconto: ~$5.600/mes | Retencao: ~$11.300/mes | <strong>Net: ~$67.700/ano</strong></li>
        </ul>
    </div>

    <div class="insight green">
        <h3>3. DevTools Product-Market Fit (unico segmento significativo p=0.004)</h3>
        <ul>
            <li><strong>Problema:</strong> DevTools tem 24.8% de churn vs 15% global — CONFIRMADO estatisticamente</li>
            <li><strong>MRR em risco:</strong> ${rev_by_segment.get('Perdido Permanente', {}).get('mrr_total', 0):,.0f}/mes total, DevTools proporcional ~$57.800/mes</li>
            <li><strong>Acao:</strong> Auditoria de product-market fit: entrevistar 10 DevTools perdidos, analise competitiva, feature gap analysis</li>
            <li><strong>Se reduzir churn de 24.8% para baseline 15%:</strong> ~$23.000/mes salvos = $274.000/ano</li>
        </ul>
    </div>

    <div class="insight green">
        <h3>4. Interromper Porta Giratoria (277 contas reincidentes)</h3>
        <ul>
            <li><strong>Problema:</strong> 55% das contas ja cancelaram pelo menos 1x. Custo escondido de re-onboarding e re-aquisicao</li>
            <li><strong>Acao:</strong> Programa "90-Day Success": milestone de valor aos 30, 60 e 90 dias pos-reativacao</li>
            <li><strong>MRR em risco:</strong> ${rev_by_segment.get('Porta Giratoria', {}).get('mrr_total', 0):,.0f}/mes</li>
            <li><strong>Se 20% menos re-churns:</strong> ~$80.900/mes protegido de volatilidade</li>
        </ul>
    </div>

    <div class="insight green">
        <h3>5. Qualificar Canal Events (marginal p=0.059)</h3>
        <ul>
            <li><strong>Problema:</strong> Signups via eventos tem 21.9% de churn — sugere expectativa desalinhada</li>
            <li><strong>Acao:</strong> Alterar pitch em eventos (demo real vs slide deck), criar nurture track especifico, trial estendido</li>
            <li><strong>Custo:</strong> Baixo (mudanca de processo, nao de produto)</li>
            <li><strong>Impacto esperado:</strong> Reduzir aquicisao de contas com baixo fit, aumentar LTV das que ficam</li>
        </ul>
    </div>

    <div class="insight" style="border-left-color:#b366ff;">
        <h3 style="color:#b366ff;">Impacto Combinado (conservador)</h3>
        <ul>
            <li><strong>Perda atual:</strong> ${total_lost_mrr:,.0f}/mes (${total_lost_mrr*12:,.0f}/ano)</li>
            <li><strong>Enterprise Save:</strong> +${top5_ent_mrr:,.0f}/mes recuperado</li>
            <li><strong>Desconto Anual:</strong> +$5.600/mes net</li>
            <li><strong>DevTools Fix:</strong> +$22.800/mes (se reduzir a baseline)</li>
            <li><strong>Total potencial:</strong> ~${top5_ent_mrr + 5600 + 22800:,.0f}/mes = ~${(top5_ent_mrr + 5600 + 22800)*12:,.0f}/ano</li>
            <li><strong>Isso representa {(top5_ent_mrr + 5600 + 22800)/total_lost_mrr*100:.0f}% da perda anual atual</strong></li>
        </ul>
    </div>
</div>

<!-- ═══════════════ DIAGNOSTIC ═══════════════ -->
<div id="diagnostic" class="section">
    <h2 class="section-title">Diagnostico Final — Respostas ao CEO</h2>

    <div class="insight" style="border-left-color: #fff;">
        <h3 style="color: #fff;">Contexto: O que o CEO disse</h3>
        <ul>
            <li>"Estamos perdendo clientes e nao sei por que"</li>
            <li>"Numeros mostram que churn subiu"</li>
            <li>"CS diz que satisfacao esta ok"</li>
            <li>"Produto diz que uso da plataforma cresceu"</li>
            <li>"Algo nao bate"</li>
        </ul>
    </div>

    <h3 style="color:#e94560;margin:30px 0 15px;">1. O que esta causando o churn?</h3>
    <div class="insight red">
        <h3>Causa Raiz: Problema Estrutural — "Porta Giratoria"</h3>
        <ul>
            <li><strong>55% das contas (277/500)</strong> ja cancelaram pelo menos uma vez e voltaram</li>
            <li><strong>175 contas</strong> cancelaram 2+ vezes — ciclo de cancelar/voltar/cancelar</li>
            <li><strong>Motivos declarados sao RUIDO</strong>: distribuicao quase uniforme (features, support, budget, competitor, pricing, unknown ~100 cada) e 63% mudam de motivo entre churns consecutivos</li>
            <li><strong>Metricas comportamentais NAO diferenciam</strong>: uso, features, erros, tickets, satisfacao — tudo igual entre quem fica e quem sai</li>
            <li><strong>O problema nao e que clientes usam pouco</strong> — High Freq + Broad Usage tem 21 perdidos. Contas com alto health score tambem churnam</li>
            <li><strong>Hipotese principal</strong>: Gap entre proposta de valor e entrega. Clientes entram, usam bastante, nao veem ROI suficiente, saem. Voltam quando precisam de novo. Saem de novo.</li>
        </ul>
    </div>

    <h3 style="color:#ffd700;margin:30px 0 15px;">2. Quais segmentos estao em risco?</h3>
    <div class="insight">
        <h3>Segmentos Criticos — priorizados por impacto financeiro E significancia estatistica</h3>
        <ul>
            <li><strong>DevTools (24.8%, p=0.004)</strong>: UNICO segmento com churn estatisticamente acima da media. 113 contas, MRR perdido significativo. <span class="tag tag-red">Confirmado</span></li>
            <li><strong>Enterprise (25 contas = ${ent_lost_mrr:,.0f}/mes = {ent_lost_pct:.0f}% do MRR perdido)</strong>: Maior impacto financeiro. Cada conta Enterprise perdida = ~${rev_lost_by_tier['Enterprise']['mrr_avg']:,.0f}/mes</li>
            <li><strong>Canal "events" (21.9%, p=0.059)</strong>: Marginalmente significativo — vale investigar com cautela. <span class="tag tag-yellow">Marginal</span></li>
            <li><strong>Contas mensais de alto valor</strong>: MRR medio perdido mensal (${billing_stats['monthly']['mrr_avg_lost']:,.0f}) e 2x o anual (${billing_stats['annual']['mrr_avg_lost']:,.0f}). Sem lock-in.</li>
            <li><strong>Alemanha, Franca, Canada</strong>: Taxas altas (22-24%), porem <span class="tag tag-orange">n insuficiente</span> (n=22-25) — NAO e possivel concluir. Monitorar com base maior.</li>
            <li><strong>High Value + "Low Risk"</strong>: 18 contas perdidas neste quadrante. Health score diz "saudavel" e churn acontece — alerta falso negativo</li>
            <li><strong>Porta Giratoria (277 contas, ${rev_by_segment.get('Porta Giratoria', {}).get('mrr_total', 0):,.0f}/mes MRR)</strong>: 55% da base com historico de cancelamento. Risco permanente de re-churn</li>
        </ul>
    </div>

    <h3 style="color:#00d2a0;margin:30px 0 15px;">3. O que a empresa deveria fazer?</h3>
    <div class="insight green">
        <h3>Recomendacoes com ROI Estimado (ver aba "Estrategia & ROI" para detalhes)</h3>
        <ul>
            <li><strong>IMEDIATO — Enterprise Save Program (ROI {strat_ent_roi:.0f}x)</strong>: 1 CSM dedicado ($8k/mes) para as 25 contas Enterprise. Se salvar 5 = ${top5_ent_mrr:,.0f}/mes recuperado. Payback em &lt;1 mes</li>
            <li><strong>IMEDIATO — Redesenhar satisfacao</strong>: Scores 3-5 only = instrumento quebrado. Implementar NPS (0-10). Custo: baixo. Impacto: visibilidade real de risco</li>
            <li><strong>CURTO PRAZO — Desconto anual para contas mensais &gt;$2k</strong>: 15% desconto para lock-in 12 meses. Net ~$67.700/ano. Reduz saida impulsiva das contas de maior valor</li>
            <li><strong>CURTO PRAZO — Auditoria DevTools (p=0.004)</strong>: Entrevistar 10 contas DevTools perdidas, analise competitiva, feature gaps. Se reduzir churn a baseline = ~$274k/ano</li>
            <li><strong>MEDIO PRAZO — Programa "90-Day Success"</strong>: Para as 277 contas porta giratoria. Milestones de valor aos 30/60/90 dias pos-reativacao. Reduzir re-churn em 20% = $80.900/mes protegido</li>
            <li><strong>MEDIO PRAZO — Qualificar canal Events</strong>: 21.9% churn (marginal p=0.059). Demo real em eventos vs slide deck. Nurture track diferenciado. Trial estendido para leads de eventos</li>
        </ul>
    </div>

    <div class="insight" style="border-left-color: #b366ff;">
        <h3 style="color: #b366ff;">Metricas que NAO funcionam (e a empresa precisa saber)</h3>
        <ul>
            <li><strong>Satisfaction Score</strong>: So mede 3-5, 41% null. Inutil como alerta ← CS esta CEGO</li>
            <li><strong>Platform Usage</strong>: Flat ha 24 meses, igual entre churned e retained ← Produto esta se enganando</li>
            <li><strong>Health Score tradicional</strong>: Identico entre segmentos (61-65). Nao prediz churn ← Dashboard de CS esta errado</li>
            <li><strong>Reason codes declarados</strong>: Distribuicao uniforme, 63% mudam entre churns. Ruido ← Nao confiar em exit surveys</li>
        </ul>
    </div>

    <div class="insight green">
        <h3>O que FUNCIONA como sinal</h3>
        <ul>
            <li><strong>Numero de churns anteriores</strong>: O melhor preditor de churn futuro e ter churnado antes. 175 contas com 2+ churns sao risco permanente</li>
            <li><strong>Segmento DevTools + Enterprise</strong>: Combinacao especifica de alto risco + alto valor. Precisa de atencao dedicada</li>
            <li><strong>Canal de aquisicao "event"</strong>: Sinal de desalinhamento expectativa vs realidade</li>
            <li><strong>Silencio</strong>: 41% nao respondem satisfacao, 47% nao deixam feedback no churn. Os silenciosos podem ser os mais em risco</li>
        </ul>
    </div>
</div>

<!-- ═══════════════ FEEDBACK ═══════════════ -->
<div id="feedback" class="section">
    <h2 class="section-title">Feedback dos Clientes</h2>
    <div class="kpi-row">
        <div class="kpi blue">
            <div class="value">{n_with_feedback}</div>
            <div class="label">Com Feedback</div>
            <div class="sub">{n_with_feedback/len(churn)*100:.0f}% dos eventos</div>
        </div>
        <div class="kpi">
            <div class="value">{n_no_feedback}</div>
            <div class="label">Sem Feedback (silenciosos)</div>
            <div class="sub">{n_no_feedback/len(churn)*100:.0f}% — risco alto</div>
        </div>
    </div>

    <div class="chart-grid">
        <div class="chart-box">
            <h3>Todos os Feedbacks (Top 15)</h3>
            {"".join(f'<div class="feedback-item">"{k}" <span class="feedback-count">{v}x</span></div>' for k, v in feedback_all.items())}
        </div>
        <div class="chart-box">
            <h3>Feedbacks dos Perdidos Permanentes</h3>
            {"".join(f'<div class="feedback-item">"{k}" <span class="feedback-count">{v}x</span></div>' for k, v in perm_fb.items()) if perm_fb else '<p style="color:#888;padding:20px">Nenhum feedback dos perdidos permanentes</p>'}
        </div>
    </div>
</div>

<!-- ═══════════════ RAW TABLES ═══════════════ -->
<div id="tables" class="section">
    <h2 class="section-title">5 Tabelas — Amostras de 50 registros cada</h2>

    <p style="color:#888;margin:10px 0;">Todas as 5 tabelas do dataset, com 50 registros mais recentes. Total: {len(accounts)} accounts, {len(subs)} subscriptions, {len(usage)} usage events, {len(tickets)} tickets, {len(churn)} churn events.</p>

    <div class="chart-box" style="margin: 20px 0; overflow-x: auto; max-height: 500px; overflow-y: auto;">
        <h3>1. ACCOUNTS ({len(accounts)} registros) — com classificacao unificada</h3>
        <table>
            <tr><th>ID</th><th>Name</th><th>Industry</th><th>Country</th><th>Signup</th><th>Referral</th><th>Plan</th><th>Seats</th><th>Trial</th><th># Churns</th><th>Segmento</th></tr>
            {"".join(f"<tr><td>{r.account_id}</td><td>{r.account_name}</td><td>{r.industry}</td><td>{r.country}</td><td>{r.signup_date.strftime('%Y-%m-%d')}</td><td>{r.referral_source}</td><td>{r.plan_tier}</td><td>{r.seats}</td><td>{'Y' if r.is_trial else ''}</td><td>{r.num_churn_events}</td><td><span class='tag {'tag-green' if r.segment=='Nunca Churnou' else 'tag-yellow' if r.segment=='Porta Giratoria' else 'tag-red' if r.segment=='Perdido Permanente' else 'tag-orange'}'>{r.segment}</span></td></tr>" for _, r in sample_accounts.iterrows())}
        </table>
    </div>

    <div class="chart-box" style="margin: 20px 0; overflow-x: auto; max-height: 500px; overflow-y: auto;">
        <h3>2. SUBSCRIPTIONS ({len(subs)} registros)</h3>
        <table>
            <tr><th>Sub ID</th><th>Account</th><th>Start</th><th>End</th><th>Plan</th><th>Seats</th><th>MRR</th><th>ARR</th><th>Trial</th><th>Up</th><th>Down</th><th>Churn</th><th>Billing</th><th>AutoRenew</th></tr>
            {"".join(f"<tr><td>{r.subscription_id}</td><td>{r.account_id}</td><td>{r.start_date.strftime('%Y-%m-%d')}</td><td>{r.end_date.strftime('%Y-%m-%d') if pd.notna(r.end_date) else '<span class=tag tag-green>Ativa</span>'}</td><td>{r.plan_tier}</td><td>{r.seats}</td><td>${r.mrr_amount:,.0f}</td><td>${r.arr_amount:,.0f}</td><td>{'Y' if r.is_trial else ''}</td><td>{'Y' if r.upgrade_flag else ''}</td><td>{'Y' if r.downgrade_flag else ''}</td><td>{'<span class=tag tag-red>Y</span>' if r.churn_flag else ''}</td><td>{r.billing_frequency}</td><td>{'Y' if r.auto_renew_flag else ''}</td></tr>" for _, r in sample_subs.iterrows())}
        </table>
    </div>

    <div class="chart-box" style="margin: 20px 0; overflow-x: auto; max-height: 500px; overflow-y: auto;">
        <h3>3. FEATURE USAGE ({len(usage)} registros)</h3>
        <table>
            <tr><th>Usage ID</th><th>Sub ID</th><th>Date</th><th>Feature</th><th>Count</th><th>Duration (s)</th><th>Errors</th><th>Beta</th></tr>
            {"".join(f"<tr><td>{r.usage_id}</td><td>{r.subscription_id}</td><td>{r.usage_date.strftime('%Y-%m-%d')}</td><td>{r.feature_name}</td><td>{r.usage_count}</td><td>{r.usage_duration_secs:,.0f}</td><td>{r.error_count}</td><td>{'<span class=tag tag-blue>Beta</span>' if r.is_beta_feature else ''}</td></tr>" for _, r in sample_usage.iterrows())}
        </table>
    </div>

    <div class="chart-box" style="margin: 20px 0; overflow-x: auto; max-height: 500px; overflow-y: auto;">
        <h3>4. SUPPORT TICKETS ({len(tickets)} registros)</h3>
        <table>
            <tr><th>Ticket ID</th><th>Account</th><th>Submitted</th><th>Closed</th><th>Resolution (h)</th><th>Priority</th><th>1st Response (min)</th><th>Satisfaction</th><th>Escalated</th></tr>
            {"".join(f"<tr><td>{r.ticket_id}</td><td>{r.account_id}</td><td>{r.submitted_at.strftime('%Y-%m-%d %H:%M') if pd.notna(r.submitted_at) else ''}</td><td>{r.closed_at.strftime('%Y-%m-%d %H:%M') if pd.notna(r.closed_at) else ''}</td><td>{r.resolution_time_hours}</td><td>{r.priority}</td><td>{r.first_response_time_minutes:.0f}</td><td>{r.satisfaction_score if pd.notna(r.satisfaction_score) else '<span style=color:#888>null</span>'}</td><td>{'<span class=tag tag-red>Y</span>' if r.escalation_flag else ''}</td></tr>" for _, r in sample_tickets.iterrows())}
        </table>
    </div>

    <div class="chart-box" style="margin: 20px 0; overflow-x: auto; max-height: 500px; overflow-y: auto;">
        <h3>5. CHURN EVENTS ({len(churn)} registros)</h3>
        <table>
            <tr><th>Event ID</th><th>Account</th><th>Date</th><th>Reason</th><th>Refund $</th><th>Upgrade?</th><th>Downgrade?</th><th>Reactivation?</th><th>Feedback</th></tr>
            {"".join(f"<tr><td>{r.churn_event_id}</td><td>{r.account_id}</td><td>{r.churn_date.strftime('%Y-%m-%d')}</td><td>{r.reason_code}</td><td>${r.refund_amount_usd:.2f}</td><td>{'Y' if r.preceding_upgrade_flag else ''}</td><td>{'Y' if r.preceding_downgrade_flag else ''}</td><td>{'Y' if r.is_reactivation else ''}</td><td>{r.feedback_text if pd.notna(r.feedback_text) else ''}</td></tr>" for _, r in sample_churn.iterrows())}
        </table>
    </div>
</div>

</div><!-- container -->

<script>
const cfg = {{responsive: true, displayModeBar: false}};
const C = {{red:'#e94560',green:'#00d2a0',blue:'#4da6ff',yellow:'#ffd700',purple:'#b366ff',orange:'#ff8c42',pink:'#ff6b9d'}};
const L = {{
    paper_bgcolor:'rgba(0,0,0,0)', plot_bgcolor:'rgba(0,0,0,0)',
    font:{{color:'#ccc',size:12}}, margin:{{l:50,r:20,t:30,b:50}},
    xaxis:{{gridcolor:'#2a2a3e',zerolinecolor:'#333'}},
    yaxis:{{gridcolor:'#2a2a3e',zerolinecolor:'#333'}}
}};

function showSection(id) {{
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav button').forEach(b => b.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    event.target.classList.add('active');
    window.dispatchEvent(new Event('resize'));
}}

// ── OVERVIEW ──
Plotly.newPlot('chart_segments_pie', [{{
    labels: ['Nunca Churnou','Porta Giratoria','Perdido Permanente','Flag sem Evento'],
    values: [{n_never},{n_revolving},{n_lost},{n_flag_only}],
    type:'pie', hole:0.5,
    marker:{{colors:[C.green,C.yellow,C.red,C.orange]}},
    textinfo:'label+value+percent',
    texttemplate:'%{{label}}<br>%{{value}} (%{{percent}})'
}}], {{...L, showlegend:false}}, cfg);

// Reasons compare
let all_reasons = {json.dumps(sorted(churn_reasons.keys()))};
Plotly.newPlot('chart_reasons_compare', [
    {{x:all_reasons, y:all_reasons.map(r => ({json.dumps(perm_reasons)})[r]||0), type:'bar', name:'Perdido Permanente', marker:{{color:C.red}}}},
    {{x:all_reasons, y:all_reasons.map(r => ({json.dumps(revolv_reasons)})[r]||0), type:'bar', name:'Porta Giratoria', marker:{{color:C.yellow}}}}
], {{...L, barmode:'group'}}, cfg);

// Events distribution
let md = {json.dumps(multi_dist)};
Plotly.newPlot('chart_events_dist', [{{
    x: Object.keys(md), y: Object.values(md), type:'bar',
    marker:{{color: Object.keys(md).map(k => k==='0'?C.green:k==='1'?C.blue:k==='2'?C.yellow:C.red)}},
    text: Object.values(md), textposition:'outside'
}}], {{...L, xaxis:{{...L.xaxis,title:'Num. Eventos de Churn'}}, yaxis:{{...L.yaxis,title:'Contas'}}}}, cfg);

// ── SEGMENTS ──
function stackedBar(divId, data, xCol) {{
    let cats = data.map(d => d[xCol]);
    Plotly.newPlot(divId, [
        {{x:cats, y:data.map(d=>d.never), type:'bar', name:'Nunca', marker:{{color:C.green}}}},
        {{x:cats, y:data.map(d=>d.revolving), type:'bar', name:'Porta Giratoria', marker:{{color:C.yellow}}}},
        {{x:cats, y:data.map(d=>d.lost), type:'bar', name:'Perdido', marker:{{color:C.red}}}}
    ], {{...L, barmode:'stack'}}, cfg);
}}

stackedBar('chart_ind_stack', {json.dumps(by_industry.to_dict('records'))}, 'industry');
stackedBar('chart_plan_stack', {json.dumps(by_plan.to_dict('records'))}, 'plan_tier');
stackedBar('chart_ref_stack', {json.dumps(by_referral.to_dict('records'))}, 'referral_source');
stackedBar('chart_country_stack', {json.dumps(by_country.to_dict('records'))}, 'country');

// Heatmaps
Plotly.newPlot('chart_heatmap_perm', [{{
    z:{json.dumps(heatmap_perm)}, x:{json.dumps(industries_list)}, y:{json.dumps(plans_list)},
    type:'heatmap', colorscale:[[0,'#1a1a2e'],[0.5,'#e94560'],[1,'#ff2020']],
    text:{json.dumps(heatmap_perm)}, texttemplate:'%{{text:.1f}}%', showscale:true,
    colorbar:{{title:'%',ticksuffix:'%'}}
}}], {{...L, yaxis:{{...L.yaxis,autorange:'reversed'}}}}, cfg);

Plotly.newPlot('chart_heatmap_ever', [{{
    z:{json.dumps(heatmap_ever)}, x:{json.dumps(industries_list)}, y:{json.dumps(plans_list)},
    type:'heatmap', colorscale:[[0,'#1a1a2e'],[0.5,'#ffd700'],[1,'#ff8c42']],
    text:{json.dumps(heatmap_ever)}, texttemplate:'%{{text:.1f}}%', showscale:true,
    colorbar:{{title:'%',ticksuffix:'%'}}
}}], {{...L, yaxis:{{...L.yaxis,autorange:'reversed'}}}}, cfg);

// ── REVENUE ──
Plotly.newPlot('chart_rev_plan', [{{
    labels:{json.dumps(list(rev_by_plan.keys()))}, values:{json.dumps(list(rev_by_plan.values()))},
    type:'pie', hole:0.5, marker:{{colors:[C.blue,C.yellow,C.red]}},
    textinfo:'label+value+percent', texttemplate:'%{{label}}<br>${{value:,.0f}}<br>(%{{percent}})'
}}], {{...L, showlegend:false}}, cfg);

Plotly.newPlot('chart_rev_industry', [{{
    labels:{json.dumps(list(rev_by_industry.keys()))}, values:{json.dumps(list(rev_by_industry.values()))},
    type:'pie', hole:0.5, marker:{{colors:[C.red,C.blue,C.green,C.yellow,C.purple]}},
    textinfo:'label+value+percent', texttemplate:'%{{label}}<br>${{value:,.0f}}<br>(%{{percent}})'
}}], {{...L, showlegend:false}}, cfg);

Plotly.newPlot('chart_mrr_dist', [
    {{x:{json.dumps(mrr_lost_list)}, type:'histogram', name:'Perdido Permanente', marker:{{color:'rgba(233,69,96,0.6)'}}, nbinsx:25}},
    {{x:{json.dumps(mrr_active_list)}, type:'histogram', name:'Ativos', marker:{{color:'rgba(0,210,160,0.4)'}}, nbinsx:25}}
], {{...L, barmode:'overlay', xaxis:{{...L.xaxis,title:'MRR ($)'}}}}, cfg);

Plotly.newPlot('chart_refund', [{{
    x:{json.dumps(refund_stats.index.tolist())}, y:{json.dumps(refund_stats['sum'].tolist())},
    type:'bar', marker:{{color:[C.red,C.orange,C.yellow,C.blue,C.purple,C.green]}},
    text:{json.dumps([f"${v:,.0f}" for v in refund_stats['sum'].tolist()])}, textposition:'outside'
}}], {{...L, yaxis:{{...L.yaxis,title:'Total Refunds ($)'}}}}, cfg);

// ── USAGE ──
function hbar(divId, data, color) {{
    Plotly.newPlot(divId, [{{
        y:Object.keys(data), x:Object.values(data), type:'bar', orientation:'h', marker:{{color:color}}
    }}], {{...L, margin:{{...L.margin,l:100}}, yaxis:{{...L.yaxis,autorange:'reversed'}}}}, cfg);
}}
hbar('chart_feat_never', {json.dumps(top_feat.get('Nunca Churnou', {}))}, C.green);
hbar('chart_feat_lost', {json.dumps(top_feat.get('Perdido Permanente', {}))}, C.red);

Plotly.newPlot('chart_errors_lost', [{{
    y:{json.dumps(err_by_feat.index.tolist())}, x:{json.dumps(err_by_feat['total_errors'].tolist())},
    type:'bar', orientation:'h', marker:{{color:C.orange}}, name:'Total Erros'
}}], {{...L, margin:{{...L.margin,l:100}}, yaxis:{{...L.yaxis,autorange:'reversed'}}}}, cfg);

// ── SUPPORT ──
Plotly.newPlot('chart_sat_dist', [{{
    x:{json.dumps(list(sat_scores.keys()))}, y:{json.dumps(list(sat_scores.values()))},
    type:'bar', marker:{{color:[C.red,C.yellow,C.green]}},
    text:{json.dumps(list(sat_scores.values()))}, textposition:'outside'
}}], {{...L, xaxis:{{...L.xaxis,title:'Score'}}, yaxis:{{...L.yaxis,title:'Tickets'}}}}, cfg);

// ── TIMELINE ──
let months = {json.dumps(all_months)};
let perm_vals = months.map(m => ({json.dumps(perm_tl)})[m]||0);
let revolv_vals = months.map(m => ({json.dumps(revolv_tl)})[m]||0);
Plotly.newPlot('chart_timeline', [
    {{x:months, y:perm_vals, type:'bar', name:'Perdido Permanente', marker:{{color:C.red}}}},
    {{x:months, y:revolv_vals, type:'bar', name:'Porta Giratoria', marker:{{color:C.yellow}}}}
], {{...L, barmode:'stack', xaxis:{{...L.xaxis,title:'Mes'}}}}, cfg);

Plotly.newPlot('chart_cohort', [
    {{x:{json.dumps(cohort['signup_month'].tolist())}, y:{json.dumps(cohort['perm_rate'].tolist())},
      type:'bar', name:'Churn Permanente %', marker:{{color:C.red}}}},
    {{x:{json.dumps(cohort['signup_month'].tolist())}, y:{json.dumps(cohort['ever_rate'].tolist())},
      type:'scatter', mode:'lines+markers', name:'Ja Churnou %', line:{{color:C.yellow,width:2}}}},
    {{x:{json.dumps(cohort['signup_month'].tolist())}, y:{json.dumps(cohort['total'].tolist())},
      type:'scatter', mode:'lines+markers', name:'Contas no Cohort', yaxis:'y2', line:{{color:C.blue,width:2,dash:'dot'}}}}
], {{...L,
    yaxis:{{...L.yaxis,title:'%'}},
    yaxis2:{{overlaying:'y',side:'right',title:'Contas',gridcolor:'transparent'}}
}}, cfg);

Plotly.newPlot('chart_days_churn', [{{
    x:{json.dumps(list(bucket_counts.keys()))}, y:{json.dumps(list(bucket_counts.values()))},
    type:'bar', marker:{{color:C.purple}},
    text:{json.dumps(list(bucket_counts.values()))}, textposition:'outside'
}}], {{...L}}, cfg);

// ── MULTI-CHURN ──
Plotly.newPlot('chart_multi_dist', [{{
    x:['1 churn','2 churns','3 churns','4 churns','5 churns'],
    y:[{json.dumps(multi_dist.get('1',0))},{json.dumps(multi_dist.get('2',0))},{json.dumps(multi_dist.get('3',0))},{json.dumps(multi_dist.get('4',0))},{json.dumps(multi_dist.get('5',0))}],
    type:'bar', marker:{{color:[C.blue,C.yellow,C.orange,C.red,C.red]}},
    text:[{json.dumps(multi_dist.get('1',0))},{json.dumps(multi_dist.get('2',0))},{json.dumps(multi_dist.get('3',0))},{json.dumps(multi_dist.get('4',0))},{json.dumps(multi_dist.get('5',0))}],
    textposition:'outside'
}}], {{...L}}, cfg);

Plotly.newPlot('chart_upgrade_seg', [{{
    x:['Perdido Permanente','Porta Giratoria'],
    y:[{up_perm},{up_revolv}],
    type:'bar', marker:{{color:[C.red,C.yellow]}},
    text:['{up_perm} ({up_perm/len(perm_churn)*100:.0f}% dos eventos)','{up_revolv} ({up_revolv/len(revolving_churn)*100:.0f}% dos eventos)'],
    textposition:'outside'
}}], {{...L, yaxis:{{...L.yaxis,title:'Eventos com Upgrade Recente'}}}}, cfg);

// ── MATRIX CHARTS ──
let segs3 = ['Nunca Churnou','Porta Giratoria','Perdido Permanente'];
let healthLists = {health_lists_json};
let healthData = segs3.map((seg,i) => ({{
    y:healthLists[seg], type:'box', name:seg, marker:{{color:[C.green,C.yellow,C.red][i]}}
}}));
Plotly.newPlot('chart_health_box', healthData, {{...L, showlegend:false}}, cfg);

let hzData = {hz_dict_json};
let zones = ['Critical','Warning','Good','Excellent'];
let zoneColors = [C.red, C.orange, C.yellow, C.green];
let hzTraces = zones.map((z,i) => ({{
    x: segs3, y: segs3.map(s => hzData[z][s]||0),
    type:'bar', name:z, marker:{{color:zoneColors[i]}}
}}));
Plotly.newPlot('chart_health_zones', hzTraces, {{...L, barmode:'stack'}}, cfg);

Plotly.newPlot('chart_vr_counts', [{{
    z: {json.dumps(vr_counts)}, x: {json.dumps(vr_risk_labels)}, y: {json.dumps(vr_labels)},
    type:'heatmap', colorscale:[[0,'#1a1a2e'],[1,'#4da6ff']],
    text: {json.dumps(vr_counts)}, texttemplate:'%{{text}}', showscale:true,
    colorbar:{{title:'Contas'}}
}}], {{...L, yaxis:{{...L.yaxis,autorange:'reversed'}}}}, cfg);

Plotly.newPlot('chart_vr_lost', [{{
    z: {json.dumps(vr_lost)}, x: {json.dumps(vr_risk_labels)}, y: {json.dumps(vr_labels)},
    type:'heatmap', colorscale:[[0,'#1a1a2e'],[0.5,'#e94560'],[1,'#ff2020']],
    text: {json.dumps(vr_lost)}, texttemplate:'%{{text}} perdidos', showscale:true,
    colorbar:{{title:'Perdidos'}}
}}], {{...L, yaxis:{{...L.yaxis,autorange:'reversed'}}}}, cfg);

let scatterData = {scatter_json};
let scatterTraces = segs3.map((seg,i) => {{
    let pts = scatterData[seg];
    return {{
        x: pts.map(p=>p.health_score), y: pts.map(p=>p.mrr_amount),
        text: pts.map(p=>p.account_id+' (events:'+p.total_events+')'),
        mode:'markers', type:'scatter', name:seg,
        marker:{{color:[C.green,C.yellow,C.red][i], size:6, opacity:0.6}}
    }};
}});
Plotly.newPlot('chart_health_scatter', scatterTraces, {{...L,
    xaxis:{{...L.xaxis,title:'Health Score'}},
    yaxis:{{...L.yaxis,title:'MRR ($)'}}
}}, cfg);

// ── STRATEGY CHARTS ──
Plotly.newPlot('chart_billing_mrr', [
    {{x:['Mensal','Anual'], y:[{billing_stats['monthly']['mrr_lost']},{billing_stats['annual']['mrr_lost']}],
      type:'bar', name:'MRR Perdido', marker:{{color:[C.red,C.orange]}},
      text:['${billing_stats["monthly"]["mrr_lost"]:,.0f} ({billing_stats["monthly"]["mrr_lost_pct"]}% do MRR)','${billing_stats["annual"]["mrr_lost"]:,.0f} ({billing_stats["annual"]["mrr_lost_pct"]}% do MRR)'],
      textposition:'outside'}},
    {{x:['Mensal','Anual'], y:[{billing_stats['monthly']['n_lost']},{billing_stats['annual']['n_lost']}],
      type:'bar', name:'Contas Perdidas', marker:{{color:['rgba(233,69,96,0.3)','rgba(255,140,66,0.3)']}},
      yaxis:'y2',
      text:['{billing_stats["monthly"]["n_lost"]} contas ({billing_stats["monthly"]["rate"]}%)','{billing_stats["annual"]["n_lost"]} contas ({billing_stats["annual"]["rate"]}%)'],
      textposition:'outside'}}
], {{...L, yaxis:{{...L.yaxis,title:'MRR Perdido ($)'}}, yaxis2:{{overlaying:'y',side:'right',title:'Contas',gridcolor:'transparent'}}}}, cfg);

Plotly.newPlot('chart_seats_analysis', [
    {{x:{json.dumps([s['bucket'] for s in seats_stats])},
      y:{json.dumps([s['mrr_lost'] for s in seats_stats])},
      type:'bar', name:'MRR Perdido', marker:{{color:C.red}},
      text:{json.dumps([f"${s['mrr_lost']:,.0f} ({s['mrr_lost_pct']}%)" for s in seats_stats])},
      textposition:'outside'}},
    {{x:{json.dumps([s['bucket'] for s in seats_stats])},
      y:{json.dumps([s['n'] for s in seats_stats])},
      type:'scatter', mode:'lines+markers', name:'Total Contas', yaxis:'y2',
      line:{{color:C.blue,width:2}}}}
], {{...L, yaxis:{{...L.yaxis,title:'MRR Perdido ($)'}}, yaxis2:{{overlaying:'y',side:'right',title:'Contas',gridcolor:'transparent'}}}}, cfg);

Plotly.newPlot('chart_strategy_impact', [
    {{x:['Enterprise Save\\n(CSM dedicado)','Desconto Anual\\n(15% lock-in)','DevTools Fix\\n(PMF audit)','Porta Giratoria\\n(90-Day Success)','Events Channel\\n(qualificacao)'],
      y:[{top5_ent_mrr*12},67700,274000,{round(rev_by_segment.get('Porta Giratoria', {}).get('mrr_total', 0)*0.20*12, 0)},0],
      type:'bar', name:'Receita Recuperada/Protegida (ano)', marker:{{color:[C.green,'#00d2a0','#4da6ff',C.yellow,C.orange]}},
      text:['${top5_ent_mrr*12:,.0f}','$67,700','$274,000','${rev_by_segment.get("Porta Giratoria", {}).get("mrr_total", 0)*0.20*12:,.0f}','Qualitativo'],
      textposition:'outside'}}
], {{...L, yaxis:{{...L.yaxis,title:'Impacto Anual ($)'}}, margin:{{l:60,r:20,t:30,b:100}}}}, cfg);

// ── CEO QUESTION CHARTS ──
let ceoMonths = {json.dumps(usage_months)};

// Total usage (what Product shows)
Plotly.newPlot('chart_ceo_total', [
    {{x:ceoMonths, y:{json.dumps(usage_by_month['total_usage'].tolist())},
      type:'scatter', mode:'lines+markers', name:'Uso Total',
      line:{{color:C.blue,width:3}}, marker:{{size:6}}}},
    {{x:ceoMonths, y:{json.dumps(usage_by_month['events'].tolist())},
      type:'bar', name:'Eventos', marker:{{color:'rgba(77,166,255,0.2)'}}, yaxis:'y2'}}
], {{...L,
    yaxis:{{...L.yaxis,title:'Uso Total (sum)'}},
    yaxis2:{{overlaying:'y',side:'right',title:'Eventos',gridcolor:'transparent'}},
    shapes:[{{type:'line',x0:ceoMonths[0],x1:ceoMonths[ceoMonths.length-1],
              y0:{usage_by_month['total_usage'].mean():.0f},y1:{usage_by_month['total_usage'].mean():.0f},
              line:{{color:C.red,width:2,dash:'dash'}}}},],
    annotations:[{{x:ceoMonths[ceoMonths.length-1],y:{usage_by_month['total_usage'].mean():.0f},
                   text:'Media: {usage_by_month["total_usage"].mean():,.0f}',showarrow:false,
                   font:{{color:C.red,size:12}},xanchor:'right',yshift:15}}]
}}, cfg);

// Per-account average (the real metric)
Plotly.newPlot('chart_ceo_per_acct', [
    {{x:ceoMonths, y:{json.dumps(per_acct_avg['avg_usage'].tolist())},
      type:'scatter', mode:'lines+markers', name:'Uso Medio/Conta',
      line:{{color:C.green,width:3}}, marker:{{size:6}}}},
    {{x:ceoMonths, y:{json.dumps(per_acct_avg['n_accounts'].astype(int).tolist())},
      type:'bar', name:'Contas Ativas', marker:{{color:'rgba(0,210,160,0.15)'}}, yaxis:'y2'}}
], {{...L,
    yaxis:{{...L.yaxis,title:'Uso Medio por Conta'}},
    yaxis2:{{overlaying:'y',side:'right',title:'Contas Ativas',gridcolor:'transparent'}},
    shapes:[{{type:'line',x0:ceoMonths[0],x1:ceoMonths[ceoMonths.length-1],
              y0:{per_acct_avg['avg_usage'].mean():.1f},y1:{per_acct_avg['avg_usage'].mean():.1f},
              line:{{color:C.red,width:2,dash:'dash'}}}}],
    annotations:[{{x:ceoMonths[ceoMonths.length-1],y:{per_acct_avg['avg_usage'].mean():.1f},
                   text:'Media: {per_acct_avg["avg_usage"].mean():.1f}',showarrow:false,
                   font:{{color:C.red,size:12}},xanchor:'right',yshift:15}}]
}}, cfg);

// Usage by segment
Plotly.newPlot('chart_ceo_by_seg', [
    {{x:ceoMonths, y:{json.dumps(seg_usage_monthly['Nunca Churnou'])},
      type:'scatter', mode:'lines', name:'Nunca Churnou', line:{{color:C.green,width:2}}, stackgroup:'one'}},
    {{x:ceoMonths, y:{json.dumps(seg_usage_monthly['Porta Giratoria'])},
      type:'scatter', mode:'lines', name:'Porta Giratoria', line:{{color:C.yellow,width:2}}, stackgroup:'one'}},
    {{x:ceoMonths, y:{json.dumps(seg_usage_monthly['Perdido Permanente'])},
      type:'scatter', mode:'lines', name:'Perdido Permanente', line:{{color:C.red,width:2}}, stackgroup:'one'}}
], {{...L, yaxis:{{...L.yaxis,title:'Uso Total'}}}}, cfg);

// Active accounts vs new signups
Plotly.newPlot('chart_ceo_accounts', [
    {{x:ceoMonths, y:{json.dumps(usage_by_month['unique_accounts'].tolist())},
      type:'scatter', mode:'lines+markers', name:'Contas Ativas/Mes',
      line:{{color:C.blue,width:3}}}},
    {{x:ceoMonths, y:{json.dumps(new_signups)},
      type:'bar', name:'Novos Signups', marker:{{color:'rgba(0,210,160,0.4)'}}}}
], {{...L,
    yaxis:{{...L.yaxis,title:'Contas'}},
    annotations:[{{x:ceoMonths[Math.floor(ceoMonths.length/2)],y:450,
                   text:'~20 signups/mes, mas base ativa nao cresce (churn anula)',
                   showarrow:false,font:{{color:C.yellow,size:13}}}}]
}}, cfg);

</script>
</body>
</html>"""

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\nDashboard v2 gerado: {OUTPUT}")
print(f"Tamanho: {os.path.getsize(OUTPUT)/1024:.0f} KB")
