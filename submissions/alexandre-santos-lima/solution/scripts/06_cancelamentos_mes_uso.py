"""Cancelamentos × mês e × uso.
1) A contagem mensal é explicada pela base ativa (Poisson com offset) ou o mês tem efeito próprio?
2) Uso × cancelamento: (a) série mensal crua vs. controlando a base; (b) por conta; (c) uso antes × depois do churn.
Uso: uv run --with pandas,scipy,statsmodels python -I solution/scripts/06_cancelamentos_mes_uso.py data/raw solution/outputs
"""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.api as sm

RAW, OUT = Path(sys.argv[1]), Path(sys.argv[2])
acc = pd.read_csv(RAW / "ravenstack_accounts.csv", parse_dates=["signup_date"])
sub = pd.read_csv(RAW / "ravenstack_subscriptions.csv", parse_dates=["start_date", "end_date"])
use = pd.read_csv(RAW / "ravenstack_feature_usage.csv", parse_dates=["usage_date"])
chn = pd.read_csv(RAW / "ravenstack_churn_events.csv", parse_dates=["churn_date"])

rows = []
for m in pd.period_range("2023-01", "2024-12", freq="M"):
    i, f = m.start_time, m.end_time
    ativas = ((sub.start_date <= f) & (sub.end_date.isna() | (sub.end_date >= i))).sum()
    contas = (acc.signup_date <= f).sum()
    rows.append(dict(mes=str(m), mes_do_ano=m.month, t=len(rows),
                     cancelamentos=int(((chn.churn_date >= i) & (chn.churn_date <= f)).sum()),
                     assinaturas_ativas=int(ativas), contas_cadastradas=int(contas),
                     uso=int(use[(use.usage_date >= i) & (use.usage_date <= f)].usage_count.sum())))
m = pd.DataFrame(rows)
m["uso_por_assinatura"] = m.uso / m.assinaturas_ativas
res = {}

# ---------- 1) contagem × base × mês
rho, p = stats.spearmanr(m.t, m.cancelamentos); res["cancel_vs_tempo"] = (rho, p)
rho, p = stats.spearmanr(m.assinaturas_ativas, m.cancelamentos); res["cancel_vs_base"] = (rho, p)
X = sm.add_constant(np.log(m.assinaturas_ativas))
pois = sm.GLM(m.cancelamentos, X, family=sm.families.Poisson()).fit()
res["elasticidade_base"] = (pois.params.iloc[1], pois.conf_int().iloc[1].tolist())
res["pseudo_r2_base"] = 1 - pois.deviance / pois.null_deviance
# o tempo acrescenta algo além da base?
X2 = sm.add_constant(np.column_stack([np.log(m.assinaturas_ativas), m.t]))
pois2 = sm.GLM(m.cancelamentos, X2, family=sm.families.Poisson()).fit()
res["lr_tempo_alem_base_p"] = stats.chi2.sf(pois.deviance - pois2.deviance, 1)
# sazonalidade: mês do ano além da base (só 2 obs por mês do ano!)
X3 = pd.concat([X, pd.get_dummies(m.mes_do_ano, prefix="m", drop_first=True).astype(float)], axis=1)
pois3 = sm.GLM(m.cancelamentos, X3, family=sm.families.Poisson()).fit()
res["lr_sazonalidade_p"] = stats.chi2.sf(pois.deviance - pois3.deviance, 11)
# sazonalidade com contas cadastradas como base (eventos são por conta)
Xc = sm.add_constant(np.log(m.contas_cadastradas))
poisc = sm.GLM(m.cancelamentos, Xc, family=sm.families.Poisson()).fit()
res["elasticidade_contas"] = (poisc.params.iloc[1], poisc.conf_int().iloc[1].tolist())
m["esperado_pela_base"] = pois.predict(X)
m["razao_obs_esp"] = m.cancelamentos / m.esperado_pela_base
# sobre-dispersão (Poisson ok?)
res["dispersao_pearson"] = pois.pearson_chi2 / pois.df_resid

