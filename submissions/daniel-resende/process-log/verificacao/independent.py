"""Independent CSV calculation. Imports no submission code."""
import csv
import json
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

BASE = Path('submissions/daniel-resende/solution')
OUT = Path('.verif/runtime') / BASE / 'out'
def read(name):
    with (BASE / 'data' / name).open(newline='') as f:
        return list(csv.DictReader(f))
def day(s):
    return date.fromisoformat(s) if s else None
rows = read('sales_pipeline.csv')
accounts = read('accounts.csv')
products = {r['product']: int(r['sales_price']) for r in read('products.csv')}
teams = read('sales_teams.csv')
byid = {r['opportunity_id']: r for r in rows}
assert len(byid) == len(rows)
for r in rows:
    r['e'] = day(r['engage_date'])
    r['c'] = day(r['close_date'])
    r['price'] = products['GTX Pro' if r['product'] == 'GTXPro' else r['product']]
def quarter_end(e):
    # Add two quarters to start of engagement quarter; subtract one day.
    m = ((e.month - 1) // 3) * 3 + 1 + 6
    return date(e.year + (m-1)//12, (m-1)%12+1, 1) - timedelta(days=1)
def snapshot(cut):
    known_closed = [r for r in rows if r['e'] and r['c'] and r['c'] <= cut]
    longest = max((r['c']-r['e']).days for r in known_closed if r['deal_stage']=='Won')
    opened = [r for r in rows if r['e'] and r['e'] <= cut and (not r['c'] or r['c'] > cut)]
    dead = {r['opportunity_id'] for r in opened if (cut-r['e']).days > longest or quarter_end(r['e']) <= cut}
    return longest, opened, dead
def outcomes(ids):
    return dict(Counter(byid[i]['deal_stage'] for i in ids))
closed = [r for r in rows if r['c']]
print('csv_rows',len(rows),'accounts',len(accounts),'products',len(products),'teams',len(teams))
print('longest_win',max((r['c']-r['e']).days for r in closed if r['deal_stage']=='Won'))
late=[r for r in closed if r['c']>quarter_end(r['e'])]
print('late_closings',len(late),'of',len(closed), [(r['opportunity_id'],r['deal_stage'],r['engage_date'],r['close_date']) for r in late])
shaping = ['2017-06-01','2017-06-16','2017-07-01','2017-07-16','2017-08-01','2017-08-16','2017-09-01','2017-09-16','2017-10-02']
confirmation = ['2017-07-08','2017-08-24','2017-09-24']
for label,cuts in [('all12', sorted(shaping+confirmation)),('confirmation3',confirmation)]:
    ever=set()
    for c in cuts:
        longest,opened,dead = snapshot(day(c))
        ever.update(dead)
        print('cut',c,'known_max',longest,'open',len(opened),'dead',len(dead),'outcomes',outcomes(dead))
    print(label,'DISTINCT',len(ever),'outcomes',outcomes(ever))

cut=day('2017-12-31')
longest,opened,dead=snapshot(cut)
alive=[r for r in opened if r['opportunity_id'] not in dead]
queue=[r for r in rows if r['deal_stage']=='Prospecting']
clean=[r for r in opened if r['opportunity_id'] in dead]
for name,group in [('alive',alive),('queue',queue),('clean',clean)]:
    print('default',name,len(group),'value',sum(r['price'] for r in group))
print('open_without_account',sum(not r['account'] for r in opened+queue),'of',len(opened+queue))
print('alive_without_account',sum(not r['account'] for r in alive))
print('queue_no_engage_date',sum(not r['e'] for r in queue),'of',len(queue))
print('sellers_without_alive',sum(not any(r['sales_agent']==t['sales_agent'] for r in alive) for t in teams))
for region in sorted({t['regional_office'] for t in teams}):
    sellers={t['sales_agent'] for t in teams if t['regional_office']==region}
    print('region',region,*[(name,len([r for r in group if r['sales_agent'] in sellers])) for name,group in [('alive',alive),('queue',queue),('clean',clean)]])
pairs=ties=0
for t in teams:
    prices=sorted(r['price'] for r in alive if r['sales_agent']==t['sales_agent'])
    pairs+=max(0,len(prices)-1)
    ties+=sum(a==b for a,b in zip(prices,prices[1:]))
print('prices',len(set(products.values())),'adjacent_pairs',pairs,'ties',ties)
for c in ['2017-08-16','2017-10-02','2017-12-31']:
    c=day(c)
    longest,_,_=snapshot(c)
    first=min(r['c'] for r in closed if r['c']<=c)
    pool=[r for r in rows if r['e'] and first<=r['e']<=c-timedelta(days=longest+1)]
    print('life_table',c,'pool',len(pool))
    for age in [0,30,60,90,120,138]:
        risk=[r for r in pool if not r['c'] or r['c']>c or (r['c']-r['e']).days>age]
        wins=sum(r['deal_stage']=='Won' and bool(r['c']) and r['c']<=c for r in risk)
        print(' age',age,'reached',len(risk),'wins',wins,'per100',round(100*wins/len(risk)) if risk else None)

for path in sorted(OUT.glob('score-*.json')):
    score=json.loads(path.read_text())
    monday=day(score['meta']['monday']); cut=monday-timedelta(days=1)
    longest,opened,dead=snapshot(cut)
    expected={r['opportunity_id']:('clean' if r['opportunity_id'] in dead else 'alive') for r in opened}
    if monday==day('2018-01-01'):
        expected.update({r['opportunity_id']:'queue' for r in queue})
    actual={r['id']:b for s in score['sellers'] for b in ['alive','queue','clean'] for r in s[b]}
    mismatch=[(i,expected.get(i),actual.get(i)) for i in expected.keys()|actual.keys() if expected.get(i)!=actual.get(i)]
    print('compare_emitted',monday,'open',len(opened),'clean',len(dead),'mismatches',len(mismatch),mismatch[:10])
    for group in ['by_manager','by_region']:
        for total in score['team'][group]:
            key='manager' if group=='by_manager' else 'region'
            ss=[s for s in score['sellers'] if s[key]==total[key]]
            for n in ['alive','alive_value','queue','queue_value','clean','clean_value','cooling']:
                assert sum(s['headline'][n] or 0 for s in ss)==total[n], (monday,group,total[key],n)
    for n in ['alive','alive_value','queue','queue_value','clean','clean_value','cooling']:
        assert sum(s['headline'][n] or 0 for s in score['sellers'])==score['team']['total'][n]
    for s in score['sellers']:
        assert s['alive']==sorted(s['alive'],key=lambda r:(-r['value'],-r['days_left'],r['id']))
    print('totals_and_alive_order_ok',monday)
    exact=[(s['seller'],r['id'],r['days_open'],r['window_end']) for s in score['sellers'] for r in s['alive'] if r['window_end']==monday.isoformat()]
    print('deadline_is_monday',monday,len(exact),exact[:5])
    if not score['meta']['past']:
        for label,predicate in [('no_alive',lambda s:not s['alive']),('nothing_to_start',lambda s:not s['queue']),('neither',lambda s:not s['alive'] and not s['queue']),('no_deals',lambda s:not s['alive'] and not s['queue'] and not s['clean'])]:
            print(label,[(s['seller'],s['headline']['alive'],s['headline']['queue'],s['headline']['clean']) for s in score['sellers'] if predicate(s)])
print('independent checks complete')
