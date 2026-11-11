"""Existe sinal no Dataset 1? Testes de significância para as perguntas do diagnóstico.

- Independência entre todas as variáveis categóricas (qui-quadrado + V de Cramér).
- CSAT por canal / prioridade / tipo / combinação (Kruskal-Wallis + IC 95% da média).
- O que é calculável de tempo (não há timestamp de abertura do ticket).

Uso: .venv/bin/python solution/analysis/01_signal_tests.py
"""
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
df = pd.read_csv(ROOT / "data/raw/ds1_customer_support/customer_support_tickets.csv")
df["Age band"] = pd.cut(df["Customer Age"], [0, 30, 45, 60, 120])

CATS = ["Ticket Type", "Ticket Priority", "Ticket Channel", "Ticket Status",
        "Ticket Subject", "Product Purchased", "Customer Gender", "Age band"]

print("## 1. Independência entre variáveis (qui-quadrado)")
rows = []
for a, b in combinations(CATS, 2):
    ct = pd.crosstab(df[a], df[b])
    chi2, p, dof, _ = stats.chi2_contingency(ct)
    v = np.sqrt(chi2 / (ct.values.sum() * (min(ct.shape) - 1)))
    rows.append((a, b, round(p, 3), round(v, 3)))
res = pd.DataFrame(rows, columns=["A", "B", "p", "cramer_v"])
print(res.sort_values("p").to_string(index=False))
print(f"\npares com p<0,05: {(res.p < 0.05).sum()} de {len(res)} "
      f"(esperado por acaso: ~{0.05 * len(res):.1f}) | maior V de Cramér: {res.cramer_v.max()}")

closed = df[df["Ticket Status"] == "Closed"]
csat = "Customer Satisfaction Rating"
print("\n## 2. CSAT (só tickets Closed, n=%d)" % len(closed))
for g in ["Ticket Channel", "Ticket Priority", "Ticket Type", "Ticket Subject", "Age band"]:
    groups = [s[csat].values for _, s in closed.groupby(g, observed=True)]
    h, p = stats.kruskal(*groups)
    summ = closed.groupby(g, observed=True)[csat].agg(["mean", "sem", "size"])
    lo, hi = (summ["mean"] - 1.96 * summ["sem"]).min(), (summ["mean"] + 1.96 * summ["sem"]).max()
    print(f"{g:18s} Kruskal p={p:.3f} | médias {summ['mean'].min():.2f}–{summ['mean'].max():.2f} | IC95% cobre {lo:.2f}–{hi:.2f}")

combo = closed.groupby(["Ticket Channel", "Ticket Priority", "Ticket Type"])[csat].agg(["mean", "size"])
h, p = stats.kruskal(*[s[csat].values for _, s in closed.groupby(["Ticket Channel", "Ticket Priority", "Ticket Type"])])
print(f"\n80 combinações canal×prioridade×tipo: n por célula {combo['size'].min()}–{combo['size'].max()}, "
      f"médias {combo['mean'].min():.2f}–{combo['mean'].max():.2f}, Kruskal p={p:.3f}")
print("  'pior' e 'melhor' combinação (o tipo de ranking que vira ruído):")
print(combo.sort_values("mean").iloc[[0, -1]].round(2).to_string())

print("\n## 3. Tempo: o que dá para calcular")
print("colunas de data:", [c for c in df.columns if "Time" in c or "Date" in c])
print("Não há data/hora de ABERTURA do ticket → 'tempo até primeira resposta' e 'tempo até resolução' não são calculáveis.")
frt, ttr = pd.to_datetime(df["First Response Time"]), pd.to_datetime(df["Time to Resolution"])
d = ((ttr - frt).dt.total_seconds() / 3600)[df["Ticket Status"] == "Closed"]
pos = d[d >= 0]
print(f"única derivação possível: TTR−FRT → {len(pos)} positivos de {len(d)}; mediana dos positivos {pos.median():.1f}h")
h, p = stats.kruskal(*[pos[closed.loc[pos.index, "Ticket Channel"] == c] for c in closed["Ticket Channel"].unique()])
print(f"TTR−FRT (positivos) por canal: Kruskal p={p:.3f}")
print("correlação de Spearman CSAT × (TTR−FRT):", round(stats.spearmanr(closed[csat], d).statistic, 3))

print("\n## 4. Achados estruturais (com a ressalva de também serem ~1/3 cada)")
print(df["Ticket Status"].value_counts(normalize=True).round(3).to_string())
