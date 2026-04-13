"""Tempo no pipeline: ganhos vs perdidos vs abertos."""
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

# Para Won/Lost: duração = close - engage
closed = df[df["deal_stage"].isin(["Won", "Lost"])].copy()
closed["duration_days"] = (closed["close_date"] - closed["engage_date"]).dt.days

def section(t):
    print("\n" + "=" * 78); print(t); print("=" * 78)

section("DURAÇÃO DOS DEALS FECHADOS — Won vs Lost")
print(closed.groupby("deal_stage")["duration_days"].describe().round(1))

section("DURAÇÃO POR PRODUTO (Won vs Lost)")
g = closed.groupby(["product", "deal_stage"])["duration_days"].agg(["mean", "median", "count"]).round(1)
print(g.to_string())

section("DURAÇÃO POR PRODUTO — Won vs Lost lado a lado")
piv = closed.pivot_table(index="product", columns="deal_stage", values="duration_days",
                         aggfunc="median").round(1)
print(piv.to_string())
print("\n→ Lost demoram MAIS ou MENOS que Won?")
print((piv["Lost"] - piv["Won"]).round(1).rename("lost-won (median)").to_string())

section("DEALS ABERTOS — quanto tempo já estão no pipeline?")
# Engaging: tem engage_date mas não close_date. Idade = max(engage_date) - engage_date
# Como referência usamos a última data observada nos dados (snapshot)
ref_date = pipe["close_date"].max()
print(f"snapshot date (última close_date no dataset): {ref_date.date()}")
print(f"última engage_date: {pipe['engage_date'].max().date()}")

eng = df[df["deal_stage"] == "Engaging"].copy()
eng["age_days"] = (ref_date - eng["engage_date"]).dt.days
print(f"\nEngaging: {len(eng)} deals")
print(eng["age_days"].describe().round(1))

section("ENGAGING vs duração média de Won — quem já está em risco?")
# Para cada produto, comparar age do engaging com mediana/p75/p90 do Won
won = closed[closed["deal_stage"] == "Won"].groupby("product")["duration_days"].agg(
    won_median="median", won_p75=lambda x: x.quantile(0.75), won_p90=lambda x: x.quantile(0.9)
).round(1)
print("Estatísticas Won por produto:")
print(won.to_string())

eng_with_won = eng.merge(won, on="product", how="left")
eng_with_won["status"] = "ok"
eng_with_won.loc[eng_with_won["age_days"] > eng_with_won["won_median"], "status"] = "atencao"
eng_with_won.loc[eng_with_won["age_days"] > eng_with_won["won_p75"], "status"] = "alerta"
eng_with_won.loc[eng_with_won["age_days"] > eng_with_won["won_p90"], "status"] = "frio"

print("\nDeals Engaging classificados por idade vs Won histórico do mesmo produto:")
print(eng_with_won["status"].value_counts().to_string())
print(f"\n→ {(eng_with_won['status'] != 'ok').sum()} de {len(eng_with_won)} deals Engaging "
      f"({(eng_with_won['status'] != 'ok').mean():.0%}) já estão acima do tempo típico de Won")

section("DEALS LOST — eles morrem RÁPIDO ou DEMORAM?")
# Hipótese: se Lost demora mais que Won, idade alta é forte sinal de perda
print("Mediana Won:", closed[closed["deal_stage"] == "Won"]["duration_days"].median())
print("Mediana Lost:", closed[closed["deal_stage"] == "Lost"]["duration_days"].median())
print("p25 Won:", closed[closed["deal_stage"] == "Won"]["duration_days"].quantile(0.25))
print("p75 Won:", closed[closed["deal_stage"] == "Won"]["duration_days"].quantile(0.75))
print("p25 Lost:", closed[closed["deal_stage"] == "Lost"]["duration_days"].quantile(0.25))
print("p75 Lost:", closed[closed["deal_stage"] == "Lost"]["duration_days"].quantile(0.75))

section("WIN RATE POR FAIXA DE DURAÇÃO")
# Bucket por faixas de dias
closed["dur_bucket"] = pd.cut(closed["duration_days"],
                              bins=[-1, 30, 60, 90, 120, 365],
                              labels=["≤30d", "31-60d", "61-90d", "91-120d", ">120d"])
wr = closed.groupby("dur_bucket", observed=True).apply(
    lambda x: pd.Series({
        "deals": len(x),
        "win_rate": (x["deal_stage"] == "Won").mean()
    })
)
print(wr.to_string())

section("PROSPECTING — característica")
prosp = df[df["deal_stage"] == "Prospecting"]
print(f"deals: {len(prosp)}")
print(f"sem account: {prosp['account'].isna().sum()} de {len(prosp)}")
print(f"sem engage_date: {prosp['engage_date'].isna().sum()} de {len(prosp)}")
print("\n→ Prospecting puro = ainda não engajou. Não tem account porque o vendedor")
print("  ainda nem identificou a empresa-alvo. Score deve tratar diferente.")
