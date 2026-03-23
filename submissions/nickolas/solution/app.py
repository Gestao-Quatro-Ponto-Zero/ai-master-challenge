import pandas as pd
from scoring import calculate_score

# Carregar dados
accounts = pd.read_csv("accounts.csv")
pipeline = pd.read_csv("sales_pipeline.csv")

# Merge dos dados
df = pipeline.merge(accounts, on="account", how="left")

results = []

for _, row in df.iterrows():
    deal = row.to_dict()
    account = row.to_dict()

    result = calculate_score(deal, account)

    results.append({
        "opportunity_id": row["opportunity_id"],
        "account": row["account"],
        "score": result["score"],
        "priority": result["priority"]
    })

# Resultado final
result_df = pd.DataFrame(results)

# Top oportunidades
top = result_df.sort_values(by="score", ascending=False).head(10)

print(top)
