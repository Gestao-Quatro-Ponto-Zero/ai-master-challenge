from common import *
from bt import *
from scipy import stats
import os, subprocess, sys
if not os.path.exists("snapshots.pkl"):  # gerado pelo bt.py
    subprocess.run([sys.executable, "bt.py"], check=True, stdout=subprocess.DEVNULL)
d = load(); S = pd.read_pickle("snapshots.pkl")
A = S["T"].isin(pd.to_datetime(CUT_A)); B = S["T"].isin(pd.to_datetime(CUT_B)); C = S["T"].isin(pd.to_datetime(CUT_C))
print("=== H3 carga do vendedor, dentro de cada escritorio (remove o efeito 'Central nao tinha zumbis') ===")
S["age_bin0"] = S.age_bin
for off in ["Central", "East", "West"]:
    for f in ["agent_open_n", "agent_open_fresh_n", "load_rel", "agent_stale_share", "agent_new30_n"]:
        out = []
        for lab, m, y in [("A", A, "y_ever"), ("B", B, "y_ever"), ("C30", C, "y30")]:
            o = fwl(S, f, y, m & (S.regional_office == off)); out.append("%s %+.1fpp p=%.3f n=%d" % (lab, 100 * o["eff"], o["p"], o["n"]))
        o = fwl(S, f, "days_to_close", (A | B) & (S.regional_office == off) & (S.closes_later == 1))
        print(off, f, " | ".join(out), "| dias ate fechar %+.1f p=%.3f" % (o["eff"], o["p"]))
print("carga 'fresca' (deals abertos com <=90d) excluindo vendedores sem zumbis: efeito em ganhar")
print("=== taxa de nunca-fechar e homogenea entre os vendedores East/West que deixam deals abertos? ===")
e = d[d.engage_date.notna() & (d.engage_date <= "2017-09-30") & (d.regional_office != "Central") & ~d.sales_agent.isin(["Donn Cantrell", "Garret Kinder", "Reed Clapper"])].copy()
e["z"] = (~e.closed).astype(int)
t = pd.crosstab(e.sales_agent, e.z); print("chi2 p=%.3f n=%d vendedores=%d faixa=%.2f-%.2f" % (stats.chi2_contingency(t)[1], len(e), len(t), e.groupby("sales_agent").z.mean().min(), e.groupby("sales_agent").z.mean().max()))
h1 = e[e.engage_date <= "2017-04-30"].groupby("sales_agent").z.mean(); h2 = e[e.engage_date > "2017-04-30"].groupby("sales_agent").z.mean()
print("persistencia (ate abr vs mai-set):", stats.spearmanr(h1, h2))
print("por office:", e.groupby("regional_office").z.agg(["mean", "size"]).round(3).to_dict(), "p=%.4f" % stats.chi2_contingency(pd.crosstab(e.regional_office, e.z))[1])
print("por manager:", e.groupby("manager").z.agg(["mean", "size"]).round(3).to_dict(), "p=%.4f" % stats.chi2_contingency(pd.crosstab(e.manager, e.z))[1])
# west vs east, estabilidade por trimestre de inicio
e["q"] = e.engage_date.dt.to_period("Q").astype(str); print(e.pivot_table(index="q", columns="regional_office", values="z", aggfunc=["mean", "size"]).round(3))
print("=== sinal 'vendedor nunca deixa deal aberto' fora da amostra: taxa historica de zumbis do vendedor (deals com >140d em T) -> fecha depois? ===")
rows = []
for T in sorted(S["T"].unique()):
    old = d[d.engage_date <= T - pd.Timedelta(days=140)]
    zr = (old.close_date.isna() | (old.close_date > T)).groupby(old.sales_agent).mean()
    s = S[(S["T"] == T) & (S.p0 > 0)].copy(); s["zr"] = s.sales_agent.map(zr); s["limpo"] = s.zr == 0
    g = s.groupby("limpo").agg(n=("deal", "size"), fecha=("closes_later", "mean"), ganha=("y_ever", "mean"), ganha30=("y30", "mean"))
    rows.append(dict(T=str(T)[:10], n_limpo=g.n.get(True, 0), fecha_limpo=g.fecha.get(True, np.nan), n_outros=g.n.get(False, 0), fecha_outros=g.fecha.get(False, np.nan),
                     ganha_limpo=g.ganha.get(True, np.nan), ganha_outros=g.ganha.get(False, np.nan), g30_limpo=g.ganha30.get(True, np.nan), g30_outros=g.ganha30.get(False, np.nan)))
