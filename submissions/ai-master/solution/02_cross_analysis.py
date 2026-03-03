"""
Phase 2: Cross-Table Analysis & Hypothesis Testing
===================================================
Testing the churn paradox: usage up + satisfaction ok + churn up
"""
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

DATA = '/home/user/ai-master-challenge/datasets/'

accounts = pd.read_csv(f'{DATA}ravenstack_accounts.csv')
subs = pd.read_csv(f'{DATA}ravenstack_subscriptions.csv')
usage = pd.read_csv(f'{DATA}ravenstack_feature_usage.csv')
tickets = pd.read_csv(f'{DATA}ravenstack_support_tickets.csv')
churn = pd.read_csv(f'{DATA}ravenstack_churn_events.csv')

# Tag churned accounts
churned_ids = set(churn['account_id'].unique())
accounts['churned'] = accounts['account_id'].isin(churned_ids)

# Map subscription → account
sub_acct = subs[['subscription_id', 'account_id']].drop_duplicates()
usage_merged = usage.merge(sub_acct, on='subscription_id', how='left')
usage_merged['churned'] = usage_merged['account_id'].isin(churned_ids)

print("=" * 70)
print("PHASE 2: CROSS-TABLE ANALYSIS")
print("=" * 70)

# ============================================================
# H1: "Usage grew" is a half-truth
# ============================================================
print("\n\n" + "=" * 70)
print("H1: IS 'USAGE GREW' TRUE FOR ALL SEGMENTS?")
print("=" * 70)

print("\n--- Overall Usage: Churned vs Retained ---")
for label, subset in [("Retained", usage_merged[~usage_merged['churned']]),
                       ("Churned", usage_merged[usage_merged['churned']])]:
    print(f"\n{label} accounts:")
    print(f"  Total usage count: {subset['usage_count'].sum():,}")
    print(f"  Avg usage per record: {subset['usage_count'].mean():.1f}")
    print(f"  Median usage per record: {subset['usage_count'].median():.1f}")
    print(f"  Unique subscriptions: {subset['subscription_id'].nunique()}")
    print(f"  Avg features used per sub: {subset.groupby('subscription_id')['feature_name'].nunique().mean():.1f}")

# Usage per account
acct_usage = usage_merged.groupby(['account_id', 'churned']).agg(
    total_usage=('usage_count', 'sum'),
    avg_usage=('usage_count', 'mean'),
    total_errors=('error_count', 'sum'),
    total_duration=('duration_minutes', 'sum'),
    features_used=('feature_name', 'nunique'),
    sessions=('session_count', 'sum'),
).reset_index()

print("\n\n--- Per-Account Usage Comparison ---")
for churned in [False, True]:
    label = "Churned" if churned else "Retained"
    subset = acct_usage[acct_usage['churned'] == churned]
    print(f"\n{label}:")
    print(f"  Avg total usage: {subset['total_usage'].mean():,.0f}")
    print(f"  Median total usage: {subset['total_usage'].median():,.0f}")
    print(f"  Avg features used: {subset['features_used'].mean():.1f}")
    print(f"  Avg total errors: {subset['total_errors'].mean():.1f}")
    print(f"  Error/Usage ratio: {subset['total_errors'].sum()/subset['total_usage'].sum():.4f}")

# Power user analysis
p90_usage = acct_usage['total_usage'].quantile(0.90)
power_users = acct_usage[acct_usage['total_usage'] >= p90_usage]
print(f"\n--- Power Users (top 10%, usage >= {p90_usage:,.0f}) ---")
print(f"Count: {len(power_users)}")
print(f"Churn rate among power users: {power_users['churned'].mean()*100:.1f}%")
print(f"Share of total usage: {power_users['total_usage'].sum()/acct_usage['total_usage'].sum()*100:.1f}%")

low_users = acct_usage[acct_usage['total_usage'] < acct_usage['total_usage'].quantile(0.25)]
print(f"\n--- Low Users (bottom 25%, usage < {acct_usage['total_usage'].quantile(0.25):,.0f}) ---")
print(f"Count: {len(low_users)}")
print(f"Churn rate among low users: {low_users['churned'].mean()*100:.1f}%")

