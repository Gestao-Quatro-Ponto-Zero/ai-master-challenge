"""Auditoria do MRR e churn por segmento pesado pela receita.

1) O MRR é valor faturado ou fórmula? Assinaturas se sobrepõem? Plano e assentos da conta batem com as assinaturas?
2) Churn de receita por segmento: % do MRR (assinaturas pagas) que está em assinaturas encerradas, com IC 95% por
   bootstrap reamostrando CONTAS (assinaturas da mesma conta não são independentes).

Uso: uv run --with pandas,scipy python -I solution/scripts/08_auditoria_mrr.py <raw> <json_saida> <docs>
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

RAW, DEST, DOCS = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
acc = pd.read_csv(RAW / "ravenstack_accounts.csv")
sub = pd.read_csv(RAW / "ravenstack_subscriptions.csv", parse_dates=["start_date", "end_date"])
paga = sub[~sub.is_trial].copy()

# ------------------------------------------------ 1) auditoria
paga["preco_assento"] = paga.mrr_amount / paga.seats
preco = paga.groupby("plan_tier").preco_assento.agg(lambda x: x.mode()[0])
formula = (paga.mrr_amount == paga.seats * paga.plan_tier.map(preco)).mean()
ativas = paga[paga.end_date.isna()]
simult = ativas.groupby("account_id").size()
mrr_conta = ativas.groupby("account_id").mrr_amount.sum()
moda = paga.groupby("account_id").plan_tier.agg(lambda x: x.mode()[0]).reindex(acc.account_id)
seats_soma = ativas.groupby("account_id").seats.sum()
rho_seats = stats.spearmanr(acc.set_index("account_id").seats.reindex(seats_soma.index), seats_soma)[0]
auditoria = dict(
    preco_por_assento={k: float(v) for k, v in preco.items()},
    pct_mrr_formula=float(formula),
    pct_arr_12x=float((sub.arr_amount == 12 * sub.mrr_amount).mean()),
    trial_mrr_zero=float((sub[sub.is_trial].mrr_amount == 0).mean()),
    ativas_simult_mediana=float(simult.median()), ativas_simult_max=int(simult.max()), contas_com_uma=int((simult == 1).sum()),
    contas_com_ativas=int(len(simult)),
    mrr_conta_mediana=float(mrr_conta.median()), mrr_conta_max=float(mrr_conta.max()), mrr_total_ativo=float(ativas.mrr_amount.sum()),
    upgrade_e_downgrade=int((paga.upgrade_flag & paga.downgrade_flag).sum()),
    pct_plano_conta_bate=float((moda.values == acc.plan_tier.values).mean()),
    rho_assentos=float(rho_seats),
    dist_simultaneas=[dict(n=int(k), contas=int(v)) for k, v in simult.value_counts().sort_index().items()],
)

# ------------------------------------------------ 2) churn de receita por segmento
paga = paga.merge(acc[["account_id", "industry", "country", "referral_source"]], on="account_id")
paga["perdido"] = paga.mrr_amount * paga.churn_flag
media = float(paga.perdido.sum() / paga.mrr_amount.sum())
rng = np.random.default_rng(42)
DIM = [("industry", "Indústria"), ("country", "País"), ("referral_source", "Canal de aquisição"),
       ("plan_tier", "Plano da assinatura"), ("billing_frequency", "Cobrança")]
segs = {}
for col, nome in DIM:
    itens = []
    for nivel, g in paga.groupby(col):
        ag = g.groupby("account_id")[["mrr_amount", "perdido"]].sum().values
        idx = rng.integers(0, len(ag), (4000, len(ag)))
        bs = ag[idx, 1].sum(1) / ag[idx, 0].sum(1)
        lo, hi = np.percentile(bs, [2.5, 97.5])
        itens.append(dict(nivel=str(nivel), n=int(len(ag)), assinaturas=int(len(g)), taxa=float(g.perdido.sum() / g.mrr_amount.sum()),
                          ic=[float(lo), float(hi)], mrr_ativo=float(g.loc[~g.churn_flag, "mrr_amount"].sum())))
    segs[nome] = dict(itens=itens, acima=[i["nivel"] for i in itens if i["ic"][0] > media],
                      abaixo=[i["nivel"] for i in itens if i["ic"][1] < media])

out = dict(auditoria=auditoria, media_receita=media, segmentos_receita=segs)
DEST.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")

br = lambda v, n=1: f"{v:,.{n}f}".replace(",", "X").replace(".", ",").replace("X", ".")
md = ["# Auditoria do MRR\n", "Gerado por `solution/scripts/08_auditoria_mrr.py`.\n",
      "| checagem | resultado | leitura |", "|---|---|---|",
      f"| MRR = assentos × preço de tabela | {br(formula * 100)}% | preço fixo por assento: " + ", ".join(f"{k} US$ {br(v, 0)}" for k, v in preco.items()) + "; sem desconto nem proporcionalidade |",
      f"| ARR = 12 × MRR | {br(auditoria['pct_arr_12x'] * 100)}% | inclusive em contrato anual |",
      f"| Assinaturas pagas ativas ao mesmo tempo por conta | mediana {br(simult.median(), 0)}, máx. {simult.max()} | só {auditoria['contas_com_uma']} contas têm uma só: assinaturas se sobrepõem |",
      f"| MRR ativo por conta | mediana US$ {br(mrr_conta.median(), 0)}, máx. US$ {br(mrr_conta.max(), 0)} | soma de assinaturas sobrepostas: total provavelmente inflado |",
      f"| MRR ativo total (soma) | US$ {br(ativas.mrr_amount.sum(), 0)} | usar com cautela |",
      f"| Assinaturas com upgrade E downgrade | {auditoria['upgrade_e_downgrade']} | marcações contraditórias |",
      f"| Plano da conta = plano mais frequente nas assinaturas | {br(auditoria['pct_plano_conta_bate'] * 100)}% | acaso seria ~33% |",
      f"| Assentos da conta × soma dos assentos ativos | ρ = {br(rho_seats, 2)} | cadastro e assinaturas não batem |",
      "\n# Churn de receita por segmento\n",
      f"% do MRR (assinaturas pagas) em assinaturas encerradas. Média geral: **{br(media * 100)}%**. IC 95% por bootstrap de contas.\n"]
for nome, s in segs.items():
    md.append(f"\n## {nome}\n\n| nível | churn de receita | IC 95% | contas | assinaturas |\n|---|---|---|---|---|")
    for i in sorted(s["itens"], key=lambda x: -x["taxa"]):
        md.append(f"| {i['nivel']} | {br(i['taxa'] * 100)}% | {br(i['ic'][0] * 100)}–{br(i['ic'][1] * 100)}% | {i['n']} | {i['assinaturas']} |")
    md.append(f"\nAcima da média com IC: {', '.join(s['acima']) or 'nenhum'} · abaixo: {', '.join(s['abaixo']) or 'nenhum'}")
(DOCS / "auditoria_mrr.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("ok", DEST)
print(json.dumps(auditoria, ensure_ascii=False))
for nome, s in segs.items():
    print(nome, "| acima:", s["acima"], "| abaixo:", s["abaixo"], "|", [(i["nivel"], round(i["taxa"] * 100, 1)) for i in s["itens"]])
