import pandas as pd
df = pd.read_csv("master_table.csv")
print("Churn by Plan Tier:")
print(df.groupby('plan_tier').agg(
    total=('account_id', 'count'),
    churned=('churn_flag', 'sum'),
    churn_rate=('churn_flag', 'mean')
))

print("\nChurn by Billing Frequency:")
print(df.groupby('billing_frequency').agg(
    total=('account_id', 'count'),
    churned=('churn_flag', 'sum'),
    churn_rate=('churn_flag', 'mean')
))

print("\nChurn by Trial Status:")
print(df.groupby('is_trial').agg(
    total=('account_id', 'count'),
    churned=('churn_flag', 'sum'),
    churn_rate=('churn_flag', 'mean')
))