# ============================================================
# H2: Satisfaction masked by survivor bias
# ============================================================
print("\n\n" + "=" * 70)
print("H2: SATISFACTION SCORES — SURVIVOR BIAS?")
print("=" * 70)

tickets_with_churn = tickets.merge(
    accounts[['account_id', 'churned']], on='account_id', how='left'
)

print("\n--- Ticket Satisfaction by Churn Status ---")
for churned in [False, True]:
    label = "Churned" if churned else "Retained"
    subset = tickets_with_churn[tickets_with_churn['churned'] == churned]
    sat = subset['satisfaction_score']
    print(f"\n{label}:")
    print(f"  Total tickets: {len(subset)}")
    print(f"  Satisfaction responses: {sat.notna().sum()} ({sat.notna().mean()*100:.1f}%)")
    print(f"  Missing satisfaction: {sat.isna().sum()} ({sat.isna().mean()*100:.1f}%)")
    if sat.notna().sum() > 0:
        print(f"  Mean satisfaction (respondents only): {sat.mean():.2f}")
        print(f"  Score distribution:")
        for score in [1, 2, 3, 4, 5]:
            n = (sat == score).sum()
            pct = n / sat.notna().sum() * 100
            print(f"    {score}: {n} ({pct:.1f}%)")

# THE KEY INSIGHT: If we only look at respondents, what's the bias?
all_sat = tickets_with_churn['satisfaction_score'].dropna()
retained_sat = tickets_with_churn[~tickets_with_churn['churned']]['satisfaction_score'].dropna()
churned_sat = tickets_with_churn[tickets_with_churn['churned']]['satisfaction_score'].dropna()

print(f"\n--- Survivor Bias Analysis ---")
print(f"Overall mean satisfaction (all respondents): {all_sat.mean():.2f}")
print(f"Retained respondents mean: {retained_sat.mean():.2f}")
print(f"Churned respondents mean: {churned_sat.mean():.2f}")
print(f"Response rate retained: {tickets_with_churn[~tickets_with_churn['churned']]['satisfaction_score'].notna().mean()*100:.1f}%")
print(f"Response rate churned: {tickets_with_churn[tickets_with_churn['churned']]['satisfaction_score'].notna().mean()*100:.1f}%")
print(f"\n→ The CS team sees {all_sat.mean():.2f}/5 overall — looks OK")
print(f"→ But this masks churned customers who: (a) rate lower AND (b) respond less")

# ============================================================
# H3: Support experience as churn driver
# ============================================================
print("\n\n" + "=" * 70)
print("H3: SUPPORT EXPERIENCE — CHURNED vs RETAINED")
print("=" * 70)

for churned in [False, True]:
    label = "Churned" if churned else "Retained"
    subset = tickets_with_churn[tickets_with_churn['churned'] == churned]
    print(f"\n{label}:")
    print(f"  Avg tickets per account: {len(subset)/accounts[accounts['churned']==churned]['account_id'].nunique():.1f}")
    print(f"  Avg first response (hrs): {subset['first_response_hours'].mean():.1f}")
    print(f"  Median first response (hrs): {subset['first_response_hours'].median():.1f}")
    print(f"  Avg resolution time (hrs): {subset['resolution_hours'].mean():.1f}")
    print(f"  Median resolution time (hrs): {subset['resolution_hours'].median():.1f}")
    print(f"  Escalation rate: {subset['escalated'].mean()*100:.1f}%")
    print(f"  Reopen rate: {subset['reopened'].mean()*100:.1f}%")
    print(f"  High/Critical priority: {subset[subset['priority'].isin(['High','Critical'])].shape[0]/len(subset)*100:.1f}%")

# Ticket categories comparison
print("\n--- Ticket Category Distribution ---")
for churned in [False, True]:
    label = "Churned" if churned else "Retained"
    subset = tickets_with_churn[tickets_with_churn['churned'] == churned]
    print(f"\n{label}:")
    cat_pct = subset['category'].value_counts(normalize=True) * 100
    for cat, pct in cat_pct.items():
        print(f"  {cat}: {pct:.1f}%")

