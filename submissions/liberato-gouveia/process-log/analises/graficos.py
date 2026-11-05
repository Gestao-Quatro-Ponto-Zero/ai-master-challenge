"""Gera os gráficos do diário de bordo a partir dos dados reais."""
import pandas as pd, numpy as np, sys, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
D, OUT = sys.argv[1], sys.argv[2]
SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, RED, GRAY = "#2a78d6", "#e34948", "#b9b8b3"
plt.rcParams.update({"figure.facecolor":SURF,"axes.facecolor":SURF,"axes.edgecolor":GRID,
  "axes.labelcolor":INK2,"xtick.color":INK2,"ytick.color":INK2,"text.color":INK,
  "font.size":11,"axes.spines.top":False,"axes.spines.right":False,"axes.grid":True,
  "grid.color":GRID,"grid.linewidth":0.8,"axes.axisbelow":True})
p=pd.read_csv(f"{D}/sales_pipeline.csv"); a=pd.read_csv(f"{D}/accounts.csv")
pr=pd.read_csv(f"{D}/products.csv"); t=pd.read_csv(f"{D}/sales_teams.csv")
p['product']=p['product'].replace('GTXPro','GTX Pro')
for c in ['engage_date','close_date']: p[c]=pd.to_datetime(p[c])
p=p.merge(pr,on='product',how='left').merge(t,on='sales_agent',how='left').merge(a,on='account',how='left')
c=p[p.deal_stage.isin(['Won','Lost'])].copy(); c['won']=(c.deal_stage=='Won').astype(int)
media=c.won.mean()
def title(fig, t1, t2):
    h=fig.get_size_inches()[1]
    fig.text(0.01,1-0.12/h,t1,fontsize=14,weight="bold",va="top"); fig.text(0.01,1-0.45/h,t2,fontsize=10.5,color=INK2,va="top")

# 1) fatores
fig,axs=plt.subplots(1,4,figsize=(13,4.6)); fig.subplots_adjust(top=0.74,wspace=0.75,left=0.1,right=0.98,bottom=0.12)
for ax,(col,nome) in zip(axs,[('product','Produto'),('sector','Setor'),('regional_office','Região'),('manager','Gerente')]):
    g=c.groupby(col).won.mean().sort_values()
    ax.barh(g.index,g.values,color=BLUE,height=0.62); ax.axvline(media,color=INK,ls="--",lw=1)
    ax.set_xlim(0,1); ax.xaxis.set_major_formatter(PercentFormatter(1,0)); ax.set_xticks([0,.5,1])
    ax.set_title(nome,loc="left",fontsize=11.5,weight="bold"); ax.grid(axis="y",visible=False); ax.tick_params(axis="y",labelsize=9)
title(fig,"Gráfico 1 · Todo mundo ganha ~63% dos deals, não importa o grupo",
      f"% de deals ganhos (de {len(c):,} fechados). Linha tracejada = média geral de {media:.0%}. As barras quase não mudam de tamanho.".replace(",","."))
fig.savefig(f"{OUT}/grafico1_fatores.png",dpi=150); plt.close(fig)

# 2) sorte x vendedores
real=c.groupby('sales_agent').won.agg(['size','mean']).sort_values('mean')
rng=np.random.default_rng(42); sims=np.sort(rng.binomial(real['size'].values,media,size=(10000,len(real)))/real['size'].values,axis=1)
x=np.arange(1,len(real)+1)
fig,ax=plt.subplots(figsize=(11,4.8)); fig.subplots_adjust(top=0.78,left=0.08,right=0.98,bottom=0.13)
ax.fill_between(x,np.percentile(sims,5,axis=0),np.percentile(sims,95,axis=0),color=GRAY,alpha=0.45,lw=0,label="Faixa da sorte: 30 vendedores IDÊNTICOS (63% de chance cada)")
ax.plot(x,real['mean'].values,"o",color=BLUE,ms=8,mec=SURF,mew=1.5,label="Os 30 vendedores reais")
ax.yaxis.set_major_formatter(PercentFormatter(1,0)); ax.set_ylim(0.45,0.8)
ax.set_xlabel("Vendedores, do pior para o melhor"); ax.set_ylabel("% de deals ganhos"); ax.set_xticks([1,10,20,30])
ax.legend(loc="upper left",frameon=False,fontsize=10)
ax.annotate(f"pior real: {real['mean'].min():.0%}",(1,real['mean'].min()),xytext=(3,0.47),fontsize=9.5,color=INK2,arrowprops=dict(arrowstyle="-",color=INK2,lw=0.8))
ax.annotate(f"melhor real: {real['mean'].max():.0%}",(30,real['mean'].max()),xytext=(22.5,0.765),fontsize=9.5,color=INK2,arrowprops=dict(arrowstyle="-",color=INK2,lw=0.8))
title(fig,"Gráfico 2 · A diferença entre vendedores é do tamanho da sorte",
      "Os pontos azuis (reais) caem dentro da faixa cinza, que é o que a sorte produziria mesmo se todos fossem igualmente bons.")
