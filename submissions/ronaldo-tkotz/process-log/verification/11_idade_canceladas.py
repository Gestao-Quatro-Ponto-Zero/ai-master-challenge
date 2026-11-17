"""11 — Confere a afirmação do Ronaldo: a idade média das contas canceladas fica entre 12 e 15 meses. Uso: python -I 11_idade_canceladas.py <pasta_dados>"""
import sys, pandas as pd, numpy as np
from scipy import stats
D = sys.argv[1]; r = lambda n: pd.read_csv(f"{D}/ravenstack_{n}.csv")
a, ce = r("accounts"), r("churn_events"); REF = pd.Timestamp("2024-12-31")
A = a.set_index("account_id"); A["signup"] = pd.to_datetime(A.signup_date)
A["idade_hoje"] = (REF - A.signup).dt.days/30.44
A["idade_no_churn"] = (pd.to_datetime(ce.churn_date).groupby(ce.account_id).max().reindex(A.index) - A.signup).dt.days/30.44
A.loc[~A.churn_flag, "idade_no_churn"] = np.nan
t = A.groupby("country").apply(lambda g: pd.Series({
  "canc": int(g.churn_flag.sum()), "idade_hoje_canc": g[g.churn_flag].idade_hoje.mean(), "idade_hoje_ativas": g[~g.churn_flag].idade_hoje.mean(),
  "idade_no_churn": g.idade_no_churn.mean(), "churn%": 100*g.churn_flag.mean()}))
print(t.round(1).to_string())
c, n = A[A.churn_flag], A[~A.churn_flag]
print(f"\nGERAL canceladas: idade hoje {c.idade_hoje.mean():.1f} m | idade no último evento {c.idade_no_churn.mean():.1f} m (mediana {c.idade_no_churn.median():.1f}) | ativas: idade hoje {n.idade_hoje.mean():.1f} m")
print(f"Mann-Whitney idade hoje canceladas x ativas: p={stats.mannwhitneyu(c.idade_hoje, n.idade_hoje).pvalue:.3f}")
print(f"países com churn > 30%: {list(t.index[t['churn%']>30])}")
