import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3] / "solution"))
import numpy as np, pandas as pd
from scipy import stats
import scoring

pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200); pd.set_option("display.max_columns", 40)
d = scoring.load_pipeline()
today = scoring.reference_date(d)
print("today", today, "n", len(d))
print(d.deal_stage.value_counts())
teams = pd.read_csv(scoring.DATA_DIR / "sales_teams.csv")
print("agents in teams", len(teams), "with deals", d.sales_agent.nunique())
print("agents w/o deals:", sorted(set(teams.sales_agent) - set(d.sales_agent)))

od, meta = scoring.score_open_deals(d, today)
print("\n== LISTAS ==")
print(od.lista.value_counts())
print("conta vazia em abertas:", od.account.isna().mean().round(3))
print(od.groupby("lista").agg(n=("lista", "size"), preco=("sales_price", "sum"), ve=("valor_esperado", "sum"), sem_conta=("account", lambda s: s.isna().mean())))
print("idade por lista"); print(od.groupby("lista").age.describe())

print("\n== POR VENDEDOR ==")
pv = od.pivot_table(index="sales_agent", columns="lista", values="opportunity_id", aggfunc="count", fill_value=0)
pv["abertas"] = pv.sum(axis=1)
pv["morto"] = pv.get("encerrar", 0) + pv.get("reativar", 0)
pv["pct_morto"] = (pv.morto / pv.abertas).round(2)
pv["pct_morto_eng"] = (pv.morto / (pv.morto + pv.foco)).round(2)
ve = od.groupby("sales_agent").valor_esperado.sum().round(0)
pv["ve"] = ve
hist = d[d.deal_stage.isin(["Won", "Lost"])]
h = hist.groupby("sales_agent").agg(fechadas=("deal_stage", "size"), ganhos=("deal_stage", lambda s: (s == "Won").sum()), receita=("close_value", "sum"))
h["wr"] = (h.ganhos / h.fechadas).round(3)
pv = pv.join(h).join(teams.set_index("sales_agent"))
pv["ganhos_mes"] = (pv.ganhos / 10).round(1)  # mar-dez 2017
pv["meses_de_foco"] = (pv.foco / (pv.fechadas / 10)).round(2)
print(pv.sort_values("abertas", ascending=False).to_string())
for c in ["abertas", "foco", "abordar", "morto", "pct_morto", "pct_morto_eng", "fechadas", "wr", "receita", "ve"]:
    s = pv[c]
    print(f"{c:14s} min {s.min():>10.2f} p25 {s.quantile(.25):>10.2f} med {s.median():>10.2f} p75 {s.quantile(.75):>10.2f} max {s.max():>10.2f} cv {s.std()/s.mean():.2f}")
print("vendedores com 0 em foco:", (pv.foco == 0).sum(), " com 0 abordar:", (pv.abordar == 0).sum())
print("top5 share of abordar:", pv.abordar.nlargest(5).sum() / pv.abordar.sum(), " top5 share foco:", pv.foco.nlargest(5).sum() / pv.foco.sum())

print("\n== POR ESCRITORIO / MANAGER ==")
for k in ["regional_office", "manager"]:
    g = pv.groupby(k).agg(vend=("abertas", "size"), abertas=("abertas", "sum"), foco=("foco", "sum"), abordar=("abordar", "sum"), morto=("morto", "sum"), ve=("ve", "sum"), fechadas=("fechadas", "sum"), ganhos=("ganhos", "sum"), receita=("receita", "sum"))
    g["foco_por_vend"] = (g.foco / g.vend).round(1); g["abordar_por_vend"] = (g.abordar / g.vend).round(1); g["wr"] = (g.ganhos / g.fechadas).round(3)
    g["pct_morto"] = (g.morto / g.abertas).round(2)
    print(g.to_string())

# redistribuicao: quanto precisaria mover p/ igualar
for c in ["foco", "abordar"]:
    m = pv[c].mean(); mv = (pv[c] - m).clip(lower=0).sum()
    print(f"redistribuir {c}: mover {mv:.0f} de {pv[c].sum()} ({mv/pv[c].sum():.0%}) iguala a carteira; media {m:.1f}")
# foco relativo a vazao historica
print("meses_de_foco (foco / fechadas por mes):"); print(pv.meses_de_foco.describe().round(2))
print("corr abertas-foco vs fechadas hist:", stats.spearmanr(pv.foco, pv.fechadas))
print("corr abordar vs fechadas hist:", stats.spearmanr(pv.abordar, pv.fechadas))

