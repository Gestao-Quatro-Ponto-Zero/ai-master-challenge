"""12 — Testa a preocupação do Ronaldo: contas anuais decidem não renovar no vencimento. Uso: python -I 12_renovacao.py <pasta_dados>"""
import sys, pandas as pd, numpy as np
from scipy import stats
D = sys.argv[1]; r = lambda n: pd.read_csv(f"{D}/ravenstack_{n}.csv")
a, s = r("accounts"), r("subscriptions"); REF = pd.Timestamp("2024-12-31")
A = a.set_index("account_id")
p = s[~s.is_trial].copy(); p["ini"] = pd.to_datetime(p.start_date); p["fim"] = pd.to_datetime(p.end_date)
print("=== 1. duração das assinaturas pagas encerradas (dias)")
e = p[p.fim.notna()].copy(); e["dur"] = (e.fim - e.ini).dt.days
print(e.groupby("billing_frequency").dur.describe()[["count","25%","50%","75%","max"]].round(0).to_string())
print(f"  anuais encerradas entre 330 e 400 dias (≈ vencimento): {e[e.billing_frequency=='annual'].dur.between(330,400).mean():.0%}")
print("\n=== 2. depois que uma assinatura paga termina, a conta abre outra paga em até 60 dias? (só fins até 31/10/2024)")
e = e[e.fim <= REF - pd.Timedelta(days=60)]
def renovou(x):
    o = p[(p.account_id==x.account_id) & (p.subscription_id!=x.subscription_id) & (p.ini >= x.fim - pd.Timedelta(days=30)) & (p.ini <= x.fim + pd.Timedelta(days=60))]
    return len(o) > 0
e["renovou"] = e.apply(renovou, axis=1)
t = e.groupby(["billing_frequency","auto_renew_flag"]).agg(n=("renovou","size"), renov=("renovou","mean"), mrr=("mrr_amount","sum")); print(t.round(3).to_string())
print(f"  anual x mensal: Fisher p={stats.fisher_exact(pd.crosstab(e.billing_frequency, e.renovou).values)[1]:.3f}")
print(f"  auto_renew sim x não: Fisher p={stats.fisher_exact(pd.crosstab(e.auto_renew_flag, e.renovou).values)[1]:.3f}")
print("\n=== 3. churn_flag da conta pelo auto_renew e frequência da última assinatura paga")
last = p.sort_values("ini").groupby("account_id").last(); A["freq"] = last.billing_frequency; A["auto"] = last.auto_renew_flag
print(A.groupby(["freq","auto"]).churn_flag.agg(["size","mean"]).round(3).to_string())
print(f"  auto_renew: Fisher p={stats.fisher_exact(pd.crosstab(A.auto, A.churn_flag).values)[1]:.3f}")
print("\n=== 4. carteira anual ativa: próximos aniversários de contrato (90 dias após 31/12/2024)")
at = p[(p.billing_frequency=="annual") & p.fim.isna()].copy()
def prox(d):
    k = max(1, int(np.ceil(((REF - d).days)/365.25))); return d + pd.DateOffset(years=k)
at["aniv"] = at.ini.apply(prox); at["dias"] = (at.aniv - REF).dt.days
j = at[at.dias <= 90]; jn = j[~j.auto_renew_flag]
print(f"  anuais ativas: {len(at)} assinaturas, {at.account_id.nunique()} contas, MRR ${at.mrr_amount.sum():,.0f}")
print(f"  aniversário em 90 dias: {len(j)} assinaturas, {j.account_id.nunique()} contas, ARR ${j.arr_amount.sum():,.0f}")
print(f"  ... dessas, SEM auto-renew: {len(jn)} assinaturas, {jn.account_id.nunique()} contas, ARR ${jn.arr_amount.sum():,.0f}")
j = j.assign(pais=j.account_id.map(A.country)); print("  por país (ARR em 90 dias):", j.groupby("pais").arr_amount.sum().sort_values(ascending=False).round(0).to_dict())
jn.assign(pais=jn.account_id.map(A.country), conta=jn.account_id.map(A.account_name)).sort_values("arr_amount", ascending=False)[["account_id","conta","pais","plan_tier","aniv","arr_amount"]].to_csv(sys.argv[2] if len(sys.argv)>2 else "/dev/null", index=False)