# ---------- 2a) uso × cancelamentos na série mensal
rho, p = stats.spearmanr(m.uso_por_assinatura, m.cancelamentos); res["cancel_vs_uso_por_assin_cru"] = (rho, p)
rho, p = stats.spearmanr(m.uso, m.cancelamentos); res["cancel_vs_uso_total_cru"] = (rho, p)
# parcial: resíduos de ambos contra log(base)
lb = np.log(m.assinaturas_ativas)
r_c = m.razao_obs_esp
r_u = sm.OLS(np.log(m.uso_por_assinatura), sm.add_constant(lb)).fit().resid
rho, p = stats.spearmanr(r_c, r_u); res["cancel_vs_uso_controlando_base"] = (rho, p)
# primeiras diferenças (remove tendência)
d = m[["cancelamentos", "uso"]].diff().dropna()
rho, p = stats.spearmanr(d.cancelamentos, d.uso); res["delta_cancel_vs_delta_uso"] = (rho, p)

# ---------- 2b) por conta: já testado no script 02 (AUC de uso). Repetimos o principal.
b = pd.read_csv(OUT / "account_360.csv")
for col in ["uso_eventos", "uso_taxa_erro", "uso_dias_desde_ultimo", "uso_variacao_2024_vs_2023"]:
    x = b[col].astype(float); y = b.churn_flag_conta.astype(bool); ok = x.notna()
    u, p = stats.mannwhitneyu(x[ok & y], x[ok & ~y]); res[f"conta_{col}_auc"] = (u / ((ok & y).sum() * (ok & ~y).sum()), p)

# ---------- 2c) uso da conta nos 90 dias antes × depois de cada churn
ux = use.merge(sub[["subscription_id", "account_id"]])
antes, depois = [], []
for e in chn.itertuples():
    uu = ux[ux.account_id == e.account_id]
    antes.append(uu[(uu.usage_date < e.churn_date) & (uu.usage_date >= e.churn_date - pd.Timedelta(days=90))].usage_count.sum())
    depois.append(uu[(uu.usage_date > e.churn_date) & (uu.usage_date <= e.churn_date + pd.Timedelta(days=90))].usage_count.sum())
ad = pd.DataFrame(dict(antes=antes, depois=depois, data=chn.churn_date))
ad = ad[ad.data <= "2024-10-01"]  # precisa de 90 dias depois dentro da base
w, p = stats.wilcoxon(ad.antes, ad.depois)
res["uso_90d_antes_depois"] = (ad.antes.mean(), ad.depois.mean(), (ad.depois > 0).mean(), p, len(ad))

m.to_csv(OUT / "cancelamentos_mensal.csv", index=False)
json.dump({k: [float(v) if np.isscalar(v) else v for v in (vals if isinstance(vals, tuple) else (vals,))] for k, vals in res.items()},
          open(OUT / "cancelamentos_mes_uso.json", "w"), indent=1, default=float)
for k, v in res.items():
    print(f"{k}: {v}")
print(m[["mes", "cancelamentos", "assinaturas_ativas", "esperado_pela_base", "razao_obs_esp", "uso_por_assinatura"]].round(2).to_string(index=False))

# ---------- robustez: quase-Poisson (corrige sobre-dispersão) e janela estável (jul/23–nov/24)
print("\n=== ROBUSTEZ")
def qp(df, extra=None):
    X = sm.add_constant(np.log(df.assinaturas_ativas).rename("log_base"))
    if extra is not None:
        X = pd.concat([X, extra.loc[df.index]], axis=1)
    return sm.GLM(df.cancelamentos, X, family=sm.families.Poisson()).fit(scale="X2"), X
