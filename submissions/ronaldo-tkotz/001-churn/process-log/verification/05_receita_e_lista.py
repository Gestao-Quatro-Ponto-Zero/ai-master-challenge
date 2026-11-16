"""05 — Evento de churn x faturamento; receita nova x encerrada; lista de contas para o CS. Uso: python -I 05_receita_e_lista.py <pasta_dados>"""
import sys, pandas as pd, numpy as np
D = sys.argv[1]; r = lambda n: pd.read_csv(f"{D}/ravenstack_{n}.csv")
a, s, u, tk, ce = r("accounts"), r("subscriptions"), r("feature_usage"), r("support_tickets"), r("churn_events")
for d, c in [(a,"signup_date"),(s,"start_date"),(s,"end_date"),(tk,"submitted_at"),(ce,"churn_date")]: d[c] = pd.to_datetime(d[c])
# evento de churn coincide com o fim de alguma assinatura da conta (±30 dias)?
ends = s.dropna(subset=["end_date"])[["account_id","end_date"]]
m = ce.merge(ends, on="account_id", how="left"); m["gap"] = (m.end_date - m.churn_date).dt.days.abs()
best = m.groupby("churn_event_id").gap.min()
print(f"eventos de churn com fim de assinatura da conta em ±30 dias: {(best<=30).mean():.1%} | em ±7 dias: {(best<=7).mean():.1%} | conta sem nenhuma assinatura encerrada: {best.isna().mean():.1%}")
# baseline do acaso: datas aleatórias na mesma conta
rng = np.random.default_rng(7); fake = ce.copy(); sg = a.set_index("account_id").signup_date
fake["churn_date"] = [sg[x] + pd.Timedelta(days=int(rng.integers(0, max((pd.Timestamp('2024-12-31')-sg[x]).days,1)))) for x in fake.account_id]
mf = fake.merge(ends, on="account_id", how="left"); mf["gap"] = (mf.end_date - mf.churn_date).dt.days.abs()
print(f"   baseline com datas aleatórias: ±30 dias = {(mf.groupby('churn_event_id').gap.min()<=30).mean():.1%}")
# receita: MRR novo x MRR encerrado por trimestre (assinaturas pagas)
q = lambda x: x.dt.to_period("Q")
pg = s[s.mrr_amount > 0]
rv = pd.DataFrame({"mrr_novo": pg.groupby(q(pg.start_date)).mrr_amount.sum(), "mrr_encerrado": pg.groupby(q(pg.end_date)).mrr_amount.sum()}).fillna(0)
rv["churn_receita_%_do_novo"] = (100*rv.mrr_encerrado/rv.mrr_novo).round(1); print("\nreceita por trimestre:\n", rv.round(0).to_string())
print("MRR 0 (trial/grátis):", (s.mrr_amount==0).sum(), "assinaturas; is_trial:", s.is_trial.sum())
# downgrade / upgrade antes do churn
print("\nchurn com downgrade anterior:", f"{ce.preceding_downgrade_flag.mean():.1%}", "| com upgrade anterior:", f"{ce.preceding_upgrade_flag.mean():.1%}", "| base de assinaturas: downgrade", f"{s.downgrade_flag.mean():.1%}", "upgrade", f"{s.upgrade_flag.mean():.1%}")
# lista para o CS: eventos nos últimos 90 dias, ordenados por MRR ativo
act = s[s.end_date.isna()].groupby("account_id").agg(mrr_ativo=("mrr_amount","sum"), subs_ativas=("subscription_id","count"))
rec = ce[ce.churn_date > pd.Timestamp("2024-10-02")].groupby("account_id").agg(eventos_90d=("churn_event_id","count"), ultimo=("churn_date","max"), motivos=("reason_code", lambda x: ", ".join(sorted(set(x)))))
tot = ce.groupby("account_id").size().rename("eventos_total")
L = rec.join(tot).join(act).join(a.set_index("account_id")[["account_name","industry","plan_tier","seats"]]).sort_values("mrr_ativo", ascending=False)
L.to_csv("outputs/05_lista_cs.csv")
print(f"\ncontas com evento de churn nos últimos 90 dias: {len(L)} | MRR ativo nelas: ${L.mrr_ativo.sum():,.0f} ({L.mrr_ativo.sum()/act.mrr_ativo.sum():.0%} do total)")
print(L.head(15).to_string())
