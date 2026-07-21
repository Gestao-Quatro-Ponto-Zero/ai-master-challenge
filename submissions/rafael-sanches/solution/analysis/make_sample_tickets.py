"""Gera sample_tickets.csv (50 tickets reais do conjunto de TESTE) pra demo auto-contida."""
import pandas as pd
from sklearn.model_selection import train_test_split

D2 = r"D:\Projetos\Case G4\data\challenge-002-support\all_tickets_processed_improved_v3.csv"
OUT = r"D:\Projetos\Case G4\solution-draft\prototype\sample_tickets.csv"

df = pd.read_csv(D2).dropna(subset=["Document", "Topic_group"])
df = df[df["Document"].astype(str).str.strip() != ""]
X, y = df["Document"].astype(str), df["Topic_group"]
_, Xte, _, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
test_df = pd.DataFrame({"Document": Xte.values, "Topic_group": yte.values})
# 50 tickets estratificados (representa as 8 categorias) — sem groupby.apply
parts = [g.sample(min(len(g), 7), random_state=7) for _, g in test_df.groupby("Topic_group")]
sample = pd.concat(parts).sample(frac=1, random_state=7).head(50).reset_index(drop=True)
sample.to_csv(OUT, index=False)
print(f"salvo {len(sample)} tickets em {OUT} | colunas: {list(sample.columns)}")
print(sample["Topic_group"].value_counts())
