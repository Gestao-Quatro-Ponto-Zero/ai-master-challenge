"""15 — Ponte de MRR por CONTA (sugestão do Ronaldo: separar identidade de conta e de assinatura). Uso: python -I 15_ponte_mrr_conta.py <pasta_dados>"""
import sys, pandas as pd, numpy as np
D = sys.argv[1]; a = pd.read_csv(f"{D}/ravenstack_accounts.csv"); s = pd.read_csv(f"{D}/ravenstack_subscriptions.csv")
p = s[~s.is_trial].copy(); p["ini"] = pd.to_datetime(p.start_date); p["fim"] = pd.to_datetime(p.end_date)
qs = pd.date_range("2023-03-31", "2024-12-31", freq="QE")
def mrr_em(t):
    x = p[(p.ini <= t) & (p.fim.isna() | (p.fim > t))]
    return x.groupby("account_id").mrr_amount.sum(), x.groupby("account_id").size()
snap = {t: mrr_em(t) for t in qs}
rows = []
for t0, t1 in zip(qs[:-1], qs[1:]):
    m0, m1 = snap[t0][0], snap[t1][0]; ids = m0.index.union(m1.index)
    m0, m1 = m0.reindex(ids).fillna(0), m1.reindex(ids).fillna(0); d = m1 - m0
    rows.append(dict(trimestre=t1.strftime("%Y-%m"), contas_ini=int((m0>0).sum()), contas_fim=int((m1>0).sum()),
        mrr_ini=m0.sum(), novo=m1[m0==0].sum(), expansao=d[(m0>0)&(m1>0)&(d>0)].sum(),
        contracao=-d[(m0>0)&(m1>0)&(d<0)].sum(), perda_total=m0[(m0>0)&(m1==0)].sum(),
        contas_perdidas=int(((m0>0)&(m1==0)).sum()), contas_contraidas=int(((m0>0)&(m1>0)&(d<0)).sum()), mrr_fim=m1.sum()))
b = pd.DataFrame(rows).set_index("trimestre")
b["GRR"] = 1 - (b.contracao + b.perda_total)/b.mrr_ini; b["NRR"] = 1 + (b.expansao - b.contracao - b.perda_total)/b.mrr_ini
pd.set_option("display.width", 250); print("=== ponte de MRR por conta (US$), trimestral — só assinaturas pagas")
print(b.round({"GRR":3,"NRR":3}).to_string(float_format=lambda v: f"{v:,.0f}" if abs(v) > 2 else f"{v:.3f}"))
n = snap[qs[-1]][1]; print(f"\nassinaturas ativas por conta em 31/12/2024: mediana {n.median():.0f}, min {n.min()}, max {n.max()} | contas com MRR > 0: {len(n)}")
flag = set(a[a.churn_flag].account_id); m = snap[qs[-1]][0]
print(f"contas com churn_flag que ainda têm MRR ativo em 31/12/2024: {len(flag & set(m.index))} de {len(flag)} (MRR ${m[m.index.isin(flag)].sum():,.0f})")
tot = b[["expansao","contracao","perda_total","novo"]].sum(); print("\nsoma 2023-Q2 a 2024-Q4:", {k: f"${v:,.0f}" for k, v in tot.items()})
