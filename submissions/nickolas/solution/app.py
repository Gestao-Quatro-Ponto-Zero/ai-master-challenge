import pandas as pd
from scoring import calculate_score

# Carregar dados reais do challenge
accounts = pd.read_csv("accounts.csv")
pipeline = pd.read_csv("sales_pipeline.csv")

# Integrar contexto da conta em cada oportunidade
df = pipeline.merge(accounts, on="account", how="left")

results = []

for _, row in df.iterrows():
    result = calculate_score(row)

    results.append(
        {
            "opportunity_id": row["opportunity_id"],
            "account": row["account"],
            "deal_stage": row["deal_stage"],
            "close_value": row["close_value"],
            "score": result["score"],
            "priority": result["priority"],
            "reasons": " | ".join(result["reasons"]),
            "actions": " | ".join(result["actions"]),
        }
    )

# Resultado final
result_df = pd.DataFrame(results)

# Ordenar melhores oportunidades
top = result_df.sort_values(by="score", ascending=False).head(10)

print(top.to_string(index=False))
