import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3] / "solution"))
import pandas as pd, scoring
d = scoring.load_pipeline(); t=scoring.reference_date(d)
sc,_=scoring.score_open_deals(d,t)
f=sc[sc.lista=="foco"]
g=f[f.score>=70]
print("foco",len(f),"score>=70",len(g),"vendedores com >=1 boa:",g.sales_agent.nunique())
print(pd.crosstab(f["product"],f.score>=70))
print("boas por vendedor",g.groupby("sales_agent").size().describe()[["min","50%","max"]].to_dict())
print("foco valor tabela",f.sales_price.sum(),"valor esperado",round(f.valor_esperado.sum()))
print("reativar tabela",sc[sc.lista=="reativar"].sales_price.sum(),"encerrar",sc[sc.lista=="encerrar"].sales_price.sum())
print("fechaEsteMes entre foco",(f.chance_soon>=0.10).sum())
# correlação score x preço dentro do foco
print("spearman score~preço",f[["score","sales_price"]].corr(method="spearman").iloc[0,1].round(2),"score~chance",f[["score","chance"]].corr(method="spearman").iloc[0,1].round(2))
print("vendedores com abertos por lista\n",sc.groupby("sales_agent").lista.value_counts().unstack(fill_value=0).describe().loc[["mean","max"]])