print(pd.DataFrame(rows).round(3).to_string())
print("(cortes de out/nov: 'fecha'/'ganha' ate 31/12 apenas, censurado)")
print("=== H5 ciclo por produto ===")
c = d[d.closed].copy(); c["curto"] = (c.cycle <= 30).astype(int)
print(c.groupby("product").agg(n=("cycle", "size"), mediana=("cycle", "median"), media=("cycle", "mean"), curto=("curto", "mean")).round(3))
print("kruskal ciclo x produto:", stats.kruskal(*[x.cycle.values for _, x in c.groupby("product")]))
print("chi2 curto x produto p=%.4f" % stats.chi2_contingency(pd.crosstab(c["product"], c.curto))[1])
c["em"] = c.engage_date.dt.to_period("M").astype(str)
for lab, m in [("iniciados ate jun", c.engage_date <= "2017-06-30"), ("iniciados jul+", c.engage_date > "2017-06-30")]:
    x = c[m]; r = x.cycle - x.groupby("em").cycle.transform("mean")
    print(lab, "ciclo medio residual (controlando mes de inicio) por produto:", r.groupby(x["product"]).mean().round(1).to_dict(), "kruskal p=%.3f" % stats.kruskal(*[v.values for _, v in r.groupby(x["product"])])[1])
for col in ["sales_agent", "sector", "regional_office", "manager", "series"]:
    r = c.cycle - c.groupby("em").cycle.transform("mean"); print("ciclo residual x", col, "kruskal p=%.3f" % stats.kruskal(*[v.values for _, v in r.groupby(c[col])])[1])
print("=== H7 Prospecting ===")
p = d[d.deal_stage == "Prospecting"]
vol = d[d.engage_date.notna()].groupby("sales_agent").size(); q3 = d[(d.engage_date >= "2017-07-01") & (d.engage_date <= "2017-09-30")].groupby("sales_agent").size()
nov = d[d.engage_date >= "2017-11-01"].groupby("sales_agent").size()
t = pd.DataFrame({"prospects": p.groupby("sales_agent").size(), "iniciados_total": vol, "iniciados_Q3": q3, "iniciados_nov_dez": nov, "zumbis_engaging": d[d.deal_stage == "Engaging"].groupby("sales_agent").size()}).dropna(subset=["prospects"])
t["prosp_por_mes_de_volume"] = t.prospects / (t.iniciados_total / 14); print(t.round(2).to_string())
print("prospects ~ volume:", stats.spearmanr(t.prospects, t.iniciados_total), "| chi2 de proporcionalidade ao volume p=%.3f" % stats.chisquare(t.prospects, t.iniciados_total / t.iniciados_total.sum() * t.prospects.sum())[1])
print("prospects ~ zumbis engaging:", stats.spearmanr(t.prospects, t.zumbis_engaging))
print("mix de produto prospects vs iniciados (Central) p=%.3f" % stats.chi2_contingency(pd.crosstab(d[d.regional_office == "Central"]["product"], d[d.regional_office == "Central"].deal_stage == "Prospecting"))[1])
print("volume mensal de inicios por escritorio"); 
# chance por coorte: de tudo que inicia em cada mes do trimestre, quanto e ganho (coortes resolvidas jan-set)
e = d[(d.engage_date >= "2017-01-01") & (d.engage_date <= "2017-09-30")].copy(); e["mes_no_trim"] = (e.engage_date.dt.month - 1) % 3 + 1; e["w"] = (e.deal_stage == "Won").astype(int)
print("P(ganho | iniciou) por mes do trimestre de inicio x trimestre"); print(e.pivot_table(index=e.engage_date.dt.to_period("Q"), columns="mes_no_trim", values="w", aggfunc="mean").round(3))
print("idem Central:"); print(e[e.regional_office == "Central"].pivot_table(index=e.engage_date.dt.to_period("Q"), columns="mes_no_trim", values="w", aggfunc="mean").round(3))
ch = scoring.win_chance_by_age(d, TODAY); print("chance que a solucao atual da a um prospect (idade 0 em 31/12): %.3f" % ch[0])
print("=== borda da base: coortes Q4 ===")
print("iniciados por mes:", d.groupby(d.engage_date.dt.to_period("M")).size().tail(6).to_dict())
for T in ["2017-06-30", "2017-09-30", "2017-12-31"]:
    T = pd.Timestamp(T); q0 = T.to_period("Q").start_time
    x = d[(d.engage_date >= q0) & (d.engage_date <= T)]
    op = x[x.close_date.isna() | (x.close_date > T)]
    print(str(T)[:10], "iniciados no trimestre:", len(x), "ainda abertos no fim:", len(op), "(%.0f%%)" % (100 * len(op) / len(x)), "por mes do trim:", (op.groupby(op.engage_date.dt.month).size() / x.groupby(x.engage_date.dt.month).size()).round(2).to_dict())
sc, _ = scoring.score_open_deals(d, TODAY)
print(sc.groupby("lista").agg(n=("chance", "size"), chance=("chance", "mean"), ve=("valor_esperado", "sum")).round(3))
f = sc[sc.lista == "foco"]; print("foco por escritorio:", f.groupby("regional_office").size().to_dict(), "chance media %.3f; ganhos esperados pela solucao: %.1f de %d" % (f.chance.mean(), f.chance.sum(), len(f)))
