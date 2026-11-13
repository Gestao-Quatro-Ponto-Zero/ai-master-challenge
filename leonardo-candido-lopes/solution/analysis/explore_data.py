import pandas as pd
pd.set_option('display.max_columns',None); pd.set_option('display.width',250); pd.set_option('display.max_colwidth',80)
for f in ['data/customer_support_tickets.csv','data/all_tickets_processed_improved_v3.csv']:
    df=pd.read_csv(f)
    print('=====',f,df.shape); print(df.dtypes); print(df.isna().sum())
    print(df.head(5)); print(df.tail(3))
    print('dups',df.duplicated().sum())
    for c in df.columns:
        if df[c].nunique()<60: print(c, df[c].value_counts(dropna=False).to_dict())
        else: print(c,'nunique',df[c].nunique())
