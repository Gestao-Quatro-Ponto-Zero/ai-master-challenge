"""A idade do negócio aberto separa o desfecho? Com robustez (outro corte, longe do teto) e o vazamento da conta vazia.

Uso: python -X utf8 idade_robustez.py <pasta crm-sales-predictive-analytics>
Saída bruta: evidencias/idade-robustez.txt. Só lê os CSVs.

A: abertos em 30/09/2017 com até 138 dias; alvo "ganhou até 31/12/2017" e "fechou até 31/12/2017";
   e só entre os que fecharam: a idade separa ganho de perda?
B: robustez: só até 60 dias (longe do teto de 138) e outro corte (30/06/2017 -> 30/09/2017).
C: preço, porte e "tem conta" na mesma população. Nenhum negócio sem conta fecha no período:
   usar "sem conta" como penalidade seria vazamento do desfecho.
"""
import sys
import pandas as pd

d = sys.argv[1]
p = pd.read_csv(d + "/sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
prod = pd.read_csv(d + "/products.csv")
acc = pd.read_csv(d + "/accounts.csv")
p["product_n"] = p["product"].replace({"GTXPro": "GTX Pro"})
p = p.merge(prod.rename(columns={"product": "product_n"}), on="product_n", how="left")
p = p.merge(acc[["account", "revenue"]], on="account", how="left")
print("hoje (close_date.max):", p.close_date.max().date(), "| deals:", len(p), "| sem preço:", int(p.sales_price.isna().sum()))


def auc(score, y):
    """AUC de Mann-Whitney com empates pela média dos postos. y = 1 é o positivo."""
    score = pd.Series(score).reset_index(drop=True)
    y = pd.Series(y).reset_index(drop=True).astype(int)
    n1 = int(y.sum()); n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = score.rank(method="average")
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def janela(corte, fim, teto=138):
    ab = p[(p.engage_date <= corte) & (p.close_date.isna() | (p.close_date > corte))].copy()
    ab["idade"] = (corte - ab.engage_date).dt.days
    j = ab[ab.idade <= teto].copy()
    fechou_ate = j.close_date.notna() & (j.close_date <= fim)
    j["ganhou"] = ((j.deal_stage == "Won") & fechou_ate).astype(int)
    j["fechou"] = fechou_ate.astype(int)
    return ab, j


def bloco(nome, corte, fim, teto=138):
    ab, j = janela(pd.Timestamp(corte), pd.Timestamp(fim), teto)
    print(f"\n=== {nome}: corte {corte}, desfecho até {fim}, idade <= {teto} d")
    print(f"abertos no corte: {len(ab)} | na janela: {len(j)} | ganharam: {j.ganhou.sum()} | fecharam: {j.fechou.sum()} | seguiram abertos: {len(j) - j.fechou.sum()}")
    print("AUC idade invertida, ganhou: %.3f" % auc(-j.idade, j.ganhou))
    print("AUC idade invertida, fechou: %.3f" % auc(-j.idade, j.fechou))
    f = j[j.fechou == 1]
    print("só os que fecharam (n=%d, Won %d / Lost %d): AUC idade invertida ganho x perda %.3f | AUC idade (não invertida) %.3f"
          % (len(f), f.ganhou.sum(), len(f) - f.ganhou.sum(), auc(-f.idade, f.ganhou), auc(f.idade, f.ganhou)))
    return j


# A. Idade nos abertos em 30/09 (até 138 d)
j = bloco("A", "2017-09-30", "2017-12-31")
j["faixa"] = pd.cut(j.idade, [-1, 7, 14, 30, 60, 90, 138])
print(j.groupby("faixa", observed=True).agg(n=("idade", "size"), ganhou_pct=("ganhou", "mean"), fechou_pct=("fechou", "mean")).round(3))

# B. Robustez
bloco("B1/B2 (longe do teto)", "2017-09-30", "2017-12-31", teto=60)
bloco("B3/B4 (outro corte)", "2017-06-30", "2017-09-30")

# C. Os outros critérios na mesma população (corte 30/09)
print("\n=== C: outros critérios na janela de A (n=%d)" % len(j))
print("C1 AUC preço de tabela, ganhou: %.3f" % auc(j.sales_price, j.ganhou))
print("C1b AUC preço de tabela, fechou: %.3f" % auc(j.sales_price, j.fechou))
jc = j[j.revenue.notna()]
print("C2 AUC receita da conta (porte), ganhou, só com conta (n=%d): %.3f" % (len(jc), auc(jc.revenue, jc.ganhou)))
tem = j.account.notna().astype(int)
print("C3 tem conta: %d de %d | AUC tem conta, fechou: %.3f | ganhou: %.3f" % (tem.sum(), len(j), auc(tem, j.fechou), auc(tem, j.ganhou)))
print(pd.crosstab(tem.rename("tem_conta"), j.fechou.rename("fechou_ate_31_12")))
# idade invertida dentro de quem tem conta (a idade sobrevive sem o vazamento da conta?)
print("C4 AUC idade invertida, ganhou, só com conta (n=%d): %.3f | fechou: %.3f"
      % (len(jc), auc(-jc.idade, jc.ganhou), auc(-jc.idade, jc.fechou)))
