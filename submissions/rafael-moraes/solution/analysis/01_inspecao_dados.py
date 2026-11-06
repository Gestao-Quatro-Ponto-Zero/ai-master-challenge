"""Fase 1 — Inspeção de qualidade dos datasets (antes de qualquer diagnóstico).
Uso: python 01_inspecao_dados.py caminho/customer_support_tickets.csv caminho/all_tickets_processed_improved_v3.csv
"""
import sys
import pandas as pd
from scipy import stats

d1 = pd.read_csv(sys.argv[1])
d2 = pd.read_csv(sys.argv[2])
print("Dataset 1:", d1.shape, "| Dataset 2:", d2.shape)

# Distribuições categóricas (uniformes = sinal de dado sintético)
for c in ["Ticket Type", "Ticket Status", "Ticket Priority", "Ticket Channel"]:
    print(c, d1[c].value_counts().to_dict())

# Textos com placeholders de template não preenchidos
print("Descrições com '{product_purchased}':",
      round(d1["Ticket Description"].str.contains("{product_purchased}", regex=False).mean() * 100, 1), "%")

# Campos de tempo são timestamps, não durações; não existe data de abertura do ticket
f = pd.to_datetime(d1["First Response Time"])
r = pd.to_datetime(d1["Time to Resolution"])
print("Janela de timestamps:", min(f.min(), r.min()), "->", max(f.max(), r.max()))
delta = ((r - f).dt.total_seconds() / 3600).dropna()
print("Fechados com resolução ANTES da 1ª resposta:", round((delta < 0).mean() * 100, 1), "%")

# Coerência tipo x assunto
print("Tipo x Assunto, qui-quadrado p =", round(stats.chi2_contingency(pd.crosstab(d1["Ticket Type"], d1["Ticket Subject"]))[1], 3))

# O que explica a satisfação? (só existe em tickets Closed)
c = d1[d1["Ticket Status"] == "Closed"]
print("CSAT:", c["Customer Satisfaction Rating"].value_counts().sort_index().to_dict())
for g in ["Ticket Channel", "Ticket Priority", "Ticket Type", "Ticket Subject", "Product Purchased"]:
    p = stats.kruskal(*[x["Customer Satisfaction Rating"].values for _, x in c.groupby(g)]).pvalue
    print(f"CSAT ~ {g}: Kruskal p = {p:.3f}")

# Dataset 2
print("DS2 nulos:", d2.isna().sum().sum(), "| duplicados:", d2.Document.duplicated().sum())
print(d2.Topic_group.value_counts().to_dict())