fig.savefig(f"{OUT}/grafico2_sorte.png",dpi=150); plt.close(fig)

# 3) duração x ganho (coorte mar-ago/2017)
c['ciclo']=(c.close_date-c.engage_date).dt.days
co=c[(c.engage_date>='2017-03-01')&(c.engage_date<='2017-08-31')]
bins=[-1,7,14,30,60,90,120,200]; lab=["até 7","8–14","15–30","31–60","61–90","91–120","121–138"]
g=co.groupby(pd.cut(co.ciclo,bins,labels=lab),observed=True).won.agg(['size','mean'])
fig,ax=plt.subplots(figsize=(11,4.8)); fig.subplots_adjust(top=0.78,left=0.08,right=0.98,bottom=0.14)
cols=[RED if l in ("até 7","8–14") else BLUE for l in g.index]
b=ax.bar(g.index.astype(str),g['mean'],color=cols,width=0.62)
for r,(v,n) in zip(b,zip(g['mean'],g['size'])): ax.text(r.get_x()+r.get_width()/2,v+0.015,f"{v:.0%}",ha="center",fontsize=10.5,color=INK)
ax.set_ylim(0,1); ax.yaxis.set_major_formatter(PercentFormatter(1,0)); ax.grid(axis="x",visible=False)
ax.set_xlabel("Quantos dias o deal levou da negociação até fechar"); ax.set_ylabel("% de deals ganhos")
title(fig,"Gráfico 3 · O \"não\" vem rápido; quem sobrevive às 2 primeiras semanas fecha mais",
      f"Deals iniciados entre mar e ago/2017 ({len(co):,} fechados). Vermelho = fechou em até 14 dias. Nenhum deal da base levou mais de {c.ciclo.max()} dias.".replace(",","."))
fig.savefig(f"{OUT}/grafico3_tempo.png",dpi=150); plt.close(fig)

# 4) zumbis
o=p[p.deal_stage=='Engaging'].copy(); o['idade']=(pd.Timestamp('2017-12-31')-o.engage_date).dt.days
bins=[-1,30,60,90,138,200,300,500]; lab=["até 30","31–60","61–90","91–138","139–200","201–300","301–423"]
g=o.groupby(pd.cut(o.idade,bins,labels=lab),observed=True).size()
fig,ax=plt.subplots(figsize=(11,4.8)); fig.subplots_adjust(top=0.78,left=0.08,right=0.98,bottom=0.14)
cols=[BLUE]*4+[RED]*3; b=ax.bar(g.index.astype(str),g.values,color=cols,width=0.62)
for r,v in zip(b,g.values): ax.text(r.get_x()+r.get_width()/2,v+12,str(v),ha="center",fontsize=10.5)
ax.axvline(3.5,color=INK,ls="--",lw=1); ax.text(3.42,560,"limite histórico:\n138 dias →",fontsize=10,color=INK,ha="right")
ax.grid(axis="x",visible=False); ax.set_xlabel("Há quantos dias o deal está em negociação (em 31/12/2017)"); ax.set_ylabel("Nº de deals abertos")
z=(o.idade>138).sum()
title(fig,f"Gráfico 4 · {z:,} de {len(o):,} deals em negociação ({z/len(o):.0%}) são \"zumbis\"".replace(",","."),
      "Vermelho = abertos há mais tempo do que QUALQUER deal da história levou para fechar.")
