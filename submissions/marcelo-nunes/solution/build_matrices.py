"""
Build account-level matrices and scoring for churn analysis.
Generates master_account_metrics.csv for use in the dashboard.
"""
import pandas as pd
import numpy as np
import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'challenges', 'data-001-churn', 'data')

# Load
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
churn['churn_date'] = pd.to_datetime(churn['churn_date'])

# Classify
events_per = churn.groupby('account_id').size()
ever_churned_ids = set(churn['account_id'])
accounts['segment'] = 'Nunca Churnou'
accounts.loc[accounts['account_id'].isin(ever_churned_ids) & ~accounts['churn_flag'], 'segment'] = 'Porta Giratoria'
accounts.loc[accounts['account_id'].isin(ever_churned_ids) & accounts['churn_flag'], 'segment'] = 'Perdido Permanente'
accounts.loc[~accounts['account_id'].isin(ever_churned_ids) & accounts['churn_flag'], 'segment'] = 'Flag sem Evento'
accounts['num_churn_events'] = accounts['account_id'].map(events_per).fillna(0).astype(int)

ref_date = pd.Timestamp('2025-01-01')

# Usage per account
usage_full = usage.merge(subs[['subscription_id', 'account_id']], on='subscription_id')
acct_usage = usage_full.groupby('account_id').agg(
    last_usage=('usage_date', 'max'),
    first_usage=('usage_date', 'min'),
    total_events=('usage_id', 'count'),
    total_usage_count=('usage_count', 'sum'),
    total_duration=('usage_duration_secs', 'sum'),
    unique_features=('feature_name', 'nunique'),
    total_errors=('error_count', 'sum'),
    beta_usage=('is_beta_feature', 'sum'),
).reset_index()
acct_usage['recency_days'] = (ref_date - acct_usage['last_usage']).dt.days
acct_usage['usage_span_days'] = (acct_usage['last_usage'] - acct_usage['first_usage']).dt.days

# Support per account
acct_tickets = tickets.groupby('account_id').agg(
    total_tickets=('ticket_id', 'count'),
    avg_resolution=('resolution_time_hours', 'mean'),
    avg_first_response=('first_response_time_minutes', 'mean'),
    avg_satisfaction=('satisfaction_score', 'mean'),
    null_satisfaction=('satisfaction_score', lambda x: x.isna().sum()),
    escalations=('escalation_flag', 'sum'),
    high_urgent=('priority', lambda x: ((x == 'high') | (x == 'urgent')).sum()),
).reset_index()

# Revenue profile (last subscription)
last_sub = subs.sort_values('start_date').groupby('account_id').last().reset_index()
acct_revenue = last_sub[['account_id', 'mrr_amount', 'arr_amount', 'plan_tier', 'seats',
                          'billing_frequency', 'auto_renew_flag', 'is_trial',
                          'upgrade_flag', 'downgrade_flag']].copy()

sub_counts = subs.groupby('account_id').agg(
    total_subs=('subscription_id', 'count'),
    upgrades=('upgrade_flag', 'sum'),
    downgrades=('downgrade_flag', 'sum'),
).reset_index()

# Master table
master = accounts[['account_id', 'account_name', 'industry', 'country', 'signup_date',
                    'referral_source', 'segment', 'num_churn_events']].copy()
master['account_age_days'] = (ref_date - master['signup_date']).dt.days
master = master.merge(acct_usage, on='account_id', how='left')
master = master.merge(acct_tickets, on='account_id', how='left')
master = master.merge(acct_revenue, on='account_id', how='left')
master = master.merge(sub_counts, on='account_id', how='left')

for col in ['total_tickets', 'escalations', 'total_events', 'high_urgent']:
    master[col] = master[col].fillna(0)

# Only score accounts with usage data
valid = master[master['total_events'] > 0].copy()

# ── RFD Score (SaaS RFM) ──
def score_q(series, ascending=True):
    labels = [1,2,3,4,5] if ascending else [5,4,3,2,1]
    return pd.qcut(series.rank(method='first'), 5, labels=labels).astype(int)

valid['R_score'] = score_q(valid['recency_days'], ascending=False)
valid['F_score'] = score_q(valid['total_events'], ascending=True)
valid['D_score'] = score_q(valid['unique_features'], ascending=True)
valid['RFD_total'] = valid['R_score'] + valid['F_score'] + valid['D_score']
valid['RFD_label'] = pd.cut(valid['RFD_total'], bins=[0,6,9,12,15], labels=['At Risk','Cooling','Healthy','Champion'])

# ── Health Score (0-100) ──
def norm(s):
    mn, mx = s.min(), s.max()
    return ((s - mn) / (mx - mn) * 100).round(1) if mx > mn else pd.Series(50.0, index=s.index)

valid['h_usage'] = norm(valid['total_usage_count'])
valid['h_features'] = norm(valid['unique_features'])
valid['h_recency'] = norm(valid['recency_days'].max() - valid['recency_days'])
valid['h_errors'] = norm(valid['total_errors'].max() - valid['total_errors'])
valid['h_tickets'] = norm(valid['total_tickets'].max() - valid['total_tickets'])

