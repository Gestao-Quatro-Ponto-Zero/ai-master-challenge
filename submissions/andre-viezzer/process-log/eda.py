import csv,collections as C,datetime as D,statistics as S
r=lambda f:list(csv.DictReader(open(f,encoding='utf-8')))
acc={a['account']:a for a in r('accounts.csv')};prod={p['product']:p for p in r('products.csv')};team={t['sales_agent']:t for t in r('sales_teams.csv')}
P=r('sales_pipeline.csv')
print(len(P),len(acc),len(prod),len(team))
print(C.Counter(p['deal_stage'] for p in P))
print('products in pipe',C.Counter(p['product'] for p in P))
print('prod table',list(prod))
print('missing account by stage',C.Counter(p['deal_stage'] for p in P if not p['account']))
print('agents not in team',set(p['sales_agent'] for p in P)-set(team), 'agents w/o deals', set(team)-set(p['sales_agent'] for p in P))
print('sectors',C.Counter(a['sector'] for a in acc.values()))
print('missing engage by stage',C.Counter(p['deal_stage'] for p in P if not p['engage_date']))
print('missing close by stage',C.Counter(p['deal_stage'] for p in P if not p['close_date']))
d=lambda s:D.date.fromisoformat(s) if s else None
for st in ['Won','Lost','Engaging','Prospecting']:
  e=[d(p['engage_date']) for p in P if p['deal_stage']==st and p['engage_date']]
  c=[d(p['close_date']) for p in P if p['deal_stage']==st and p['close_date']]
  print(st,'engage',min(e) if e else None,max(e) if e else None,'close',min(c) if c else None,max(c) if c else None)
cyc=[(d(p['close_date'])-d(p['engage_date'])).days for p in P if p['deal_stage'] in('Won','Lost')]
won=[(d(p['close_date'])-d(p['engage_date'])).days for p in P if p['deal_stage']=='Won']
lost=[(d(p['close_date'])-d(p['engage_date'])).days for p in P if p['deal_stage']=='Lost']
q=lambda x:S.quantiles(x,n=10)
print('won cycle deciles',q(won));print('lost cycle deciles',q(lost))
# win rate by cycle bucket
b=C.defaultdict(lambda:[0,0])
for p in P:
  if p['deal_stage'] in('Won','Lost'):
    k=min((d(p['close_date'])-d(p['engage_date'])).days//15,8); b[k][p['deal_stage']=='Won']+=1
for k in sorted(b): print('cycle',k*15,b[k][1]/sum(b[k]),sum(b[k]))
def wr(key):
  t=C.defaultdict(lambda:[0,0])
  for p in P:
    if p['deal_stage'] in('Won','Lost'): t[key(p)][p['deal_stage']=='Won']+=1
  return sorted(((k,round(v[1]/sum(v),3),sum(v)) for k,v in t.items()),key=lambda x:-x[1])
print('overall',wr(lambda p:1))
print('product',wr(lambda p:p['product']))
print('sector',wr(lambda p:acc.get(p['account'],{}).get('sector','?')))
print('region',wr(lambda p:team.get(p['sales_agent'],{}).get('regional_office')))
print('manager',wr(lambda p:team.get(p['sales_agent'],{}).get('manager')))
a=wr(lambda p:p['sales_agent']);print('agent',a[:3],a[-3:])
ac=wr(lambda p:p['account']);print('account',ac[:3],ac[-3:])
print('engage month',wr(lambda p:p['engage_date'][:7]))
print('close month',wr(lambda p:p['close_date'][:7]))
# close value vs price
ratios=[int(p['close_value'])/int(prod.get(p['product'],prod.get('GTX Pro'))['sales_price']) for p in P if p['deal_stage']=='Won']
print('won value/price deciles',q(ratios))
print('lost close values',C.Counter(p['close_value'] for p in P if p['deal_stage']=='Lost'))
print('open close_value',C.Counter(p['close_value'] for p in P if p['deal_stage'] in('Engaging','Prospecting')).most_common(3))
# open deals per agent
o=C.Counter(p['sales_agent'] for p in P if p['deal_stage'] in('Engaging','Prospecting'));print('open/agent',min(o.values()),max(o.values()),len(o))
# revenue bucket
print('size',wr(lambda p:'big' if p['account'] and float(acc[p['account']]['revenue'])>1000 else ('small' if p['account'] else 'na')))
# repeat account-product history
