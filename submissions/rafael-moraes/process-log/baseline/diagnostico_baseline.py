"""
Challenge 002 — Diagnóstico operacional (Dataset 1: Customer Support Ticket Dataset)
Uso: python diagnostico.py caminho/para/customer_support_tickets.csv
"""
import sys, json
import numpy as np
import pandas as pd
from scipy import stats

path = sys.argv[1]
df = pd.read_csv(path)
for c in ["First Response Time", "Time to Resolution", "Date of Purchase"]:
    df[c] = pd.to_datetime(df[c])

out = {}
P = lambda *a: print(*a)

# ---------------------------------------------------------------- 0. Qualidade dos dados
P("=" * 70, "\n0. QUALIDADE DOS DADOS\n" + "=" * 70)
n = len(df)
out["n"] = n
P("Registros:", n)
P("Status:\n", df["Ticket Status"].value_counts().to_string())
closed = df[df["Ticket Status"] == "Closed"].copy()
closed["res_h"] = (closed["Time to Resolution"] - closed["First Response Time"]).dt.total_seconds() / 3600
neg = (closed["res_h"] < 0).mean()
out["neg_share"] = neg
P(f"Fechados com resolução ANTES da 1a resposta: {neg:.1%}")
P("Janela de First Response Time:", df["First Response Time"].min(), "->", df["First Response Time"].max())
P("Janela de Time to Resolution:", df["Time to Resolution"].min(), "->", df["Time to Resolution"].max())
P("Descrições com placeholder '{product_purchased}':", f"{df['Ticket Description'].str.contains('{product_purchased}', regex=False).mean():.1%}")
P("CSAT preenchido só em Closed:", df.loc[df['Customer Satisfaction Rating'].notna(), 'Ticket Status'].unique())
P("Distribuição CSAT:\n", closed["Customer Satisfaction Rating"].value_counts().sort_index().to_string())
chi = stats.chisquare(closed["Customer Satisfaction Rating"].value_counts().values)
out["csat_uniform_p"] = chi.pvalue
P(f"Teste de uniformidade do CSAT (qui²): p={chi.pvalue:.3f}")

# Duração utilizável: só fechados com duração positiva
v = closed[closed["res_h"] > 0].copy()
out["n_valid"] = len(v)
P("Fechados com duração válida (>0):", len(v))

# ---------------------------------------------------------------- 1. Onde o fluxo trava
P("\n" + "=" * 70, "\n1. ONDE O FLUXO TRAVA\n" + "=" * 70)

# 1a. Funil / backlog
funnel = df["Ticket Status"].value_counts(normalize=True)
out["funnel"] = funnel.to_dict()
P("Funil (share):\n", funnel.round(3).to_string())

for dim in ["Ticket Channel", "Ticket Priority", "Ticket Type"]:
    t = pd.crosstab(df[dim], df["Ticket Status"], normalize="index").round(3)
    t["n"] = df[dim].value_counts()
    P(f"\nStatus por {dim}:\n", t.to_string())
    ch = stats.chi2_contingency(pd.crosstab(df[dim], df["Ticket Status"]))
    P(f"  qui² independência status x {dim}: p={ch.pvalue:.3f}")
    out[f"status_p_{dim}"] = ch.pvalue

# 1b. Tempo de resolução por dimensão
P(f"\nTempo de resolução (h) — fechados válidos, n={len(v)}: mediana {v.res_h.median():.2f}, média {v.res_h.mean():.2f}, p90 {v.res_h.quantile(.9):.2f}")
out["res_median"] = v.res_h.median(); out["res_mean"] = v.res_h.mean()
for dim in ["Ticket Channel", "Ticket Priority", "Ticket Type", "Ticket Subject"]:
    g = v.groupby(dim)["res_h"].agg(["count", "mean", "median"]).sort_values("mean", ascending=False).round(2)
    kw = stats.kruskal(*[x["res_h"].values for _, x in v.groupby(dim)])
    P(f"\nResolução por {dim} (Kruskal p={kw.pvalue:.3f}):\n", g.to_string())
    out[f"res_kw_{dim}"] = kw.pvalue

