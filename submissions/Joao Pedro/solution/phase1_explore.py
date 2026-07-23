import kagglehub
import pandas as pd
import os

path = kagglehub.dataset_download("rivalytics/saas-subscription-and-churn-analytics-dataset")

dfs = {}
for f in ['ravenstack_accounts.csv', 'ravenstack_churn_events.csv', 'ravenstack_feature_usage.csv', 'ravenstack_subscriptions.csv', 'ravenstack_support_tickets.csv']:
    dfs[f] = pd.read_csv(os.path.join(path, f))

# Cardinality and Dates
print("\n--- Phase 1: Cardinality and Dates ---")
for f, df in dfs.items():
    print(f"[{f}]")
    date_cols = [c for c in df.columns if 'date' in c or 'at' in c]
    for dc in date_cols:
        try:
            df[dc] = pd.to_datetime(df[dc])
            print(f"  {dc} min: {df[dc].min()} | max: {df[dc].max()}")
        except Exception as e:
            pass
            
    id_cols = [c for c in df.columns if 'id' in c]
    for ic in id_cols:
        print(f"  {ic} unique: {df[ic].nunique()}")

print("\n--- Phase 1: Referential Integrity ---")
acc_in_acc = set(dfs['ravenstack_accounts.csv']['account_id'])
acc_in_subs = set(dfs['ravenstack_subscriptions.csv']['account_id'])
acc_in_tickets = set(dfs['ravenstack_support_tickets.csv']['account_id'])
acc_in_churn = set(dfs['ravenstack_churn_events.csv']['account_id'])

print("Accounts in Subs but not in Accounts:", len(acc_in_subs - acc_in_acc))
print("Accounts in Tickets but not in Accounts:", len(acc_in_tickets - acc_in_acc))
print("Accounts in Churn but not in Accounts:", len(acc_in_churn - acc_in_acc))

sub_in_subs = set(dfs['ravenstack_subscriptions.csv']['subscription_id'])
sub_in_usage = set(dfs['ravenstack_feature_usage.csv']['subscription_id'])
print("Subscriptions in Usage but not in Subs:", len(sub_in_usage - sub_in_subs))

# Checking if some accounts have no usage
subs_with_usage = set(dfs['ravenstack_feature_usage.csv']['subscription_id'])
subs_without_usage = sub_in_subs - subs_with_usage
print("Subscriptions without usage:", len(subs_without_usage))

acc_with_churn = set(dfs['ravenstack_accounts.csv'][dfs['ravenstack_accounts.csv']['churn_flag'] == True]['account_id'])
print("Accounts marked as churned in Accounts:", len(acc_with_churn))
print("Accounts in Churn events:", len(acc_in_churn))