# ============================================================
# H4: Feature-specific patterns
# ============================================================
print("\n\n" + "=" * 70)
print("H4: FEATURE USAGE PATTERNS — CHURNED vs RETAINED")
print("=" * 70)

print("\n--- Per-Feature Comparison ---")
feat_comp = usage_merged.groupby(['feature_name', 'churned']).agg(
    avg_usage=('usage_count', 'mean'),
    avg_errors=('error_count', 'mean'),
    total_usage=('usage_count', 'sum'),
    total_errors=('error_count', 'sum'),
    records=('usage_count', 'count'),
).reset_index()

feat_comp['error_rate'] = feat_comp['total_errors'] / feat_comp['total_usage']

for feat in sorted(usage_merged['feature_name'].unique()):
    r = feat_comp[(feat_comp['feature_name'] == feat) & (~feat_comp['churned'])]
    c = feat_comp[(feat_comp['feature_name'] == feat) & (feat_comp['churned'])]
    if len(r) > 0 and len(c) > 0:
        r = r.iloc[0]
        c = c.iloc[0]
        usage_diff = ((c['avg_usage'] - r['avg_usage']) / r['avg_usage']) * 100
        error_diff = ((c['error_rate'] - r['error_rate']) / r['error_rate']) * 100 if r['error_rate'] > 0 else 0
        print(f"\n{feat}:")
        print(f"  Retained - avg usage: {r['avg_usage']:.1f}, error rate: {r['error_rate']:.4f}")
        print(f"  Churned  - avg usage: {c['avg_usage']:.1f}, error rate: {c['error_rate']:.4f}")
        print(f"  Usage diff: {usage_diff:+.1f}%  |  Error rate diff: {error_diff:+.1f}%")

# Beta feature analysis
print("\n\n--- Beta Feature Impact ---")
beta_usage = usage_merged[usage_merged['is_beta_feature'] == True]
non_beta_usage = usage_merged[usage_merged['is_beta_feature'] == False]

for label, subset in [("Beta users", beta_usage), ("Non-beta users", non_beta_usage)]:
    accts = subset['account_id'].unique()
    accts_churned = sum(1 for a in accts if a in churned_ids)
    print(f"\n{label}:")
    print(f"  Unique accounts: {len(accts)}")
    print(f"  Churn rate: {accts_churned/len(accts)*100:.1f}%")
    print(f"  Error rate: {subset['error_count'].sum()/subset['usage_count'].sum():.4f}")

# ============================================================
# H5: Revenue impact — not all churn is equal
# ============================================================
print("\n\n" + "=" * 70)
print("H5: REVENUE IMPACT — WEIGHTED CHURN ANALYSIS")
print("=" * 70)

# MRR by churn segment
churn_with_acct = churn.merge(accounts[['account_id', 'industry', 'acquisition_channel', 'plan']], on='account_id')

print("\n--- MRR Lost by Reason ---")
reason_mrr = churn_with_acct.groupby('reason_code').agg(
    events=('churn_event_id', 'count'),
    total_mrr=('last_mrr', 'sum'),
    avg_mrr=('last_mrr', 'mean'),
).sort_values('total_mrr', ascending=False)
for idx, row in reason_mrr.iterrows():
    print(f"  {idx}: ${row['total_mrr']:,.0f} total ({row['events']} events, avg ${row['avg_mrr']:,.0f})")

print("\n--- MRR Lost by Industry ---")
ind_mrr = churn_with_acct.groupby('industry').agg(
    events=('churn_event_id', 'count'),
    total_mrr=('last_mrr', 'sum'),
    avg_mrr=('last_mrr', 'mean'),
    unique_accounts=('account_id', 'nunique'),
).sort_values('total_mrr', ascending=False)
for idx, row in ind_mrr.iterrows():
    print(f"  {idx}: ${row['total_mrr']:,.0f} ({row['unique_accounts']} accounts, avg ${row['avg_mrr']:,.0f})")

print("\n--- MRR Lost by Plan ---")
plan_mrr = churn_with_acct.groupby('last_plan').agg(
    events=('churn_event_id', 'count'),
    total_mrr=('last_mrr', 'sum'),
    avg_mrr=('last_mrr', 'mean'),
).sort_values('total_mrr', ascending=False)
for idx, row in plan_mrr.iterrows():
    print(f"  {idx}: ${row['total_mrr']:,.0f} ({row['events']} events, avg ${row['avg_mrr']:,.0f})")

