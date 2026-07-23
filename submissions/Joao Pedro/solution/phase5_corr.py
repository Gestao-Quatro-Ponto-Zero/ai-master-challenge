import pandas as pd
df = pd.read_csv("master_table.csv")
numeric_df = df.select_dtypes(include=['number', 'bool']).copy()
numeric_df.dropna(subset=['churn_flag'], inplace=True)
corr = numeric_df.corr()['churn_flag'].sort_values()
print(corr)