print("\n== WIN RATE POR VENDEDOR / PRODUTO / ESCRITORIO (qui2) ==")
for k in ["sales_agent", "product", "regional_office", "manager", "sector"]:
    ct = pd.crosstab(hist[k], hist.deal_stage)
    chi = stats.chi2_contingency(ct)
    wr = ct.Won / ct.sum(axis=1)
    print(f"{k:16s} p={chi[1]:.3f}  wr min {wr.min():.3f} max {wr.max():.3f}")

print("\n== CICLO: ganhos e perdidos por idade ==")
hist = hist.assign(dur=(hist.close_date - hist.engage_date).dt.days)
print(hist.groupby("deal_stage").dur.describe().round(1))
print("max dur Won:", hist[hist.deal_stage == "Won"].dur.max(), " Lost:", hist[hist.deal_stage == "Lost"].dur.max())
won = hist[hist.deal_stage == "Won"]; lost = hist[hist.deal_stage == "Lost"]
tot = won.close_value.sum()
eng_open = od[od.deal_stage == "Engaging"]
print("thr | ganhos apos thr (n, %, receita %) | perdidos apos thr | abertas Engaging acima thr (n, %)")
for t in [14, 30, 45, 60, 75, 90, 100, 110, 120, 130, 138, 140, 150, 180]:
    w = won[won.dur > t]; l = lost[lost.dur > t]
    print(f"{t:4d} | {len(w):5d} {len(w)/len(won):6.1%} {w.close_value.sum()/tot:6.1%} | {len(l):5d} {len(l)/len(lost):6.1%} | {(eng_open.age > t).sum():5d} {(eng_open.age > t).mean():6.1%}")
print("receita ganha por faixa de duracao")
bins = [-1, 7, 14, 30, 60, 90, 120, 200]
won_b = won.groupby(pd.cut(won.dur, bins)).agg(n=("dur", "size"), rec=("close_value", "sum")); won_b["pct_rec"] = (won_b.rec / tot).round(3)
lost_b = lost.groupby(pd.cut(lost.dur, bins)).size()
won_b["perdidos"] = lost_b; won_b["wr"] = (won_b.n / (won_b.n + won_b.perdidos)).round(3)
print(won_b)
# deal-days gastos em perdidos
print("deal-dias: ganhos", won.dur.sum(), "perdidos", lost.dur.sum(), "pct perdidos", lost.dur.sum() / (won.dur.sum() + lost.dur.sum()))
print("deal-dias acumulados nas abertas Engaging:", eng_open.age.sum(), " das quais mortas:", od[od.lista.isin(["encerrar", "reativar"])].age.sum())
print("idade abertas Engaging:"); print(eng_open.age.describe())
print(pd.cut(eng_open.age, [0, 30, 60, 90, 120, 150, 180, 250, 400, 600]).value_counts().sort_index())

print("\n== SAZONALIDADE (artefato?) ==")
print("engage por mes"); print(d.groupby(d.engage_date.dt.to_period("M")).size().to_string())
print("close por mes"); print(hist.groupby([hist.close_date.dt.to_period("M"), "deal_stage"]).size().unstack().to_string())
print("abertas Engaging por mes de engage"); print(eng_open.groupby(eng_open.engage_date.dt.to_period("M")).size().to_string())
# trimestre de fechamento vs trimestre de engage
q = (won.close_date.dt.year * 4 + won.close_date.dt.quarter) - (won.engage_date.dt.year * 4 + won.engage_date.dt.quarter)
print("ganhos: trimestres entre engage e close"); print(q.value_counts().sort_index())

print("\n== CARGA x RESULTADO ==")
# carga concorrente no momento do engage: n de deals do vendedor engajados e nao fechados naquela data (so deals que depois fecharam + abertas hoje)
alld = d[d.engage_date.notna()].copy()
alld["end"] = alld.close_date.fillna(pd.Timestamp("2099-01-01"))
loads = []
for ag, g in alld.groupby("sales_agent"):
    e = g.engage_date.values; en = g.end.values
    for i in range(len(g)):
        loads.append((g.index[i], ((e <= e[i]) & (en > e[i])).sum() - 1))
