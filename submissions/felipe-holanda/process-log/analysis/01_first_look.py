"""Etapa 1 — Primeira olhada: estrutura, qualidade e o que é pipeline aberto.

Rodado com: python3 01_first_look.py > 01_first_look.out.txt
"""
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parents[2] / "solution" / "data"
pd.set_option("display.width", 200)

p = pd.read_csv(DATA / "sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
a = pd.read_csv(DATA / "accounts.csv")
t = pd.read_csv(DATA / "sales_teams.csv")
pr = pd.read_csv(DATA / "products.csv")

print("=== Estágios ===")
print(p.deal_stage.value_counts())
print("\n=== Nulos por estágio ===")
print(p.isna().groupby(p.deal_stage).sum().to_string())
print("\n=== Integridade das chaves ===")
print("produtos no pipeline que não existem no catálogo:", set(p["product"]) - set(pr["product"]))
print("vendedores sem nenhum deal:", sorted(set(t.sales_agent) - set(p.sales_agent)))
print("contas do pipeline fora da tabela de contas:", set(p.account.dropna()) - set(a.account))
print("setores:", sorted(a.sector.unique()))
print("\n=== Datas ===")
print("engage:", p.engage_date.min().date(), "->", p.engage_date.max().date())
print("close: ", p.close_date.min().date(), "->", p.close_date.max().date())
print("\n=== Valor ===")
print(pr.sort_values("sales_price").to_string(index=False))
print("razão maior/menor preço:", round(pr.sales_price.max() / pr.sales_price.min(), 1))
print(p.groupby("deal_stage").close_value.describe().to_string())
print("\n=== Time ===")
print(t.groupby(["regional_office", "manager"]).size().to_string())
