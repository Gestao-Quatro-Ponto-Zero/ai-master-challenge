"""Diagnóstico do DS1: cortes por dimensão para as 3 perguntas do challenge (ADR-0003).

Para cada dimensão (canal, prioridade, tipo, assunto, produto):
  - fluxo: volume, % sem 1ª resposta (Open), % aguardando cliente (Pending), % fechado;
  - tempo: 1ª resposta → resolução, só em registros coerentes (resolução depois da resposta);
  - CSAT: média com IC 95%, só em tickets respondidos (Closed);
  - p-valor de cada diferença (qui-quadrado para status, Kruskal-Wallis para CSAT e tempo).
Também: o quanto TODAS as variáveis juntas explicam o CSAT (R² de um modelo linear).

Saída: tabela no terminal + solution/analysis/output/diagnostic_cuts.csv (alimenta o dashboard).
Uso: .venv/bin/python solution/analysis/02_diagnostic_cuts.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import linalg, stats

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "solution/analysis/output"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(ROOT / "data/raw/ds1_customer_support/customer_support_tickets.csv")
df["hours"] = (pd.to_datetime(df["Time to Resolution"]) - pd.to_datetime(df["First Response Time"])).dt.total_seconds() / 3600
df["coherent"] = df["hours"] >= 0
closed = df[df["Ticket Status"] == "Closed"]
CSAT = "Customer Satisfaction Rating"
DIMS = {"Ticket Channel": "canal", "Ticket Priority": "prioridade", "Ticket Type": "tipo",
        "Ticket Subject": "assunto", "Product Purchased": "produto"}

print("## Visão geral")
print(f"tickets {len(df)} | sem 1ª resposta (Open) {df['Ticket Status'].eq('Open').mean():.1%} | "
      f"aguardando cliente {df['Ticket Status'].eq('Pending Customer Response').mean():.1%} | fechados {len(closed)}")
coh = closed[closed["coherent"]]
print(f"fechados com registro coerente (resolução após 1ª resposta): {len(coh)} de {len(closed)} ({len(coh)/len(closed):.1%})")
print(f"1ª resposta → resolução (coerentes): média {coh['hours'].mean():.1f}h | mediana {coh['hours'].median():.1f}h | "
      f"p90 {coh['hours'].quantile(.9):.1f}h")
print(f"CSAT (fechados): média {closed[CSAT].mean():.2f} | IC95% {closed[CSAT].mean() - 1.96*closed[CSAT].sem():.2f}–"
      f"{closed[CSAT].mean() + 1.96*closed[CSAT].sem():.2f}")

rows, summary = [], []
for col, label in DIMS.items():
    g = df.groupby(col)
    t = pd.DataFrame({
        "n": g.size(),
        "pct_open": g["Ticket Status"].apply(lambda s: (s == "Open").mean()),
        "pct_pending": g["Ticket Status"].apply(lambda s: (s == "Pending Customer Response").mean()),
    })
    gc = closed.groupby(col)
    t["n_closed"] = gc.size()
    t["csat_mean"] = gc[CSAT].mean()
    t["csat_ci_low"] = t["csat_mean"] - 1.96 * gc[CSAT].sem()
    t["csat_ci_high"] = t["csat_mean"] + 1.96 * gc[CSAT].sem()
    gh = coh.groupby(col)["hours"]
    t["hours_median_coherent"] = gh.median()
    t["pct_incoherent"] = 1 - gc["coherent"].mean()
    p_status = stats.chi2_contingency(pd.crosstab(df[col], df["Ticket Status"]))[1]
    p_csat = stats.kruskal(*[s[CSAT] for _, s in gc]).pvalue
    p_hours = stats.kruskal(*[s for _, s in gh]).pvalue
    t.insert(0, "dimension", label)
    rows.append(t.reset_index(names="value"))
    summary.append((label, len(t), f"{t['csat_mean'].min():.2f}–{t['csat_mean'].max():.2f}", round(p_csat, 2),
                    f"{t['hours_median_coherent'].min():.1f}–{t['hours_median_coherent'].max():.1f}h", round(p_hours, 2),
                    f"{t['pct_open'].min():.0%}–{t['pct_open'].max():.0%}", round(p_status, 2)))

print("\n## Resumo por dimensão (a diferença entre grupos é real se p < 0,05)")
print(pd.DataFrame(summary, columns=["dimensão", "grupos", "CSAT (faixa)", "p CSAT", "tempo mediano (faixa)",
                                     "p tempo", "% sem resposta (faixa)", "p status"]).to_string(index=False))

out = pd.concat(rows, ignore_index=True)
out.round(4).to_csv(OUT / "diagnostic_cuts.csv", index=False)
print("\n## Exemplo — canal")
print(out[out.dimension == "canal"].drop(columns="dimension").round(2).to_string(index=False))

print("\n## O que explica o CSAT? (fechados, todas as variáveis juntas)")
X = pd.get_dummies(closed[list(DIMS) + ["Customer Gender"]], drop_first=True).astype(float)
X["age"], X["hours"] = closed["Customer Age"], closed["hours"]
X = np.column_stack([np.ones(len(X)), X.values])
y = closed[CSAT].values
beta, *_ = linalg.lstsq(X, y)
# soma elemento a elemento: o matmul do numpy no macOS (Accelerate) emite avisos espúrios aqui
fitted = (X * beta).sum(axis=1)
assert np.isfinite(fitted).all()
r2 = 1 - ((y - fitted) ** 2).sum() / ((y - y.mean()) ** 2).sum()
k = X.shape[1] - 1
adj = 1 - (1 - r2) * (len(y) - 1) / (len(y) - k - 1)
print(f"{k} variáveis | R² = {r2:.3f} | R² ajustado = {adj:.3f} (≈0 → nenhuma combinação explica a nota)")
print(f"\ncsv: {OUT.relative_to(ROOT)}/diagnostic_cuts.csv ({len(out)} linhas)")