alld["load"] = pd.Series(dict(loads))
cl = alld[alld.deal_stage.isin(["Won", "Lost"]) & (alld.engage_date >= "2017-03-01")].copy()
cl["won"] = (cl.deal_stage == "Won").astype(int); cl["dur"] = (cl.close_date - cl.engage_date).dt.days
cl["load_q"] = pd.qcut(cl.load, 5, duplicates="drop")
print(cl.groupby("load_q").agg(n=("won", "size"), wr=("won", "mean"), dur=("dur", "median"), dur_won=("dur", lambda s: s[cl.loc[s.index, "won"] == 1].median())).round(3))
print("spearman load~won", stats.spearmanr(cl.load, cl.won)); print("spearman load~dur", stats.spearmanr(cl.load, cl.dur))
# dentro do vendedor (desvio da propria media)
cl["load_dm"] = cl.load - cl.groupby("sales_agent").load.transform("mean"); cl["won_dm"] = cl.won - cl.groupby("sales_agent").won.transform("mean"); cl["dur_dm"] = cl.dur - cl.groupby("sales_agent").dur.transform("mean")
print("within-agent load~won", stats.pearsonr(cl.load_dm, cl.won_dm)); print("within-agent load~dur", stats.pearsonr(cl.load_dm, cl.dur_dm))
# nivel vendedor
print("agente: fechadas vs wr", stats.spearmanr(pv.fechadas, pv.wr)); print("agente: abertas vs wr", stats.spearmanr(pv.abertas, pv.wr))
ad = hist.groupby("sales_agent").dur.median(); print("agente: fechadas vs dur mediana", stats.spearmanr(pv.fechadas, ad.reindex(pv.index)))
print("agente: receita vs fechadas", stats.spearmanr(pv.receita, pv.fechadas), " receita vs wr", stats.spearmanr(pv.receita, pv.wr))
tk = (pv.receita / pv.ganhos); print("ticket medio por vendedor min/med/max", tk.min().round(0), tk.median().round(0), tk.max().round(0), " receita~ticket", stats.spearmanr(pv.receita, tk))
print("receita por vendedor: min/med/max", pv.receita.min(), pv.receita.median(), pv.receita.max())
r2 = np.corrcoef(np.log(pv.receita), np.log(pv.fechadas))[0, 1] ** 2; r2t = np.corrcoef(np.log(pv.receita), np.log(tk))[0, 1] ** 2
print("R2 log receita ~ log volume", round(r2, 2), " ~ log ticket", round(r2t, 2))

print("\n== MIX DE PRODUTO ==")
pm = hist.groupby("product").agg(n=("dur", "size"), wr=("deal_stage", lambda s: (s == "Won").mean()), rec=("close_value", "sum"), preco=("sales_price", "first"), dur=("dur", "median")).round(3)
pm["pct_rec"] = (pm.rec / tot).round(3); print(pm)
print("abertas por produto x lista"); print(pd.crosstab(od["product"], od.lista))
print("desconto: close_value/price ganhos"); print((won.close_value / won.sales_price).describe().round(3))
# produto por vendedor: share de deals caros
exp = hist.assign(caro=hist.sales_price >= 3000).groupby("sales_agent").caro.mean()
print("share de deals caros (>=3000) por vendedor: min/med/max", exp.min().round(2), exp.median().round(2), exp.max().round(2), " receita~share caro", stats.spearmanr(pv.receita, exp.reindex(pv.index)))

print("\n== CONTAS ==")
print("conta vazia por stage"); print(d.groupby("deal_stage").account.apply(lambda s: s.isna().mean()).round(3))
ac = hist.groupby("account").agg(n=("dur", "size"), wr=("deal_stage", lambda s: (s == "Won").mean()), rec=("close_value", "sum"))
print("contas", len(ac), "wr min/max", ac.wr.min().round(3), ac.wr.max().round(3), "deals por conta med", ac.n.median())
print("top10 contas share receita", ac.rec.nlargest(10).sum() / ac.rec.sum())
# conta atendida por quantos vendedores
print("vendedores distintos por conta (mediana):", d.groupby("account").sales_agent.nunique().median(), " contas por vendedor (med):", d.groupby("sales_agent").account.nunique().median())
# abertas com conta: conta ja comprou antes?
oa = od[od.account.notna()]
print("abertas com conta:", len(oa), " em contas com ganho previo:", oa.account.isin(won.account).mean())

print("\n== PROSPECTING ==")
pr = od[od.deal_stage == "Prospecting"]
print("n", len(pr), "preco tabela total", pr.sales_price.sum(), "sem conta", pr.account.isna().mean())
print("x taxa base 63% x preco:", pr.sales_price.sum() * 0.63)
print("VE do foco:", od[od.lista == "foco"].valor_esperado.sum(), " n foco", (od.lista == "foco").sum(), "preco foco", od[od.lista == "foco"].sales_price.sum())
print("preco de tabela das mortas:", od[od.lista.isin(["reativar", "encerrar"])].sales_price.sum())
print("faixa do foco"); print(od[od.lista == "foco"].faixa.value_counts())
print("receita media mensal ganha:", tot / 10, " receita ult. trimestre:", won[won.close_date >= "2017-10-01"].close_value.sum())
pv.to_csv(str(__import__("pathlib").Path(__file__).with_name("por_vendedor.csv")))
