import os
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
"""
Challenge 001 — Passo 5: graficos nivel consultoria (paleta validada dataviz).
Salva PNGs em outputs/charts/ para embutir no relatorio HTML.
"""
import pandas as pd, numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

DATA=os.path.join(_ROOT,'data')
OUT =os.path.join(_ROOT,'solution','outputs')
import os; os.makedirs(f'{OUT}/charts', exist_ok=True)

# ---- paleta dataviz ----
BLUE='#2a78d6'; RED='#d03b3b'; INK='#0b0b0b'; SEC='#52514e'; MUTE='#9a998f'; GRID='#e7e6e2'; SURF='#fcfcfb'
mpl.rcParams.update({
    'figure.facecolor':SURF,'axes.facecolor':SURF,'savefig.facecolor':SURF,
    'font.size':12,'axes.titlesize':14,'axes.titleweight':'bold','axes.titlecolor':INK,
    'text.color':INK,'axes.labelcolor':SEC,'xtick.color':SEC,'ytick.color':SEC,
    'axes.edgecolor':GRID,'axes.linewidth':1,
})
def clean(ax):
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(GRID); ax.spines['bottom'].set_color(GRID)
    ax.grid(axis='y', color=GRID, lw=1, zorder=0); ax.set_axisbelow(True)

acc=pd.read_csv(f'{DATA}/ravenstack_accounts.csv')
use=pd.read_csv(f'{DATA}/ravenstack_feature_usage.csv', parse_dates=['usage_date'])
tik=pd.read_csv(f'{DATA}/ravenstack_support_tickets.csv')
chn=pd.read_csv(f'{DATA}/ravenstack_churn_events.csv', parse_dates=['churn_date'])
m=pd.read_csv(f'{OUT}/account_master_clean.csv')

# 1) CHURN AO LONGO DO TEMPO (subiu = VERDADE)
chn['ym']=chn.churn_date.dt.to_period('M').dt.to_timestamp()
mc=chn.groupby('ym').size()
mc=mc[mc.index>='2023-01-01']
fig,ax=plt.subplots(figsize=(8,4.2)); clean(ax)
ax.plot(mc.index,mc.values,color=BLUE,lw=2.5,zorder=3)
ax.fill_between(mc.index,mc.values,color=BLUE,alpha=0.08,zorder=1)
ax.scatter([mc.index[-1]],[mc.values[-1]],color=BLUE,s=40,zorder=4)
ax.annotate(f'{mc.values[-1]} eventos',(mc.index[-1],mc.values[-1]),
            xytext=(-8,6),textcoords='offset points',ha='right',fontweight='bold',color=BLUE)
ax.set_title('Churn acelerou 20x em 24 meses',loc='left')
ax.set_ylabel('Eventos de churn / mês')
fig.text(0.125,0.01,"Afirmação do CEO “o churn subiu” → CONFIRMADA",color=SEC,fontsize=10)
fig.tight_layout(rect=[0,0.03,1,1]); fig.savefig(f'{OUT}/charts/1_churn_trend.png',dpi=150); plt.close()

