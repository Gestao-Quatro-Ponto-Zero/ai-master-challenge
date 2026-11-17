"""04 — Testes de causalidade e sinal: timing do churn, quem continua pagando, uso antes do churn, modelo. Uso: python -I 04_profundo.py <pasta_dados>"""
import sys, pandas as pd, numpy as np
from scipy import stats
D = sys.argv[1]; r = lambda n: pd.read_csv(f"{D}/ravenstack_{n}.csv")
a, s, u, tk, ce = r("accounts"), r("subscriptions"), r("feature_usage"), r("support_tickets"), r("churn_events")
for d, c in [(a,"signup_date"),(s,"start_date"),(s,"end_date"),(u,"usage_date"),(tk,"submitted_at"),(ce,"churn_date")]: d[c] = pd.to_datetime(d[c])
END = pd.Timestamp("2024-12-31"); sg = a.set_index("account_id").signup_date
# (a) posição do churn entre signup e fim da base: uniforme => sem padrão de ciclo de vida
pos = (ce.churn_date - ce.account_id.map(sg)).dt.days / (END - ce.account_id.map(sg)).dt.days
print("(a) posição relativa do churn [0=signup,1=fim da base]: quartis", pos.quantile([.25,.5,.75]).round(2).tolist(), "| KS vs uniforme p=", round(stats.kstest(pos.clip(0,1), "uniform").pvalue,3))
ten = (ce.churn_date - ce.account_id.map(sg)).dt.days
print("    dias do signup até o churn: mediana", ten.median(), "| % nos primeiros 90 dias:", round((ten<=90).mean()*100,1))
# taxa de churn por conta-mês (exposição): calendário
ex = []
for m in pd.period_range("2023-01","2024-12",freq="M"):
    expo = (sg <= m.end_time).sum(); ev = (ce.churn_date.dt.to_period("M")==m).sum(); ex.append((str(m), expo, ev))
ex = pd.DataFrame(ex, columns=["mes","contas_expostas","eventos"]); ex["taxa"] = ex.eventos/ex.contas_expostas
h1, h2 = ex.iloc[:12], ex.iloc[12:]
print(f"    taxa mensal média de eventos por conta exposta: 2023={h1.eventos.sum()/h1.contas_expostas.sum():.3f}  2024={h2.eventos.sum()/h2.contas_expostas.sum():.3f}")
# (b) quem teve evento de churn continua pagando?
act = s[s.end_date.isna()]
print("\n(b) contas com >=1 assinatura ativa em 31/12/2024:", act.account_id.nunique(), "de 500")
last_ev = ce.groupby("account_id").churn_date.max()
subs_after = s.merge(last_ev.rename("ult_churn"), left_on="account_id", right_index=True)
novas = subs_after[subs_after.start_date > subs_after.ult_churn]
print("    contas com evento de churn que abriram assinatura NOVA depois do último evento:", novas.account_id.nunique(), "de", len(last_ev))
mrr_ativo = act.groupby("account_id").mrr_amount.sum()
print(f"    MRR em assinaturas ativas: total ${mrr_ativo.sum():,.0f} | em contas com evento de churn ${mrr_ativo[mrr_ativo.index.isin(last_ev.index)].sum():,.0f}")
fl = a.set_index("account_id").churn_flag
print(f"    contas churn_flag=True ainda com assinatura ativa: {fl[fl].index.isin(act.account_id).sum()} de {fl.sum()}")
print("    eventos por conta:", ce.groupby("account_id").size().value_counts().sort_index().to_dict(), "| reativação flag:", ce.is_reactivation.sum())
print(f"    refund: total ${ce.refund_amount_usd.sum():,.0f}, mediana ${ce.refund_amount_usd.median():.0f}, zero em {(ce.refund_amount_usd==0).mean():.0%}")
print("    receita das assinaturas encerradas por mês (end_date) — dez/2024 concentra:", round((s.end_date.dt.to_period('M')==pd.Period('2024-12')).sum()/s.end_date.notna().sum()*100,1), "% dos encerramentos")
# (c) uso antes do churn: 90d antes vs 90-180d antes (só churners com histórico)
us = u.merge(s[["subscription_id","account_id"]], on="subscription_id")
rows=[]
for _, e in ce.iterrows():
    x = us[us.account_id==e.account_id]; d = (e.churn_date - x.usage_date).dt.days
    rows.append((x[(d>0)&(d<=90)].usage_count.sum(), x[(d>90)&(d<=180)].usage_count.sum(), x[(d>0)&(d<=90)].error_count.sum(), x[(d>90)&(d<=180)].error_count.sum()))
rr = pd.DataFrame(rows, columns=["uso_0_90","uso_90_180","err_0_90","err_90_180"])
print("\n(c) uso 0-90d antes do churn vs 90-180d antes: medianas", rr.uso_0_90.median(), "vs", rr.uso_90_180.median(), "| Wilcoxon p=", round(stats.wilcoxon(rr.uso_0_90, rr.uso_90_180).pvalue,3))
print("    erros 0-90d vs 90-180d: medianas", rr.err_0_90.median(), "vs", rr.err_90_180.median(), "| p=", round(stats.wilcoxon(rr.err_0_90, rr.err_90_180, zero_method="zsplit").pvalue,3))
tt = tk.merge(ce[["account_id","churn_date"]], on="account_id"); dd = (tt.churn_date - tt.submitted_at).dt.days
print("    tickets nos 90d antes de um churn: CSAT", round(tt[(dd>0)&(dd<=90)].satisfaction_score.mean(),2), "| demais tickets:", round(tk.satisfaction_score.mean(),2))
# (d) uso por segmento ao longo do tempo
us2 = us.merge(a[["account_id","plan_tier","industry"]], on="account_id"); us2["sem"] = us2.usage_date.dt.year.astype(str)+"H"+((us2.usage_date.dt.month>6)+1).astype(str)
print("\n(d) uso total por semestre e plano:\n", us2.pivot_table(index="plan_tier", columns="sem", values="usage_count", aggfunc="sum").to_string())
print(" uso total por semestre e indústria:\n", us2.pivot_table(index="industry", columns="sem", values="usage_count", aggfunc="sum").to_string())
# (e) modelo: há sinal preditivo?
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
A = pd.read_csv("outputs/03_contas.csv", index_col=0)
num = ["seats","idade_dias","n_subs","mrr_medio_sub","share_anual","share_autorenew","n_upgrades","n_downgrades","uso_eventos","uso_total","uso_por_seat","erros","taxa_erro","dur_media_s","share_beta","n_features","tickets","csat","csat_resp","escal","resol_h","frt_min","urgentes"]
X = pd.get_dummies(A[num+["industry","country","referral_source","plan_tier","is_trial"]], columns=["industry","country","referral_source","plan_tier"]).astype(float).fillna(A[num].median())
cv = StratifiedKFold(5, shuffle=True, random_state=7)
for alvo in ["churn_evento","churn_flag"]:
    y = A[alvo].astype(int)
    for nome, mdl in [("logística", make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))), ("gradient boosting", GradientBoostingClassifier(random_state=7))]:
        sc = cross_val_score(mdl, X, y, cv=cv, scoring="roc_auc"); print(f"(e) {alvo:13s} {nome:18s} AUC CV = {sc.mean():.3f} ± {sc.std():.3f}")
# placebo: alvo embaralhado
y = A.churn_evento.sample(frac=1, random_state=1).astype(int).values
print("    placebo (alvo embaralhado) logística AUC =", round(cross_val_score(make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)), X, y, cv=cv, scoring="roc_auc").mean(),3))
