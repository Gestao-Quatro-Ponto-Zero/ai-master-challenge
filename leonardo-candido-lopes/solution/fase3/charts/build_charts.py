import json, plotly.graph_objects as go
d=json.load(open('../analysis/eda_d2_results.json'))
dist=d['dist']; ir=d['imbalance_ratio']
items=sorted(dist.items(),key=lambda x:-x[1][0])
names=[k for k,_ in items]; cnt=[v[0] for _,v in items]; pct=[v[1]*100 for _,v in items]
f=go.Figure(go.Bar(x=names,y=pct,text=[f"{p:.2f}%<br>{c:,}".replace(',','.') for p,c in zip(pct,cnt)],textposition='outside',hovertemplate='%{x}<br>%{y:.2f}%<extra></extra>'))
f.add_hline(y=12.5,line_dash='dash',annotation_text='Distribuição uniforme (1/8 = 12,5%)')
f.update_layout(title=f'D2: distribuição das 8 categorias de TI (n = {sum(cnt):,})'.replace(',','.'),yaxis_title='% dos tickets',yaxis_range=[0,max(pct)*1.25])
f.write_json('charts/f3_categorias.json')
mn=min(cnt); ratio=[c/mn for c in cnt]
cum=[];s=0
for p in pct: s+=p; cum.append(s)
g=go.Figure()
g.add_bar(y=names[::-1],x=ratio[::-1],orientation='h',text=[f"{r:.2f}×" for r in ratio[::-1]],textposition='outside',name='Razão vs menor classe',hovertemplate='%{y}: %{x:.2f}× a menor classe<extra></extra>')
g.add_annotation(x=ratio[0],y=names[0],text=f'Desbalanceamento máx/mín = {ir}×',showarrow=True,ax=-120,ay=40)
g.update_layout(title='D2: desbalanceamento (volume ÷ menor classe, Administrative rights)',xaxis_title='Múltiplo da menor classe',xaxis_range=[0,max(ratio)*1.2],yaxis=dict(automargin=True))
g.write_json('charts/f3_desbalanceamento.json')
ids=['R','P1','P2','P3']; labels=['Redesign de Suporte','Pilar 1: Triagem inteligente','Pilar 2: Autoatendimento','Pilar 3: Instrumentação de SLA']; parents=['','R','R','R']
subs={'P1':['Detecção de domínio (TI vs Financeiro/Comercial)','Classificação nas 8 classes','Limiares de confiança (0,85 / 0,60, proposta)','Prioridade e roteamento'],
'P2':[f"Purchase ({dist['Purchase'][1]*100:.2f}%)",f"Storage ({dist['Storage'][1]*100:.2f}%)",f"Access – subtipos elegíveis ({dist['Access'][1]*100:.2f}% total)",'Fallback para agente'],
'P3':['Timestamps reais por etapa','SLA por prioridade','Fechamento por inatividade (regra a validar)','Painel de KPIs + loop de feedback']}
for p,l in subs.items():
    for i,x in enumerate(l): ids.append(f'{p}_{i}'); labels.append(x); parents.append(p)
h=go.Figure(go.Treemap(ids=ids,labels=labels,parents=parents,root_color='lightgrey',hovertemplate='%{label}<extra></extra>'))
h.update_layout(title='Estrutura do redesign em 3 pilares (clique para expandir)',height=600,margin=dict(t=50,l=10,r=10,b=10))
h.write_json('charts/f3_pilares.json')