for nome, df in [("todos os meses", m), ("jul/23–nov/24", m[(m.mes >= "2023-07") & (m.mes <= "2024-11")])]:
    b0, _ = qp(df)
    bt, _ = qp(df, df[["t"]].astype(float))
    sea = pd.get_dummies(m.mes_do_ano, prefix="m", drop_first=True).astype(float)
    bs, _ = qp(df, sea)
    F_t = ((b0.deviance - bt.deviance) / 1) / (bt.deviance / bt.df_resid)
    F_s = ((b0.deviance - bs.deviance) / (bs.df_model - b0.df_model)) / (bs.deviance / max(bs.df_resid, 1))
    print(f"[{nome}] n={len(df)} elasticidade base={b0.params.iloc[1]:.2f} IC={b0.conf_int().iloc[1].round(2).tolist()} "
          f"| tendência além da base p={stats.f.sf(F_t, 1, bt.df_resid):.3f} "
          f"| sazonalidade p={stats.f.sf(F_s, bs.df_model - b0.df_model, max(bs.df_resid,1)):.3f} (df resid {bs.df_resid})")
    rr = df.cancelamentos / b0.predict()
    ru = sm.OLS(np.log(df.uso_por_assinatura), sm.add_constant(np.log(df.assinaturas_ativas))).fit().resid
    print(f"   uso × cancelamentos controlando a base: rho={stats.spearmanr(rr, ru)[0]:.2f} p={stats.spearmanr(rr, ru)[1]:.3f}")
    dd = df[["cancelamentos", "uso"]].diff().dropna()
    print(f"   variação mensal uso × variação cancelamentos: rho={stats.spearmanr(dd.cancelamentos, dd.uso)[0]:.2f} p={stats.spearmanr(dd.cancelamentos, dd.uso)[1]:.3f}")
    print(f"   cru uso/assinatura × cancelamentos: rho={stats.spearmanr(df.uso_por_assinatura, df.cancelamentos)[0]:.2f}")

# ---------- exporta para o dashboard (solution/dashboard/src/mes_uso.json)
JAN = (m.mes >= "2023-07") & (m.mes <= "2024-11")         # janela estável
est = m[JAN]
b0 = sm.GLM(est.cancelamentos, sm.add_constant(np.log(est.assinaturas_ativas)), family=sm.families.Poisson()).fit(scale="X2")
phi = max(b0.scale, 1.0)  # conservador: nunca estreita a faixa abaixo do Poisson
Xall = sm.add_constant(np.log(m.assinaturas_ativas))
m["esp"] = b0.predict(Xall)
m["lo"] = np.clip(m.esp - 1.96 * np.sqrt(phi * m.esp), 0, None)
m["hi"] = m.esp + 1.96 * np.sqrt(phi * m.esp)
m["razao"] = m.cancelamentos / m.esp
m["estavel"] = JAN
ru = sm.OLS(np.log(est.uso_por_assinatura), sm.add_constant(np.log(est.assinaturas_ativas))).fit()
m["uso_resid"] = np.log(m.uso_por_assinatura) - ru.predict(sm.add_constant(np.log(m.assinaturas_ativas)))
m["cancel_resid"] = np.log(m.razao.replace(0, np.nan))
grid = np.linspace(m.assinaturas_ativas[m.assinaturas_ativas > 0].min(), m.assinaturas_ativas.max(), 60)
curva = [dict(base=float(g), esp=float(b0.predict(np.array([[1.0, np.log(g)]]))[0])) for g in grid]
r2 = 1 - b0.deviance / b0.null_deviance
# sazonalidade: razão por mês do ano em cada ano
saz = []
for mm in range(1, 13):
    r23 = m[(m.mes_do_ano == mm) & (m.mes.str.startswith("2023"))].iloc[0]
    r24 = m[(m.mes_do_ano == mm) & (m.mes.str.startswith("2024"))].iloc[0]
    saz.append(dict(mes=mm, r2023=float(r23.razao), r2024=float(r24.razao), esp2023=float(r23.esp), esp2024=float(r24.esp)))
