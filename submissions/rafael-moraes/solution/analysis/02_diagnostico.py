"""Fase 2 — Diagnóstico operacional (Dataset 1).
Responde às 3 perguntas do Diretor e testa se cada diferença é distinguível de ruído.
Uso: python 02_diagnostico.py caminho/customer_support_tickets.csv
"""
import sys
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

d = pd.read_csv(sys.argv[1])
dims = ["Ticket Channel", "Ticket Priority", "Ticket Type"]
rng = np.random.default_rng(42)

print("=" * 70, "\nPERGUNTA 1 — Onde o fluxo trava?\n" + "=" * 70)
d["sem_resposta"] = d["Ticket Status"].eq("Open")          # Open = sem 1ª resposta registrada
d["nao_resolvido"] = d["Ticket Status"].ne("Closed")
print(f"Tickets: {len(d)} | sem 1ª resposta: {d.sem_resposta.sum()} ({d.sem_resposta.mean():.1%}) "
      f"| não resolvidos: {d.nao_resolvido.sum()} ({d.nao_resolvido.mean():.1%})")
crit = d[d["Ticket Priority"] == "Critical"]
print(f"Critical sem 1ª resposta: {crit.sem_resposta.sum()} de {len(crit)} ({crit.sem_resposta.mean():.1%})")

for c in dims:
    t = pd.crosstab(d[c], d["Ticket Status"])
    p = stats.chi2_contingency(t)[1]
    taxa = d.groupby(c)["nao_resolvido"].mean()
    print(f"\n{c}: % não resolvido {taxa.min():.1%}–{taxa.max():.1%} | qui-quadrado p = {p:.3f}")

# Combinações canal x prioridade x tipo: o pior grupo é pior que o acaso?
g = d.groupby(dims)["nao_resolvido"].agg(["mean", "size"])
obs_spread = g["mean"].max() - g["mean"].min()
perm = []
for _ in range(1000):
    s = d.assign(x=rng.permutation(d["nao_resolvido"].values)).groupby(dims)["x"].mean()
    perm.append(s.max() - s.min())
p_perm = (np.array(perm) >= obs_spread).mean()
print(f"\n{len(g)} combinações | pior: {g['mean'].idxmax()} = {g['mean'].max():.1%} | "
      f"melhor: {g['mean'].min():.1%}")
print(f"Amplitude observada {obs_spread:.1%} vs embaralhado (mediana) {np.median(perm):.1%} → p = {p_perm:.3f}")

# Tempo: por que não dá para medir
f = pd.to_datetime(d["First Response Time"]); r = pd.to_datetime(d["Time to Resolution"])
delta = ((r - f).dt.total_seconds() / 3600).dropna()
print(f"\nTempo: não há data de abertura; 'tempo' entre 1ª resposta e resolução é negativo em {(delta<0).mean():.1%} dos fechados")

print("\n" + "=" * 70, "\nPERGUNTA 2 — O que impacta a satisfação?\n" + "=" * 70)
c = d[d["Ticket Status"] == "Closed"].copy()
c["horas"] = ((r - f).dt.total_seconds() / 3600)[c.index]
y = c["Customer Satisfaction Rating"].astype(int)
print("Distribuição CSAT:", y.value_counts().sort_index().to_dict(), "| média", round(y.mean(), 2))
for col in dims + ["Ticket Subject", "Product Purchased", "Customer Gender"]:
    p = stats.kruskal(*[x["Customer Satisfaction Rating"] for _, x in c.groupby(col)]).pvalue
    print(f"CSAT ~ {col:20s} Kruskal p = {p:.3f}")
for col in ["horas", "Customer Age"]:
    rho, p = stats.spearmanr(c[col], y)
    print(f"CSAT ~ {col:20s} Spearman rho = {rho:+.3f}, p = {p:.3f}")

X = pd.get_dummies(c[dims + ["Ticket Subject", "Product Purchased", "Customer Gender"]]).assign(
    horas=c["horas"], idade=c["Customer Age"])
acc = cross_val_score(RandomForestClassifier(300, random_state=42, n_jobs=-1), X, y, cv=5).mean()
print(f"Modelo (Random Forest, 5-fold) prevendo a nota: acurácia {acc:.1%} vs acaso {y.value_counts(normalize=True).max():.1%}")

print("\n" + "=" * 70, "\nPERGUNTA 3 — Quanto estamos desperdiçando? (com premissas)\n" + "=" * 70)
print("O dataset não registra esforço do agente. Estimativa paramétrica — premissas a decidir pelo Rafael:")
volume_ano = 30000  # volume anual declarado no briefing
for min_triagem in (2, 4, 6):
    horas = volume_ano * min_triagem / 60
    print(f"  Triagem manual de {min_triagem} min/ticket × {volume_ano} tickets/ano = {horas:,.0f} h/ano ({horas/12:,.0f} h/mês)")
