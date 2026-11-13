import pandas as pd,numpy as np,json,itertools
from collections import Counter
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS as SW
D='/home/ubuntu/g4_challenge/'
d=pd.read_csv(D+'data/all_tickets_processed_improved_v3.csv')
bp=set(SW)|set('hi hello dear please thank thanks regards kind best pm am re sent monday tuesday wednesday thursday friday saturday sunday january february march april may june july august september october november december fw fwd cheers ca la si help need team guys'.split())
d['tok']=d.Document.str.split().apply(lambda t:[w for w in t if w not in bp and len(w)>2])
R={'boilerplate_list_size':len(bp),'tokens_removed_pct':round(1-d.tok.str.len().sum()/d.Document.str.split().str.len().sum(),4),'empty_after_clean':int((d.tok.str.len()==0).sum()),'lt3_after_clean':int((d.tok.str.len()<3).sum())}
cats=d.Topic_group.value_counts().index.tolist()
docf={c:Counter(w for t in d[d.Topic_group==c].tok for w in set(t)) for c in cats}
cc={c:Counter(w for t in d[d.Topic_group==c].tok for w in t) for c in cats}
R['top10_clean']={c:[w for w,_ in docf[c].most_common(10)] for c in cats}
vocab=sorted(set().union(*[set(x) for x in cc.values()])); idx={w:i for i,w in enumerate(vocab)}
def vec(c):
    v=np.zeros(len(vocab))
    for w,f in cc[c].items(): v[idx[w]]=f
    return v/np.linalg.norm(v)
V={c:vec(c) for c in cats}; top={c:set(w for w,_ in docf[c].most_common(200)) for c in cats}
pr=[dict(a=a,b=b,jaccard_top200=round(len(top[a]&top[b])/len(top[a]|top[b]),3),cosine_tf=round(float(V[a]@V[b]),3)) for a,b in itertools.combinations(cats,2)]
R['pairs_clean']=sorted(pr,key=lambda r:-r['cosine_tf'])
json.dump(R,open(D+'analysis/eda_d2_clean_results.json','w'),indent=1,ensure_ascii=False)
import plotly.graph_objects as go
M=np.array([[float(V[a]@V[b]) for b in cats] for a in cats])
fig=go.Figure(go.Heatmap(z=M,x=cats,y=cats,text=np.round(M,2),texttemplate='%{text}',colorscale='Reds',zmin=0,zmax=1))
fig.update_layout(title='Dataset 2 — Similaridade de vocabulário entre categorias (cosseno, após remover stopwords e boilerplate de e-mail)'); fig.write_json(D+'analysis/charts/d2_overlap.json')
print(json.dumps(R,ensure_ascii=False)[:5000])
