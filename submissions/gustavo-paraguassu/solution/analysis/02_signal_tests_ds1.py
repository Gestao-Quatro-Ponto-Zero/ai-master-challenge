"""02 — Existe sinal operacional no Dataset 1?

Testa, com estatística e com permutação, se as variáveis de gargalo e de satisfação
carregam alguma informação. Se o dataset for ruído, qualquer "gargalo" encontrado
nele é artefato de comparações múltiplas.

Uso: python 02_signal_tests_ds1.py <caminho/customer_support_tickets.csv>
"""
import sys
import itertools
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import make_pipeline

rng = np.random.default_rng(42)
df = pd.read_csv(sys.argv[1])
frt = pd.to_datetime(df["First Response Time"], errors="coerce")
ttr = pd.to_datetime(df["Time to Resolution"], errors="coerce")
df["delta_h"] = (ttr - frt).dt.total_seconds() / 3600
df["frt_hour"] = frt.dt.hour
CATS = ["Ticket Type", "Ticket Subject", "Ticket Priority", "Ticket Channel",
        "Ticket Status", "Customer Gender", "Product Purchased"]


def cramers_v(a, b):
    ct = pd.crosstab(a, b)
    chi2, p, dof, _ = stats.chi2_contingency(ct)
    n = ct.values.sum()
    v = np.sqrt(chi2 / (n * (min(ct.shape) - 1)))
    return chi2, p, v


print("== 1. Associação entre variáveis categóricas (todas as combinações)")
rows = []
for a, b in itertools.combinations(CATS, 2):
    chi2, p, v = cramers_v(df[a], df[b])
    rows.append((a, b, round(v, 3), round(p, 3)))
assoc = pd.DataFrame(rows, columns=["var_a", "var_b", "cramers_v", "p"]).sort_values("cramers_v", ascending=False)
print(assoc.to_string(index=False))
print(f"pares com p<0.05: {(assoc.p < 0.05).sum()} de {len(assoc)} (esperado por acaso: {0.05*len(assoc):.1f})")

print("\n== 1b. Ticket Type x Ticket Subject (deveriam ser fortemente ligados num dado real)")
print(pd.crosstab(df["Ticket Subject"], df["Ticket Type"]).to_string())

closed = df[df["Ticket Status"] == "Closed"].copy()
y = closed["Customer Satisfaction Rating"]
print(f"\n== 2. Satisfação (n={len(closed)} tickets fechados)")
for c in ["Ticket Type", "Ticket Subject", "Ticket Priority", "Ticket Channel",
          "Customer Gender", "Product Purchased"]:
    groups = [g["Customer Satisfaction Rating"].values for _, g in closed.groupby(c)]
    h, p = stats.kruskal(*groups)
    m = closed.groupby(c)["Customer Satisfaction Rating"].mean()
    print(f"{c:18s} Kruskal p={p:.3f} | média min={m.min():.2f} ({m.idxmin()}) max={m.max():.2f} ({m.idxmax()})")
for c in ["Customer Age", "delta_h", "frt_hour"]:
    r, p = stats.spearmanr(closed[c], y, nan_policy="omit")
    print(f"{c:18s} Spearman rho={r:+.3f} p={p:.3f}")

print("\n== 3. Dá pra PREVER satisfação? (5-fold CV)")
feat_cat = ["Ticket Type", "Ticket Subject", "Ticket Priority", "Ticket Channel",
            "Customer Gender", "Product Purchased"]
feat_num = ["Customer Age", "delta_h", "frt_hour"]
X = closed[feat_cat + feat_num]
pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), feat_cat)], remainder="passthrough")
cv = StratifiedKFold(5, shuffle=True, random_state=0)
for name, model in [("logistic", LogisticRegression(max_iter=2000)),
                    ("grad_boost", HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05))]:
    acc = cross_val_score(make_pipeline(pre, model), X, y.astype(int), cv=cv, scoring="accuracy")
    print(f"{name:10s} acurácia={acc.mean():.3f} ± {acc.std():.3f}  (chute = {y.value_counts(normalize=True).max():.3f})")
# CSAT alto (4-5) vs baixo (1-2) — versão binária, mais fácil
yb = (y >= 4).astype(int)
auc = cross_val_score(make_pipeline(pre, HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05)),
                      X, yb, cv=cv, scoring="roc_auc")
print(f"grad_boost CSAT>=4 AUC={auc.mean():.3f} ± {auc.std():.3f}  (chute = 0.500)")

print("\n== 4. 'Tempo de resolução' respeita prioridade? (num suporte real, Critical < Low)")
pos = closed[closed["delta_h"] > 0]
print("delta_h (só positivos) por prioridade:")
print(pos.groupby("Ticket Priority")["delta_h"].describe()[["count", "mean", "50%"]].round(2))
print("Kruskal p =", round(stats.kruskal(*[g.delta_h for _, g in pos.groupby("Ticket Priority")]).pvalue, 3))

print("\n== 5. Armadilha das comparações múltiplas: 'piores combinações' canal x prioridade x tipo")
keys = ["Ticket Channel", "Ticket Priority", "Ticket Type"]


def spread(d, col):
    m = d.groupby(keys)[col].agg(["mean", "size"])
    m = m[m["size"] >= 20]
    return m["mean"].max() - m["mean"].min(), m


obs_spread, cells = spread(pos, "delta_h")
print(f"células com n>=20: {len(cells)} | pior-melhor observado = {obs_spread:.2f}h")
print("3 'piores' combinações (o que um relatório ingênuo apontaria como gargalo):")
print(cells.sort_values("mean", ascending=False).head(3).round(2).to_string())
null = []
tmp = pos.copy()
for _ in range(500):
    tmp["delta_h"] = rng.permutation(pos["delta_h"].values)
    null.append(spread(tmp, "delta_h")[0])
null = np.array(null)
print(f"mesmo cálculo com tempos EMBARALHADOS (500x): mediana={np.median(null):.2f}h, "
      f"p(spread>=observado)={np.mean(null >= obs_spread):.2f}")

obs_c, cells_c = spread(closed, "Customer Satisfaction Rating")
null_c = []
tmp = closed.copy()
for _ in range(500):
    tmp["Customer Satisfaction Rating"] = rng.permutation(closed["Customer Satisfaction Rating"].values)
    null_c.append(spread(tmp, "Customer Satisfaction Rating")[0])
print(f"CSAT: pior-melhor observado = {obs_c:.2f} pts | embaralhado: mediana={np.median(null_c):.2f}, "
      f"p={np.mean(np.array(null_c) >= obs_c):.2f}")

print("\n== 6. Uniformidade (assinatura de gerador aleatório)")
for c in ["Ticket Type", "Ticket Priority", "Ticket Channel", "Ticket Status"]:
    obs = df[c].value_counts().values
    print(f"{c:16s} chi2 vs uniforme p={stats.chisquare(obs).pvalue:.3f}")
print("CSAT 1..5       chi2 vs uniforme p=%.3f" % stats.chisquare(y.value_counts().values).pvalue)
age = df["Customer Age"]
# Idade é inteira (discreta): KS não se aplica (dava p=0.000, falso alarme — ver process-log E1).
# Qui-quadrado sobre a contagem de cada idade inteira no intervalo observado.
age_counts = age.value_counts().reindex(range(age.min(), age.max() + 1), fill_value=0).values
print(f"Idade: min={age.min()} max={age.max()} chi2 vs uniforme (discreta) p="
      f"{stats.chisquare(age_counts).pvalue:.3f}")