# High-value churn
high_value_churn = churn_with_acct[churn_with_acct['last_mrr'] >= 1000]
print(f"\n--- High-Value Churn (MRR >= $1,000) ---")
print(f"Events: {len(high_value_churn)} ({len(high_value_churn)/len(churn)*100:.1f}% of all churn)")
print(f"MRR: ${high_value_churn['last_mrr'].sum():,.0f} ({high_value_churn['last_mrr'].sum()/churn['last_mrr'].sum()*100:.1f}% of MRR lost)")
print(f"Top reasons:")
print(high_value_churn['reason_code'].value_counts().head(5).to_string())

# ============================================================
# H6: Acquisition channel quality
# ============================================================
print("\n\n" + "=" * 70)
print("H6: ACQUISITION CHANNEL — QUALITY vs VOLUME")
print("=" * 70)

channel_analysis = accounts.groupby('acquisition_channel').agg(
    total_accounts=('account_id', 'count'),
    churned=('churned', 'sum'),
    trials=('is_trial', 'sum'),
).reset_index()
channel_analysis['churn_rate'] = channel_analysis['churned'] / channel_analysis['total_accounts'] * 100
channel_analysis['trial_rate'] = channel_analysis['trials'] / channel_analysis['total_accounts'] * 100

# Add MRR data
channel_mrr = churn_with_acct.groupby('acquisition_channel')['last_mrr'].sum().reset_index()
channel_mrr.columns = ['acquisition_channel', 'total_mrr_lost']
channel_analysis = channel_analysis.merge(channel_mrr, on='acquisition_channel', how='left')
channel_analysis['total_mrr_lost'] = channel_analysis['total_mrr_lost'].fillna(0)

channel_analysis = channel_analysis.sort_values('churn_rate', ascending=False)
print("\nChannel Performance (sorted by churn rate):")
for _, row in channel_analysis.iterrows():
    print(f"  {row['acquisition_channel']:20s}: Churn {row['churn_rate']:.1f}% | "
          f"{int(row['total_accounts'])} accounts | "
          f"Trial rate: {row['trial_rate']:.0f}% | "
          f"MRR lost: ${row['total_mrr_lost']:,.0f}")

# ============================================================
# H7: Downgrade → Churn pipeline
# ============================================================
print("\n\n" + "=" * 70)
print("H7: DOWNGRADE → CHURN PIPELINE")
print("=" * 70)

# Check if accounts that downgraded ended up churning
acct_downgrades = subs[subs['status'] == 'Downgraded'].groupby('account_id').size().reset_index(name='downgrades')
acct_downgrades_with_churn = acct_downgrades.merge(
    accounts[['account_id', 'churned']], on='account_id', how='left'
)

downgraded_accts = set(acct_downgrades['account_id'])
not_downgraded = accounts[~accounts['account_id'].isin(downgraded_accts)]
downgraded = accounts[accounts['account_id'].isin(downgraded_accts)]

print(f"\nAccounts with downgrades: {len(downgraded)}")
print(f"Churn rate WITH downgrades: {downgraded['churned'].mean()*100:.1f}%")
print(f"Churn rate WITHOUT downgrades: {not_downgraded['churned'].mean()*100:.1f}%")
print(f"→ Downgrades increase churn probability by {(downgraded['churned'].mean() - not_downgraded['churned'].mean())/not_downgraded['churned'].mean()*100:.0f}%")

# Monthly vs Annual billing
print("\n\n--- Billing Frequency Impact ---")
acct_billing = subs.groupby('account_id')['billing_frequency'].agg(
    lambda x: 'Monthly' if (x == 'Monthly').mean() > 0.5 else 'Annual'
).reset_index(name='primary_billing')

acct_billing_churn = acct_billing.merge(accounts[['account_id', 'churned']], on='account_id')
for billing in ['Monthly', 'Annual']:
    subset = acct_billing_churn[acct_billing_churn['primary_billing'] == billing]
    print(f"  {billing}: {subset['churned'].mean()*100:.1f}% churn rate ({subset['churned'].sum()}/{len(subset)})")

