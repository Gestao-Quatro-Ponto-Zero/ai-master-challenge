"""Continuação: produto recorrente, vendedor x conta, close_value vs revenue."""
import pandas as pd
import numpy as np
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
prod = pd.read_csv(DATA / "products.csv")
team = pd.read_csv(DATA / "sales_teams.csv")
acc = pd.read_csv(DATA / "accounts.csv")
pipe = pd.read_csv(DATA / "sales_pipeline.csv")
pipe["product"] = pipe["product"].replace({"GTXPro": "GTX Pro"})
pipe["engage_date"] = pd.to_datetime(pipe["engage_date"])
pipe["close_date"] = pd.to_datetime(pipe["close_date"])

df = pipe.merge(prod, on="product", how="left") \
         .merge(team, on="sales_agent", how="left") \
         .merge(acc, on="account", how="left", suffixes=("", "_acc"))

closed = df[df["deal_stage"].isin(["Won", "Lost"])].copy()
c = closed.dropna(subset=["account", "engage_date"]).sort_values("engage_date").reset_index(drop=True)

def section(t):
    print("\n" + "=" * 78); print(t); print("=" * 78)

# --- Mesmo produto, mesma conta, já comprado antes ---
section("CONTA JÁ COMPROU ESTE PRODUTO ESPECÍFICO?")
bought_before = []
seen = {}  # account -> set of products won
for _, row in c.iterrows():
    a = row["account"]
    p = row["product"]
    bought_before.append(p in seen.get(a, set()))
    if row["deal_stage"] == "Won":
        seen.setdefault(a, set()).add(p)
c["bought_this_product_before"] = bought_before
print(c.groupby("bought_this_product_before").apply(
    lambda x: pd.Series({"deals": len(x), "win_rate": (x["deal_stage"] == "Won").mean()})
).to_string())

# --- Vendedor já vendeu pra conta ---
section("VENDEDOR JÁ FECHOU UM DEAL COM ESTA CONTA?")
agent_won = []
seen = set()
for _, row in c.iterrows():
    key = (row["sales_agent"], row["account"])
    agent_won.append(key in seen)
    if row["deal_stage"] == "Won":
        seen.add(key)
c["agent_won_this_account_before"] = agent_won
print(c.groupby("agent_won_this_account_before").apply(
    lambda x: pd.Series({"deals": len(x), "win_rate": (x["deal_stage"] == "Won").mean()})
).to_string())

# --- Combinação: vendedor já fechou ESTE produto pra ESTA conta ---
section("VENDEDOR JÁ VENDEU ESTE PRODUTO PRA ESTA CONTA?")
agent_prod_won = []
seen = set()
for _, row in c.iterrows():
    key = (row["sales_agent"], row["account"], row["product"])
    agent_prod_won.append(key in seen)
    if row["deal_stage"] == "Won":
        seen.add(key)
c["agent_won_this_combo_before"] = agent_prod_won
print(c.groupby("agent_won_this_combo_before").apply(
    lambda x: pd.Series({"deals": len(x), "win_rate": (x["deal_stage"] == "Won").mean()})
).to_string())

# --- Tempo desde último Won da conta ---
section("DIAS DESDE A ÚLTIMA VITÓRIA NA CONTA")
last_won = {}
gap_days = []
for _, row in c.iterrows():
    a = row["account"]
    if a in last_won:
        gap_days.append((row["engage_date"] - last_won[a]).days)
    else:
        gap_days.append(np.nan)
    if row["deal_stage"] == "Won":
        last_won[a] = row["close_date"] if pd.notna(row["close_date"]) else row["engage_date"]
c["days_since_last_won"] = gap_days

c2 = c.dropna(subset=["days_since_last_won"]).copy()
c2["gap_bucket"] = pd.cut(c2["days_since_last_won"],
                          bins=[-1, 30, 90, 180, 365, 9999],
                          labels=["≤30d", "31-90d", "91-180d", "181-365d", ">365d"])
print(c2.groupby("gap_bucket", observed=True).apply(
    lambda x: pd.Series({"deals": len(x), "win_rate": (x["deal_stage"] == "Won").mean()})
).to_string())

# --- close_value vs revenue da conta (escala) ---
section("CLOSE VALUE: tamanho da conta importa para QUANTO?")
won_only = c[c["deal_stage"] == "Won"].dropna(subset=["revenue"]).copy()
won_only["rev_bucket"] = pd.qcut(won_only["revenue"], q=4, labels=["Q1", "Q2", "Q3", "Q4"])
print("Close value médio por quartil de receita da conta:")
print(won_only.groupby("rev_bucket", observed=True)["close_value"].agg(["mean", "median", "count"]).round(0).to_string())

print("\nClose value real vs sales_price (Won apenas):")
print(won_only.groupby("product").agg(
    avg_close=("close_value", "mean"),
    median_close=("close_value", "median"),
    list_price=("sales_price", "first"),
).round(0).assign(disc=lambda d: ((1 - d["avg_close"]/d["list_price"])*100).round(1)).to_string())

# --- VOLUME DE PIPELINE POR VENDEDOR (carga de trabalho) ---
section("CARGA DE PIPELINE ABERTO POR VENDEDOR (Engaging + Prospecting)")
opened = df[df["deal_stage"].isin(["Engaging", "Prospecting"])]
load = opened.groupby("sales_agent").size().sort_values(ascending=False)
print(f"vendedores: {len(load)}")
print(f"mediana de deals abertos: {load.median():.0f}")
print(f"min: {load.min()}, max: {load.max()}")
print("\ntop 5 mais carregados:")
print(load.head(5))
print("\nbottom 5:")
print(load.tail(5))

# --- VENDEDOR: histórico recente vs antigo (achou padrão?) ---
section("VENDEDOR: top performers tem o quê em comum?")
vendor_stats = closed.groupby("sales_agent").agg(
    total=("opportunity_id", "size"),
    won=("deal_stage", lambda x: (x == "Won").sum()),
    revenue=("close_value", "sum"),
).assign(
    win_rate=lambda d: d["won"]/d["total"],
    avg_deal_size=lambda d: d["revenue"]/d["won"]
)
print("Correlação entre métricas do vendedor:")
print(vendor_stats[["total", "win_rate", "avg_deal_size", "revenue"]].corr().round(2).to_string())
print("\n→ Vendedor com mais volume tem mais ou menos win rate?")
print(f"  correlação volume x win_rate: {vendor_stats['total'].corr(vendor_stats['win_rate']):.2f}")
print(f"  correlação volume x avg_deal_size: {vendor_stats['total'].corr(vendor_stats['avg_deal_size']):.2f}")
