"""Números da página de Sugestões e da Previsão (solution/dashboard/src/sugestoes.json).

Previsão — só o que os dados sustentam:
  * por safra: proporção de assinaturas pagas que cancela (IC de Wilson);
  * pelo tamanho da base: registros de churn por mês esperados para N assinaturas ativas
    (quase-Poisson na janela estável jul/23–nov/24, faixa de predição 95%), marcando extrapolação.
Não prevê datas: isso exigiria prever o crescimento da base e as datas de encerramento não são confiáveis.

Uso: uv run --with pandas,scipy,statsmodels python -I solution/scripts/07_sugestoes_previsao.py <raw> <outputs> <json_saida>
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

RAW, OUT, DEST = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
acc = pd.read_csv(RAW / "ravenstack_accounts.csv")
sub = pd.read_csv(RAW / "ravenstack_subscriptions.csv", parse_dates=["start_date", "end_date"])
b = pd.read_csv(OUT / "account_360.csv")
mes = pd.read_csv(OUT / "cancelamentos_mensal.csv")


def wilson(k, n, z=1.96):
    ph = k / n; d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d; h = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return [float(c - h), float(c + h)]


# ------------------------------------------------ previsão por safra
paga = sub[~sub.is_trial]
k, n = int(paga.churn_flag.sum()), len(paga)
enc = paga[paga.churn_flag]
safra = dict(canceladas=k, total=n, taxa=k / n, ic=wilson(k, n),
             pct_mrr_perdido=float(enc.mrr_amount.sum() / paga.mrr_amount.sum()))

# ------------------------------------------------ previsão pelo tamanho da base
est = mes[(mes.mes >= "2023-07") & (mes.mes <= "2024-11")]
X = sm.add_constant(np.log(est.assinaturas_ativas))
fit = sm.GLM(est.cancelamentos, X, family=sm.families.Poisson()).fit(scale="X2")
phi = max(fit.scale, 1.0)
obs_min, obs_max = int(est.assinaturas_ativas.min()), int(mes.assinaturas_ativas.max())
grid = np.unique(np.concatenate([np.linspace(200, obs_max * 1.6, 80), [obs_max]])).round()
pr = fit.get_prediction(sm.add_constant(np.log(grid), has_constant="add")).summary_frame(alpha=0.05)
curva = []
for g, (_, r) in zip(grid, pr.iterrows()):
    lo = stats.poisson.ppf(0.025, r.mean_ci_lower / phi) * phi
    hi = stats.poisson.ppf(0.975, r.mean_ci_upper / phi) * phi
    curva.append(dict(base=int(g), esperado=float(r["mean"]), lo=float(lo), hi=float(hi), extrapolado=bool(g > obs_max)))
base_atual = int(mes.assinaturas_ativas.iloc[-1])

# ------------------------------------------------ impacto de 1 ponto percentual (aritmética, não previsão)
ativas_pagas = int((sub.end_date.isna() & ~sub.is_trial).sum())
impacto = dict(ativas_pagas=ativas_pagas, assinaturas_por_pp=ativas_pagas / 100,
               mrr_medio_cancelada=float(enc.mrr_amount.mean()), mrr_mediano_cancelada=float(enc.mrr_amount.median()))

# ------------------------------------------------ hipóteses no limite: quantas contas para confirmar?
media = b.churn_flag_conta.mean()
hip = []
for col, nivel, nome in [("perfil_industry", "DevTools", "Indústria DevTools"), ("perfil_referral_source", "event", "Canal de aquisição “event”")]:
    g = b[b[col] == nivel]; kk, nn = int(g.churn_flag_conta.sum()), len(g)
    resto = b[b[col] != nivel]
    _, p = stats.fisher_exact(pd.crosstab(b[col] == nivel, b.churn_flag_conta))
    es = abs(proportion_effectsize(kk / nn, resto.churn_flag_conta.mean()))
    # nos dados atuais o p bruto não sobrevive à correção para ~25 segmentos testados;
    # num teste NOVO, com a hipótese registrada antes, α = 0,05 basta.
    n_nec = NormalIndPower().solve_power(effect_size=es, alpha=0.05, power=0.8, ratio=1)
    ritmo = nn / 2  # contas novas por ano no segmento (2 anos de dados)
    hip.append(dict(nome=nome, taxa=kk / nn, n=nn, ic=wilson(kk, nn), taxa_resto=float(resto.churn_flag_conta.mean()),
                    p=float(p), p_corrigido=float(min(1, p * 25)), contas_necessarias=int(np.ceil(n_nec)),
                    contas_por_ano=float(ritmo), anos=float(np.ceil(n_nec) / ritmo)))

# ------------------------------------------------ contas para investigar primeiro (os dois registros concordam)
alvo = b[b.churn_flag_conta & (b.churn_eventos > 0)].sort_values("receita_mrr_perdido", ascending=False)
contas = [dict(id=r.account_id, nome=r.perfil_account_name, industria=r.perfil_industry, pais=r.perfil_country,
               plano=r.perfil_plan_tier, mrr_perdido=float(r.receita_mrr_perdido), mrr_ativo=float(r.receita_mrr_ativo),
               eventos=int(r.churn_eventos), motivo=r.churn_motivo_ultimo, feedback=None if pd.isna(r.churn_feedback_ultimo) else r.churn_feedback_ultimo,
               tickets=int(r.suporte_tickets), sem_nota=None if pd.isna(r.suporte_pct_sem_nota) else float(r.suporte_pct_sem_nota))
          for r in alvo.head(15).itertuples()]

out = dict(safra=safra, curva=curva, base_atual=base_atual, base_obs=[obs_min, obs_max], dispersao=phi,
           impacto=impacto, hipoteses=hip, contas_investigar=contas, n_contas_concordam=int(len(alvo)),
           mrr_perdido_contas_concordam=float(alvo.receita_mrr_perdido.sum()))
DEST.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
print("ok", DEST)
print(json.dumps({k: v for k, v in out.items() if k not in ("curva", "contas_investigar")}, indent=1, ensure_ascii=False))
print("base atual", base_atual, [c for c in curva if c["base"] == obs_max])
