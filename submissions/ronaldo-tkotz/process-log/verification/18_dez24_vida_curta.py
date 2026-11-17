"""18 — As 103 assinaturas que nasceram e morreram em dez/2024. Uso: python -I 18_dez24_vida_curta.py <pasta_dados>"""
import sys, pandas as pd, numpy as np
D = sys.argv[1]; a = pd.read_csv(f"{D}/ravenstack_accounts.csv"); s = pd.read_csv(f"{D}/ravenstack_subscriptions.csv"); ce = pd.read_csv(f"{D}/ravenstack_churn_events.csv")
s["ini"] = pd.to_datetime(s.start_date); s["fim"] = pd.to_datetime(s.end_date); s["dur"] = (s.fim - s.ini).dt.days
s = s.merge(a[["account_id","signup_date","country","industry","churn_flag"]].rename(columns={"churn_flag":"conta_churn"}), on="account_id")
s["mes_ini"] = s.ini.dt.to_period("M"); s["mes_fim"] = s.fim.dt.to_period("M")
dez = pd.Period("2024-12", "M"); x = s[(s.mes_ini == dez) & (s.mes_fim == dez)]
print(f"=== as {len(x)} assinaturas")
print(f"  trial: {x.is_trial.mean():.0%} | duração (dias) mediana {x.dur.median():.0f}, min {x.dur.min()}, max {x.dur.max()} | ARR ${x.arr_amount.sum():,.0f}")
print("  plano:", x.plan_tier.value_counts().to_dict(), "| frequência:", x.billing_frequency.value_counts().to_dict())
print(f"  upgrade_flag {x.upgrade_flag.mean():.0%} | downgrade_flag {x.downgrade_flag.mean():.0%} | auto_renew {x.auto_renew_flag.mean():.0%} | churn_flag da assinatura {x.churn_flag.mean():.0%}")
print(f"  contas distintas: {x.account_id.nunique()} | conta com churn_flag: {x.conta_churn.mean():.0%} | conta criada em dez/24: {(pd.to_datetime(x.signup_date).dt.to_period('M') == dez).mean():.0%}")
ativa_fim = lambda r: ((s.account_id == r.account_id) & (s.subscription_id != r.subscription_id) & (s.ini <= r.fim) & (s.fim.isna() | (s.fim > r.fim))).any()
print(f"  a conta tinha outra assinatura ativa no dia do fim: {x.apply(ativa_fim, axis=1).mean():.0%}")
print("  dia do mês do fim:", x.fim.dt.day.describe()[["min","50%","max"]].to_dict(), "| fim em 31/12:", int((x.fim == "2024-12-31").sum()))
print("\n=== é coisa de dezembro? por mês de início: % das novas assinaturas que terminam no mesmo mês")
m = s.groupby("mes_ini").agg(novas=("subscription_id","size"), mesmo_mes=("mes_fim", lambda v: (v == v.name).sum()))
m["mesmo_mes"] = [((s.mes_ini == p) & (s.mes_fim == p)).sum() for p in m.index]; m["%"] = m.mesmo_mes/m.novas
print(m.loc["2024-01":].to_string(float_format=lambda v: f"{v:.1%}"))
print(f"  2024 jan–nov: {m.loc['2024-01':'2024-11','mesmo_mes'].sum()/m.loc['2024-01':'2024-11','novas'].sum():.1%} | dez: {m.loc['2024-12','%']:.1%}")
print("\n=== duração das encerradas: dezembro x resto (dias)")
e = s[s.fim.notna()]; print(e.groupby(e.mes_fim == dez).dur.describe()[["count","25%","50%","75%"]].to_string())
print("\n=== janela observável: quem começa no mês m só aparece como encerrada se durar até 31/12/2024")
for p in ["2024-06","2024-09","2024-10","2024-11","2024-12"]:
    q = s[s.mes_ini == pd.Period(p, "M")]; print(f"  início {p}: {len(q)} novas, encerradas até 31/12: {q.fim.notna().mean():.1%}, das encerradas com <31 dias: {(q.dur < 31).sum()}")
from scipy import stats
print("\n=== % encerradas até 31/12/2024 por mês de início (todas as safras)")
REF = pd.Timestamp("2024-12-31"); g = s.groupby("mes_ini").agg(novas=("subscription_id","size"), enc=("fim", lambda v: v.notna().mean()))
print(g.T.to_string(float_format=lambda v: f"{v:.2f}"))
print(f"  correlação (Spearman) meses de observação x % encerradas: {stats.spearmanr((REF.to_period('M') - g.index).map(lambda d: d.n), g.enc)[0]:.2f}")
e = s[s.fim.notna()].copy(); e["pos"] = (e.fim - e.ini).dt.days / (REF - e.ini).dt.days
print(f"  posição do fim dentro da janela disponível (0 = no início, 1 = em 31/12): quartis {e.pos.quantile([.25,.5,.75]).round(2).tolist()} | KS contra uniforme p={stats.kstest(e.pos.replace([np.inf,-np.inf],np.nan).dropna().clip(0,1), 'uniform').pvalue:.3f}")
