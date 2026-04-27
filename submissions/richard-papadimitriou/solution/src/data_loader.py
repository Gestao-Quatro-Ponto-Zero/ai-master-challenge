import pandas as pd
import os

def load_data(data_dir=None):
    """
    Loads and merges the 4 CSV files: accounts, products, sales_teams, sales_pipeline.
    """
    # Force path relative to this script: src/.. -> solution/data
    if data_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, 'data')
        
    # Load CSVs
    accounts = pd.read_csv(os.path.join(data_dir, 'accounts.csv'))
    products = pd.read_csv(os.path.join(data_dir, 'products.csv'))
    teams = pd.read_csv(os.path.join(data_dir, 'sales_teams.csv'))
    pipeline = pd.read_csv(os.path.join(data_dir, 'sales_pipeline.csv'))

    # Basic Cleaning
    pipeline['engage_date'] = pd.to_datetime(pipeline['engage_date'])
    pipeline['close_date'] = pd.to_datetime(pipeline['close_date'])
    
    # Ensure close_value is numeric
    pipeline['close_value'] = pd.to_numeric(pipeline['close_value'], errors='coerce').fillna(0)

    # Merging
    # pipeline -> teams (sales_agent)
    df = pipeline.merge(teams, on='sales_agent', how='left')
    
    # df -> products (product)
    df = df.merge(products, on='product', how='left')
    
    # df -> accounts (account)
    df = df.merge(accounts, on='account', how='left')

    return df

if __name__ == "__main__":
    # Test loading
    try:
        df = load_data('data')
        print(f"Data loaded successfully. Total rows: {len(df)}")
        print(f"Columns: {df.columns.tolist()}")
    except Exception as e:
        print(f"Error loading data: {e}")
