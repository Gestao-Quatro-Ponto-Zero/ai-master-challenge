"""Etapa 2 — Quais features têm sinal de verdade?

Pergunta: antes de construir um score, quais variáveis separam Won de Lost
mais do que o acaso? Rodado com: python3 02_signal_tests.py > 02_signal_tests.out.txt
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, mannwhitneyu

DATA = Path(__file__).resolve().parents[2] / "solution" / "data"
pd.set_option("display.width", 200)

p = pd.read_csv(DATA / "sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
p["product"] = p["product"].replace({"GTXPro": "GTX Pro"})
a = pd.read_csv(DATA / "accounts.csv")
t = pd.read_csv(DATA / "sales_teams.csv")
pr = pd.read_csv(DATA / "products.csv")
d = p.merge(t, on="sales_agent", how="left").merge(pr, on="product", how="left").merge(a, on="account", how="left")
c = d[d.deal_stage.isin(["Won", "Lost"])].copy()
c["won"] = (c.deal_stage == "Won").astype(int)
c["days"] = (c.close_date - c.engage_date).dt.days
c["rev_bin"] = pd.qcut(c.revenue, 4, labels=["Q1", "Q2", "Q3", "Q4"])
c["emp_bin"] = pd.qcut(c.employees, 4, labels=["Q1", "Q2", "Q3", "Q4"])
c["is_sub"] = c.subsidiary_of.notna()
c["us"] = c.office_location == "United States"
c["engage_q_pos"] = ((c.engage_date.dt.month - 1) % 3)  # 0,1,2 = mês dentro do trimestre
c["close_q_end"] = c.close_date.dt.month.isin([3, 6, 9, 12])

print("=== 1. Teste qui-quadrado: feature x (Won/Lost) ===")
print("p < 0.05 = há sinal estatístico; spread = maior win rate - menor win rate entre grupos (n>=30)\n")
rows = []
for col in ["deal_stage_dummy", "product", "series", "regional_office", "manager", "sales_agent", "sector",
            "account", "office_location", "rev_bin", "emp_bin", "is_sub", "us", "engage_q_pos", "close_q_end"]:
    if col not in c:
        continue
    ct = pd.crosstab(c[col], c.won)
    chi, pv, dof, _ = chi2_contingency(ct)
    g = c.groupby(col, observed=True).won.agg(["mean", "count"])
    g = g[g["count"] >= 30]
    rows.append((col, ct.shape[0], round(pv, 4), round(g["mean"].max() - g["mean"].min(), 3)))
print(pd.DataFrame(rows, columns=["feature", "grupos", "p_valor", "spread_wr"]).sort_values("p_valor").to_string(index=False))

print("\n=== 2. Duração do ciclo (dias engage->close) ===")
print(c.groupby("won").days.describe())
print("Mann-Whitney won vs lost:", mannwhitneyu(c[c.won == 1].days, c[c.won == 0].days).pvalue)
print("\nP(win | deal ainda aberto após X dias)  — curva de sobrevivência empírica")
for x in [0, 7, 14, 21, 30, 60, 90, 120, 130, 138]:
    s = c[c.days > x]
    print(f"  > {x:3d} dias: n={len(s):5d}  win_rate={s.won.mean() if len(s) else float('nan'):.3f}")
print("Maior ciclo observado em TODO o histórico:", c.days.max(), "dias")

print("\n=== 3. Efeito fim de trimestre (mês de fechamento) ===")
print(c.groupby(c.close_date.dt.to_period("M")).won.agg(["mean", "count"]).to_string())

print("\n=== 4. Agente x produto (interação) ===")
ap = c.groupby(["sales_agent", "product"]).won.agg(["mean", "count"])
ap = ap[ap["count"] >= 20]
print("combinações com n>=20:", len(ap), " spread:", round(ap["mean"].max() - ap["mean"].min(), 3))
print("desvio padrão observado:", round(ap["mean"].std(), 3),
      " desvio esperado só por ruído (binomial):", round(np.sqrt(0.63 * 0.37 / ap["count"]).mean(), 3))

print("\n=== 5. Conta: histórico prévio prediz? (temporal, sem vazamento) ===")
c = c.sort_values("close_date")
prior = []
for _, r in c.iterrows():
    h = c[(c.account == r.account) & (c.close_date < r.engage_date)]
    prior.append(h.won.mean() if len(h) >= 5 else np.nan)
c["acct_prior_wr"] = prior
cc = c.dropna(subset=["acct_prior_wr"])
print("deals com >=5 deals prévios fechados na conta:", len(cc))
print("corr(prior_wr_conta, won):", round(cc[["acct_prior_wr", "won"]].corr().iloc[0, 1], 4))

print("\n=== 6. Carga do vendedor no momento do engage ===")
allp = d.copy()
loads = []
for _, r in c.iterrows():
    ag = allp[allp.sales_agent == r.sales_agent]
    open_then = ((ag.engage_date <= r.engage_date) & ((ag.close_date.isna()) | (ag.close_date > r.engage_date))).sum()
    loads.append(open_then)
c["load"] = loads
c["load_bin"] = pd.qcut(c.load, 4)
print(c.groupby("load_bin", observed=True).won.agg(["mean", "count"]))

print("\n=== 7. Valor realizado vs preço de lista (Won) ===")
w = c[c.won == 1]
print((w.close_value / w.sales_price).describe())

print("\n=== 8. Pipeline aberto ===")
o = d[d.deal_stage.isin(["Engaging", "Prospecting"])].copy()
snap = d.close_date.max()
o["age"] = (snap - o.engage_date).dt.days
print("data de referência (último evento no CRM):", snap.date())
print(o.deal_stage.value_counts())
print("sem conta preenchida:", o.account.isna().sum(), "de", len(o))
print("Engaging mais velhos que o maior ciclo já observado (138d):", (o.age > 138).sum(), "de", (o.deal_stage == "Engaging").sum())
print("valor de lista em aberto (US$):", int(o.sales_price.sum()))
print("valor de lista em aberto em deals > 138d:", int(o[o.age > 138].sales_price.sum()))
