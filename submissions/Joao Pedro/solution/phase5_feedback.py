import pandas as pd
df = pd.read_csv("master_table.csv")
churned = df[df['churn_flag'] == True]
print("--- Reason Codes ---")
print(churned['reason_code'].value_counts(dropna=False))

print("\n--- Examples of feedback text (from original churn_events) ---")
churn_events = pd.read_csv("C:/Users/User/.cache/kagglehub/datasets/rivalytics/saas-subscription-and-churn-analytics-dataset/versions/1/ravenstack_churn_events.csv")
print(churn_events['feedback_text'].dropna().head(20).tolist())
