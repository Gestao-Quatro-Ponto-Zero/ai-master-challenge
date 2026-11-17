"""17 — Concentração do ARR perdido em dez/2024 (país, setor, plano) comparada com a exposição. Uso: python -I 17_concentracao_dez24.py <pasta_dados>"""
import sys, pandas as pd
from scipy import stats
D = sys.argv[1]; a = pd.read_csv(f"{D}/ravenstack_accounts.csv"); s = pd.read_csv(f"{D}/ravenstack_subscriptions.csv")
s["ini"] = pd.to_datetime(s.start_date); s["fim"] = pd.to_datetime(s.end_date)
s = s.merge(a[["account_id","country","industry"]], on="account_id")
t0, t1 = pd.Timestamp("2024-11-30"), pd.Timestamp("2024-12-31")
base = s[(s.ini <= t0) & (s.fim.isna() | (s.fim > t0))]          # ativas no início de dezembro (exposição)
lost = base[(base.fim > t0) & (base.fim <= t1)]                    # dessas, encerradas em dezembro
allend = s[(s.fim > t0) & (s.fim <= t1)]
print(f"encerradas em dez/24: {len(allend)} assinaturas, ARR ${allend.arr_amount.sum():,.0f} | das ativas em 30/11: {len(lost)}, ARR ${lost.arr_amount.sum():,.0f}")
for dim in ["country","industry","plan_tier"]:
    g = pd.DataFrame({"ARR_perdido": allend.groupby(dim).arr_amount.sum(), "ARR_exposto_30nov": base.groupby(dim).arr_amount.sum(),
                      "assin_perdidas": lost.groupby(dim).size(), "assin_expostas": base.groupby(dim).size()}).fillna(0)
    g["%_do_perdido"] = g.ARR_perdido/g.ARR_perdido.sum(); g["%_da_exposicao"] = g.ARR_exposto_30nov/g.ARR_exposto_30nov.sum()
    g["taxa_ARR"] = lost.groupby(dim).arr_amount.sum().reindex(g.index).fillna(0)/g.ARR_exposto_30nov
    g["taxa_assin"] = g.assin_perdidas/g.assin_expostas
    p = stats.chi2_contingency(pd.DataFrame({"perd": g.assin_perdidas, "fic": g.assin_expostas - g.assin_perdidas}).values)[1]
    print(f"\n=== {dim}  (taxa de assinaturas perdidas difere entre grupos? qui-quadrado p={p:.3f})")
    print(g.sort_values("ARR_perdido", ascending=False).to_string(float_format=lambda v: f"{v:,.3f}" if v < 2 else f"{v:,.0f}"))
print("\nARR médio por assinatura ativa (30/11):", base.groupby("plan_tier").arr_amount.mean().round(0).to_dict())
