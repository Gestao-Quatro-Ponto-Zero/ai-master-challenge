import pandas as pd, numpy as np, json, re
from scipy import stats
D='/home/ubuntu/g4_challenge/'
d=pd.read_csv(D+'data/customer_support_tickets.csv')
R={}
def gof(s):
    v=s.value_counts(); c,p=stats.chisquare(v.values); return dict(chi2=round(c,2),p=round(p,4),k=len(v),min=int(v.min()),max=int(v.max()),ratio=round(v.max()/v.min(),3))
def cv(a,b):
    t=pd.crosstab(a,b); c,p,dof,_=stats.chi2_contingency(t); n=t.values.sum()
    return dict(chi2=round(c,2),p=round(p,4),dof=dof,cramers_v=round(np.sqrt(c/(n*(min(t.shape)-1))),4),n=int(n))
R['shape']=d.shape; R['nulls']=d.isna().sum().to_dict()
R['dup_exact']=int(d.duplicated().sum()); R['dup_excl_id']=int(d.drop(columns='Ticket ID').duplicated().sum())
R['dup_name_email']=int(d.duplicated(['Customer Name','Customer Email']).sum())
R['dup_email']=int(d['Customer Email'].duplicated().sum()); R['dup_desc']=int(d['Ticket Description'].duplicated().sum())
R['email_domains']=d['Customer Email'].str.split('@').str[1].value_counts().head(5).to_dict()
R['name_suffix']=int(d['Customer Name'].str.contains(r'\b(?:MD|PhD|DDS|DVM|Jr\.|II|III)\b').sum())
# uniformity GOF
R['gof']={c:gof(d[c]) for c in ['Ticket Type','Ticket Channel','Ticket Priority','Ticket Status','Customer Gender','Ticket Subject','Product Purchased','Customer Age']}
R['gof']['Customer Satisfaction Rating']=gof(d['Customer Satisfaction Rating'].dropna())
R['age_range']=[int(d['Customer Age'].min()),int(d['Customer Age'].max())]
# independence
cl=d[d['Ticket Status']=='Closed']
pairs=[('Ticket Priority','Ticket Channel',d),('Ticket Priority','Ticket Type',d),('Ticket Type','Ticket Subject',d),('Ticket Type','Ticket Channel',d),('Ticket Priority','Ticket Status',d),('Ticket Channel','Ticket Status',d),('Ticket Type','Ticket Status',d),('Customer Gender','Ticket Type',d),('Product Purchased','Ticket Subject',d),
       ('Ticket Priority','Customer Satisfaction Rating',cl),('Ticket Channel','Customer Satisfaction Rating',cl),('Ticket Type','Customer Satisfaction Rating',cl)]
