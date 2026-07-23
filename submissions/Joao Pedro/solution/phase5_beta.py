import pandas as pd
df = pd.read_csv("master_table.csv")
print("Beta Usage Distribution:")
print(df.groupby('used_beta').agg(
    total=('account_id', 'count'),
    churned=('churn_flag', 'sum'),
    churn_rate=('churn_flag', 'mean'),
    avg_errors=('total_error_count', 'mean')
))
