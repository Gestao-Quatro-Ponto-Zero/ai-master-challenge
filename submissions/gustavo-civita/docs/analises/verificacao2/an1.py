import sys, json, hashlib
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3] / "solution"))
import pandas as pd, numpy as np
import scoring, backtest, build
pd.set_option("display.width",250); pd.set_option("display.max_rows",200)
deals = scoring.load_pipeline()
today = scoring.reference_date(deals)
scored, model = scoring.score_open_deals(deals, today)
print("stages", deals.deal_stage.value_counts().to_dict())
print("lists", scored.lista.value_counts().to_dict())
print("faixa", scored.faixa.value_counts().to_dict())
print("fechaEsteMes among foco", (scored[scored.lista=='foco'].chance_soon>=0.10).sum())
print("Engaging sem engage_date", ((deals.deal_stage=='Engaging')&deals.engage_date.isna()).sum())
op = scored
print("open sem conta", op.account.isna().mean().round(3), "por lista", op.groupby('lista').account.apply(lambda s: s.isna().mean().round(3)).to_dict())
print("closed sem conta", deals[deals.deal_stage.isin(['Won','Lost'])].account.isna().sum())
teams = pd.read_csv(scoring.DATA_DIR/"sales_teams.csv")
print("sellers total", len(teams), "com deal", deals.sales_agent.nunique(), "com aberto", op.sales_agent.nunique())
print("sem nenhum deal:", sorted(set(teams.sales_agent)-set(deals.sales_agent)))
print("sem aberto:", sorted(set(teams.sales_agent)-set(op.sales_agent)))
t = op.pivot_table(index=['regional_office','sales_agent'], columns='lista', values='opportunity_id', aggfunc='count', fill_value=0)
t['hot']=op[op.chance_soon>=0.10].groupby(['regional_office','sales_agent']).size()
t['semconta']=op[op.account.isna()].groupby(['regional_office','sales_agent']).size()
print(t.fillna(0).astype(int))
f = op[op.lista=='foco']
print("foco age describe", f.age.describe().to_dict())
print("foco age hist", f.age.value_counts(bins=[0,15,30,45,60,75,90,105,120,140]).sort_index().to_dict())
print("foco chance by faixa/age", f.groupby('faixa').age.agg(['min','max','count']))
print("chance curve today:", [(a, round(model['chance_by_age'][a],3)) for a in range(0,141,10)])
print("soon curve today:", [(a, round(model['soon_by_age'][a],3)) for a in range(0,141,10)])
print("longest cycle", model['longest_cycle'])
eng = op[op.deal_stage=='Engaging']
print("engaging age", eng.age.describe().to_dict())
# ordering = price ordering?
same=0; tot=0; kend=[]
for a,g in f.groupby('sales_agent'):
    tot+=1
    o1=g.sort_values(['valor_esperado','sales_price'],ascending=False).opportunity_id.tolist()
    o2=g.sort_values(['sales_price'],ascending=False,kind='stable').sales_price.tolist()
    p1=g.sort_values(['valor_esperado','sales_price'],ascending=False).sales_price.tolist()
    same += (p1==o2)
print("sellers whose foco order is identical to pure price order:", same, "/", tot)
print("corr spearman score x price", f[['score','sales_price','chance']].corr(method='spearman').round(3).to_dict())
print("distinct chance values in foco", f.chance.round(3).nunique(), "range", f.chance.min(), f.chance.max())
# determinism of build
import io
payload_txt = open(__import__("pathlib").Path(__file__).resolve().parents[3] / "solution" / "app" / "data.js",encoding='utf-8').read()
build.OUT = __import__('pathlib').Path(__import__("tempfile").mkdtemp()) / "data.js"
build.main()
new = open(build.OUT,encoding='utf-8').read()
print("data.js identical to regenerated:", new==payload_txt, len(new), len(payload_txt))