R['indep']={f'{a} x {b}':cv(df[a],df[b]) for a,b,df in pairs}
# subject vs type coherence
ct=pd.crosstab(d['Ticket Subject'],d['Ticket Type'],normalize='index').round(3)
R['subj_type_pct']=ct.loc[['Refund request','Cancellation request','Payment issue','Software bug','Hardware issue']].to_dict('index')
R['refund_subject_not_refund_type']=float(round(1-ct.loc['Refund request','Refund request'],3))
# product vs subject incoherence examples
sw=['Microsoft Office','Adobe Photoshop','Autodesk AutoCAD']
R['software_with_battery_or_hardware']=int(d[d['Product Purchased'].isin(sw)&d['Ticket Subject'].isin(['Battery life','Hardware issue','Display issue'])].shape[0]); R['software_n']=int(d['Product Purchased'].isin(sw).sum())
# timestamps
f=pd.to_datetime(d['First Response Time']); t=pd.to_datetime(d['Time to Resolution'])
R['frt_range']=[str(f.min()),str(f.max())]; R['ttr_range']=[str(t.min()),str(t.max())]
R['frt_on_0601_pct']=round((f.dt.date.astype(str)=='2023-06-01').sum()/f.notna().sum(),4); R['frt_n']=int(f.notna().sum())
R['same_seconds_pct']=float(((f.dt.second==t.dt.second)[t.notna()]).mean())
R['purchase_range']=[d['Date of Purchase'].min(),d['Date of Purchase'].max()]
d['delta_h']=(t-f).dt.total_seconds()/3600
dl=d['delta_h'].dropna(); R['delta_n']=int(len(dl)); R['delta_neg']=int((dl<0).sum()); R['delta_zero']=int((dl==0).sum())
R['delta_desc']=dl.describe().round(3).to_dict()
R['delta_ks_uniform_pm24']=dict(zip(['D','p'],[round(x,4) for x in stats.kstest(dl,'uniform',args=(-24,48))]))
R['delta_minutes_integer_pct']=float(((dl*60).round(6)%1==0).mean())
d['frt_hour']=f.dt.hour
R['frt_hour_gof']=gof(d['frt_hour'].dropna().astype(int)[f.dt.date.astype(str)=='2023-06-01'])
# text
desc=d['Ticket Description']
R['desc_unique']=int(desc.nunique()); R['placeholder_pct']=float(desc.str.contains('{product_purchased}',regex=False).mean())
first=desc.str.split(r'(?<=[.!?])\s',n=1,regex=True).str[0]
R['first_sentence_unique']=int(first.nunique()); R['first_sentence_top5']=first.value_counts().head(5).to_dict()
R['first_sentence_top10_cover']=round(first.value_counts().head(10).sum()/len(d),4)
res=d['Resolution'].dropna(); R['res_unique']=int(res.nunique()); R['res_n']=int(len(res))
R['res_words_median']=float(res.str.split().str.len().median())
tech=['replace','reset','update','refund','restart','install','reinstall','driver','firmware','cable','password','charger']
R['res_with_support_term_pct']=round(res.str.lower().str.contains('|'.join(tech)).mean(),4)
R['desc_words']=desc.str.split().str.len().describe(percentiles=[.25,.5,.75,.9]).round(1).to_dict()
# keyword coherence subject vs description
kw={'Battery life':'batter|charg','Network problem':'network|wifi|wi-fi|internet|connect','Data loss':'data|lost|file','Display issue':'display|screen','Account access':'account|log ?in|password|access'}
R['subject_keyword_hit']={s:dict(in_subject=round(desc[d['Ticket Subject']==s].str.lower().str.contains(p).mean(),3),other_subjects=round(desc[d['Ticket Subject']!=s].str.lower().str.contains(p).mean(),3)) for s,p in kw.items()}
# ---------- operational
R['status']=d['Ticket Status'].value_counts().to_dict()
R['vol']={c:{k:[int(v),round(v/len(d),4)] for k,v in d[c].value_counts().items()} for c in ['Ticket Channel','Ticket Type','Ticket Priority','Ticket Subject']}
def pct(s): return dict(n=int(s.count()),p25=round(s.quantile(.25),2),median=round(s.median(),2),p75=round(s.quantile(.75),2),p90=round(s.quantile(.9),2),p95=round(s.quantile(.95),2))
c=d[d['Ticket Status']=='Closed'].copy(); v=c[c.delta_h>=0].copy()
R['delta_all']=pct(c.delta_h); R['delta_valid']=pct(v.delta_h)
for g in ['Ticket Channel','Ticket Priority','Ticket Type']:
    R['delta_valid_by_'+g]={k:pct(x.delta_h) for k,x in v.groupby(g)}
    R['delta_all_by_'+g]={k:pct(x.delta_h) for k,x in c.groupby(g)}
    R['kw_valid_'+g]=dict(zip(['H','p'],[round(x,4) for x in stats.kruskal(*[x.delta_h for _,x in v.groupby(g)])]))
    R['neg_share_by_'+g]=c.groupby(g).delta_h.apply(lambda s:round((s<0).mean(),3)).to_dict()
