"""08 — Testa as hipóteses levantadas pelo Ronaldo na revisão da 1ª versão. Uso: python -I 08_hipoteses_humanas.py <pasta_dados>"""
import sys, pandas as pd, numpy as np
from scipy import stats
D = sys.argv[1]; r = lambda n: pd.read_csv(f"{D}/ravenstack_{n}.csv")
a, s, u, tk, ce = r("accounts"), r("subscriptions"), r("feature_usage"), r("support_tickets"), r("churn_events")
for d, c in [(a,"signup_date"),(s,"start_date"),(s,"end_date"),(u,"usage_date"),(tk,"submitted_at"),(ce,"churn_date")]: d[c] = pd.to_datetime(d[c])
act = s[s.end_date.isna()]; last_ev = ce.groupby("account_id").churn_date.max()
print("=== H1: 110 contas com churn_flag=True — estão canceladas ou ativas?")
fl = a[a.churn_flag].account_id
x = act[act.account_id.isin(fl)].copy(); x["ult_evento"] = x.account_id.map(last_ev)
print(f"  contas: {len(fl)} | com assinatura ativa: {x.account_id.nunique()} | MRR ativo nelas: ${x.mrr_amount.sum():,.0f} ({x.mrr_amount.sum()/act.mrr_amount.sum():.1%} do MRR ativo)")
print(f"  sem nenhum evento de churn: {(~fl.isin(ce.account_id)).sum()}")
com = x[x.ult_evento.notna()]
print(f"  assinaturas ativas abertas ANTES do último evento (nunca fechadas): {(com.start_date <= com.ult_evento).sum()} | DEPOIS do evento: {(com.start_date > com.ult_evento).sum()}")
acc_after = com[com.start_date > com.ult_evento].groupby("account_id").mrr_amount.sum()
print(f"  contas churn_flag com assinatura PAGA aberta depois do último evento: {(acc_after>0).sum()} de {com.account_id.nunique()}")
print("\n=== H2: impacto financeiro")
e = s[s.end_date.notna()]
print(f"  MRR de assinaturas encerradas no período: ${e.mrr_amount.sum():,.0f} em {len(e)} assinaturas | refunds: ${ce.refund_amount_usd.sum():,.0f}")
print(f"  MRR encerrado em contas churn_flag=True: ${e[e.account_id.isin(fl)].mrr_amount.sum():,.0f} | em contas com evento: ${e[e.account_id.isin(ce.account_id)].mrr_amount.sum():,.0f} | em contas sem evento: ${e[~e.account_id.isin(ce.account_id)].mrr_amount.sum():,.0f}")
print(f"  taxa de encerramento de assinaturas — contas com evento {s[s.account_id.isin(ce.account_id)].churn_flag.mean():.1%} vs sem evento {s[~s.account_id.isin(ce.account_id)].churn_flag.mean():.1%}")
print(f"  taxa de encerramento — contas churn_flag=True {s[s.account_id.isin(fl)].churn_flag.mean():.1%} vs False {s[~s.account_id.isin(fl)].churn_flag.mean():.1%}")
print("\n=== H3: reativação — flag x assinaturas")
ce2 = ce.copy(); nxt = []
for _, ev in ce2.iterrows():
    later = s[(s.account_id==ev.account_id) & (s.start_date > ev.churn_date) & (s.mrr_amount>0)]
    nxt.append((later.start_date.min() - ev.churn_date).days if len(later) else np.nan)
ce2["dias_ate_nova_paga"] = nxt
print(f"  eventos seguidos de assinatura PAGA nova: {ce2.dias_ate_nova_paga.notna().mean():.1%} (mediana {ce2.dias_ate_nova_paga.median():.0f} dias)")
print("  por is_reactivation:", ce2.groupby("is_reactivation").dias_ate_nova_paga.apply(lambda v: f"{v.notna().mean():.1%} com nova paga").to_dict())
print("\n=== H4: uso — volume, erros, sessões longas")
print(f"  ações (soma usage_count): {u.usage_count.sum():,} | registros (sessões): {len(u):,} | erros: {u.error_count.sum():,} | taxa de erro: {u.error_count.sum()/u.usage_count.sum():.2%}")
print(f"  duração média: {u.usage_duration_secs.mean()/60:.1f} min | sessões > 50 min: {(u.usage_duration_secs>3000).mean():.1%}")
print(f"  Spearman erro x duração: {stats.spearmanr(u.error_count, u.usage_duration_secs)[0]:.3f} | erro x ações: {stats.spearmanr(u.error_count, u.usage_count)[0]:.3f} | ações x duração: {stats.spearmanr(u.usage_count, u.usage_duration_secs)[0]:.3f}")
lg = u.usage_duration_secs > 3000
print(f"  erros por ação — sessões >50 min: {u[lg].error_count.sum()/u[lg].usage_count.sum():.2%} vs ≤50 min: {u[~lg].error_count.sum()/u[~lg].usage_count.sum():.2%}")
print(f"  erros por ação — beta: {u[u.is_beta_feature].error_count.sum()/u[u.is_beta_feature].usage_count.sum():.2%} vs não beta: {u[~u.is_beta_feature].error_count.sum()/u[~u.is_beta_feature].usage_count.sum():.2%}")
fe = u.groupby("feature_name").agg(acoes=("usage_count","sum"), erros=("error_count","sum")); fe["taxa"] = fe.erros/fe.acoes
print(f"  taxa de erro por feature: min {fe.taxa.min():.2%}, max {fe.taxa.max():.2%} (40 features)")
q = u.groupby(u.usage_date.dt.to_period("Q")).agg(acoes=("usage_count","sum"), erros=("error_count","sum"), dur=("usage_duration_secs","mean"))
q["taxa"] = (100*q.erros/q.acoes).round(2); q["dur_min"] = (q.dur/60).round(1); print(q[["acoes","erros","taxa","dur_min"]].to_string())
A = pd.read_csv("outputs/03_contas.csv", index_col=0)
A["dur_longa"] = A.index.map(u.merge(s[["subscription_id","account_id"]], on="subscription_id").assign(l=lambda d: d.usage_duration_secs>3000).groupby("account_id").l.mean())
for c in ["taxa_erro","erros","dur_media_s","dur_longa"]:
    for alvo in ["churn_flag","churn_evento"]:
        x0, x1 = A.loc[~A[alvo], c].dropna(), A.loc[A[alvo], c].dropna(); U, p = stats.mannwhitneyu(x1, x0)
        print(f"  {c:12s} x {alvo:12s}: ficou {x0.median():.4f} | churn {x1.median():.4f} | p={p:.3f} AUC={U/(len(x0)*len(x1)):.2f}")