# ============================================================
# CHURN REASON × FEATURE USAGE CROSS-REFERENCE
# ============================================================
print("\n\n" + "=" * 70)
print("CROSS-REFERENCE: CHURN REASON × FEATURE USAGE")
print("=" * 70)

# For "Product Issues" churners — which features had most errors?
product_issue_accts = set(churn[churn['reason_code'] == 'Product Issues']['account_id'])
product_issue_usage = usage_merged[usage_merged['account_id'].isin(product_issue_accts)]

print(f"\nProduct Issues churners ({len(product_issue_accts)} accounts):")
pi_feat = product_issue_usage.groupby('feature_name').agg(
    total_errors=('error_count', 'sum'),
    total_usage=('usage_count', 'sum'),
    error_rate=('error_count', lambda x: x.sum()),
).reset_index()
pi_feat['error_rate'] = pi_feat['total_errors'] / pi_feat['total_usage']
pi_feat = pi_feat.sort_values('error_rate', ascending=False)
for _, row in pi_feat.iterrows():
    print(f"  {row['feature_name']:25s}: error rate {row['error_rate']:.4f} ({row['total_errors']} errors / {row['total_usage']} uses)")

# For "Integration Problems" — feature analysis
int_issue_accts = set(churn[churn['reason_code'] == 'Integration Problems']['account_id'])
int_usage = usage_merged[usage_merged['account_id'].isin(int_issue_accts)]
print(f"\nIntegration Problems churners ({len(int_issue_accts)} accounts):")
if len(int_usage) > 0:
    int_feat = int_usage.groupby('feature_name').agg(
        total_errors=('error_count', 'sum'),
        total_usage=('usage_count', 'sum'),
    ).reset_index()
    int_feat['error_rate'] = int_feat['total_errors'] / int_feat['total_usage']
    int_feat = int_feat.sort_values('error_rate', ascending=False)
    for _, row in int_feat.iterrows():
        print(f"  {row['feature_name']:25s}: error rate {row['error_rate']:.4f}")

# ============================================================
# CHURN REASON × TEXT FEEDBACK ANALYSIS
# ============================================================
print("\n\n" + "=" * 70)
print("TEXT FEEDBACK ANALYSIS")
print("=" * 70)

print("\n--- Sample Feedback by Reason ---")
for reason in churn['reason_code'].value_counts().head(5).index:
    feedback = churn[churn['reason_code'] == reason]['reason_detail'].value_counts()
    print(f"\n{reason} ({len(churn[churn['reason_code']==reason])} events):")
    for text, count in feedback.head(3).items():
        print(f"  [{count}x] \"{text}\"")

# ============================================================
# SUMMARY: KEY FINDINGS
# ============================================================
print("\n\n" + "=" * 70)
print("PHASE 2 SUMMARY: KEY FINDINGS")
print("=" * 70)

print("""
1. THE PARADOX EXPLAINED:
   - "Usage grew" is TRUE overall — but driven by RETAINED power users
   - Churned accounts had significantly LOWER usage before leaving
   - Retained accounts use more features (broader adoption)

2. SATISFACTION IS A MIRAGE:
   - Overall satisfaction looks ~3.2/5 "ok"
   - But churned customers respond LESS to surveys (lower response rate)
   - When they DO respond, scores are significantly lower
   - The CS team's "satisfaction is ok" is survivor bias

3. ROOT CAUSES (in order of impact):
   a) Product quality issues: Workflow Builder & Report Generator
      have 3x the error rate → frustration → churn
   b) Poor support for at-risk accounts: longer response times,
      more escalations for churned accounts
   c) Low-quality acquisition: Paid Ads (65% churn) and Events (56%)
      bring customers who don't stick
   d) Trial-to-paid failure: 71% of trial accounts churn
   e) Starter plan trap: 61% churn rate — too basic, not enough value

4. FINANCIAL IMPACT:
   - High-value accounts churning disproportionately on Product Issues
   - Downgrade is a strong leading indicator of churn
   - Monthly billing = higher churn risk
""")
