import pandas as pd
usage = pd.read_csv("C:/Users/User/.cache/kagglehub/datasets/rivalytics/saas-subscription-and-churn-analytics-dataset/versions/1/ravenstack_feature_usage.csv")
subs = pd.read_csv("C:/Users/User/.cache/kagglehub/datasets/rivalytics/saas-subscription-and-churn-analytics-dataset/versions/1/ravenstack_subscriptions.csv")
accounts = pd.read_csv("C:/Users/User/.cache/kagglehub/datasets/rivalytics/saas-subscription-and-churn-analytics-dataset/versions/1/ravenstack_accounts.csv")

usage = usage.merge(subs[['subscription_id', 'account_id']], on='subscription_id', how='left')
usage = usage.merge(accounts[['account_id', 'churn_flag']], on='account_id', how='left')

churned_feat = usage[usage['churn_flag'] == True].groupby('feature_name').size().sort_values(ascending=False).head(5)
active_feat = usage[usage['churn_flag'] == False].groupby('feature_name').size().sort_values(ascending=False).head(5)

print("Top features for churned accounts:\n", churned_feat)
print("\nTop features for active accounts:\n", active_feat)
