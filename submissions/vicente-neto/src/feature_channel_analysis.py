"""
RavenStack | Análises complementares da Fase 3
- feature_trends.csv: tendência da duração por uso e da taxa de erro por feature (40 testes),
  com correção de Benjamini-Hochberg. Só uso válido (a partir do cadastro da conta).
- channel_churn_analysis.csv: churn, MRR e sobrevivência por canal de aquisição;
  log-rank de ads contra os demais canais, com teste de permutação.
Uso: python src/feature_channel_analysis.py   (depois de outputs/accounts_master.csv existir)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import DATA, OUT
import numpy as np, pandas as pd
from scipy import stats

a = pd.read_csv(f'{DATA}/ravenstack_accounts.csv', parse_dates=['signup_date'])
s = pd.read_csv(f'{DATA}/ravenstack_subscriptions.csv')
f = pd.read_csv(f'{DATA}/ravenstack_feature_usage.csv', parse_dates=['usage_date'])
m = pd.read_csv(f'{OUT}/accounts_master.csv', parse_dates=['signup_date', 'cutoff_date'])
m['has_churn_event'] = m.has_churn_event.astype(str) == 'True'

# ---------------- tendência por feature ----------------
u = f.merge(s[['subscription_id', 'account_id']], on='subscription_id').merge(a[['account_id', 'signup_date']], on='account_id')
u = u[u.usage_date >= u.signup_date].copy()
u['t'] = (u.usage_date - pd.Timestamp('2023-01-01')).dt.days / 365
u['dpu'] = u.usage_duration_secs / u.usage_count.clip(lower=1)

def bh(p):
    p = np.asarray(p, float); n = len(p); o = np.argsort(p); q = np.empty(n); prev = 1.0
    for i, idx in enumerate(o[::-1]):
        k = n - i; prev = min(prev, p[idx] * n / k); q[idx] = prev
    return q

rows = []
for feat, d in u.groupby('feature_name'):
    lr = stats.linregress(d.t, d.dpu)
    ct = d.groupby(d.usage_date.dt.year).agg(err=('error_count', 'sum'), use=('usage_count', 'sum'))
    p_err = stats.chi2_contingency(np.array([ct.err.values, (ct.use - ct.err).clip(lower=0).values]))[1] if len(ct) > 1 else np.nan
    rows.append(dict(feature=feat, linhas_uso_valido=len(d),
                     tendencia_duracao_s_por_uso_ao_ano=round(lr.slope, 1), p_duracao=lr.pvalue,
                     erros_por_100_usos_2023=round(100 * ct.err.iloc[0] / ct.use.iloc[0], 2) if 2023 in ct.index else np.nan,
                     erros_por_100_usos_2024=round(100 * ct.err.iloc[-1] / ct.use.iloc[-1], 2),
                     p_erro=p_err, pct_uso_beta=round(100 * d.is_beta_feature.mean(), 1)))
F = pd.DataFrame(rows)
F['q_duracao_BH'] = bh(F.p_duracao); F['q_erro_BH'] = bh(F.p_erro.fillna(1))
F = F.round(4).sort_values('p_duracao')
F.to_csv(f'{OUT}/feature_trends.csv', index=False)
print(f'Features: p_duracao<0,05 = {(F.p_duracao<0.05).sum()} (após BH: {(F.q_duracao_BH<0.05).sum()}); '
      f'p_erro<0,05 = {(F.p_erro<0.05).sum()} (após BH: {(F.q_erro_BH<0.05).sum()})')

# ---------------- canal de aquisição ----------------
m['dur'] = (m.cutoff_date - m.signup_date).dt.days.astype(float); m['ev'] = m.has_churn_event.astype(int)

def logrank(dur, ev, g):
    O = E = V = 0.0
    for t in np.unique(dur[ev == 1]):
        at = dur >= t; n = at.sum(); nA = (at & g).sum()
        d = ((dur == t) & (ev == 1)).sum(); dA = ((dur == t) & (ev == 1) & g).sum()
        if n < 2: continue
        O += dA; E += d * nA / n; V += d * (nA / n) * (1 - nA / n) * (n - d) / (n - 1)
    z = (O - E) / np.sqrt(V); return z, 2 * (1 - stats.norm.cdf(abs(z)))

def km(d, day=365):
    S = 1.0
    for t in np.sort(d.dur.unique()):
        if t > day: break
        n = (d.dur >= t).sum(); e = ((d.dur == t) & (d.ev == 1)).sum(); S *= (1 - e / n) if n else 1
    return S

ads = (m.referral_source == 'ads').values
z, p = logrank(m.dur.values, m.ev.values, ads)
rng = np.random.default_rng(7)
zs = [abs(logrank(m.dur.values, m.ev.values, rng.permutation(ads))[0]) for _ in range(2000)]
p_perm = (np.sum(np.array(zs) >= abs(z)) + 1) / 2001
rows = []
for ch, d in m.groupby('referral_source'):
    rows.append(dict(canal=ch, contas=len(d), churn_pct=round(100 * d.has_churn_event.mean(), 1),
                     mrr_ativo=int(d.mrr_active_sum.sum()),
                     pct_mrr_churn=round(100 * d[d.has_churn_event].mrr_active_sum.sum() / d.mrr_active_sum.sum(), 1),
                     sobrevivencia_365d_pct=round(100 * km(d), 1),
                     teste_vs_demais=(f'log-rank p={p:.3f}; permutação p={p_perm:.3f}; Bonferroni (5 canais) p={min(1, 5*p):.3f}' if ch == 'ads' else '')))
C = pd.DataFrame(rows); C.to_csv(f'{OUT}/channel_churn_analysis.csv', index=False)
print(C.drop(columns='teste_vs_demais').to_string(index=False)); print(f'ads vs demais: log-rank p={p:.4f}, permutação p={p_perm:.4f}')
