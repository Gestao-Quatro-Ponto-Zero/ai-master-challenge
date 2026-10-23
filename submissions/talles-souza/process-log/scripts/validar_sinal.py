"""E2 — os atributos do deal predizem ganho fora da amostra? E quão velhos estão os abertos?

Uso: python -X utf8 validar_sinal.py <pasta crm-sales-predictive-analytics>
Treina taxas encolhidas (vendedor, conta, produto, setor) nos deals fechados até 30/09/2017
e mede a AUC nos fechados do 4º trimestre. Saída bruta: evidencias/validar-sinal.txt.
"""
import sys
from pathlib import Path

import pandas as pd

D = Path(sys.argv[1])
pipe = pd.read_csv(D / "sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
acc = pd.read_csv(D / "accounts.csv")
pipe["product"] = pipe["product"].replace({"GTXPro": "GTX Pro"})
df = pipe.merge(acc[["account", "sector"]], on="account", how="left")
df["sector"] = df.sector.fillna("sem conta")
df["account"] = df.account.fillna("sem conta")

REF = df.close_date.max()
fech = df[df.deal_stage.isin(["Won", "Lost"])].copy()
fech["won"] = (fech.deal_stage == "Won").astype(int)
fech["dias"] = (fech.close_date - fech.engage_date).dt.days


def auc(y, s):
    """AUC por postos (Mann-Whitney), sem depender de sklearn."""
    r = s.rank()
    n1 = int(y.sum()); n0 = len(y) - n1
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def encolhida(treino, col, k=50):
    """Taxa de ganho por categoria puxada para a média geral (k = peso da média)."""
    m = treino.won.mean()
    g = treino.groupby(col).won.agg(["sum", "size"])
    return ((g["sum"] + k * m) / (g["size"] + k)).rename(col + "_wr"), m


corte = pd.Timestamp("2017-10-01")
tr, te = fech[fech.close_date < corte], fech[fech.close_date >= corte].copy()
print(f"treino: {len(tr)} fechados até 30/09/2017 · teste: {len(te)} fechados no 4º tri")

print("\n=== AUC no teste, atributo por atributo (0,5 = moeda)")
soma = pd.Series(0.0, index=te.index)
for col in ["sales_agent", "account", "product", "sector"]:
    wr, m = encolhida(tr, col)
    s = te[col].map(wr).fillna(m)
    soma += s - m
    print(f"  {col:<12} AUC {auc(te.won, s):.3f}")
print(f"  {'combinado':<12} AUC {auc(te.won, soma):.3f}  (soma dos desvios encolhidos)")

print("\n=== Duração como sinal (só existe depois do fechamento; aqui para referência)")
print(f"  dias engage→close   AUC {auc(te.won, te.dias):.3f}")

print("\n=== Abertos (Engaging) contra a duração dos fechados")
ab = df[df.deal_stage == "Engaging"].copy()
ab["idade"] = (REF - ab.engage_date).dt.days
mx_won, mx_all = fech[fech.won == 1].dias.max(), fech.dias.max()
p95_won = fech[fech.won == 1].dias.quantile(0.95)
print(f"  duração máxima de um ganho: {mx_won} d · p95 dos ganhos: {p95_won:.0f} d")
for lim, nome in [(p95_won, "p95 dos ganhos"), (mx_all, "máximo de qualquer fechado")]:
    n = int((ab.idade > lim).sum())
    print(f"  Engaging mais velhos que o {nome}: {n} de {len(ab)} ({n / len(ab):.0%})")
print(f"  Engaging sem conta: {int((ab.account == 'sem conta').sum())} de {len(ab)}")
print("  idade dos Engaging por trimestre de engajamento:")
print(ab.groupby(ab.engage_date.dt.to_period("Q").astype(str)).idade.agg(["size", "min", "max"]).to_string())

print("\n=== Prospecting: sem engage_date, então sem idade")
pr = df[df.deal_stage == "Prospecting"]
print(f"  {len(pr)} deals · sem conta: {int((pr.account == 'sem conta').sum())}")
