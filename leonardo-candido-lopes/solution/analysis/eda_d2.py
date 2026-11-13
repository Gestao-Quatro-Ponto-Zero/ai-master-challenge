import pandas as pd, numpy as np, json, re, itertools
from collections import Counter
from scipy import stats
D='/home/ubuntu/g4_challenge/'
d=pd.read_csv(D+'data/all_tickets_processed_improved_v3.csv'); R={}
R['shape']=d.shape; R['nulls']=d.isna().sum().to_dict(); R['dup_exact']=int(d.duplicated().sum()); R['dup_doc']=int(d.Document.duplicated().sum())
d['tok']=d.Document.str.split(); d['nw']=d.tok.str.len(); d['nc']=d.Document.str.len()
norm=d.Document.str.replace(r'\s+',' ',regex=True).str.strip()
R['dup_norm']=int(norm.duplicated().sum())
R['dup_first15w']=int(d.tok.str[:15].str.join(' ').duplicated().sum())
g=d.assign(k=d.tok.str[:15].str.join(' ')); gg=g[g.k.duplicated(keep=False)].groupby('k').Topic_group.nunique()
R['first15w_groups_conflicting_label']=int((gg>1).sum()); R['first15w_groups']=int(len(gg))
vc=d.Topic_group.value_counts(); R['dist']={k:[int(v),round(v/len(d),4)] for k,v in vc.items()}; R['imbalance_ratio']=round(vc.max()/vc.min(),2)
def P(s): return dict(n=int(s.count()),min=int(s.min()),p25=float(s.quantile(.25)),median=float(s.median()),p75=float(s.quantile(.75)),p90=float(s.quantile(.9)),max=int(s.max()))
R['words']=P(d.nw); R['chars']=P(d.nc)
R['words_by_cat']={k:P(x.nw) for k,x in d.groupby('Topic_group')}
R['kw_len_cat']=float(stats.kruskal(*[x.nw for _,x in d.groupby('Topic_group')])[1])
R['lt5w']=int((d.nw<5).sum()); R['lt5w_by_cat']=d[d.nw<5].Topic_group.value_counts().to_dict(); R['lt5w_examples']=d[d.nw<5].head(8)[['Document','Topic_group']].values.tolist()
R['lt10w']=int((d.nw<10).sum()); R['gt300w']=int((d.nw>300).sum())
R['has_upper']=float(d.Document.str.contains('[A-Z]').mean()); R['has_digit']=float(d.Document.str.contains(r'\d').mean())
allc=Counter(w for t in d.tok for w in t); R['vocab_total']=len(allc); R['hapax']=sum(1 for v in allc.values() if v==1)
R['top20_global']=allc.most_common(20)
cats=vc.index.tolist(); cc={c:Counter(w for t in d[d.Topic_group==c].tok for w in t) for c in cats}
docf={c:Counter(w for t in d[d.Topic_group==c].tok for w in set(t)) for c in cats}
R['vocab_by_cat']={c:dict(vocab=len(cc[c]),tokens=int(sum(cc[c].values())),ttr=round(len(cc[c])/sum(cc[c].values()),4)) for c in cats}
# distinctive words: doc freq in class vs others (lift), min df 50
N={c:(d.Topic_group==c).sum() for c in cats}; tot=Counter(); [tot.update(docf[c]) for c in cats]
dist={}
for c in cats:
    rows=[]
    for w,f in docf[c].items():
        if f<50: continue
        pin=f/N[c]; pout=(tot[w]-f)/(len(d)-N[c]); rows.append((w,round(pin,3),round(pout,3),round(pin/(pout+1e-6),1)))
    dist[c]=sorted(rows,key=lambda r:-r[3])[:10]
R['distinctive']=dist
R['top15_by_cat']={c:[w for w,_ in docf[c].most_common(15)] for c in cats}
# overlap: jaccard top-200 doc-freq words, and cosine of tf vectors
top={c:set(w for w,_ in docf[c].most_common(200)) for c in cats}
vocab=sorted(allc); idx={w:i for i,w in enumerate(vocab)}
def vec(c):
    v=np.zeros(len(vocab)); 
    for w,f in cc[c].items(): v[idx[w]]=f
    return v/np.linalg.norm(v)
