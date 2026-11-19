import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3] / "solution"))
import pandas as pd, numpy as np
import scoring, backtest
pd.set_option("display.width",250); pd.set_option("display.max_rows",200); pd.set_option("display.max_columns",30)
deals = scoring.load_pipeline()
today = scoring.reference_date(deals)
op,_ = scoring.score_open_deals(deals, today)
t = op.pivot_table(index=['regional_office','manager','sales_agent'], columns='lista', values='opportunity_id', aggfunc='count', fill_value=0)
t['hot']=op[op.chance_soon>=0.10].groupby(['regional_office','manager','sales_agent']).size()
t['foco_alta']=op[op.faixa=='alta'].groupby(['regional_office','manager','sales_agent']).size()
t['score70']=op[op.score>=70].groupby(['regional_office','manager','sales_agent']).size()
print(t.fillna(0).astype(int).to_string())
print("sellers with 0 foco:", (t.foco==0).sum(), "with <=3 foco:", (t.foco<=3).sum())

# ---- backtest sensitivity
snaps=[]
for d in backtest.SNAPSHOTS:
    s=backtest.snapshot_with_predictions(deals,pd.Timestamp(d)); s['snap']=d; snaps.append(s)
A=pd.concat(snaps)
print("deal-weeks", len(A), "unique deals", A.opportunity_id.nunique())
parked=A[A.chance<scoring.MIN_CHANCE]
print("parked deal-weeks", len(parked), "unique", parked.opportunity_id.nunique(), "unique won", parked[parked.won_after].opportunity_id.nunique(), "unique lost", parked[parked.lost_after].opportunity_id.nunique(), "still open", parked[~parked.won_after&~parked.lost_after].opportunity_id.nunique())
live=A[A.chance>=scoring.MIN_CHANCE].copy(); live['faixa']=live.chance.map(scoring.band)
print("bands unique deals:", live.groupby('faixa').opportunity_id.nunique().to_dict())
# first-seen band per deal
fs=live.sort_values('snap').groupby('opportunity_id').first()
print("band at first sighting -> win rate", fs.groupby('faixa').won_after.agg(['size','mean']).round(3).to_dict())
# este mes among live only
fl = live.soon>=0.10
print("esteMes among live: flagged", fl.sum(), live[fl].won_soon.mean().round(3), "not flagged", (~fl).sum(), live[~fl].won_soon.mean().round(3))
# calibration by age bucket
A['ageb']=pd.cut(A.age,[-1,15,30,45,60,75,90,105,140,500])
print(A.groupby('ageb',observed=True).agg(n=('chance','size'),pred=('chance','mean'),real=('won_after','mean')).round(3))
for q,g in A.groupby(pd.to_datetime(A.snap).dt.quarter):
    print("Q",q); print(g.groupby('ageb',observed=True).agg(n=('chance','size'),pred=('chance','mean'),real=('won_after','mean')).round(3))
# max single-snapshot miscalibration 60-75
m=A[(A.age>=60)&(A.age<=75)].groupby('snap').agg(n=('chance','size'),pred=('chance','mean'),real=('won_after','mean')).round(3)
print(m.assign(d=m.pred-m.real).sort_values('d').tail(4))

def captured(s, col, n):
    top=s.sort_values([col,'sales_price'],ascending=False).groupby('sales_agent').head(n)
    return top.revenue_after.sum()
rows=[]
for n in (3,5,10,20):
    for X in (45,60,75,90,105,120,138):
        tool=0; base=0; wins=0
        for d,s in A.groupby('snap'):
            s=s.copy(); s['b']=s.sales_price.where(s.age<=X,0)
            a=captured(s,'valor_esperado',n); b=captured(s,'b',n)
            tool+=a; base+=b; wins+= a>b
        rows.append((n,X,round(tool),round(base),round(tool/base-1,3),wins))
print(pd.DataFrame(rows,columns=['topN','recentDays','tool','base','gain','weeksWon']).to_string(index=False))
# newest first baseline, and ceiling (oracle)
for n in (5,10):
    tool=base=orc=0
    for d,s in A.groupby('snap'):
        s=s.copy(); s['young']=-s.age
        tool+=captured(s,'valor_esperado',n); base+=captured(s,'young',n); orc+=captured(s,'revenue_after',n)
    print("topN",n,"tool",round(tool),"youngest-first",round(base),"oracle",round(orc))
# independence: how many distinct deals in tool's top10 across weeks
print("total revenue of all deals ever open in window (unique):", A.drop_duplicates('opportunity_id').revenue_after.sum())
# quarter-end claim
for qe in ("2017-03-31","2017-06-30","2017-09-30","2017-12-31"):
    qe=pd.Timestamp(qe); qs=qe-pd.offsets.QuarterBegin(startingMonth=1)
    qs=pd.Timestamp(qe.year,qe.month-2,1)
    inq=deals[(deals.engage_date>=qs)&(deals.engage_date<=qe)]
    stillopen=inq.close_date.isna()|(inq.close_date>qe)
    print(qe.date(), "engaged in quarter", len(inq), "still open at QE", round(stillopen.mean(),3))
# max cycle & closes after next quarter
c=deals[deals.close_date.notna()]
print("cycle max", (c.close_date-c.engage_date).dt.days.max(), "first close", deals.close_date.min().date(), "engage range", deals.engage_date.min().date(), deals.engage_date.max().date())
eq=c.engage_date.dt.year*4+c.engage_date.dt.quarter; cq=c.close_date.dt.year*4+c.close_date.dt.quarter
print("quarters between engage and close", (cq-eq).value_counts().to_dict())
# snapshot at 09-30: what happened to bands
s=backtest.snapshot_with_predictions(deals,pd.Timestamp("2017-09-30")); s=s[s.chance>=0.01]; s['faixa']=s.chance.map(scoring.band)
print("09-30 snapshot bands", s.groupby('faixa').won_after.agg(['size','mean']).round(3).to_dict())
# vendor effect incl. open deals (stalled share)
e=deals[deals.deal_stage!='Prospecting']
g=e.groupby('sales_agent').apply(lambda x: pd.Series({'n':len(x),'won_closed':(x.deal_stage=='Won').sum()/max(1,x.deal_stage.isin(['Won','Lost']).sum()),'stuck':(x.deal_stage=='Engaging').mean()}))
print(g.sort_values('stuck').round(3).to_string())
from scipy.stats import chi2_contingency
print("chi2 p stuck x seller", chi2_contingency(pd.crosstab(e.sales_agent,e.deal_stage=='Engaging'))[1])
print("chi2 p stuck x region", chi2_contingency(pd.crosstab(e.regional_office,e.deal_stage=='Engaging'))[1], e.groupby('regional_office').apply(lambda x:(x.deal_stage=='Engaging').mean()).round(3).to_dict())
print("chi2 p stuck x product", chi2_contingency(pd.crosstab(e['product'],e.deal_stage=='Engaging'))[1], e.groupby('product').apply(lambda x:(x.deal_stage=='Engaging').mean()).round(3).to_dict())
