"""H1 em nivel de deal (so fechados): a taxa de ganho historica do grupo/par ate T preve ganho vs perda depois de T?
Modelo de probabilidade linear com efeito fixo de mes de fechamento (o calendario domina a taxa de ganho)."""
from common import *
from bt import shrunk, key, bh
from scipy import stats
d = load(); d["size_b"] = pd.qcut(d.revenue, 3, labels=["P", "M", "G"]).astype(object)
d["emp_b"] = pd.qcut(d.employees, 3, labels=["P", "M", "G"]).astype(object)
c = d[d.closed].copy(); c["cm"] = c.close_date.dt.to_period("M").astype(str)
groups = {"vendedor": ["sales_agent"], "produto": ["product"], "conta": ["account"], "setor": ["sector"],
          "vendedor x produto": ["sales_agent", "product"], "vendedor x conta": ["sales_agent", "account"], "conta x produto": ["account", "product"],
          "setor x produto": ["sector", "product"], "porte(receita) x produto": ["size_b", "product"], "porte(func.) x produto": ["emp_b", "product"],
          "vendedor x setor": ["sales_agent", "sector"], "manager x produto": ["manager", "product"], "subsidiaria x produto": ["is_sub", "product"],
          "pais x produto": ["office_location", "product"], "serie x setor": ["series", "sector"]}
rows = []
for T in ["2017-06-30", "2017-08-31", "2017-09-30"]:
    tr = c[c.close_date <= T]; te = c[c.close_date > T].copy()
    for name, cols in groups.items():
        wr, n, w = shrunk(key(tr, cols), tr.won, key(te, cols), tr.won.mean())
        te["f"] = wr.values
        rf = te.f - te.groupby("cm").f.transform("mean"); ry = te.won - te.groupby("cm").won.transform("mean")
        beta = (rf * ry).sum() / (rf ** 2).sum(); e = ry - beta * rf
        se = np.sqrt(((rf * e) ** 2).sum()) / (rf ** 2).sum()
        spread = te.f.quantile(.9) - te.f.quantile(.1)
        # correlacao bruta entre WR do grupo no treino e no teste (grupos com >=15 dos dois lados)
        a = tr.groupby(key(tr, cols)).won.agg(["mean", "count"]); b = te.groupby(key(te, cols)).won.agg(["mean", "count"])
        j = a.join(b, lsuffix="_tr", rsuffix="_te", how="inner"); j = j[(j.count_tr >= 15) & (j.count_te >= 15)]
        r = stats.spearmanr(j.mean_tr, j.mean_te) if len(j) >= 5 else (np.nan, np.nan)
        rows.append(dict(corte=T, grupo=name, n_treino=len(tr), n_teste=len(te), grupos=len(j), spread_wr_treino_pp=100 * spread,
                         efeito_teste_pp=100 * beta * spread, slope=beta, p=2 * stats.norm.sf(abs(beta / se)), rho_grupos=r[0], p_rho=r[1]))
R = pd.DataFrame(rows); R["q"] = bh(R.p)
R.to_csv("06_interacoes_oot.csv", index=False)
print(R.round(3).to_string())
print("slope=1 seria sinal perfeitamente persistente; slope~0 = ruido. p<0.05:", (R.p < .05).sum(), "de", len(R), "| q<0.05:", (R.q < .05).sum())
# recompra: mesma conta ja comprou o MESMO produto antes (ganho anterior), no momento do engage
c = c.sort_values("close_date")
for T in ["2017-06-30", "2017-09-30"]:
    tr = c[c.close_date <= T]; te = c[(c.close_date > T)].copy()
    bought = set(zip(tr[tr.won == 1].account, tr[tr.won == 1]["product"])); lost = set(zip(tr[tr.won == 0].account, tr[tr.won == 0]["product"]))
    te["recompra"] = [(a, p) in bought for a, p in zip(te.account, te["product"])]
    te["perdeu_antes"] = [(a, p) in lost for a, p in zip(te.account, te["product"])]
    for f in ["recompra", "perdeu_antes"]:
        t = pd.crosstab(te[f], te.won); ch, p, _, _ = stats.chi2_contingency(t)
        print(T, f, te.groupby(f).won.agg(["mean", "count"]).round(3).to_dict(), "p=%.3f" % p)
