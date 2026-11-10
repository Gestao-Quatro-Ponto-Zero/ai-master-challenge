"""Adversarial in-memory mutation; imported only from temporary working copy."""
import copy
import sys
from datetime import date
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path('.verif/runtime/submissions/daniel-resende/solution').resolve()))
import build
deals=build.v.load()
teams=build.v.read('sales_teams.csv')
monday=date(2017,10,2)
cut=date(2017,10,1)
end=date(2017,12,31)
def membership(ds):
    s=build.build_monday(ds,teams,monday,end)
    return [(x['seller'],b,[(d['id'],d['rank'],d['play']) for d in x[b]]) for x in s['sellers'] for b in ['alive','queue','clean']]
original=membership(deals)
mutated=copy.deepcopy(deals)
changed=0
for d in mutated:
    d['account']='VERIFIER_SENTINEL'
    if d['close'] and d['close']>cut:
        d['close']=date(2017,12,31)
        d['close_value']='987654321'
        d['stage']='Lost' if d['stage']=='Won' else 'Won'
        changed+=1
assert membership(mutated)==original
print('Future close date/value/final stage/time-to-close mutated:',changed,'rows; accounts mutated:',len(mutated))
print('Block/rank/play unchanged for 2017-10-02')
synthetic=copy.deepcopy(deals[0])
synthetic.update(id='VERIFIER_BOUNDARY',stage='Engaging',close=None,close_value='',engage=date(2018,9,20))
for monday in [date(2018,12,31),date(2019,1,7)]:
    score=build.build_monday(deals+[synthetic],teams,monday,date(2019,1,31))
    matches=[(b,d['days_open'],d['deadline'],d['days_left']) for s in score['sellers'] for b in ['alive','queue','clean'] for d in s[b] if d['id']=='VERIFIER_BOUNDARY']
    print('Synthetic exact quarter deadline Monday',monday,matches)
