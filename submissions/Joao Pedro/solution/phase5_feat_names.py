import pandas as pd
usage = pd.read_csv("C:/Users/User/.cache/kagglehub/datasets/rivalytics/saas-subscription-and-churn-analytics-dataset/versions/1/ravenstack_feature_usage.csv")
print("Unique feature names:", usage['feature_name'].unique())
