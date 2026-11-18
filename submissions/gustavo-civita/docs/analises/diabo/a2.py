import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3] / "solution"))
import numpy as np, pandas as pd, scoring, backtest as bt
from scipy.stats import spearmanr, rankdata
d = scoring.load_pipeline()
def auc(score, y):
    y=np.asarray(y).astype(bool); 
    if y.sum()==0 or (~y).sum()==0: return np.nan
    r=rankdata(score); return (r[y].sum()-y.sum()*(y.sum()+1)/2)/(y.sum()*(~y).sum())
snaps=[]
for date in bt.SNAPSHOTS:
    s=bt.snapshot_with_predictions(d,pd.Timestamp(date)); s["date"]=date; snaps.append(s)
A=pd.concat(snaps)
A["closed"]=A.won_after|A.lost_after
print("deal-semanas",len(A),"deals unicos",A.opportunity_id.nunique())
print("AUC chance vs ganho (todos):",round(auc(A.chance,A.won_after),3))
print("AUC -idade vs ganho (todos):",round(auc(-A.age,A.won_after),3))
live=A[A.chance>=0.01]
print("AUC chance vs ganho (vivos):",round(auc(live.chance,live.won_after),3))
cl=A[A.closed]
print("Entre os que fecharam (Won vs Lost): n",len(cl),"AUC chance:",round(auc(cl.chance,cl.won_after),3), "win rate",round(cl.won_after.mean(),3))
print("AUC chance vs 'fecha (won ou lost)':",round(auc(A.chance,A.closed),3))
# por faixa: destino
live=live.copy(); live["faixa"]=live.chance.map(scoring.band)
print(live.groupby("faixa").agg(n=("won_after","size"),won=("won_after","mean"),lost=("lost_after","mean")).assign(aberto=lambda x:1-x.won-x.lost, win_entre_fechados=lambda x:x.won/(x.won+x.lost)).round(3))
# parados
p=A[A.chance<0.01]
print("parados deal-semanas",len(p),"unicos",p.opportunity_id.nunique(),"ganhos",p.won_after.sum(),"perdidos unicos",p[p.lost_after].opportunity_id.nunique(), "ainda Engaging no fim (unicos)",p[~p.closed].opportunity_id.nunique())
print("idade parados", p.age.describe()[["min","50%","max"]].to_dict())
# vivos por vendedor por semana vs top10
lv=A[A.chance>=0.01].groupby(["date","sales_agent"]).size()
al=A.groupby(["date","sales_agent"]).size()
print("vivos por vendedor-semana: mediana",lv.median(),"p25",lv.quantile(.25),"frac <=10:",round((lv<=10).mean(),3))
print("abertos por vendedor-semana mediana",al.median())
# sweep baseline
def cap(s,col): return s.sort_values([col,"sales_price"],ascending=False).groupby("sales_agent").head(10).revenue_after.sum()
rows=[]
for R in [45,60,75,80,90,95,100,105,110,120]:
    tot={"Q3":0,"Q4":0}; wins=0
    for s in snaps:
        s=s.copy(); s["b"]=s.sales_price.where(s.age<=R,0); q="Q3" if s.date.iloc[0]<"2017-10-01" else "Q4"
        v=cap(s,"b"); tot[q]+=v; wins+= cap(s,"valor_esperado")>v
    rows.append((R,round(tot["Q3"]),round(tot["Q4"]),wins))
T={"Q3":0,"Q4":0}
for s in snaps:
    q="Q3" if s.date.iloc[0]<"2017-10-01" else "Q4"; T[q]+=cap(s,"valor_esperado")
print("ferramenta",{k:round(v) for k,v in T.items()})
print(pd.DataFrame(rows,columns=["dias","Q3","Q4","semanas_ferramenta_ganha"]))
# baseline: preço entre vivos (chance>=0.01), sem usar a chance para ordenar
tot={"Q3":0,"Q4":0};wins=0
for s in snaps:
    s=s.copy(); s["b"]=s.sales_price.where(s.chance>=0.01,0); q="Q3" if s.date.iloc[0]<"2017-10-01" else "Q4"
    v=cap(s,"b"); tot[q]+=v; wins+=cap(s,"valor_esperado")>v
print("preço entre 'vivos'",{k:round(v) for k,v in tot.items()},"ferramenta ganha em",wins,"semanas")
# teto: receita total disponível (todos os deals do vendedor) -> quanto top10 captura
tot_all=sum(s.revenue_after.sum() for s in snaps); print("receita total em todos os abertos (soma semanas)",round(tot_all),"ferramenta captura",round(sum(T.values())/tot_all,3))
# evidência indireta de tempo gasto: por vendedor, zumbis vs desempenho
z=d[d.deal_stage=="Engaging"].groupby("sales_agent").size().rename("zumbis")
w=d[d.deal_stage=="Won"].groupby("sales_agent").agg(won=("close_value","size"),rev=("close_value","sum"))
cl2=d[d.deal_stage.isin(["Won","Lost"])].groupby("sales_agent").agg(n=("deal_stage","size"),wr=("deal_stage",lambda s:(s=="Won").mean()))
m=pd.concat([z,w,cl2],axis=1).dropna(); m["zshare"]=m.zumbis/(m.zumbis+m.n)
print("n vendedores",len(m))
for a,b in [("zumbis","won"),("zumbis","rev"),("zshare","wr"),("zshare","rev"),("zumbis","n")]:
    r=spearmanr(m[a],m[b]); print(a,b,"rho=%.2f p=%.3f"%(r.correlation,r.pvalue))
# perdas: tempo até perder
c=d[d.deal_stage=="Lost"]; cyc=(c.close_date-c.engage_date).dt.days
print("Lost: mediana dias",cyc.median(),"frac<=14d",round((cyc<=14).mean(),3),"dias-deal Lost total",cyc.sum(),"Won total",(d[d.deal_stage=="Won"].close_date-d[d.deal_stage=="Won"].engage_date).dt.days.sum())
