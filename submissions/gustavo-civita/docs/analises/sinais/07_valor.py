"""H4: close_value / preco de tabela (ratio) entre os ganhos e previsivel?"""
from common import *
from bt import bh
from scipy import stats
d = load(); w = d[d.deal_stage == "Won"].copy()
w["cm"] = w.close_date.dt.to_period("M").astype(str); w["mq"] = (w.close_date.dt.month - 1) % 3 + 1
w["dq"] = (w.close_date - w.close_date.dt.to_period("Q").dt.start_time).dt.days
w["size_b"] = pd.qcut(w.revenue, 4, labels=False)
print("ratio: media %.4f dp %.4f n %d | min %.3f max %.3f" % (w.ratio.mean(), w.ratio.std(), len(w), w.ratio.min(), w.ratio.max()))
print("normalidade (D'Agostino):", stats.normaltest(w.ratio), " skew %.3f kurt %.3f" % (stats.skew(w.ratio), stats.kurtosis(w.ratio)))
rows = []
for col in ["sales_agent", "account", "product", "sector", "manager", "regional_office", "cm", "mq", "size_b", "is_sub", "office_location"]:
    g = [x.ratio.values for _, x in w.groupby(col)]
    F, p = stats.f_oneway(*g); H, pk = stats.kruskal(*g)
    eta2 = sum(len(x) * (x.mean() - w.ratio.mean()) ** 2 for x in g) / ((w.ratio - w.ratio.mean()) ** 2).sum()
    gm = w.groupby(col).ratio.mean()
    rows.append(dict(fator=col, niveis=len(g), F=F, p_anova=p, p_kruskal=pk, eta2=eta2, min_media=gm.min(), max_media=gm.max()))
R = pd.DataFrame(rows); R["q"] = bh(R.p_anova); print(R.round(4).to_string())
for col in ["cycle", "dq", "revenue", "employees", "sales_price"]:
    print("spearman ratio x", col, stats.spearmanr(w.ratio, w[col]))
print("variancia do ratio por produto (Levene):", stats.levene(*[x.ratio.values for _, x in w.groupby("product")]))
print(w.groupby("product").ratio.agg(["mean", "std", "count"]).round(4))
# fora da amostra: ratio medio do vendedor / conta / vendedor x produto ate T preve o ratio depois?
for T in ["2017-06-30", "2017-09-30"]:
    tr = w[w.close_date <= T]; te = w[w.close_date > T]
    for cols in [["sales_agent"], ["account"], ["product"], ["sales_agent", "product"], ["sales_agent", "account"], ["account", "product"]]:
        a = tr.groupby(cols).ratio.agg(["mean", "count"]); b = te.groupby(cols).ratio.agg(["mean", "count"])
        j = a.join(b, lsuffix="_tr", rsuffix="_te", how="inner"); j = j[(j.count_tr >= 5) & (j.count_te >= 5)]
        r = stats.spearmanr(j.mean_tr, j.mean_te)
        # ganho de erro: prever valor = preco x ratio_grupo(treino, encolhido) vs preco x ratio global
        m = te.merge(a.reset_index(), on=cols, how="left"); k = 20
        pred = ((m["mean"].fillna(tr.ratio.mean()) * m["count"].fillna(0) + k * tr.ratio.mean()) / (m["count"].fillna(0) + k))
        mae0 = (m.ratio - tr.ratio.mean()).abs().mean(); mae1 = (m.ratio - pred).abs().mean()
        print(T, "x".join(cols), "grupos=%d rho=%.3f p=%.3f | MAE ratio global=%.4f grupo=%.4f (n_teste=%d)" % (len(j), r[0], r[1], mae0, mae1, len(te)))
# valor esperado: usar preco de tabela vs media historica de close_value por produto
print((w.groupby("product").close_value.mean() / w.groupby("product").sales_price.first()).round(4))
