import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3] / "solution"))
import pandas as pd, numpy as np, itertools
import scoring
pd.set_option("display.width",250); pd.set_option("display.max_columns",40); pd.set_option("display.max_rows",200)
d = scoring.load_pipeline(); ref = scoring.reference_date(d)
teams = pd.read_csv(scoring.DATA_DIR/"sales_teams.csv")
print("sem deals:", teams[~teams.sales_agent.isin(d.sales_agent)].to_string(index=False))
MAXC = 138
o,_ = scoring.score_open_deals(d, ref)
eng = o[o.deal_stage=="Engaging"].copy()
eng["morto"] = eng.age > MAXC
eng["fora_foco"] = eng.lista.isin(["reativar","encerrar"])
def spread(s):
    return f"min {s.min():.3g} | p25 {s.quantile(.25):.3g} | med {s.median():.3g} | p75 {s.quantile(.75):.3g} | max {s.max():.3g} | n={len(s)}"
def report(name, f, df):
    print(f"\n### {name}")
    print("empresa:", round(f(df),3))
    print("escritorio:", df.groupby("regional_office").apply(f).round(3).to_dict())
    print("manager:", df.groupby("manager").apply(f).round(3).to_dict())
    print("vendedores:", spread(df.groupby("sales_agent").apply(f)))
report("A1 % Engaging abertos com idade > 138d (qtd)", lambda x: x.morto.mean(), eng)
report("A1b % do valor de tabela Engaging aberto em deals > 138d", lambda x: x.loc[x.morto,"sales_price"].sum()/x.sales_price.sum(), eng)
report("A1c % Engaging fora do foco (reativar+encerrar, regra da ferramenta)", lambda x: x.fora_foco.mean(), eng)
report("A1d n Engaging abertos por vendedor", lambda x: len(x)/x.sales_agent.nunique(), eng)
report("A1e n mortos por vendedor", lambda x: x.morto.sum()/x.sales_agent.nunique(), eng)
report("foco por vendedor", lambda x: (x.lista=="foco").sum()/x.sales_agent.nunique(), eng)
report("Prospecting por vendedor", lambda x: len(x)/x.sales_agent.nunique(), o[o.deal_stage=="Prospecting"])
print("idade mediana Engaging aberto:", eng.age.median(), "valor tabela morto:", eng.loc[eng.morto,"sales_price"].sum(), "total", eng.sales_price.sum())

closed = d[d.deal_stage.isin(["Won","Lost"])].copy()
closed["cyc"]=(closed.close_date-closed.engage_date).dt.days
closed["won"]=closed.deal_stage=="Won"
lost=closed[~closed.won]; won=closed[closed.won]
report("A2 dias medianos ate Lost", lambda x: x.cyc.median(), lost)
report("A2b % dos Lost que levaram >30d", lambda x: (x.cyc>30).mean(), lost)
report("A2c dias medios ate Lost", lambda x: x.cyc.mean(), lost)
print("lost cyc hist:", np.histogram(lost.cyc, bins=[0,7,14,30,60,90,120,140])[0])
print("won cyc hist:", np.histogram(won.cyc, bins=[0,7,14,30,60,90,120,140])[0])

# coorte madura
coh = d[d.engage_date.notna() & (d.engage_date <= ref - pd.Timedelta(days=MAXC))].copy()
coh["aberto"]=coh.deal_stage=="Engaging"; coh["won"]=coh.deal_stage=="Won"
print("\ncoorte madura n=", len(coh), "ate", (ref - pd.Timedelta(days=MAXC)).date())
report("B1 % da coorte madura nunca fechada (esfriou/abandonada)", lambda x: x.aberto.mean(), coh)
report("B3a conversao de coorte Won/engajados", lambda x: x.won.mean(), coh)
print(coh.groupby(coh.engage_date.dt.to_period("M")).agg(n=("won","size"), aberto=("aberto","mean"), won=("won","mean")).round(3))
report("B3b win rate Won/(Won+Lost)", lambda x: x.won.mean(), closed)
report("B3c ciclo mediano Won (dias)", lambda x: x.cyc.median(), won)
report("B3d ticket medio Won", lambda x: x.close_value.mean(), won)
print("win rate se 987 'encerrar' virarem Lost:", 4238/(6711+987), " se 1461:", 4238/(6711+1461))
print("close_value/sales_price won:", (won.close_value/won.sales_price).describe().round(3).to_dict())

# painel vendedor-mes
closed["m"]=closed.close_date.dt.to_period("M")
agents = sorted(d.sales_agent.unique()); months = pd.period_range("2017-03","2017-12",freq="M")
rev = won.assign(m=won.close_date.dt.to_period("M")).pivot_table(index="sales_agent",columns="m",values="close_value",aggfunc="sum").reindex(index=agents,columns=months).fillna(0)
nw = won.assign(m=won.close_date.dt.to_period("M")).pivot_table(index="sales_agent",columns="m",values="close_value",aggfunc="size").reindex(index=agents,columns=months).fillna(0)
ncl = closed.pivot_table(index="sales_agent",columns="m",values="won",aggfunc="size").reindex(index=agents,columns=months).fillna(0)
print("\n### painel vendedor-mes (30 vendedores x 10 meses)")
for nm,p in [("receita",rev),("ganhos",nw),("fechados",ncl)]:
    am = p.mean(axis=1)
    within = p.sub(am,axis=0).values.std(ddof=1)
    # remove efeito de mes tambem
    resid = p.sub(am,axis=0).sub(p.mean(axis=0)-p.values.mean(),axis=1)
    print(nm, "media/vend/mes", round(p.values.mean(),1), "| entre vendedores:", spread(am), "CV entre", round(am.std()/am.mean(),2),
          "| SD mensal dentro do vendedor", round(within,1), "CV", round(within/p.values.mean(),2), "| SD resid (tirando mes)", round(resid.values.std(),1), "CV", round(resid.values.std()/p.values.mean(),2))
print("receita mensal empresa:", rev.sum().round(0).to_dict())
moq = closed.assign(moq=((closed.close_date.dt.month-1)%3)+1).groupby("moq").agg(n=("won","size"),wr=("won","mean"),rev=("close_value","sum"))
print(moq)
tm = teams.set_index("sales_agent")
qrev = rev.T.groupby(lambda p: f"Q{p.quarter}").sum().T
qn = nw.T.groupby(lambda p: f"Q{p.quarter}").sum().T
print("receita trimestral por vendedor:\n", qrev.describe().round(0))
print("corr trimestre a trimestre receita:", qrev[["Q2","Q3","Q4"]].corr().round(2).values.tolist())
print("corr ganhos:", qn[["Q2","Q3","Q4"]].corr().round(2).values.tolist())
# ICC manager
def icc(series, groups):
    df=pd.DataFrame({"y":series,"g":groups}); k=df.groupby("g").size().mean(); 
    msb=k*df.groupby("g").y.mean().var(ddof=1); msw=df.groupby("g").y.var(ddof=1).mean()
    return (msb-msw)/(msb+(k-1)*msw)
for q in ["Q2","Q3","Q4"]:
    print(q,"ICC receita por manager", round(icc(qrev[q], tm.loc[qrev.index,"manager"].values),2), "por escritorio", round(icc(qrev[q], tm.loc[qrev.index,"regional_office"].values),2))
qrev.to_csv("receita_trimestral_vendedor.csv"); rev.to_csv("receita_mensal_vendedor.csv"); nw.to_csv("ganhos_mensal_vendedor.csv")
