"""Distribuição de stages, qualidade, win rate por todos os recortes relevantes."""
import pandas as pd
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
acc = pd.read_csv(DATA / "accounts.csv")
prod = pd.read_csv(DATA / "products.csv")
team = pd.read_csv(DATA / "sales_teams.csv")
pipe = pd.read_csv(DATA / "sales_pipeline.csv")

# Normaliza bug: GTXPro -> GTX Pro
pipe["product"] = pipe["product"].replace({"GTXPro": "GTX Pro"})

# Parse datas
pipe["engage_date"] = pd.to_datetime(pipe["engage_date"])
pipe["close_date"] = pd.to_datetime(pipe["close_date"])

# Joins enriquecidos
df = pipe.merge(prod, on="product", how="left") \
         .merge(team, on="sales_agent", how="left") \
         .merge(acc, on="account", how="left", suffixes=("", "_acc"))

def section(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)

section("DISTRIBUIÇÃO DE STAGES")
total = len(df)
counts = df["deal_stage"].value_counts()
for stage, n in counts.items():
    print(f"  {stage:<13} {n:>5}  ({n/total:.1%})")

closed = df[df["deal_stage"].isin(["Won", "Lost"])]
won_n = (closed["deal_stage"] == "Won").sum()
print(f"\nFechados totais: {len(closed)}")
print(f"Win rate global: {won_n/len(closed):.1%}")

section("QUALIDADE DOS DADOS — onde estão os 1425 nulls de account?")
print(df[df["account"].isna()]["deal_stage"].value_counts())
print("\n→ todos os Prospecting (500) + parte dos Engaging (1589) não têm account?")
print(df.groupby("deal_stage")["account"].apply(lambda x: x.isna().sum()))

section("WIN RATE POR PRODUTO")
wr = closed.groupby("product").agg(
    deals=("opportunity_id", "size"),
    won=("deal_stage", lambda x: (x == "Won").sum()),
    avg_val=("close_value", "mean"),
).assign(win_rate=lambda d: d["won"] / d["deals"])
wr = wr.merge(prod[["product", "sales_price"]], on="product")
print(wr.sort_values("win_rate", ascending=False).to_string(index=False))

section("WIN RATE POR SETOR (indústria)")
wr = closed.groupby("sector").agg(
    deals=("opportunity_id", "size"),
    won=("deal_stage", lambda x: (x == "Won").sum()),
).assign(win_rate=lambda d: d["won"] / d["deals"])
print(wr.sort_values("win_rate", ascending=False).to_string())

section("WIN RATE POR VENDEDOR (top + bottom 5)")
wr = closed.groupby("sales_agent").agg(
    deals=("opportunity_id", "size"),
    won=("deal_stage", lambda x: (x == "Won").sum()),
    revenue=("close_value", "sum"),
).assign(win_rate=lambda d: d["won"] / d["deals"]).sort_values("win_rate", ascending=False)
print("TOP 5:")
print(wr.head(5).to_string())
print("\nBOTTOM 5:")
print(wr.tail(5).to_string())
print(f"\nspread: {wr['win_rate'].max() - wr['win_rate'].min():.1%}")
print(f"std: {wr['win_rate'].std():.1%}")

section("WIN RATE POR MANAGER")
wr = closed.groupby("manager").agg(
    deals=("opportunity_id", "size"),
    won=("deal_stage", lambda x: (x == "Won").sum()),
    revenue=("close_value", "sum"),
).assign(win_rate=lambda d: d["won"] / d["deals"]).sort_values("win_rate", ascending=False)
print(wr.to_string())
print(f"\nspread: {wr['win_rate'].max() - wr['win_rate'].min():.1%}")

section("WIN RATE POR REGIONAL OFFICE")
wr = closed.groupby("regional_office").agg(
    deals=("opportunity_id", "size"),
    won=("deal_stage", lambda x: (x == "Won").sum()),
).assign(win_rate=lambda d: d["won"] / d["deals"])
print(wr.to_string())

section("WIN RATE POR SETOR x PRODUTO (matriz parcial)")
m = closed.assign(won=lambda d: (d["deal_stage"] == "Won").astype(int)) \
          .pivot_table(index="sector", columns="product", values="won", aggfunc="mean")
print(m.round(2).fillna("-").to_string())

section("WIN RATE POR LOCAL DA CONTA")
wr = closed.groupby("office_location").agg(
    deals=("opportunity_id", "size"),
    won=("deal_stage", lambda x: (x == "Won").sum()),
).assign(win_rate=lambda d: d["won"] / d["deals"]).sort_values("win_rate", ascending=False)
print(wr.to_string())

section("REVENUE / EMPLOYEES DA CONTA — discriminam?")
# Bucketize
closed_acc = closed.dropna(subset=["revenue", "employees"]).copy()
closed_acc["revenue_bucket"] = pd.qcut(closed_acc["revenue"], q=4, labels=["Q1-low", "Q2", "Q3", "Q4-high"])
closed_acc["emp_bucket"] = pd.qcut(closed_acc["employees"], q=4, labels=["Q1-low", "Q2", "Q3", "Q4-high"])

print("Win rate por quartil de revenue da conta:")
print(closed_acc.groupby("revenue_bucket", observed=True).apply(
    lambda x: pd.Series({
        "deals": len(x),
        "win_rate": (x["deal_stage"] == "Won").mean()
    })
).to_string())

print("\nWin rate por quartil de employees da conta:")
print(closed_acc.groupby("emp_bucket", observed=True).apply(
    lambda x: pd.Series({
        "deals": len(x),
        "win_rate": (x["deal_stage"] == "Won").mean()
    })
).to_string())

section("ANO DE FUNDAÇÃO DA CONTA — discrimina?")
closed_acc["age_bucket"] = pd.cut(closed_acc["year_established"],
                                   bins=[1900, 1980, 2000, 2010, 2025],
                                   labels=["pre-1980", "1980-2000", "2000-2010", "post-2010"])
print(closed_acc.groupby("age_bucket", observed=True).apply(
    lambda x: pd.Series({
        "deals": len(x),
        "win_rate": (x["deal_stage"] == "Won").mean()
    })
).to_string())

section("SUBSIDIÁRIA vs INDEPENDENTE")
closed_acc["is_subsidiary"] = closed_acc["subsidiary_of"].notna()
print(closed_acc.groupby("is_subsidiary").apply(
    lambda x: pd.Series({
        "deals": len(x),
        "win_rate": (x["deal_stage"] == "Won").mean()
    })
).to_string())
