import csv,collections as C,datetime as D,statistics as S
r=lambda f:list(csv.DictReader(open(f,encoding='utf-8')))
acc={a['account']:a for a in r('accounts.csv')};prod={p['product']:p for p in r('products.csv')};team={t['sales_agent']:t for t in r('sales_teams.csv')}
P=r('sales_pipeline.csv');d=D.date.fromisoformat
cl=[p for p in P if p['deal_stage'] in('Won','Lost')]
cy=lambda p:(d(p['close_date'])-d(p['engage_date'])).days
print('max cycle won',max(cy(p) for p in cl if p['deal_stage']=='Won'),'lost',max(cy(p) for p in cl if p['deal_stage']=='Lost'))
# conditional win given survived t days
for t in [0,7,14,21,30,45,60,90,120,138]:
  s=[p for p in cl if cy(p)>=t]; print('survived',t,len(s),round(sum(p['deal_stage']=='Won' for p in s)/len(s),3) if s else None)
snap=D.date(2017,12,31)
ages=[(snap-d(p['engage_date'])).days for p in P if p['deal_stage']=='Engaging']
print('engaging age deciles',S.quantiles(ages,n=10),'>138:',sum(a>138 for a in ages),'of',len(ages))
# engaged-date months of open deals
print(sorted(C.Counter(p['engage_date'][:7] for p in P if p['deal_stage']=='Engaging').items()))
# agent x product
t=C.defaultdict(lambda:[0,0])
for p in cl: t[(p['sales_agent'],p['product'])][p['deal_stage']=='Won']+=1
x=sorted(((k,round(v[1]/sum(v),2),sum(v)) for k,v in t.items() if sum(v)>=20),key=lambda z:z[1]);print('agentxprod lo',x[:4],'hi',x[-4:])
# account x product repeat purchases
w=C.Counter((p['account'],p['product']) for p in cl if p['deal_stage']=='Won');print('acct-prod pairs',len(w))
# agent stats: open load vs win rate
for a in sorted(team):
  o=sum(1 for p in P if p['sales_agent']==a and p['deal_stage'] in('Engaging','Prospecting'))
  c=[p for p in cl if p['sales_agent']==a]
  if c: print(a[:16].ljust(16),team[a]['manager'][:12],team[a]['regional_office'],'open',o,'closed',len(c),'wr',round(sum(p['deal_stage']=='Won' for p in c)/len(c),3),'avg won',round(S.mean([int(p['close_value']) for p in c if p['deal_stage']=='Won'])))
print('subsidiary',C.Counter(bool(a['subsidiary_of']) for a in acc.values()))
print('office',C.Counter(a['office_location'] for a in acc.values()).most_common(5))