print("\n=== H5: churn logo após upgrade")
print(f"  eventos com preceding_upgrade_flag: {ce.preceding_upgrade_flag.sum()} de {len(ce)} ({ce.preceding_upgrade_flag.mean():.1%})")
up = s[s.upgrade_flag][["account_id","start_date"]]
def upg_antes(df, janela):
    m = df[["account_id","churn_date"]].reset_index().merge(up, on="account_id", how="left"); d = (m.churn_date - m.start_date).dt.days
    m["ok"] = (d >= 0) & (d <= janela); return m.groupby("index").ok.any()
rng = np.random.default_rng(7); sg = a.set_index("account_id").signup_date
fake = ce.copy(); fake["churn_date"] = [sg[x] + pd.Timedelta(days=int(rng.integers(0, max((pd.Timestamp('2024-12-31')-sg[x]).days,1)))) for x in fake.account_id]
for j in [30, 90]:
    real, base = upg_antes(ce, j), upg_antes(fake, j)
    print(f"  upgrade (assinatura com upgrade_flag) iniciada até {j}d antes: eventos reais {real.mean():.1%} | datas sorteadas {base.mean():.1%}")
    print(f"     concordância com preceding_upgrade_flag: flag=True → {real[ce.preceding_upgrade_flag.values].mean():.1%} | flag=False → {real[~ce.preceding_upgrade_flag.values].mean():.1%}")
ua = s.groupby("account_id").upgrade_flag.any()
print(f"  contas com algum upgrade: churn_flag {a.set_index('account_id').churn_flag[ua].mean():.1%} vs sem upgrade {a.set_index('account_id').churn_flag[~ua].mean():.1%} | evento {a.account_id.isin(ce.account_id)[ua.reindex(a.account_id).values].mean():.1%} vs {a.account_id.isin(ce.account_id)[~ua.reindex(a.account_id).values].mean():.1%}")
print(f"  assinaturas com upgrade_flag encerram: {s[s.upgrade_flag].churn_flag.mean():.1%} vs sem: {s[~s.upgrade_flag].churn_flag.mean():.1%}")
print("  motivo dos eventos pós-upgrade:", ce[ce.preceding_upgrade_flag].reason_code.value_counts(normalize=True).round(2).to_dict())
print("  motivo dos demais:            ", ce[~ce.preceding_upgrade_flag].reason_code.value_counts(normalize=True).round(2).to_dict())
print(f"  qui-quadrado motivo x pós-upgrade: p={stats.chi2_contingency(pd.crosstab(ce.reason_code, ce.preceding_upgrade_flag))[1]:.3f}")
print("\n=== H6: CSAT — viés de não resposta")
tk["resp"] = tk.satisfaction_score.notna()
print("  taxa de resposta por prioridade:", tk.groupby("priority").resp.mean().round(3).to_dict(), "| escalado:", tk.groupby("escalation_flag").resp.mean().round(3).to_dict())
print(f"  resolução (h) respondidos {tk[tk.resp].resolution_time_hours.median()} vs sem resposta {tk[~tk.resp].resolution_time_hours.median()} | p={stats.mannwhitneyu(tk[tk.resp].resolution_time_hours, tk[~tk.resp].resolution_time_hours).pvalue:.3f}")
tk["churn_conta"] = tk.account_id.isin(fl)
print("  taxa de resposta — contas churn_flag:", round(tk[tk.churn_conta].resp.mean(),3), "| demais:", round(tk[~tk.churn_conta].resp.mean(),3))
print("  CSAT por escalonamento:", tk.groupby("escalation_flag").satisfaction_score.mean().round(2).to_dict(), "| por prioridade:", tk.groupby("priority").satisfaction_score.mean().round(2).to_dict())
