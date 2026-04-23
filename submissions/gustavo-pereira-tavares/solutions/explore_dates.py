import pandas as pd
import numpy as np

accounts = pd.read_csv('data/ravenstack_accounts.csv')
subscriptions = pd.read_csv('data/ravenstack_subscriptions.csv')
churn = pd.read_csv('data/ravenstack_churn_events.csv')
usage = pd.read_csv('data/ravenstack_feature_usage.csv')
tickets = pd.read_csv('data/ravenstack_support_tickets.csv')

print('=== ACCOUNTS ===')
print(accounts[['account_id', 'signup_date']].head(3))
print()

print('=== SUBSCRIPTIONS ===')
print(subscriptions[['account_id', 'subscription_id', 'start_date', 'end_date']].head(3))
print()

print('=== CHURN EVENTS ===')
print(churn[['account_id', 'churn_date', 'reason_code', 'refund_amount_usd', 'preceding_upgrade_flag', 'preceding_downgrade_flag']].head(3))
print()

print('=== FEATURE USAGE ===')
print(usage[['subscription_id', 'usage_date']].head(3))
print()

print('=== SUPPORT TICKETS ===')
print(tickets[['account_id', 'submitted_at']].head(3))
print()

print('=== CHURN DATE RANGE ===')
churn['churn_date'] = pd.to_datetime(churn['churn_date'])
print(f"Min: {churn['churn_date'].min()}")
print(f"Max: {churn['churn_date'].max()}")
print()

print('=== CHURN - preceding flags info ===')
print(f"Filled preceding_upgrade_flag: {churn['preceding_upgrade_flag'].notna().sum()}/{len(churn)}")
print(f"Filled preceding_downgrade_flag: {churn['preceding_downgrade_flag'].notna().sum()}/{len(churn)}")
print()

print('=== Refund amounts ===')
print(f"Non-zero refunds: {(churn['refund_amount_usd'] > 0).sum()}/{len(churn)}")
print(f"Refund stats: {churn['refund_amount_usd'].describe()}")
