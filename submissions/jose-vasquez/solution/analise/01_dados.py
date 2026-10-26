"""Etapa 2 — olhar os dados.

Pergunta: o que, nos dados, separa venda ganha de venda perdida?
Cada hipótese vira um número. Nada aqui entra na nota sem passar por teste.

Rodar: python3 solution/analise/01_dados.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
HOJE = pd.Timestamp("2017-12-31")  # último dia com dado no dataset


def carregar():
    p = pd.read_csv(DATA / "sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
    a = pd.read_csv(DATA / "accounts.csv")
    pr = pd.read_csv(DATA / "products.csv")
    t = pd.read_csv(DATA / "sales_teams.csv")
    return p, a, pr, t


def titulo(txt):
    print(f"\n=== {txt}")


def qualidade(p, a, pr, t):
    titulo("1. Qualidade dos dados")
    sem_preco = sorted(set(p["product"]) - set(pr["product"]))
    print(f"Produtos da tabela de vendas sem preço no catálogo: {sem_preco}")
    print(f"Setores escritos no cadastro de clientes: {sorted(a.sector.unique())}")
    print(f"Vendedores sem nenhuma venda: {(~t.sales_agent.isin(p.sales_agent)).sum()} de {len(t)}")
    print("Vendas por fase:")
    print(p.deal_stage.value_counts().to_string())
    print("Sem data de início, por fase:")
    print(p[p.engage_date.isna()].deal_stage.value_counts().to_string())
    print("Sem cliente, por fase:")
    print(p[p.account.isna()].deal_stage.value_counts().to_string())
    print(f"Datas: de {p.engage_date.min().date()} a {p.close_date.max().date()}")


def juntar(p, a, pr, t):
    p = p.copy()
    p["product"] = p["product"].replace({"GTXPro": "GTX Pro"})
    a = a.assign(sector=a.sector.replace({"technolgy": "technology"}))
    df = (p.merge(t, on="sales_agent", how="left")
           .merge(pr, on="product", how="left")
           .merge(a, on="account", how="left"))
    return df


def taxas(fech):
    titulo("2. Taxa de ganho por grupo (vendas encerradas)")
    print(f"Geral: {fech.ganhou.mean():.1%} de {len(fech)} vendas")
    fech = fech.assign(porte=pd.qcut(fech.revenue, 4, labels=["pequeno", "médio", "grande", "muito grande"]))
    for col in ["product", "sector", "regional_office", "manager", "porte", "sales_agent"]:
        g = fech.groupby(col, observed=True).ganhou.agg(["mean", "count"])
        print(f"{col:16} de {g['mean'].min():.0%} a {g['mean'].max():.0%}  ({len(g)} grupos)")


def diferenca_entre_vendedores(fech, vezes=1000):
    titulo("3. A diferença entre vendedores é real ou acaso?")
    rng = np.random.default_rng(0)
    real = fech.groupby("sales_agent").ganhou.mean().std()
    sims = []
    for _ in range(vezes):
        emb = pd.Series(rng.permutation(fech.ganhou.values), index=fech.index)
        sims.append(emb.groupby(fech.sales_agent).mean().std())
    p = (np.array(sims) >= real).mean()
    print(f"Variação real entre vendedores: {real:.3f}. Com resultados sorteados: {np.mean(sims):.3f}."
          f" Chance de ser acaso: {p:.0%}")


def metade_prevê_metade(fech):
    titulo("4. A taxa da 1ª metade do período prevê a 2ª metade?")
    corte = fech.close_date.median()
    a, b = fech[fech.close_date <= corte], fech[fech.close_date > corte]
    for col in ["sales_agent", "product", "sector"]:
        ga = a.groupby(col).ganhou.agg(["mean", "count"]).add_suffix("_a")
        gb = b.groupby(col).ganhou.agg(["mean", "count"]).add_suffix("_b")
        j = ga.join(gb).query("count_a >= 15 and count_b >= 15")
        print(f"{col:12} correlação {j.mean_a.corr(j.mean_b):+.2f}  ({len(j)} grupos)")


def tempo(fech):
    titulo("5. Tempo de negociação (do início ao fechamento)")
    print(fech.groupby("ganhou").dias.describe()[["count", "50%", "max"]].round(0).to_string())
    for x in [14, 30, 90]:
        print(f"Encerradas que passaram de {x} dias: {fech[fech.dias > x].ganhou.mean():.0%} ganhas"
              " (atenção: só conta quem já fechou)")


def trimestre(fech):
    titulo("6. Mês de fechamento")
    tri = fech.close_date.dt.month.isin([3, 6, 9, 12])
    print(f"Ganhas em mês de fim de trimestre: {fech[tri].ganhou.mean():.0%}; outros meses: {fech[~tri].ganhou.mean():.0%}")


def valor(fech, pr):
    titulo("7. Valor")
    g = fech[fech.ganhou]
    print(f"Valor fechado / preço de tabela: média {(g.close_value / g.sales_price).mean():.2f}")
    print(f"Preço: de US$ {pr.sales_price.min()} a US$ {pr.sales_price.max()} ({pr.sales_price.max() / pr.sales_price.min():.0f} vezes)")


def abertas(df, fech):
    titulo("8. Vendas abertas em 31/12/2017")
    ab = df[df.deal_stage.isin(["Engaging", "Prospecting"])].copy()
    ab["dias"] = (HOJE - ab.engage_date).dt.days
    eng = ab[ab.deal_stage == "Engaging"]
    limite = fech.dias.max()
    paradas = eng[eng.dias > limite]
    print(f"Abertas: {len(ab)} ({len(eng)} em negociação, {len(ab) - len(eng)} em prospecção)")
    print(f"Em negociação há mais de {limite} dias (a venda mais longa da história): {len(paradas)}"
          f" ({len(paradas) / len(eng):.0%}), US$ {paradas.sales_price.sum() / 1e6:.1f} mi de preço de tabela")
    print(f"Abertas sem cliente: {ab.account.isna().sum()} de {len(ab)}. Encerradas sem cliente: {fech.account.isna().sum()} de {len(fech)}")
    print("Por região:")
    print(ab.groupby(["regional_office", "deal_stage"]).size().to_string())


def main():
    p, a, pr, t = carregar()
    qualidade(p, a, pr, t)
    df = juntar(p, a, pr, t)
    fech = df[df.deal_stage.isin(["Won", "Lost"])].copy()
    fech["ganhou"] = fech.deal_stage.eq("Won")
    fech["dias"] = (fech.close_date - fech.engage_date).dt.days
    taxas(fech)
    diferenca_entre_vendedores(fech)
    metade_prevê_metade(fech)
    tempo(fech)
    trimestre(fech)
    valor(fech, pr)
    abertas(df, fech)


if __name__ == "__main__":
    main()