# Prioridade: SLA invertido?
P("\nPrioridade — média resolução (h):", v.groupby("Ticket Priority")["res_h"].mean().round(2).to_dict())

# 1c. Combinações canal x prioridade x tipo (n>=15)
combo = (v.groupby(["Ticket Channel", "Ticket Priority", "Ticket Type"])["res_h"]
           .agg(["count", "mean", "median"]).query("count>=15").sort_values("mean", ascending=False))
P("\nTop 10 piores combinações (n>=15):\n", combo.head(10).round(2).to_string())
P("\nTop 5 melhores combinações:\n", combo.tail(5).round(2).to_string())
out["combo_worst"] = combo.head(5).round(2).reset_index().to_dict("records")
out["combo_best"] = combo.tail(3).round(2).reset_index().to_dict("records")

# Teste de permutação: a dispersão entre combinações é maior que o acaso?
rng = np.random.default_rng(42)
keys = ["Ticket Channel", "Ticket Priority", "Ticket Type"]
real_spread = combo["mean"].max() - combo["mean"].min()
spreads = []
tmp = v[keys + ["res_h"]].copy()
for _ in range(500):
    tmp["res_h"] = rng.permutation(tmp["res_h"].values)
    cc = tmp.groupby(keys)["res_h"].agg(["count", "mean"]).query("count>=15")
    spreads.append(cc["mean"].max() - cc["mean"].min())
perm_p = (np.array(spreads) >= real_spread).mean()
out["combo_spread"] = real_spread; out["combo_perm_p"] = perm_p
P(f"\nAmplitude real pior-melhor combinação: {real_spread:.2f}h | p (permutação, 500x) = {perm_p:.3f}")

# ---------------------------------------------------------------- 2. O que impacta satisfação
P("\n" + "=" * 70, "\n2. O QUE IMPACTA SATISFAÇÃO\n" + "=" * 70)
cs = v.copy()
P(f"CSAT médio (fechados): {closed['Customer Satisfaction Rating'].mean():.2f}")
out["csat_mean"] = closed["Customer Satisfaction Rating"].mean()
for dim in ["Ticket Channel", "Ticket Priority", "Ticket Type", "Ticket Subject", "Customer Gender", "Product Purchased"]:
    g = closed.groupby(dim)["Customer Satisfaction Rating"].mean()
    kw = stats.kruskal(*[x["Customer Satisfaction Rating"].values for _, x in closed.groupby(dim)])
    P(f"CSAT por {dim}: min {g.min():.2f} ({g.idxmin()}) | max {g.max():.2f} ({g.idxmax()}) | Kruskal p={kw.pvalue:.3f}")
    out[f"csat_kw_{dim}"] = (round(g.min(), 2), g.idxmin(), round(g.max(), 2), g.idxmax(), kw.pvalue)
r = stats.spearmanr(cs["res_h"], cs["Customer Satisfaction Rating"])
P(f"Spearman tempo de resolução x CSAT: rho={r.statistic:.3f}, p={r.pvalue:.3f}")
out["csat_rho_res"] = (r.statistic, r.pvalue)
r2 = stats.spearmanr(closed["Customer Age"], closed["Customer Satisfaction Rating"])
P(f"Spearman idade x CSAT: rho={r2.statistic:.3f}, p={r2.pvalue:.3f}")
cs["fast"] = pd.qcut(cs["res_h"], 4, labels=["Q1 rápido", "Q2", "Q3", "Q4 lento"])
P("CSAT por quartil de tempo de resolução:", cs.groupby("fast", observed=True)["Customer Satisfaction Rating"].mean().round(2).to_dict())
out["csat_by_quartile"] = cs.groupby("fast", observed=True)["Customer Satisfaction Rating"].mean().round(2).to_dict()
P("% CSAT<=2 (detratores):", f"{(closed['Customer Satisfaction Rating']<=2).mean():.1%}")
out["detractors"] = (closed["Customer Satisfaction Rating"] <= 2).mean()