V={c:vec(c) for c in cats}
pr=[dict(a=a,b=b,jaccard_top200=round(len(top[a]&top[b])/len(top[a]|top[b]),3),cosine_tf=round(float(V[a]@V[b]),3)) for a,b in itertools.combinations(cats,2)]
R['pairs']=sorted(pr,key=lambda r:-r['cosine_tf'])
# label-quality probes: strong keywords appearing in "unexpected" classes
probes={'password':'Access','laptop':'Hardware','purchase':'Purchase','order':'Purchase','administrator':'Administrative rights','admin':'Administrative rights','disk':'Storage','storage':'Storage','salary':'HR Support','project':'Internal Project'}
R['probes']={}
for w,exp in probes.items():
    m=d.tok.apply(lambda t:w in t); s=d[m].Topic_group.value_counts(normalize=True).round(3)
    R['probes'][w]=dict(n=int(m.sum()),expected=exp,pct_expected=float(s.get(exp,0)),top_classes=s.head(3).to_dict())
# samples for manual inspection
rng=np.random.default_rng(1)
R['samples']={c:[x[:220] for x in d[d.Topic_group==c].Document.sample(3,random_state=1)] for c in cats}
# HR Support sanity: check how HR-ish the HR class is
hrw=['salary','payroll','leave','vacation','holiday','employee','hr','contract','benefits','onboarding']
R['hr_terms_pct']={c:round(d[d.Topic_group==c].tok.apply(lambda t:any(w in t for w in hrw)).mean(),3) for c in cats}
# cross-dataset
d1=pd.read_csv(D+'data/customer_support_tickets.csv')
txt=(d1['Ticket Subject']+' '+d1['Ticket Description'].str.replace('{product_purchased}',' ',regex=False)).str.lower().str.findall(r'[a-z]+')
t1=Counter(w for t in txt for w in t)
R['d1_vocab']=len(t1); R['d1_token_coverage_by_d2']=round(sum(f for w,f in t1.items() if w in allc)/sum(t1.values()),4); R['d1_type_coverage_by_d2']=round(sum(1 for w in t1 if w in allc)/len(t1),4)
d1top=[w for w,_ in t1.most_common(300)]; R['d1_top300_in_d2_top300']=len(set(d1top)&set(w for w,_ in allc.most_common(300)))
R['d1_cols']=d1.columns.tolist()
R['common_cols']=list(set(d1.columns)&set(d.columns))
R['d1_frt_hour_flat']=dict(zip(['chi2','p'],map(float,stats.chisquare(pd.to_datetime(d1['First Response Time']).dt.hour.value_counts().values))))
json.dump(R,open(D+'analysis/eda_d2_results.json','w'),indent=1,default=str,ensure_ascii=False)
import plotly.graph_objects as go
fig=go.Figure(go.Bar(x=vc.index,y=vc.values,text=[f'{v/len(d):.1%}' for v in vc.values],textposition='outside'))
fig.add_hline(y=len(d)/8,line_dash='dot',annotation_text='Distribuição balanceada (1/8)')
fig.update_layout(title=f'Dataset 2 — Tickets por categoria (n={len(d):,}) · razão maior/menor = {R["imbalance_ratio"]}x',yaxis_title='tickets'); fig.write_json(D+'analysis/charts/d2_categories.json')
fig=go.Figure([go.Box(y=d[d.Topic_group==c].nw.clip(upper=d.nw.quantile(.99)),name=c) for c in cats])
fig.update_layout(title='Dataset 2 — Comprimento dos textos por categoria (palavras, truncado no P99)',yaxis_title='palavras',showlegend=False); fig.write_json(D+'analysis/charts/d2_length.json')
M=np.array([[float(V[a]@V[b]) for b in cats] for a in cats])
fig=go.Figure(go.Heatmap(z=M,x=cats,y=cats,text=np.round(M,2),texttemplate='%{text}',colorscale='Reds',zmin=0.5,zmax=1))
fig.update_layout(title='Dataset 2 — Similaridade de vocabulário entre categorias (cosseno de frequências)'); fig.write_json(D+'analysis/charts/d2_overlap.json')
print('ok')