fig.savefig(f"{OUT}/grafico4_zumbis.png",dpi=150); plt.close(fig)

# 5) régua AUC
fig,ax=plt.subplots(figsize=(11,3.4)); fig.subplots_adjust(top=0.70,left=0.05,right=0.95,bottom=0.05)
ax.set_xlim(47,103); ax.set_ylim(0,1); ax.axis("off")
ax.plot([50,100],[0.5,0.5],color=GRID,lw=10,solid_capstyle="round")
ax.plot([50,54.3],[0.5,0.5],color=RED,lw=10,solid_capstyle="round")
for v,txt,col,up in [(50,"50%: chute\n(cara ou coroa)",INK2,True),(54.3,"54%: nosso modelo\ncom TODOS os dados",RED,False),(70,"70%: a partir daqui\no modelo é útil",INK2,True),(100,"100%: acerta\nsempre",INK2,False)]:
    ax.plot([v,v],[0.36,0.64],color=col,lw=1.5)
    ax.text(v,0.72 if up else 0.28,txt,ha="center",va="bottom" if up else "top",fontsize=9.5,color=col)
title(fig,"Gráfico 5 · O teste de machine learning (AUC): quase um chute",
      "Mostramos ao modelo pares (1 deal ganho + 1 perdido) que ele nunca viu e pedimos para apontar o ganho.")
fig.savefig(f"{OUT}/grafico5_auc.png",dpi=150); plt.close(fig)
# 6) chance por idade ATUAL (sem futuro) - Fase 1, item A
safra=p[(p.engage_date>='2017-03-01')&(p.engage_date<='2017-06-30')].copy()
safra['ciclo']=(safra.close_date-safra.engage_date).dt.days
idades=[0,7,14,30,60,90,120,138]; rows=[]
for i in idades:
    v=safra if i==0 else safra[safra.ciclo.isna()|(safra.ciclo>=i)]
    rows.append(((v.deal_stage=='Won').mean(),(v.deal_stage=='Lost').mean(),(v.deal_stage=='Engaging').mean(),len(v)))
r=np.array([x[:3] for x in rows]); ns=[x[3] for x in rows]
lab=[f"{i} dias" for i in idades]
fig,ax=plt.subplots(figsize=(11,5.2)); fig.subplots_adjust(top=0.76,left=0.08,right=0.98,bottom=0.2)
x=np.arange(len(idades)); w=0.62
ax.bar(x,r[:,0],w,color=BLUE,label="foi ganho",edgecolor=SURF,linewidth=2)
ax.bar(x,r[:,1],w,bottom=r[:,0],color=GRAY,label="foi perdido",edgecolor=SURF,linewidth=2)
ax.bar(x,r[:,2],w,bottom=r[:,0]+r[:,1],color=RED,label="nunca fechou (até 31/12/2017)",edgecolor=SURF,linewidth=2)
for xi,v in zip(x,r[:,0]):
    if v>0.1: ax.text(xi,v/2,f"{v:.0%}",ha="center",va="center",color="white",fontsize=11,weight="bold")
    else: ax.text(xi,0.16,f"{v:.0%}\nganho",ha="center",va="center",color="white",fontsize=10.5,weight="bold")
ax.set_xticks(x); ax.set_xticklabels([f"{l}\n(n={n:,})".replace(",",".") for l,n in zip(lab,ns)],fontsize=9.5)
ax.set_ylim(0,1); ax.yaxis.set_major_formatter(PercentFormatter(1,0)); ax.grid(axis="x",visible=False)
ax.set_xlabel("Deals que ainda estavam abertos com esta idade")
ax.legend(loc="upper center",bbox_to_anchor=(0.5,-0.2),ncol=3,frameon=False,fontsize=10)
title(fig,"Gráfico 6 · Quanto mais velho o deal aberto, MENOR a chance de ser ganho",
      "Usa só o que se sabe hoje (a idade do deal). Deals iniciados entre mar e jun/2017, todos acompanhados por pelo menos 184 dias.")
fig.savefig(f"{OUT}/grafico6_chance_por_idade.png",dpi=150); plt.close(fig)
print("ok")
