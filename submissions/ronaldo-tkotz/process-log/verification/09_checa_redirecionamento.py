"""09 — Checa os números do texto "Redirecionamento Diagnóstico" proposto pelo Ronaldo. Uso: python -I 09_checa_redirecionamento.py <pasta_dados>"""
import sys, pandas as pd, numpy as np
from scipy import stats
D = sys.argv[1]; r = lambda n: pd.read_csv(f"{D}/ravenstack_{n}.csv")
a, s, u, tk = r("accounts"), r("subscriptions"), r("feature_usage"), r("support_tickets")
A = a.set_index("account_id"); A["upg"] = s.groupby("account_id").upgrade_flag.any().reindex(A.index).fillna(False)
print("=== upgrade x cancelamento (churn_flag)")
for k, g in A.groupby("upg"): print(f"  upgrade={k}: {len(g)} contas, {g.churn_flag.sum()} canceladas ({g.churn_flag.mean():.1%})")
ct = pd.crosstab(A.upg, A.churn_flag); print(f"  qui-quadrado p={stats.chi2_contingency(ct)[1]:.3f} | Fisher p={stats.fisher_exact(ct.values)[1]:.3f}")
lo, hi = stats.binomtest(int(A[A.upg].churn_flag.sum()), int(A.upg.sum())).proportion_ci(); print(f"  IC95% da taxa com upgrade: {lo:.1%}–{hi:.1%}")
lo, hi = stats.binomtest(int(A[~A.upg].churn_flag.sum()), int((~A.upg).sum())).proportion_ci(); print(f"  IC95% da taxa sem upgrade: {lo:.1%}–{hi:.1%}")
print("  por plano (plan_tier da conta):")
for p, g in A.groupby("plan_tier"):
    w, wo = g[g.upg], g[~g.upg]; pv = stats.fisher_exact(pd.crosstab(g.upg, g.churn_flag).values)[1]
    print(f"    {p:10s} com upgrade {len(w)} contas, retenção {1-w.churn_flag.mean():.1%} | sem upgrade {len(wo)} contas, retenção {1-wo.churn_flag.mean():.1%} | Fisher p={pv:.3f}")
print(f"  retenção geral: {1-A.churn_flag.mean():.1%}")
print("\n=== erros por feature")
f = u.groupby("feature_name").agg(acoes=("usage_count","sum"), erros=("error_count","sum"), sessoes=("usage_id","count")); f["taxa"] = f.erros/f.acoes
f = f.sort_values("erros", ascending=False); f["rank_erros"] = range(1, len(f)+1); f["rank_acoes"] = f.acoes.rank(ascending=False).astype(int); f["rank_taxa"] = f.taxa.rank(ascending=False).astype(int)
print(f.head(6).to_string()); print(f"  correlação erros x ações entre features (Spearman): {stats.spearmanr(f.erros, f.acoes)[0]:.2f}")
chi = stats.chi2_contingency(np.c_[f.erros, f.acoes - f.erros]); print(f"  taxas de erro diferem entre features? qui-quadrado p={chi[1]:.3f}")
us = u.merge(s[["subscription_id","account_id"]], on="subscription_id"); us["churn"] = us.account_id.map(A.churn_flag)
for feat in ["feature_4","feature_9"]:
    g = us[us.feature_name==feat].groupby("account_id").agg(e=("error_count","sum"), c=("usage_count","sum")); g["taxa"] = g.e/g.c; g["churn"] = g.index.map(A.churn_flag)
    U, p = stats.mannwhitneyu(g[g.churn].taxa, g[~g.churn].taxa); print(f"  {feat}: taxa de erro por conta — canceladas {g[g.churn].taxa.median():.3f} vs ativas {g[~g.churn].taxa.median():.3f} | p={p:.3f}")
print("\n=== suporte")
print(f"  sem avaliação: {tk.satisfaction_score.isna().mean():.1%}")
print("  resolução (h) por prioridade:\n", tk.groupby("priority").resolution_time_hours.describe()[["count","mean","50%"]].round(1).to_string())
print("  1ª resposta (min) por prioridade:", tk.groupby("priority").first_response_time_minutes.median().to_dict())
print(f"  Kruskal resolução entre prioridades: p={stats.kruskal(*[g.resolution_time_hours for _, g in tk.groupby('priority')]).pvalue:.3f}")
