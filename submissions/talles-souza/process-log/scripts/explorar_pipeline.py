"""E2 — entender o sales_pipeline antes de definir o score.

Uso: python -X utf8 explorar_pipeline.py <pasta crm-sales-predictive-analytics>
Só lê os CSVs e imprime; a saída bruta vai para evidencias/explorar-pipeline.txt.
"""
import sys
from pathlib import Path

import pandas as pd

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 20)

D = Path(sys.argv[1])
pipe = pd.read_csv(D / "sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
acc = pd.read_csv(D / "accounts.csv")
prod = pd.read_csv(D / "products.csv")
team = pd.read_csv(D / "sales_teams.csv")


def titulo(t):
    print(f"\n=== {t}")


def taxa(df, col, min_n=30):
    """Win rate entre fechados, por categoria, com n e diferença para a média."""
    f = df[df.deal_stage.isin(["Won", "Lost"])]
    g = f.groupby(col).deal_stage.agg(n="size", ganhos=lambda s: (s == "Won").sum())
    g["win_rate"] = (g.ganhos / g.n).round(3)
    g["vs_media"] = (g.win_rate - (f.deal_stage == "Won").mean()).round(3)
    return g[g.n >= min_n].sort_values("win_rate", ascending=False)


titulo("Tamanho e estágios")
print(len(pipe), "oportunidades")
print(pipe.deal_stage.value_counts().to_string())

titulo("Lacunas por estágio (quantos nulos)")
print(pipe.drop(columns="opportunity_id").isna().groupby(pipe.deal_stage).sum().to_string())

titulo("Datas")
print("engage_date:", pipe.engage_date.min().date(), "→", pipe.engage_date.max().date())
print("close_date: ", pipe.close_date.min().date(), "→", pipe.close_date.max().date())
REF = pipe.close_date.max()
print("data de referência para 'hoje' (último close_date):", REF.date())

titulo("Integridade das ligações")
print("produtos no pipeline sem cadastro:", sorted(set(pipe["product"]) - set(prod["product"])))
print("produtos no cadastro:", sorted(prod["product"]))
print("contas no pipeline sem cadastro:", sorted(set(pipe.account.dropna()) - set(acc.account)))
print("vendedores sem cadastro:", sorted(set(pipe.sales_agent) - set(team.sales_agent)))
print("setores:", sorted(acc.sector.unique()))
print("vendedores com 0 deals:", sorted(set(team.sales_agent) - set(pipe.sales_agent)))

# normalização mínima, só para medir; a decisão de normalizar entra no log
pipe["product_n"] = pipe["product"].replace({"GTXPro": "GTX Pro"})
df = (pipe.merge(team, on="sales_agent", how="left")
          .merge(acc, on="account", how="left")
          .merge(prod, left_on="product_n", right_on="product", how="left", suffixes=("", "_cat")))

titulo("Win rate geral (fechados)")
fech = df[df.deal_stage.isin(["Won", "Lost"])]
print(f"{(fech.deal_stage == 'Won').mean():.3f} em {len(fech)} fechados")

for col in ["product_n", "series", "manager", "regional_office", "sector", "sales_agent"]:
    titulo(f"Win rate por {col}")
    print(taxa(df, col).to_string())

titulo("Win rate por porte da conta (receita, quartis) e conta sem cadastro")
df["porte"] = pd.qcut(df.revenue, 4, labels=["Q1 menor", "Q2", "Q3", "Q4 maior"]).astype(str)
df.loc[df.account.isna(), "porte"] = "sem conta"
print(taxa(df, "porte").to_string())

titulo("Win rate por conta (top e base, contas com >= 40 fechados)")
t = taxa(df, "account", min_n=40)
print(t.head(5).to_string()); print("…"); print(t.tail(5).to_string())

titulo("Vendedor × produto: o efeito do vendedor sobrevive dentro do produto?")
f = df[df.deal_stage.isin(["Won", "Lost"])].copy()
f["won"] = (f.deal_stage == "Won").astype(int)
base_prod = f.groupby("product_n").won.transform("mean")
f["resid"] = f.won - base_prod  # quanto o vendedor ganha acima do esperado pelo produto
r = f.groupby("sales_agent").agg(n=("won", "size"), wr=("won", "mean"), acima_do_produto=("resid", "mean"))
print(r.round(3).sort_values("acima_do_produto").to_string())

titulo("Tempo: dias de engage → close nos fechados")
f["dias"] = (f.close_date - f.engage_date).dt.days
print(f.groupby("deal_stage").dias.describe().round(1).to_string())

titulo("Chance de ganhar dado que o deal já passou de A dias aberto (fechados)")
for a in [0, 7, 14, 30, 45, 60, 90, 120]:
    s = f[f.dias >= a]
    print(f"  >= {a:>3} d: win rate {s.won.mean():.3f}  (n={len(s)})")

titulo("Win rate por faixa de duração (fechados)")
f["faixa"] = pd.cut(f.dias, [-1, 7, 14, 30, 60, 90, 1000], labels=["0-7", "8-14", "15-30", "31-60", "61-90", "90+"])
print(f.groupby("faixa", observed=True).won.agg(["size", "mean"]).round(3).to_string())

titulo("Abertos: idade em dias até a referência")
ab = df[df.deal_stage.isin(["Engaging", "Prospecting"])].copy()
ab["idade"] = (REF - ab.engage_date).dt.days
print(ab.groupby("deal_stage").idade.describe().round(1).to_string())
print("Engaging com mais de 90 d:", int((ab.idade > 90).sum()), "de", int((ab.deal_stage == "Engaging").sum()))

titulo("Valor: close_value dos ganhos × preço de tabela")
g = df[df.deal_stage == "Won"]
v = g.groupby("product_n").agg(n=("close_value", "size"), preco=("sales_price", "first"),
                               mediana=("close_value", "median"), media=("close_value", "mean"))
v["mediana/preco"] = (v.mediana / v.preco).round(2)
print(v.round(0).to_string())

titulo("Carga: deals abertos por vendedor")
print(ab.groupby("sales_agent").size().describe().round(1).to_string())

titulo("Sazonalidade: win rate por trimestre de fechamento")
f["tri"] = f.close_date.dt.to_period("Q").astype(str)
print(f.groupby("tri").won.agg(["size", "mean"]).round(3).to_string())
