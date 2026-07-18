import pandas as pd
import numpy as np

# Load tables
df = pd.read_csv("master_table.csv")
usage = pd.read_csv("C:/Users/User/.cache/kagglehub/datasets/rivalytics/saas-subscription-and-churn-analytics-dataset/versions/1/ravenstack_feature_usage.csv")
subs = pd.read_csv("C:/Users/User/.cache/kagglehub/datasets/rivalytics/saas-subscription-and-churn-analytics-dataset/versions/1/ravenstack_subscriptions.csv")
accounts = pd.read_csv("C:/Users/User/.cache/kagglehub/datasets/rivalytics/saas-subscription-and-churn-analytics-dataset/versions/1/ravenstack_accounts.csv")

# Merge usage
usage['usage_date'] = pd.to_datetime(usage['usage_date'])
usage = usage.merge(subs[['subscription_id', 'account_id']], on='subscription_id', how='left')
usage = usage.merge(accounts[['account_id', 'churn_flag']], on='account_id', how='left')

# Get anchor dates (max date per account or churn date)
anchor_dates = df[['account_id', 'anchor_date']].copy()
anchor_dates['anchor_date'] = pd.to_datetime(anchor_dates['anchor_date'])
usage = usage.merge(anchor_dates, on='account_id', how='left')
usage['days_to_anchor'] = (usage['anchor_date'] - usage['usage_date']).dt.days
usage = usage[usage['days_to_anchor'] >= 0]

# Calculate distinct features used in last 30 days vs 30-60 days
usage_30 = usage[usage['days_to_anchor'] <= 30]
usage_60 = usage[(usage['days_to_anchor'] > 30) & (usage['days_to_anchor'] <= 60)]

feat_30 = usage_30.groupby('account_id').agg(
    vol_30=('usage_count', 'sum'),
    dist_feat_30=('feature_name', 'nunique')
).reset_index()

feat_60 = usage_60.groupby('account_id').agg(
    vol_60=('usage_count', 'sum'),
    dist_feat_60=('feature_name', 'nunique')
).reset_index()

agg = df[['account_id', 'churn_flag', 'industry', 'plan_tier']].merge(feat_30, on='account_id', how='left').merge(feat_60, on='account_id', how='left')
agg = agg.fillna(0)

# Paradoxo do uso: Cresceu em volume, mas profundidade (distinct features) caiu?
agg['vol_diff'] = agg['vol_30'] - agg['vol_60']
agg['dist_feat_diff'] = agg['dist_feat_30'] - agg['dist_feat_60']

print("--- Análise de Uso (Últimos 30 vs 30-60 dias antes do churn/fim) ---")
print("Média de Volume de Uso:")
print("Churned - 30d:", agg[agg['churn_flag']==True]['vol_30'].mean(), "| 60d:", agg[agg['churn_flag']==True]['vol_60'].mean())
print("Active - 30d:", agg[agg['churn_flag']==False]['vol_30'].mean(), "| 60d:", agg[agg['churn_flag']==False]['vol_60'].mean())

print("\nMédia de Features Distintas:")
print("Churned - 30d:", agg[agg['churn_flag']==True]['dist_feat_30'].mean(), "| 60d:", agg[agg['churn_flag']==True]['dist_feat_60'].mean())
print("Active - 30d:", agg[agg['churn_flag']==False]['dist_feat_30'].mean(), "| 60d:", agg[agg['churn_flag']==False]['dist_feat_60'].mean())

# Paradoxo CS: Tickets e CSAT vs Churn
print("\n--- Análise de CS (Satisfação) ---")
print(df.groupby('churn_flag')[['avg_csat', 'num_tickets', 'avg_resolution_hours']].mean())