# 2) USO AGREGADO (cresceu = FALSO — estagnado)
use['ym']=use.usage_date.dt.to_period('M').dt.to_timestamp()
mu=use.groupby('ym').usage_count.sum(); mu=mu[mu.index>='2023-01-01']
fig,ax=plt.subplots(figsize=(8,4.2)); clean(ax)
ax.plot(mu.index,mu.values,color=SEC,lw=2.5,zorder=3)
ax.axhline(mu.mean(),color=MUTE,ls='--',lw=1.2,zorder=2)
ax.set_ylim(0,mu.max()*1.25)
ax.annotate('média estável ~10,5k',(mu.index[len(mu)//2],mu.mean()),
            xytext=(0,8),textcoords='offset points',ha='center',color=SEC,fontsize=10)
ax.set_title('O uso NÃO cresceu — está estagnado',loc='left')
ax.set_ylabel('Eventos de uso / mês')
fig.text(0.125,0.01,"Afirmação do CEO “o uso cresceu” → NÃO SUSTENTADA pelos dados",color=SEC,fontsize=10)
fig.tight_layout(rect=[0,0.03,1,1]); fig.savefig(f'{OUT}/charts/2_usage_flat.png',dpi=150); plt.close()

# 3) SATISFACAO churned vs retained (identica = sinal cego)
sat_ret=m.loc[~m.churn_flag,'avg_satisfaction'].mean()
sat_chn=m.loc[m.churn_flag,'avg_satisfaction'].mean()
fig,ax=plt.subplots(figsize=(6.4,4.2)); clean(ax)
bars=ax.bar(['Ficaram','Cancelaram'],[sat_ret,sat_chn],color=[BLUE,RED],width=0.5,zorder=3)
for b,v in zip(bars,[sat_ret,sat_chn]):
    ax.text(b.get_x()+b.get_width()/2,v+0.06,f'{v:.2f}',ha='center',fontweight='bold')
ax.set_ylim(0,5); ax.set_ylabel('Satisfação média (1–5)')
ax.set_title('Satisfação não distingue quem cancela',loc='left')
fig.text(0.125,0.01,"Diferença de 0,02 ponto — o sinal em que o CS confia é cego",color=SEC,fontsize=10)
fig.tight_layout(rect=[0,0.03,1,1]); fig.savefig(f'{OUT}/charts/3_satisfaction_blind.png',dpi=150); plt.close()

# 4) AUC — churn imprevisivel (coin flip)
labels=['LogReg\n(oficial)','RandForest\n(oficial)','LogReg\n(eventos)','RandForest\n(eventos)']
aucs=[0.541,0.474,0.492,0.495]
fig,ax=plt.subplots(figsize=(7.2,4.2)); clean(ax)
bars=ax.bar(labels,aucs,color=MUTE,width=0.6,zorder=3)
ax.axhline(0.5,color=RED,lw=1.6,ls='--',zorder=4)
ax.text(-0.45,0.5,'acaso\n(0,50)',color=RED,ha='left',va='center',fontweight='bold',fontsize=9.5,
        bbox=dict(boxstyle='round,pad=0.2',fc=SURF,ec='none'))
for b,v in zip(bars,aucs):
    ax.text(b.get_x()+b.get_width()/2,v+0.008,f'{v:.2f}',ha='center',fontweight='bold',fontsize=10)
ax.set_ylim(0,0.7); ax.set_ylabel('AUC (poder preditivo)')
ax.set_title('Nenhum modelo prevê churn melhor que cara-ou-coroa',loc='left')
fig.text(0.125,0.01,"4 modelos × 2 rótulos, validação cruzada 5-fold. Sinal ausente, não escondido.",color=SEC,fontsize=9.5)
fig.tight_layout(rect=[0,0.03,1,1]); fig.savefig(f'{OUT}/charts/4_auc_coinflip.png',dpi=150); plt.close()

# 5) CONCENTRACAO DE RECEITA (curva de Lorenz)
mm=m.sort_values('mrr_amount',ascending=False).reset_index()
x=np.arange(1,len(mm)+1)/len(mm)*100
y=mm.mrr_amount.cumsum()/mm.mrr_amount.sum()*100
fig,ax=plt.subplots(figsize=(7.2,4.2)); clean(ax)
ax.plot(x,y,color=BLUE,lw=2.5,zorder=3)
ax.plot([0,100],[0,100],color=MUTE,ls='--',lw=1,zorder=2)
ax.axvline(20,color=RED,lw=1.2,ls=':',zorder=2)
y20=y[int(len(y)*0.2)-1]
ax.scatter([20],[y20],color=RED,s=45,zorder=5)
ax.annotate(f'top 20% = {y20:.0f}% do MRR',(20,y20),xytext=(8,-4),
            textcoords='offset points',color=RED,fontweight='bold')
ax.set_xlim(0,100); ax.set_ylim(0,100)
ax.set_xlabel('% das contas (maiores → menores)'); ax.set_ylabel('% do MRR acumulado')
ax.set_title('A receita está concentrada — onde focar a retenção',loc='left')
fig.text(0.125,0.01,"67% do faturamento em 100 contas. Priorize por valor, já que não dá pra prever risco.",color=SEC,fontsize=9.5)
fig.tight_layout(rect=[0,0.03,1,1]); fig.savefig(f'{OUT}/charts/5_revenue_concentration.png',dpi=150); plt.close()

# 6) ICP EM RISCO — churn por industria, DevTools destacado (build vs buy)
ind=m.groupby('industry').agg(churn=('churn_flag','mean'),mrr=('mrr_amount','mean'),n=('account_id','count'))
ind['churn']*=100; ind=ind.sort_values('churn')
fig,ax=plt.subplots(figsize=(8,4.4)); clean(ax)
colors=[RED if i=='DevTools' else '#c7c6bf' for i in ind.index]
bars=ax.barh(ind.index,ind.churn,color=colors,height=0.62,zorder=3)
for i,(idx,r) in enumerate(ind.iterrows()):
    ax.text(r.churn+0.5,i,f'{r.churn:.0f}%',va='center',fontweight='bold',
            color=RED if idx=='DevTools' else SEC,fontsize=11)
    ax.text(0.5,i,f'MRR médio ${r.mrr:,.0f}',va='center',ha='left',color='#fff' if idx=='DevTools' else SEC,fontsize=9)
ax.set_xlim(0,38); ax.set_xlabel('Taxa de churn (%)')
ax.grid(axis='x',color=GRID,lw=1,zorder=0); ax.grid(axis='y',visible=False)
ax.set_title('DevTools: mais churn, menores contas',loc='left',fontsize=14)
fig.text(0.125,0.012,"O ICP mais capaz de reconstruir a ferramenta interna (build vs buy) é o que mais sai. Direcional.",color=SEC,fontsize=9.5)
fig.tight_layout(rect=[0,0.03,1,1]); fig.savefig(f'{OUT}/charts/6_icp_devtools.png',dpi=150); plt.close()

print("6 graficos salvos em outputs/charts/")
import glob; [print(' -',os.path.basename(f)) for f in sorted(glob.glob(f'{OUT}/charts/*.png'))]
