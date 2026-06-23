import pandas as pd

data = pd.read_csv('outputs/preprocessed_data.csv')
print("Columns:", list(data.columns))
print("\nShape:", data.shape)
print("\nData types:")
print(data.dtypes)