# Modelo: o conjunto de variáveis explica o CSAT?
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score
X = pd.get_dummies(cs[["Ticket Channel", "Ticket Priority", "Ticket Type", "Ticket Subject", "Customer Gender", "Product Purchased"]])
X["res_h"] = cs["res_h"].values; X["age"] = cs["Customer Age"].values
X["desc_len"] = cs["Ticket Description"].str.len().values
y = cs["Customer Satisfaction Rating"].values
r2s = cross_val_score(GradientBoostingRegressor(random_state=0), X, y, cv=5, scoring="r2")
acc = cross_val_score(RandomForestClassifier(300, random_state=0, n_jobs=-1), X, (y >= 4).astype(int), cv=5, scoring="roc_auc")
P(f"GBM R² (5-fold): {r2s.mean():.3f} | RF AUC satisfeito(>=4): {acc.mean():.3f}")
out["csat_r2"] = r2s.mean(); out["csat_auc"] = acc.mean()

# ---------------------------------------------------------------- 3. Desperdício
P("\n" + "=" * 70, "\n3. QUANTO ESTAMOS DESPERDIÇANDO\n" + "=" * 70)
pending = (df["Ticket Status"] == "Pending Customer Response").sum()
openn = (df["Ticket Status"] == "Open").sum()
generic = df["Ticket Description"].str.startswith("I'm having an issue with the {product_purchased}. Please assist.").sum()
out.update(pending=int(pending), open=int(openn), generic=int(generic))
P("Pendentes de resposta do cliente:", pending, "| Abertos sem 1a resposta:", openn)
P("Descrições genéricas ('I'm having an issue... Please assist'):", generic, f"({generic/n:.1%})")
gen_status = pd.crosstab(df["Ticket Description"].str.startswith("I'm having an issue with the {product_purchased}. Please assist."),
                         df["Ticket Status"], normalize="index").round(3)
P("Status x descrição genérica:\n", gen_status.to_string())

# Volume por tipo — candidatos a triagem/autosserviço
P("Volume por Ticket Subject:\n", df["Ticket Subject"].value_counts().to_string())

# Excesso de espera sobre benchmark interno (mediana)
med = v.res_h.median()
excess = (v.res_h - med).clip(lower=0).sum()
out["excess_hours_sample"] = excess
P(f"Horas de espera do cliente acima da mediana ({med:.2f}h) nos fechados válidos: {excess:,.0f}h")

json.dump(out, open("resultados.json", "w"), default=str, indent=1, ensure_ascii=False)

# ---------------------------------------------------------------- 3b. Modelo de desperdício (premissas explícitas)
P("\n3b. MODELO DE DESPERDÍCIO — anualizado para 30.000 tickets/ano")
VOL = 30000
share_pending = (df["Ticket Status"] == "Pending Customer Response").mean()
share_nontech = (df["Ticket Type"] != "Technical issue").mean()
scen = {  # (min por ciclo extra, min triagem manual, min redação, % redação economizada, R$/h)
    "conservador": (6, 2, 6, 0.30, 35),
    "base":        (10, 3, 8, 0.40, 45),
    "agressivo":   (15, 4, 10, 0.50, 60),
}
rows = []
for k, (m_cycle, m_tri, m_draft, save, rate) in scen.items():
    h_ping = VOL * share_pending * m_cycle / 60
    h_tri = VOL * m_tri / 60
    h_draft = VOL * share_nontech * m_draft * save / 60
    tot = h_ping + h_tri + h_draft
    rows.append(dict(cenario=k, ping_pong_h=h_ping, triagem_h=h_tri, redacao_h=h_draft, total_h=tot,
                     fte=tot / 1760, custo_R=tot * rate, custo_mes_R=tot * rate / 12))
w = pd.DataFrame(rows).set_index("cenario").round(1)
P(f"share pending={share_pending:.3f} | share não-técnico={share_nontech:.3f}")
P(w.to_string())
out["waste"] = w.to_dict("index"); out["share_nontech"] = share_nontech
exc_per = excess / len(v)
P(f"Espera excedente do cliente: {exc_per:.2f}h/ticket fechado acima da mediana -> {exc_per*VOL*len(closed)/n:,.0f}h-cliente/ano (se a proporção de fechados se mantiver)")
json.dump(out, open("resultados.json", "w"), default=str, indent=1, ensure_ascii=False)
