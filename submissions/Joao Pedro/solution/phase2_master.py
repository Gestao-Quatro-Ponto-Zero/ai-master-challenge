import kagglehub
import pandas as pd
import numpy as np
import os

path = kagglehub.dataset_download("rivalytics/saas-subscription-and-churn-analytics-dataset")

accounts = pd.read_csv(os.path.join(path, "ravenstack_accounts.csv"))
subs = pd.read_csv(os.path.join(path, "ravenstack_subscriptions.csv"))
usage = pd.read_csv(os.path.join(path, "ravenstack_feature_usage.csv"))
tickets = pd.read_csv(os.path.join(path, "ravenstack_support_tickets.csv"))
churn = pd.read_csv(os.path.join(path, "ravenstack_churn_events.csv"))

# Convert dates
accounts['signup_date'] = pd.to_datetime(accounts['signup_date'])
subs['start_date'] = pd.to_datetime(subs['start_date'])
subs['end_date'] = pd.to_datetime(subs['end_date'])
usage['usage_date'] = pd.to_datetime(usage['usage_date'])
tickets['submitted_at'] = pd.to_datetime(tickets['submitted_at'])
churn['churn_date'] = pd.to_datetime(churn['churn_date'])

MAX_DATE = pd.to_datetime("2024-12-31")

# Get anchor date per account (latest churn date, or MAX_DATE if not churned in accounts table)
# We use the current churn flag in accounts as the definitive "is currently churned" flag
anchor_dates = accounts[['account_id', 'churn_flag', 'signup_date']].copy()

latest_churn = churn.groupby('account_id')['churn_date'].max().reset_index()
anchor_dates = anchor_dates.merge(latest_churn, on='account_id', how='left')

anchor_dates['anchor_date'] = np.where(
    anchor_dates['churn_flag'] == True,
    anchor_dates['churn_date'].fillna(MAX_DATE), # Fallback if missing
    MAX_DATE
)

# 1. Subscriptions Aggregation
subs_agg = subs.groupby('account_id').agg(
    current_mrr=('mrr_amount', lambda x: x.iloc[-1]), # Simplification
    total_mrr=('mrr_amount', 'sum'),
    num_upgrades=('upgrade_flag', 'sum'),
    num_downgrades=('downgrade_flag', 'sum'),
    billing_frequency=('billing_frequency', lambda x: x.mode()[0] if not x.mode().empty else 'monthly'),
    tenure_days=('start_date', lambda x: (MAX_DATE - x.min()).days)
).reset_index()

# Update tenure_days based on anchor date
subs_agg = subs_agg.merge(anchor_dates[['account_id', 'anchor_date', 'signup_date']], on='account_id')
subs_agg['tenure_days'] = (subs_agg['anchor_date'] - subs_agg['signup_date']).dt.days

# 2. Usage Aggregation (time series)
# Merge usage with subs to get account_id
usage = usage.merge(subs[['subscription_id', 'account_id']], on='subscription_id', how='left')
usage = usage.merge(anchor_dates[['account_id', 'anchor_date']], on='account_id', how='left')
usage['days_to_anchor'] = (usage['anchor_date'] - usage['usage_date']).dt.days

# Filter out usage after anchor date (if any)
usage = usage[usage['days_to_anchor'] >= 0]

usage_agg = usage.groupby('account_id').agg(
    total_usage_count=('usage_count', 'sum'),
    distinct_features=('feature_name', 'nunique'),
    total_error_count=('error_count', 'sum'),
    used_beta=('is_beta_feature', 'max')
).reset_index()

# Usage in last 30 days vs previous 30-90 days
u_30 = usage[usage['days_to_anchor'] <= 30].groupby('account_id')['usage_count'].sum().reset_index(name='usage_last_30')
u_90 = usage[(usage['days_to_anchor'] > 30) & (usage['days_to_anchor'] <= 90)].groupby('account_id')['usage_count'].sum().reset_index(name='usage_prev_60')
u_90['usage_prev_60_normalized'] = u_90['usage_prev_60'] / 2  # normalize to 30-day equivalent

usage_trends = u_30.merge(u_90, on='account_id', how='outer').fillna(0)
usage_trends['usage_trend'] = np.where(usage_trends['usage_last_30'] > usage_trends['usage_prev_60_normalized'] * 1.1, 'Growing',
                              np.where(usage_trends['usage_last_30'] < usage_trends['usage_prev_60_normalized'] * 0.9, 'Declining', 'Stable'))
usage_agg = usage_agg.merge(usage_trends, on='account_id', how='left')

# 3. Tickets Aggregation
tickets = tickets.merge(anchor_dates[['account_id', 'anchor_date']], on='account_id', how='left')
tickets['days_to_anchor'] = (tickets['anchor_date'] - tickets['submitted_at']).dt.days
tickets = tickets[tickets['days_to_anchor'] >= 0]

tickets_agg = tickets.groupby('account_id').agg(
    num_tickets=('ticket_id', 'count'),
    avg_resolution_hours=('resolution_time_hours', 'mean'),
    avg_first_response_mins=('first_response_time_minutes', 'mean'),
    avg_csat=('satisfaction_score', 'mean'),
    num_escalations=('escalation_flag', 'sum')
).reset_index()

# Tickets trend (last 30 days vs before)
t_30 = tickets[tickets['days_to_anchor'] <= 30].groupby('account_id')['ticket_id'].count().reset_index(name='tickets_last_30')
tickets_agg = tickets_agg.merge(t_30, on='account_id', how='left').fillna({'tickets_last_30': 0})

# 4. Master Table Construction
master = accounts.merge(subs_agg, on='account_id', how='left')
master = master.merge(usage_agg, on='account_id', how='left')
master = master.merge(tickets_agg, on='account_id', how='left')

# Add latest churn reason and lost MRR
latest_churn_details = churn.sort_values('churn_date', ascending=False).drop_duplicates('account_id')
master = master.merge(latest_churn_details[['account_id', 'reason_code', 'refund_amount_usd']], on='account_id', how='left')

# Save to CSV
master.to_csv("master_table.csv", index=False)
print("Master table created with shape:", master.shape)
print("Columns:", master.columns.tolist())