cb=v.groupby(['Ticket Channel','Ticket Priority','Ticket Type']).delta_h.agg(n='count',median='median',p90=lambda s:s.quantile(.9)).reset_index()
R['combos_total']=len(cb); R['combo_n_median']=float(cb.n.median())
top=cb[cb.n>=10].sort_values('median',ascending=False).head(10).round(2); R['top10']=top.to_dict('records'); R['combos_n_ge10']=int((cb.n>=10).sum())
R['top10_bottom_median_ref']=round(cb[cb.n>=10]['median'].min(),2)
cr=c[c['Ticket Priority']=='Critical']
R['critical']=dict(closed=int(len(cr)),total=int((d['Ticket Priority']=='Critical').sum()),neg=int((cr.delta_h<0).sum()),**{f'le{h}h_valid':round((cr[cr.delta_h>=0].delta_h<=h).mean(),4) for h in [4,8,12,24,48,72]})
R['critical_valid_n']=int((cr.delta_h>=0).sum())
# satisfaction
R['sat_dist']=c['Customer Satisfaction Rating'].value_counts().sort_index().to_dict(); R['sat_median']=float(c['Customer Satisfaction Rating'].median())
R['sat_spearman_all']=dict(zip(['rho','p'],[round(x,4) for x in stats.spearmanr(c.delta_h,c['Customer Satisfaction Rating'])]))
R['sat_spearman_valid']=dict(zip(['rho','p'],[round(x,4) for x in stats.spearmanr(v.delta_h,v['Customer Satisfaction Rating'])]))
v['band']=pd.cut(v.delta_h,[0,2,4,8,12,16,24.01],right=False,labels=['0-2h','2-4h','4-8h','8-12h','12-16h','16-24h'])
R['sat_by_band']=v.groupby('band',observed=True)['Customer Satisfaction Rating'].agg(n='count',median='median',mean='mean',pct_1_2=lambda s:(s<=2).mean(),pct_4_5=lambda s:(s>=4).mean()).round(3).reset_index().astype({'band':str}).to_dict('records')
R['sat_by_priority']=c.groupby('Ticket Priority')['Customer Satisfaction Rating'].agg(n='count',median='median',mean='mean').round(3).to_dict('index')
R['sat_by_channel']=c.groupby('Ticket Channel')['Customer Satisfaction Rating'].agg(n='count',median='median',mean='mean').round(3).to_dict('index')
R['sat_age_spearman']=round(stats.spearmanr(c['Customer Age'],c['Customer Satisfaction Rating'])[0],4)
q1,q3=v.delta_h.quantile([.25,.75]); R['iqr_outliers_valid']=int(((v.delta_h<q1-1.5*(q3-q1))|(v.delta_h>q3+1.5*(q3-q1))).sum())
json.dump(R,open(D+'analysis/eda_d1_results.json','w'),indent=1,default=str,ensure_ascii=False)
d.to_pickle(D+'analysis/d1_cache.pkl')
# ---- charts
import plotly.graph_objects as go; from plotly.subplots import make_subplots; import plotly.express as px
C='/home/ubuntu/g4_challenge/analysis/charts/'
fig=make_subplots(1,3,subplot_titles=['Canal','Prioridade','Tipo de ticket'])
for i,col in enumerate(['Ticket Channel','Ticket Priority','Ticket Type']):
    vc=d[col].value_counts(); fig.add_bar(x=vc.index,y=vc.values,text=[f'{x/len(d):.1%}' for x in vc.values],textposition='outside',row=1,col=i+1,showlegend=False)
fig.update_layout(title=f'Dataset 1 — Volume de tickets (n={len(d):,}): distribuição quase perfeitamente uniforme'); fig.update_yaxes(range=[0,2600]); fig.write_json(C+'d1_volumes.json')
po=['Low','Medium','High','Critical']
fig=make_subplots(1,2,subplot_titles=['Por canal','Por prioridade'],shared_yaxes=True)
for k in sorted(v['Ticket Channel'].unique()): fig.add_box(y=v[v['Ticket Channel']==k].delta_h,name=k,row=1,col=1,showlegend=False)
for k in po: fig.add_box(y=v[v['Ticket Priority']==k].delta_h,name=k,row=1,col=2,showlegend=False)
fig.update_layout(title=f'Proxy de tempo de resolução (Resolução − 1ª resposta, h) — apenas tickets Closed com delta ≥ 0 (n={len(v):,})'); fig.update_yaxes(title='horas',row=1,col=1); fig.write_json(C+'d1_box_resolution.json')
fig=go.Figure(go.Histogram(x=c.delta_h,xbins=dict(start=-24,end=24,size=1)))
fig.add_vline(x=0,line_dash='dash',annotation_text=f'{(c.delta_h<0).mean():.1%} dos tickets "resolvidos antes da 1ª resposta"')
fig.update_layout(title=f'Evidência de dado sintético: delta Resolução − 1ª resposta é ~uniforme em ±24h (n={len(c):,} Closed)',xaxis_title='horas',yaxis_title='tickets'); fig.write_json(C+'d1_delta_hist.json')
hm=pd.crosstab(v['band'],v['Customer Satisfaction Rating'],normalize='index')
fig=go.Figure(go.Heatmap(z=hm.values,x=[str(int(x)) for x in hm.columns],y=[str(x) for x in hm.index],text=np.round(hm.values*100,1),texttemplate='%{text}%',colorscale='Blues'))
fig.update_layout(title=f'Satisfação × faixa de tempo (% por linha) — Spearman ρ={R["sat_spearman_valid"]["rho"]} (n={len(v):,})',xaxis_title='Nota de satisfação',yaxis_title='Faixa de tempo'); fig.write_json(C+'d1_sat_heatmap.json')
s=c['Customer Satisfaction Rating'].value_counts().sort_index()
fig=go.Figure(go.Bar(x=[str(int(i)) for i in s.index],y=s.values,text=[f'{x/s.sum():.1%}' for x in s.values],textposition='outside'))
fig.update_layout(title=f'Distribuição das notas de satisfação (n={int(s.sum()):,} tickets Closed)',xaxis_title='Nota',yaxis_title='tickets'); fig.write_json(C+'d1_sat_dist.json')
print('ok')