valid['health_score'] = (
    valid['h_usage'] * 0.25 +
    valid['h_features'] * 0.20 +
    valid['h_recency'] * 0.25 +
    valid['h_errors'] * 0.15 +
    valid['h_tickets'] * 0.15
).round(1)

valid['health_zone'] = pd.cut(valid['health_score'], bins=[-1,30,50,70,100],
                               labels=['Critical','Warning','Good','Excellent'])

# ── Value x Risk Matrix ──
valid['value_tier'] = pd.qcut(valid['mrr_amount'].rank(method='first'), 3,
                               labels=['Low Value','Mid Value','High Value'])
valid['risk_tier'] = pd.cut(valid['health_score'], bins=[-1,40,65,100],
                             labels=['High Risk','Medium Risk','Low Risk'])

# ── Engagement Matrix ──
valid['freq_tier'] = pd.qcut(valid['total_events'].rank(method='first'), 3,
                              labels=['Low Freq','Mid Freq','High Freq'])
valid['breadth_tier'] = pd.qcut(valid['unique_features'].rank(method='first'), 3,
                                 labels=['Narrow','Medium','Broad'])

# ── Print summaries ──
print("="*70)
print("RFD DISTRIBUTION BY SEGMENT")
print("="*70)
print(valid.groupby(['segment', 'RFD_label']).size().unstack(fill_value=0))

print("\n" + "="*70)
print("HEALTH SCORE BY SEGMENT")
print("="*70)
print(valid.groupby('segment')['health_score'].describe().round(1))

print("\n" + "="*70)
print("HEALTH ZONES BY SEGMENT")
print("="*70)
print(valid.groupby(['segment', 'health_zone']).size().unstack(fill_value=0))

print("\n" + "="*70)
print("VALUE x RISK MATRIX")
print("="*70)
vr = valid.groupby(['value_tier', 'risk_tier']).agg(
    count=('account_id', 'count'),
    total_mrr=('mrr_amount', 'sum'),
    perm_lost=('segment', lambda x: (x == 'Perdido Permanente').sum()),
).reset_index()
for _, r in vr.iterrows():
    print(f"  {r['value_tier']:>12} x {r['risk_tier']:>12}: {r['count']:>3} accts, MRR=${r['total_mrr']:>10,.0f}, {r['perm_lost']} lost")

print("\n" + "="*70)
print("ENGAGEMENT DEPTH MATRIX")
print("="*70)
ed = valid.groupby(['freq_tier', 'breadth_tier']).agg(
    count=('account_id', 'count'),
    perm_lost=('segment', lambda x: (x == 'Perdido Permanente').sum()),
    revolving=('segment', lambda x: (x == 'Porta Giratoria').sum()),
    avg_health=('health_score', 'mean'),
).round(1).reset_index()
for _, r in ed.iterrows():
    print(f"  {r['freq_tier']:>10} x {r['breadth_tier']:>8}: {r['count']:>3} accts, {r['perm_lost']} lost, {r['revolving']} revolving, health={r['avg_health']}")

# ── SUPPORT BURDEN ──
print("\n" + "="*70)
print("SUPPORT BURDEN BY SEGMENT")
print("="*70)
valid['support_per_dollar'] = (valid['total_tickets'] / valid['mrr_amount'].replace(0, np.nan)).round(4)
for seg in ['Nunca Churnou', 'Porta Giratoria', 'Perdido Permanente']:
    sub = valid[valid['segment'] == seg]
    t_total = sub['total_tickets'].sum()
    print(f"\n[{seg}] ({len(sub)} contas)")
    print(f"  Tickets/conta: {sub['total_tickets'].mean():.1f}")
    if t_total > 0:
        print(f"  High/Urgent %: {sub['high_urgent'].sum() / t_total * 100:.1f}%")
    print(f"  Escalation total: {sub['escalations'].sum():.0f}")
    print(f"  Avg Health: {sub['health_score'].mean():.1f}")

# Save
out_path = os.path.join(os.path.dirname(__file__), 'master_account_metrics.csv')
valid.to_csv(out_path, index=False)
print(f"\nSaved: {out_path} ({len(valid)} rows)")

# Also save summary JSONs for dashboard
summaries = {
    'rfd_by_seg': valid.groupby(['segment', 'RFD_label']).size().unstack(fill_value=0).to_dict(),
    'health_by_seg': valid.groupby('segment')['health_score'].describe().round(1).to_dict(),
    'health_zones': valid.groupby(['segment', 'health_zone']).size().unstack(fill_value=0).to_dict(),
    'value_risk': vr.to_dict('records'),
    'engagement': ed.to_dict('records'),
}
json_path = os.path.join(os.path.dirname(__file__), 'matrix_summaries.json')
with open(json_path, 'w') as f:
    json.dump(summaries, f, indent=2, default=str)
print(f"Saved: {json_path}")
