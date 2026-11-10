"""Check stored placeholders against emitted score, without submission imports."""
import json
import re
from pathlib import Path
ROOT=Path('submissions/daniel-resende/solution')
OUT=Path('.verif/runtime')/ROOT/'out'
score=json.loads((OUT/'score-2018-01-01.json').read_text())
index=json.loads((OUT/'index.json').read_text())
texts=json.loads((ROOT/'ai/textos.json').read_text())['texts']
seller={s['seller']:s for s in score['sellers']}
managers={m['manager']:m for m in score['team']['by_manager']}
deals={d['id']:(s,d) for s in score['sellers'] for d in s['alive']}
play={'trabalhar':'Trabalhar esta semana','confirmar':'Confirmar esta semana se segue de pé','engajar':'Engajar e registrar a data','encerrar':'Encerrar no CRM e tirar da segunda-feira'}
def left(n):
    return 'é o último dia do prazo' if n==0 else 'falta 1 dia de prazo' if n==1 else f'faltam {n} dias de prazo'
def phrases(n,name,plural,zero):
    return zero if n==0 else f'{n} {name if n==1 else plural}'
def summary(counts):
    f={k:counts[k] for k in ['alive','alive_value','queue','queue_value','clean','clean_value','cooling']}
    for key,noun,plural,zero in [('alive','negócio no prazo','negócios no prazo','nenhum negócio no prazo'),('queue','negócio para iniciar','negócios para iniciar','nenhum negócio para iniciar'),('clean','negócio vencido','negócios vencidos','nenhum negócio vencido')]:
        f[key+'_phrase']=phrases(f[key],noun,plural,zero)
    if f['cooling']:f['cooling_phrase']=f"{f['cooling']} com o prazo acabando"
    ev=index['evidence']; f.update(evidence_deals=ev['distinct_deals_past_window'],evidence_won=ev['won_after'])
    assert ev['won_after']==0
    f['evidence_phrase']=f"nenhum dos {f['evidence_deals']} negócios distintos que venceram foi ganho depois"
    return f
def expected(t):
    f={'monday':score['meta']['monday']}
    if t['kind']=='deal':
        s,d=deals[t['target']['deal_id']]
        f.update(seller=s['seller'],product=d['product'],value=d['value'],engage_date=d['engage_date'],days_open=d['days_open'],days_left=d['days_left'],window_end=d['window_end'],block='no prazo',play_label=play[d['play']],rank=d['rank'],alive_count=s['headline']['alive'],longest_win_days=score['meta']['window']['longest_win_days'],time_sentence=d['time_sentence'],days_left_phrase=left(d['days_left']))
        f['days_open_phrase']=f"aberto há {d['days_open']} {'dia' if d['days_open']==1 else 'dias'}"
        if d['account']:f['account']=d['account']
        if d['cooling']:f['cooling_label']='com o prazo acabando'
    elif t['kind']=='briefing':
        s=seller[t['target']['seller']]
        f.update(summary(s['headline']),seller=s['seller'],longest_win_days=score['meta']['window']['longest_win_days'])
        for i,d in enumerate(s['alive'][:3],1):
            for key in ['product','value','days_left']:f[f'{key}_{i}']=d[key]
            f[f'days_left_phrase_{i}']=left(d['days_left'])
            if d['account']:f[f'account_{i}']=d['account']
    else:
        m=managers[t['target']['manager']]
        f.update(summary(m),manager=m['manager'],region=m['region'],sellers=m['sellers'],sellers_without_alive=m['sellers_without_alive'])
        names=[s['seller'] for s in score['sellers'] if s['manager']==m['manager'] and not s['alive']]
        if names:f['names_without_alive']=names
        f['without_alive_phrase']=f"{m['sellers_without_alive']} de {m['sellers']} vendedores sem nenhum negócio no prazo" if names else 'nenhum vendedor sem negócio no prazo'
    return f
MONEY={'value','alive_value','queue_value','clean_value','value_1','value_2','value_3'}
DATE={'engage_date','window_end','counted_on','monday'}
def fmt(k,v):
    if k in MONEY:return 'US$ '+f'{v:,.0f}'.replace(',','.')
    if k in DATE:return '/'.join(v.split('-')[::-1])
    if isinstance(v,list):return ', '.join(v[:-1])+' e '+v[-1] if len(v)>1 else ''.join(v)
    return str(v)
seen=set(); parts=placeholders=0
for t in texts:
    assert t['id'] not in seen;seen.add(t['id'])
    f=expected(t)
    assert f==t['facts'],(t['id'],'facts differ',[(k,f.get(k),t['facts'].get(k)) for k in f.keys()|t['facts'].keys() if f.get(k)!=t['facts'].get(k)])
    for p in t['parts'].values():
        parts+=1;template=p['template']; placeholders+=len(re.findall(r'\{([^{}]+)\}',template))
        assert not re.search(r'\d',re.sub(r'\{[^{}]+\}','',template)),t['id']
        rendered=re.sub(r'\{([^{}]+)\}',lambda m:fmt(m[1],f[m[1]]),template)
        rendered=re.sub(r'(^|[.!?] +)([a-zà-ÿ])',lambda m:m[1]+m[2].upper(),rendered)
        assert rendered==p['text'],(t['id'],'render mismatch')
    assert t['provenance']['model'] and re.fullmatch(r'\d{4}-\d{2}-\d{2}',t['provenance']['generated_on'])
print('independent AI check:',len(texts),'targets',parts,'parts',placeholders,'placeholders; facts/render/digits/provenance OK')
print('kinds:',{k:sum(t['kind']==k for t in texts) for k in ['deal','briefing','manager']})
# Deliberate sample, spread across every kind and every template batch.
sample=[t for t in texts if t['kind']=='deal'][::5][:20]+[t for t in texts if t['kind']=='briefing'][::4][:7]+[t for t in texts if t['kind']=='manager'][::2][:3]
assert len(sample)==30
for t in sample:
    print('\nSAMPLE',t['id'],t['provenance']['model'],t['provenance']['generated_on'])
    for name,p in t['parts'].items():print(name+':',p['text'])
