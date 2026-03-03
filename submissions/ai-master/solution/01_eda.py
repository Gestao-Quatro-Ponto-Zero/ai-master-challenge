"""
Phase 1: Exploratory Data Analysis — RavenStack Churn Diagnostic
================================================================
Objective: Understand each table's structure, distributions, and data quality
before cross-referencing.
"""
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

DATA = '/home/user/ai-master-challenge/datasets/'

# Load all datasets
print("=" * 70)
print("PHASE 1: EXPLORATORY DATA ANALYSIS")
print("=" * 70)

accounts = pd.read_csv(f'{DATA}ravenstack_accounts.csv')
subs = pd.read_csv(f'{DATA}ravenstack_subscriptions.csv')
usage = pd.read_csv(f'{DATA}ravenstack_feature_usage.csv')
tickets = pd.read_csv(f'{DATA}ravenstack_support_tickets.csv')
churn = pd.read_csv(f'{DATA}ravenstack_churn_events.csv')

datasets = {
    'Accounts': accounts,
    'Subscriptions': subs,
    'Feature Usage': usage,
    'Support Tickets': tickets,
    'Churn Events': churn
}

# ---- BASIC SHAPE & TYPES ----
print("\n1. DATASET OVERVIEW")
print("-" * 50)
for name, df in datasets.items():
    print(f"\n{name}: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"  Columns: {list(df.columns)}")
    null_cols = df.isnull().sum()
    null_cols = null_cols[null_cols > 0]
    if len(null_cols) > 0:
        print(f"  Missing values:")
        for col, cnt in null_cols.items():
            print(f"    {col}: {cnt} ({cnt/len(df)*100:.1f}%)")

# ---- ACCOUNTS ----
print("\n\n2. ACCOUNTS ANALYSIS")
print("-" * 50)
print(f"Total accounts: {len(accounts)}")
print(f"\nPlan distribution:")
print(accounts['plan'].value_counts().to_string())
print(f"\nIndustry distribution:")
print(accounts['industry'].value_counts().to_string())
print(f"\nCountry distribution:")
print(accounts['country'].value_counts().head(10).to_string())
print(f"\nAcquisition channel:")
print(accounts['acquisition_channel'].value_counts().to_string())
print(f"\nTrial accounts: {accounts['is_trial'].sum()} ({accounts['is_trial'].mean()*100:.1f}%)")
print(f"\nEmployee count stats:")
print(accounts['employee_count'].describe().to_string())

# ---- SUBSCRIPTIONS ----
print("\n\n3. SUBSCRIPTIONS ANALYSIS")
print("-" * 50)
print(f"Total subscriptions: {len(subs)}")
print(f"Unique accounts: {subs['account_id'].nunique()}")
print(f"Avg subs per account: {len(subs)/subs['account_id'].nunique():.1f}")
print(f"\nStatus distribution:")
print(subs['status'].value_counts().to_string())
print(f"\nBilling frequency:")
print(subs['billing_frequency'].value_counts().to_string())
print(f"\nMRR statistics:")
print(subs['mrr'].describe().to_string())
print(f"\nTotal MRR (all subs): ${subs['mrr'].sum():,.2f}")
print(f"Active subs MRR: ${subs[subs['status']=='Active']['mrr'].sum():,.2f}")
print(f"\nPlan distribution:")
print(subs['plan'].value_counts().to_string())
print(f"\nPayment method:")
print(subs['payment_method'].value_counts().to_string())
print(f"\nDiscount distribution:")
print(subs['discount_pct'].value_counts().sort_index().to_string())

# Churned/Cancelled subs
churned_subs = subs[subs['status'].isin(['Churned', 'Cancelled'])]
active_subs = subs[subs['status'] == 'Active']
print(f"\nChurned/Cancelled subs: {len(churned_subs)} ({len(churned_subs)/len(subs)*100:.1f}%)")
print(f"Active subs: {len(active_subs)} ({len(active_subs)/len(subs)*100:.1f}%)")
print(f"\nChurned MRR avg: ${churned_subs['mrr'].mean():,.2f}")
print(f"Active MRR avg: ${active_subs['mrr'].mean():,.2f}")

# ---- FEATURE USAGE ----
print("\n\n4. FEATURE USAGE ANALYSIS")
print("-" * 50)
print(f"Total usage records: {len(usage)}")
print(f"Unique subscriptions: {usage['subscription_id'].nunique()}")
print(f"\nFeature popularity (by usage_count):")
feat_agg = usage.groupby('feature_name').agg(
    total_usage=('usage_count', 'sum'),
    avg_usage=('usage_count', 'mean'),
    total_errors=('error_count', 'sum'),
    avg_errors=('error_count', 'mean'),
    total_duration=('duration_minutes', 'sum'),
    records=('usage_count', 'count')
).sort_values('total_usage', ascending=False)
feat_agg['error_rate'] = feat_agg['total_errors'] / feat_agg['total_usage']
print(feat_agg.to_string())

print(f"\nBeta features:")
beta = usage[usage['is_beta_feature'] == True]
print(f"  Records with beta=True: {len(beta)} ({len(beta)/len(usage)*100:.1f}%)")
print(f"  Beta features: {beta['feature_name'].value_counts().to_string()}")
print(f"  Beta error rate: {beta['error_count'].sum()/beta['usage_count'].sum():.3f}")
non_beta = usage[usage['is_beta_feature'] == False]
print(f"  Non-beta error rate: {non_beta['error_count'].sum()/non_beta['usage_count'].sum():.3f}")

# ---- SUPPORT TICKETS ----
print("\n\n5. SUPPORT TICKETS ANALYSIS")
print("-" * 50)
print(f"Total tickets: {len(tickets)}")
print(f"Unique accounts: {tickets['account_id'].nunique()}")
print(f"\nCategory distribution:")
print(tickets['category'].value_counts().to_string())
print(f"\nPriority distribution:")
print(tickets['priority'].value_counts().to_string())
print(f"\nStatus:")
print(tickets['status'].value_counts().to_string())
print(f"\nFirst response time (hours):")
print(tickets['first_response_hours'].describe().to_string())
print(f"\nResolution time (hours):")
print(tickets['resolution_hours'].describe().to_string())
print(f"\nSatisfaction score distribution:")
sat = tickets['satisfaction_score'].dropna()
print(sat.value_counts().sort_index().to_string())
print(f"  Mean satisfaction (responding): {sat.mean():.2f}")
print(f"  Missing satisfaction: {tickets['satisfaction_score'].isnull().sum()} ({tickets['satisfaction_score'].isnull().mean()*100:.1f}%)")
print(f"\nEscalation rate: {tickets['escalated'].mean()*100:.1f}%")
print(f"Reopen rate: {tickets['reopened'].mean()*100:.1f}%")

# ---- CHURN EVENTS ----
print("\n\n6. CHURN EVENTS ANALYSIS")
print("-" * 50)
print(f"Total churn events: {len(churn)}")
print(f"Unique accounts: {churn['account_id'].nunique()}")
print(f"Avg events per churned account: {len(churn)/churn['account_id'].nunique():.1f}")
print(f"\nReason code distribution:")
print(churn['reason_code'].value_counts().to_string())
print(f"\nLast plan distribution:")
print(churn['last_plan'].value_counts().to_string())
print(f"\nRefund stats:")
print(churn['refund_amount'].describe().to_string())
print(f"Total refunds: ${churn['refund_amount'].sum():,.2f}")
print(f"\nMRR lost stats:")
print(churn['last_mrr'].describe().to_string())
print(f"Total MRR at risk: ${churn['last_mrr'].sum():,.2f}")
print(f"\nExit survey completed: {churn['exit_survey_completed'].mean()*100:.1f}%")
print(f"Win-back eligible: {churn['win_back_eligible'].mean()*100:.1f}%")

# ---- KEY RELATIONSHIP ANALYSIS ----
print("\n\n7. KEY RELATIONSHIPS")
print("-" * 50)

# Which accounts churned (appear in churn_events)?
churned_acct_ids = set(churn['account_id'].unique())
all_acct_ids = set(accounts['account_id'].unique())
retained_acct_ids = all_acct_ids - churned_acct_ids

print(f"Accounts that churned: {len(churned_acct_ids)} ({len(churned_acct_ids)/len(all_acct_ids)*100:.1f}%)")
print(f"Accounts retained: {len(retained_acct_ids)} ({len(retained_acct_ids)/len(all_acct_ids)*100:.1f}%)")

# MRR impact
churned_last_mrr = churn.drop_duplicates('account_id')['last_mrr'].sum()
print(f"\nTotal MRR lost (unique accounts): ${churned_last_mrr:,.2f}")

# Churned vs Retained by plan
accounts_with_churn = accounts.copy()
accounts_with_churn['churned'] = accounts_with_churn['account_id'].isin(churned_acct_ids)

print(f"\nChurn rate by plan:")
for plan in ['Starter', 'Professional', 'Enterprise', 'Custom']:
    subset = accounts_with_churn[accounts_with_churn['plan'] == plan]
    rate = subset['churned'].mean() * 100
    print(f"  {plan}: {rate:.1f}% ({subset['churned'].sum()}/{len(subset)})")

print(f"\nChurn rate by acquisition channel:")
for ch in accounts_with_churn['acquisition_channel'].unique():
    subset = accounts_with_churn[accounts_with_churn['acquisition_channel'] == ch]
    rate = subset['churned'].mean() * 100
    print(f"  {ch}: {rate:.1f}% ({subset['churned'].sum()}/{len(subset)})")

print(f"\nChurn rate by industry:")
for ind in sorted(accounts_with_churn['industry'].unique()):
    subset = accounts_with_churn[accounts_with_churn['industry'] == ind]
    rate = subset['churned'].mean() * 100
    n = subset['churned'].sum()
    print(f"  {ind}: {rate:.1f}% ({n}/{len(subset)})")

print(f"\nChurn rate for trial vs non-trial:")
for trial in [True, False]:
    subset = accounts_with_churn[accounts_with_churn['is_trial'] == trial]
    rate = subset['churned'].mean() * 100
    print(f"  Trial={trial}: {rate:.1f}% ({subset['churned'].sum()}/{len(subset)})")

print("\n" + "=" * 70)
print("EDA COMPLETE — Key observations to investigate in Phase 2")
print("=" * 70)