sz = pd.DataFrame(saz); comp = sz[(sz.esp2023 >= 5) & (sz.mes != 12)]
rho_saz, p_saz = stats.spearmanr(comp.r2023, comp.r2024)
# testes estáveis
bt = sm.GLM(est.cancelamentos, sm.add_constant(np.column_stack([np.log(est.assinaturas_ativas), est.t])), family=sm.families.Poisson()).fit(scale="X2")
F_t = (b0.deviance - bt.deviance) / (bt.deviance / bt.df_resid)
sea = pd.get_dummies(est.mes_do_ano, prefix="m", drop_first=True).astype(float)
bs = sm.GLM(est.cancelamentos, pd.concat([sm.add_constant(np.log(est.assinaturas_ativas)), sea], axis=1), family=sm.families.Poisson()).fit(scale="X2")
k = bs.df_model - b0.df_model
F_s = ((b0.deviance - bs.deviance) / k) / (bs.deviance / max(bs.df_resid, 1))
rho_c, p_c = stats.spearmanr(est.cancelamentos / b0.predict(), ru.resid)
dd = est[["cancelamentos", "uso"]].diff().dropna(); rho_d, p_d = stats.spearmanr(dd.cancelamentos, dd.uso)
rho_cru, p_cru = stats.spearmanr(est.uso_por_assinatura, est.cancelamentos)
# antes × depois
ad2 = ad.copy()
rho_ad, _ = stats.spearmanr(ad2.antes, ad2.depois)
# uso por conta: histograma em % de contas
y = b.churn_flag_conta.astype(bool); x = b.uso_eventos.astype(float)
bins = np.arange(0, x.max() + 100, 100)
h1, _ = np.histogram(x[y], bins); h0, _ = np.histogram(x[~y], bins)
hist = [dict(faixa=f"{int(bins[i])}–{int(bins[i+1])}", churn=float(h1[i] / y.sum()), retida=float(h0[i] / (~y).sum())) for i in range(len(h1))]
u, p_conta = stats.mannwhitneyu(x[y], x[~y]); auc = u / (y.sum() * (~y).sum())
ks, p_ks = stats.ks_2samp(x[y], x[~y])
out = dict(
    mensal=[dict(mes=r.mes, cancelamentos=int(r.cancelamentos), base=int(r.assinaturas_ativas), esp=round(float(r.esp), 2),
                 faixa=[round(float(r.lo), 2), round(float(r.hi), 2)], razao=round(float(r.razao), 3), uso=int(r.uso),
                 uso_por_assinatura=round(float(r.uso_por_assinatura), 2), uso_resid=round(float(r.uso_resid), 4),
                 cancel_resid=None if np.isnan(r.cancel_resid) else round(float(r.cancel_resid), 4), estavel=bool(r.estavel))
            for r in m.itertuples()],
    curva=curva, sazonal=saz,
    stats=dict(r2=float(r2), elasticidade=float(b0.params.iloc[1]), elasticidade_ic=[float(v) for v in b0.conf_int().iloc[1]],
               dispersao=float(phi), p_tendencia=float(stats.f.sf(F_t, 1, bt.df_resid)),
               p_sazonal=float(stats.f.sf(F_s, k, max(bs.df_resid, 1))), rho_saz=float(rho_saz), p_saz=float(p_saz), n_saz=int(len(comp)),
               dentro_faixa=int(((est.cancelamentos >= m.loc[est.index, "lo"]) & (est.cancelamentos <= m.loc[est.index, "hi"])).sum()), n_estavel=int(len(est)),
               rho_cru=float(rho_cru), p_cru=float(p_cru), rho_controlado=float(rho_c), p_controlado=float(p_c),
               rho_delta=float(rho_d), p_delta=float(p_d),
               antes_media=float(ad2.antes.mean()), depois_media=float(ad2.depois.mean()), pct_usa_depois=float((ad2.depois > 0).mean()),
               p_antes_depois=float(res["uso_90d_antes_depois"][3]), n_antes_depois=int(len(ad2)), rho_antes_depois=float(rho_ad),
               auc_conta=float(auc), p_conta=float(p_conta), ks=float(ks), p_ks=float(p_ks)),
    antes_depois=[dict(antes=int(a), depois=int(d_)) for a, d_ in zip(ad2.antes, ad2.depois)],
    hist_conta=hist,
)
dest = Path(sys.argv[3]) if len(sys.argv) > 3 else None
if dest:
    dest.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print("\nexport ok", dest, json.dumps(out["stats"], indent=0))
