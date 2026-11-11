"""Perfil inicial dos dois datasets do Challenge 002.

Objetivo: verificar a qualidade e a estrutura dos dados ANTES de qualquer diagnóstico.
Os números de context/data-findings.md saem deste script.

Uso: .venv/bin/python solution/analysis/00_data_profile.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DS1 = ROOT / "data/raw/ds1_customer_support/customer_support_tickets.csv"
DS2 = ROOT / "data/raw/ds2_it_tickets/all_tickets_processed_improved_v3.csv"


def section(title: str) -> None:
    print(f"\n## {title}")


df = pd.read_csv(DS1)
it = pd.read_csv(DS2)

section("DS1 — volume e nulos")
print("tickets:", len(df), "| linhas físicas no CSV:", sum(1 for _ in open(DS1, encoding="utf-8")))
print(df.isna().sum()[lambda s: s > 0].to_string())

section("DS1 — distribuições categóricas")
for col in ["Ticket Type", "Ticket Status", "Ticket Priority", "Ticket Channel", "Customer Gender"]:
    print(f"\n{col}:\n" + df[col].value_counts().to_string())
print("\nprodutos distintos:", df["Product Purchased"].nunique(), "| assuntos distintos:", df["Ticket Subject"].nunique())

section("DS1 — onde existem métricas")
print(df.groupby("Ticket Status")[["First Response Time", "Time to Resolution", "Customer Satisfaction Rating", "Resolution"]]
      .apply(lambda g: g.notna().mean()).round(2).to_string())

section("DS1 — tempos (são timestamps, não durações)")
frt = pd.to_datetime(df["First Response Time"])
ttr = pd.to_datetime(df["Time to Resolution"])
print("janela FRT:", frt.min(), "→", frt.max())
print("janela TTR:", ttr.min(), "→", ttr.max())
delta_h = ((ttr - frt).dt.total_seconds() / 3600).dropna()
print(f"TTR - FRT (h), n={len(delta_h)}: min={delta_h.min():.1f} mediana={delta_h.median():.2f} "
      f"média={delta_h.mean():.2f} max={delta_h.max():.1f}")
print(f"resolução ANTES da primeira resposta: {(delta_h < 0).sum()} ({(delta_h < 0).mean():.1%})")

section("DS1 — CSAT")
print(df["Customer Satisfaction Rating"].value_counts().sort_index().to_string())
closed = df[df["Ticket Status"] == "Closed"].assign(delta_h=delta_h)
for g in ["Ticket Channel", "Ticket Priority", "Ticket Type"]:
    print(f"\nCSAT médio por {g}:\n" + closed.groupby(g)["Customer Satisfaction Rating"].mean().round(2).to_string())
print("\ncorrelação CSAT x (TTR-FRT):", round(closed["Customer Satisfaction Rating"].corr(closed["delta_h"]), 3))
print("correlação CSAT x idade:", round(closed["Customer Satisfaction Rating"].corr(closed["Customer Age"]), 3))

section("DS1 — sinais de dado sintético")
print("descrições com placeholder {product_purchased}:",
      f"{df['Ticket Description'].str.contains('{product_purchased}', regex=False).mean():.0%}")
print("resoluções distintas / não nulas:", df["Resolution"].nunique(), "/", df["Resolution"].notna().sum())
print("amostra de resoluções:\n" + df["Resolution"].dropna().sample(4, random_state=1).to_string())
print("\nassunto x tipo (assunto deveria determinar o tipo?):")
print(pd.crosstab(df["Ticket Subject"], df["Ticket Type"]).head(4).to_string())

section("DS2 — volume, classes e texto")
print("documentos:", len(it), "| duplicados:", it["Document"].duplicated().sum())
vc = it["Topic_group"].value_counts()
print(pd.DataFrame({"n": vc, "share": (vc / len(it)).round(3)}).to_string())
print("\npalavras por documento:\n" + it["Document"].str.split().str.len().describe().round(1).to_string())
