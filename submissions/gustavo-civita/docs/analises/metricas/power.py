import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3] / "solution"))
import pandas as pd, numpy as np, itertools
import scoring
pd.set_option("display.width",250)
d = scoring.load_pipeline(); ref=scoring.reference_date(d)
print(d[d.engage_date.notna()].groupby([d.engage_date.dt.to_period("M"),"regional_office"]).size().unstack().fillna(0).astype(int).T)
print(d.groupby(["regional_office","deal_stage"]).size().unstack())
won = d[d.deal_stage=="Won"].assign(m=lambda x:x.close_date.dt.to_period("M"))
closed = d[d.deal_stage.isin(["Won","Lost"])].assign(m=lambda x:x.close_date.dt.to_period("M"), won=lambda x:(x.deal_stage=="Won").astype(int))
agents=sorted(d.sales_agent.unique()); months=pd.period_range("2017-03","2017-12",freq="M")
tm=pd.read_csv(scoring.DATA_DIR/"sales_teams.csv").set_index("sales_agent").loc[agents]
P={"receita":won.pivot_table(index="sales_agent",columns="m",values="close_value",aggfunc="sum"),
   "ganhos":won.pivot_table(index="sales_agent",columns="m",values="close_value",aggfunc="size"),
   "fechados":closed.pivot_table(index="sales_agent",columns="m",values="won",aggfunc="size")}
P={k:v.reindex(index=agents,columns=months).fillna(0) for k,v in P.items()}
rng=np.random.default_rng(7)
mgr=tm.manager.values; off=tm.regional_office.values
def strat_assign():
    t=np.zeros(len(agents),bool)
    for m in np.unique(mgr):
        idx=np.where(mgr==m)[0]; rng.shuffle(idx); k=len(idx)//2 + (rng.random()<0.5 if len(idx)%2 else 0)
        t[idx[:int(k)]]=True
    return t
def est(pre,post,t,kind):
    if kind=="raw": return (post[t].mean()-post[~t].mean())/post.mean()
    if kind=="did":
        s=post.mean()/pre.mean()  # escala pre para post
        dd=post-pre*s; return (dd[t].mean()-dd[~t].mean())/post.mean()
    if kind=="ancova":
        X=np.column_stack([np.ones(len(pre)),pre,t.astype(float)]); b=np.linalg.lstsq(X,post,rcond=None)[0]; return b[2]/post.mean()
def mde(sd): return 2.8*sd
scen={"1 mes (pre Q3, pos out)":(["2017-07","2017-08","2017-09"],["2017-10"]),
      "1 trimestre (pre Q3, pos Q4)":(["2017-07","2017-08","2017-09"],["2017-10","2017-11","2017-12"]),
      "1 trimestre (pre Q2, pos Q3)":(["2017-04","2017-05","2017-06"],["2017-07","2017-08","2017-09"]),
      "2 trimestres (pre Q2, pos Q3+Q4)":(["2017-04","2017-05","2017-06"],["2017-07","2017-08","2017-09","2017-10","2017-11","2017-12"])}
rows=[]
for name,(pre_m,post_m) in scen.items():
    for out,p in P.items():
        pre=p[[pd.Period(x) for x in pre_m]].sum(axis=1).values; post=p[[pd.Period(x) for x in post_m]].sum(axis=1).values
        r={"cenario":name,"metrica":out}
        for kind in ["raw","did","ancova"]:
            sims=np.array([est(pre,post,strat_assign(),kind) for _ in range(4000)])
            r[f"MDE80_{kind}"]=round(mde(sims.std()),3)
        # cluster por manager 3x3 (todas as 20 divisoes), DiD
        ms=np.unique(mgr); cs=[]
        for combo in itertools.combinations(ms,3):
            t=np.isin(mgr,combo); cs.append(est(pre,post,t,"did"))
        r["SD_cluster_mgr_did"]=round(np.std(cs),3); r["max|placebo|_mgr"]=round(np.max(np.abs(cs)),3)
        os_=[est(pre,post,off==o,"did") for o in np.unique(off)]
        r["placebo_escritorio_did"]=[round(x,3) for x in os_]
        rows.append(r)
res=pd.DataFrame(rows); print(res.to_string(index=False)); res.to_csv("poder_placebo.csv",index=False)

# taxa de ganho em nivel de deal: efeito de desenho
cl=closed[closed.close_date>="2017-10-01"]
n=len(cl); p=cl.won.mean(); ag=cl.groupby("sales_agent").won.agg(["mean","size"])
m=ag["size"].mean(); between=ag["mean"].var(ddof=1); expected=(p*(1-p)/ag["size"]).mean()
icc=max(0,(between-expected)/(p*(1-p))); deff=1+(m-1)*icc
se=np.sqrt(2*p*(1-p)/(n/2)*deff)
print(f"Q4 fechados n={n} p={p:.3f} ICC vendedor={icc:.4f} deff={deff:.2f} MDE win rate (15x15, 1 tri) = {2.8*se:.3f} pp abs = {2.8*se/p:.1%} relativo")
# coorte: conversao Won/engajados em 1 trimestre
e=d[(d.engage_date>="2017-04-01")&(d.engage_date<"2017-07-01")]; n=len(e); p=(e.deal_stage=="Won").mean()
print(f"coorte Q2 engajados n={n} conv={p:.3f} MDE (metade/metade, sem cluster) = {2.8*np.sqrt(2*p*(1-p)/(n/2)):.3f} abs = {2.8*np.sqrt(2*p*(1-p)/(n/2))/p:.1%} rel")
# analitico: n por braco necessario p/ 10% com ANCOVA
for out,p in P.items():
    pre=p[[pd.Period(x) for x in ["2017-07","2017-08","2017-09"]]].sum(axis=1).values; post=p[[pd.Period(x) for x in ["2017-10","2017-11","2017-12"]]].sum(axis=1).values
    X=np.column_stack([np.ones(30),pre]); resid=post-X@np.linalg.lstsq(X,post,rcond=None)[0]
    cv=resid.std(ddof=2)/post.mean(); cvraw=post.std(ddof=1)/post.mean()
    print(out,"CV bruto",round(cvraw,2),"CV residual ANCOVA",round(cv,2),"| n por braco p/ 10%: bruto",int(np.ceil(2*(2.8*cvraw/0.10)**2)),"ancova",int(np.ceil(2*(2.8*cv/0.10)**2)),"| MDE 15x15 ancova",round(2.8*cv*np.sqrt(2/15),3),"| 17x18",round(2.8*cv*np.sqrt(1/17+1/18),3))
# reativacao: holdout por deal
from scipy.stats import binom, fisher_exact
o,_=scoring.score_open_deals(d,ref); nre=(o.lista=="reativar").sum(); h=nre//2
kmin=next(k for k in range(1,50) if fisher_exact([[k,h-k],[0,h]])[1]<0.05)
print("reativar n",nre,"por braco",h,"k minimo significativo",kmin,{r:round(1-binom.cdf(kmin-1,h,r),2) for r in [0.02,0.03,0.04,0.05]})
print("deals já ganhos depois de 138d:", ((d.deal_stage=="Won")&((d.close_date-d.engage_date).dt.days>138)).sum())
