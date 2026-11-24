"""Mesmo teste do 02, mas no nível de assinatura (alvo: subscriptions.churn_flag = assinatura encerrada).
Aqui uso e cancelamento estão na MESMA linha, então é o teste mais favorável para achar sinal.
Uso: uv run --with pandas,scipy python -I solution/scripts/03_correlacoes_assinatura.py <outputs> <docs>
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats

OUT, DOCS = Path(sys.argv[1]), Path(sys.argv[2])
s = pd.read_csv(OUT / "subscription_360.csv")
s = s[~s.is_trial]  # trial tem MRR 0, distorce receita
y = s.churn_flag.astype(bool)
s["anual"] = s.billing_frequency.eq("annual")
s["taxa_erro"] = s.uso_erros / s.uso_eventos.replace(0, np.nan)
s["pct_beta"] = s.uso_registros_beta / s.uso_registros.replace(0, np.nan)
s["eventos_por_seat"] = s.uso_eventos / s.seats.replace(0, np.nan)
cat_ = {"receita": ["plan_tier", "seats", "mrr_amount", "anual", "auto_renew_flag", "upgrade_flag", "downgrade_flag"],
        "uso": ["uso_registros", "uso_eventos", "uso_duracao_h", "uso_erros", "taxa_erro", "uso_features_distintas",
                "pct_beta", "eventos_por_seat"],
        "perfil": ["conta_industry", "conta_referral_source", "conta_country", "conta_plan_tier"]}
rows = []
for cat, cols in cat_.items():
    for c in cols:
        x = s[c]
        if pd.api.types.is_bool_dtype(x) or not pd.api.types.is_numeric_dtype(x):
            tab = pd.crosstab(x, y); chi2, p, *_ = stats.chi2_contingency(tab)
            f = np.sqrt(chi2 / (tab.values.sum() * (min(tab.shape) - 1)))
            t = y.groupby(x).mean(); leit = " · ".join(f"{k}: {v:.1%}" for k, v in t.items())
        else:
            x = pd.to_numeric(x, errors="coerce").astype(float); ok = x.notna(); u, p = stats.mannwhitneyu(x[ok & y], x[ok & ~y]); auc = u / ((ok & y).sum() * (ok & ~y).sum())
            f = abs(auc - .5) * 2; leit = f"encerrada {x[y].mean():,.2f} × ativa {x[~y].mean():,.2f}"
        rows.append(dict(categoria=cat, variavel=c, forca=f, p=p, leitura=leit))
r = pd.DataFrame(rows)
o = np.argsort(r.p.values); n = len(r); q = r.p.values[o] * n / np.arange(1, n + 1)
q = np.minimum.accumulate(q[::-1])[::-1]; r.loc[r.index[o], "q_bh"] = np.minimum(q, 1)
r = r.sort_values("forca", ascending=False)
r.to_csv(OUT / "correlacoes_assinatura.csv", index=False)
md = [f"# Correlação com encerramento de assinatura (n={len(s)} pagas, {y.mean():.1%} encerradas)\n",
      "| categoria | variável | força | p | q | leitura |", "|---|---|---|---|---|---|"]
md += [f"| {l.categoria} | `{l.variavel}`{' ✅' if l.q_bh < .05 else ''} | {l.forca:.2f} | {l.p:.3f} | {l.q_bh:.3f} | {l.leitura} |" for l in r.itertuples()]
(DOCS / "correlacoes_assinatura.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("\n".join(md))
