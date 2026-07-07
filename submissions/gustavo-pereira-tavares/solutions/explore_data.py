import pandas as pd
import os

datasets = {
    'accounts': 'ravenstack_accounts.csv',
    'subscriptions': 'ravenstack_subscriptions.csv',
    'churn_events': 'ravenstack_churn_events.csv',
    'feature_usage': 'ravenstack_feature_usage.csv',
    'support_tickets': 'ravenstack_support_tickets.csv'
}

for name, file in datasets.items():
    print(f"\n{'='*60}")
    print(f"DATASET: {name.upper()}")
    print(f"{'='*60}")
    df = pd.read_csv(file)
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"Dtypes:\n{df.dtypes}")
    print(f"\nFirst 2 rows:")
    print(df.head(2).to_string())
    print(f"\nMissing values:\n{df.isnull().sum()}")
