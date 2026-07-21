"""
FASE 0 — Auditoria de integridade do Dataset 1.
Confirma (ou derruba) os 3 landmines que decidem o que é analisavel no diagnostico:
  L1. Timestamps: sao datas coerentes? Duracao (TTR - FRT) tem % negativa?
  L2. CSAT tem algum driver, ou e ruido? (ANOVA + R2 de regressao)
  L3. Canal/Prioridade/Tipo sao uniformes? (qui-quadrado de aderencia)
+ Backlog (status) e um sweep "existe QUALQUER sinal?".
"""
import pandas as pd
import numpy as np
from scipy import stats

pd.set_option("display.width", 140)
D1 = r"D:\Projetos\Case G4\data\challenge-002-support\customer_support_tickets.csv"
df = pd.read_csv(D1)


def h(t):
    print("\n" + "=" * 88 + "\n" + t + "\n" + "=" * 88)


# ---------------------------------------------------------------------------
h("BACKLOG — distribuicao de status")
st = df["Ticket Status"].value_counts()
print(st)
not_closed = st.drop("Closed").sum()
print(f"\nNao-fechados (Open + Pending): {not_closed} / {len(df)} = {not_closed/len(df)*100:.1f}%")

# ---------------------------------------------------------------------------
h("L1 — INTEGRIDADE DOS TIMESTAMPS (so tickets Closed)")
closed = df[df["Ticket Status"] == "Closed"].copy()
print(f"Tickets Closed: {len(closed)}")

frt = pd.to_datetime(closed["First Response Time"], errors="coerce")
ttr = pd.to_datetime(closed["Time to Resolution"], errors="coerce")
print(f"FRT parseados: {frt.notna().sum()} | TTR parseados: {ttr.notna().sum()}")

print(f"\nRange FRT: {frt.min()}  ->  {frt.max()}")
print(f"Range TTR: {ttr.min()}  ->  {ttr.max()}")

same_day = (frt.dt.date == ttr.dt.date)
print(f"\nFRT e TTR no MESMO DIA: {same_day.sum()} / {len(closed)} = {same_day.mean()*100:.1f}%")
print("(se ~100%, o 'tempo de resolucao' esta preso ao mesmo dia -> hora aleatoria, nao duracao real)")

delta_h = (ttr - frt).dt.total_seconds() / 3600.0
neg = (delta_h < 0)
print(f"\nDuracao (TTR - FRT) em horas:")
print(f"  negativas: {neg.sum()} / {delta_h.notna().sum()} = {neg.mean()*100:.1f}%")
print(f"  min={delta_h.min():.1f}h  mediana={delta_h.median():.1f}h  max={delta_h.max():.1f}h")
print(f"  media |delta|={delta_h.abs().mean():.1f}h")

# ---------------------------------------------------------------------------
h("L2 — CSAT TEM DRIVER? (so Closed, CSAT nao-nulo)")
c = closed[closed["Customer Satisfaction Rating"].notna()].copy()
c["dur_h"] = (pd.to_datetime(c["Time to Resolution"], errors="coerce")
              - pd.to_datetime(c["First Response Time"], errors="coerce")).dt.total_seconds()/3600.0
print(f"n = {len(c)} | CSAT media={c['Customer Satisfaction Rating'].mean():.3f} std={c['Customer Satisfaction Rating'].std():.3f}")

for col in ["Ticket Channel", "Ticket Priority", "Ticket Type"]:
    groups = [g["Customer Satisfaction Rating"].values for _, g in c.groupby(col)]
    F, p = stats.f_oneway(*groups)
    means = c.groupby(col)["Customer Satisfaction Rating"].mean().round(3).to_dict()
    print(f"\nANOVA CSAT ~ {col}: F={F:.3f} p={p:.3f}  {'<-- SIGNIFICATIVO' if p < 0.05 else '(nulo)'}")
    print(f"   medias: {means}")

rho, prho = stats.spearmanr(c["dur_h"], c["Customer Satisfaction Rating"], nan_policy="omit")
print(f"\nSpearman CSAT vs duracao: rho={rho:.3f} p={prho:.3f}  {'<-- SIGNIFICATIVO' if prho < 0.05 else '(nulo)'}")

# R2 de regressao linear com todos os fatores (one-hot)
X = pd.get_dummies(c[["Ticket Channel", "Ticket Priority", "Ticket Type"]], drop_first=True).astype(float)
X["dur_h"] = c["dur_h"].fillna(c["dur_h"].median()).values
y = c["Customer Satisfaction Rating"].values
Xb = np.column_stack([np.ones(len(X)), X.values])
beta, *_ = np.linalg.lstsq(Xb, y, rcond=None)
yhat = Xb @ beta
ss_res = ((y - yhat) ** 2).sum()
ss_tot = ((y - y.mean()) ** 2).sum()
r2 = 1 - ss_res / ss_tot
print(f"\nR2 (CSAT ~ canal+prioridade+tipo+duracao): {r2:.4f}")
print("(R2 ~ 0 => nenhuma variavel capturada explica satisfacao)")

# ---------------------------------------------------------------------------
h("L3 — UNIFORMIDADE (qui-quadrado de aderencia a uniforme)")
for col in ["Ticket Type", "Ticket Priority", "Ticket Channel"]:
    obs = df[col].value_counts().sort_index()
    exp = np.full(len(obs), len(df)/len(obs))
    chi2, p = stats.chisquare(obs.values, exp)
    print(f"\n{col}: chi2={chi2:.2f} p={p:.3f}  {'<-- NAO-uniforme (ha concentracao)' if p < 0.05 else '-> compativel com UNIFORME (sem concentracao real)'}")
    print(f"   {obs.to_dict()}")

h("FIM FASE 0")
