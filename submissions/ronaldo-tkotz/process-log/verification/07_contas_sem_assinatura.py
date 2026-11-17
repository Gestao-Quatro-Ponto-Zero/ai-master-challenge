"""07 — Em cada fim de trimestre, quantas contas já cadastradas estavam sem nenhuma assinatura ativa (paga ou não)? Uso: python -I 07_contas_sem_assinatura.py <pasta_dados>"""
import sys, pandas as pd
D = sys.argv[1]
a = pd.read_csv(f"{D}/ravenstack_accounts.csv", parse_dates=["signup_date"])
s = pd.read_csv(f"{D}/ravenstack_subscriptions.csv", parse_dates=["start_date","end_date"])
for q in pd.period_range("2023Q1", "2024Q4", freq="Q"):
    t = q.end_time.normalize()
    cad = a[a.signup_date <= t].account_id
    ativas = s[(s.start_date <= t) & (s.end_date.isna() | (s.end_date >= t))]
    pagas = ativas[ativas.mrr_amount > 0]
    teve_antes = s[s.start_date <= t].account_id.unique()
    sem = cad[~cad.isin(ativas.account_id)]; sem_paga = cad[~cad.isin(pagas.account_id)]
    print(f"{q}: cadastradas={len(cad)} | sem assinatura ativa={len(sem)} (das quais já tiveram alguma antes: {sem.isin(teve_antes).sum()}) | sem assinatura PAGA ativa={len(sem_paga)} (já tiveram antes: {sem_paga.isin(teve_antes).sum()})")
