"""Histórico de conta: recompra, número de deals anteriores, efeito de relacionamento."""
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

def section(t):
    print("\n" + "=" * 78); print(t); print("=" * 78)

section("QUANTOS DEALS POR CONTA")
deals_per_acc = df.dropna(subset=["account"]).groupby("account").size().sort_values(ascending=False)
print(f"contas com pelo menos 1 deal: {len(deals_per_acc)}")
print(f"mediana: {deals_per_acc.median():.0f}")
print(f"média: {deals_per_acc.mean():.0f}")
print(f"max: {deals_per_acc.max()}")
print(f"min: {deals_per_acc.min()}")
print("\ntop 10:")
print(deals_per_acc.head(10))

section("WIN RATE POR PRIMEIRO/RECOMPRA")
# Para cada deal, ordenar por engage_date e marcar se é o primeiro da conta
closed_sorted = closed.dropna(subset=["account", "engage_date"]).sort_values("engage_date")
closed_sorted["deal_order"] = closed_sorted.groupby("account").cumcount() + 1
closed_sorted["is_first"] = closed_sorted["deal_order"] == 1
print("Win rate em primeira tentativa vs deals subsequentes:")
print(closed_sorted.groupby("is_first").apply(
    lambda x: pd.Series({
        "deals": len(x),
        "win_rate": (x["deal_stage"] == "Won").mean()
    })
).to_string())

section("WIN RATE POR ORDEM DO DEAL NA CONTA")
print(closed_sorted.groupby(closed_sorted["deal_order"].clip(upper=10)).apply(
    lambda x: pd.Series({
        "deals": len(x),
        "win_rate": (x["deal_stage"] == "Won").mean()
    })
).to_string())

section("EFEITO 'A CONTA JÁ COMPROU' — feature mais útil")
# Para cada deal fechado, contar quantos deals Won a conta tinha ANTES daquela engage_date
def prior_wins(group):
    group = group.sort_values("engage_date")
    won_count = []
    cum = 0
    for _, row in group.iterrows():
        won_count.append(cum)
        if row["deal_stage"] == "Won":
            cum += 1
    group["prior_wins"] = won_count
    return group

closed_sorted = closed_sorted.groupby("account", group_keys=False).apply(prior_wins)
closed_sorted["had_prior_win"] = closed_sorted["prior_wins"] > 0

print("Win rate com vs sem vitória anterior na conta:")
print(closed_sorted.groupby("had_prior_win").apply(
    lambda x: pd.Series({
        "deals": len(x),
        "win_rate": (x["deal_stage"] == "Won").mean()
    })
).to_string())

print("\nWin rate por número de vitórias anteriores na conta:")
print(closed_sorted.groupby(closed_sorted["prior_wins"].clip(upper=8)).apply(
    lambda x: pd.Series({
        "deals": len(x),
        "win_rate": (x["deal_stage"] == "Won").mean()
    })
).to_string())

section("MESMO PRODUTO, MESMA CONTA: a conta já comprou ESTE produto?")
def prior_same_product_win(group):
    group = group.sort_values("engage_date")
    flag = []
    seen_products_won = set()
    for _, row in group.iterrows():
        flag.append(row["product"] in seen_products_won)
        if row["deal_stage"] == "Won":
            seen_products_won.add(row["product"])
    group["bought_this_before"] = flag
    return group

closed_sorted = closed_sorted.groupby("account", group_keys=False).apply(prior_same_product_win)
print(closed_sorted.groupby("bought_this_before").apply(
    lambda x: pd.Series({
        "deals": len(x),
        "win_rate": (x["deal_stage"] == "Won").mean()
    })
).to_string())

section("COMBINAÇÃO VENDEDOR + CONTA: vendedor que JÁ vendeu pra essa conta")
def prior_agent_account_win(group):
    group = group.sort_values("engage_date")
    flag = []
    seen = set()
    for _, row in group.iterrows():
        flag.append((row["sales_agent"], row["account"]) in seen)
        if row["deal_stage"] == "Won":
            seen.add((row["sales_agent"], row["account"]))
    group["agent_won_this_account"] = flag
    return group

closed_sorted = prior_agent_account_win(closed_sorted)
print(closed_sorted.groupby("agent_won_this_account").apply(
    lambda x: pd.Series({
        "deals": len(x),
        "win_rate": (x["deal_stage"] == "Won").mean()
    })
).to_string())

section("CLOSE VALUE: quanto tamanho da conta importa para VALOR (não para SE fecha)")
won_only = closed_sorted[closed_sorted["deal_stage"] == "Won"].dropna(subset=["revenue"]).copy()
won_only["rev_bucket"] = pd.qcut(won_only["revenue"], q=4, labels=["Q1-low", "Q2", "Q3", "Q4-high"])
print("Close value médio por quartil de receita da conta:")
print(won_only.groupby("rev_bucket", observed=True)["close_value"].agg(["mean", "median", "count"]).round(0).to_string())

section("CLOSE VALUE por produto vs sales_price (sanity check)")
print(won_only.groupby("product").agg(
    avg_close=("close_value", "mean"),
    median_close=("close_value", "median"),
    list_price=("sales_price", "first")
).round(0).to_string())
