import pandas as pd
from scoring import calculate_score


# Carregar dados reais do challenge
accounts = pd.read_csv("accounts.csv")
pipeline = pd.read_csv("sales_pipeline.csv")

# Integrar contexto da conta em cada oportunidade
df = pipeline.merge(accounts, on="account", how="left")

# Calibração por distribuição real dos dados
thresholds = {
    "revenue_p75": df["revenue"].fillna(0).quantile(0.75),
    "revenue_p40": df["revenue"].fillna(0).quantile(0.40),
    "close_value_p75": df["close_value"].fillna(0).quantile(0.75),
    "close_value_p40": df["close_value"].fillna(0).quantile(0.40),
}

results = []

for _, row in df.iterrows():
    result = calculate_score(row, thresholds)

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

result_df = pd.DataFrame(results)

# Priorização operacional: deals ativos
active_df = result_df[~result_df["deal_stage"].isin(["Won", "Lost"])].copy()

top = active_df.sort_values(by="score", ascending=False).head(10)

print(top.to_string(index=False))
