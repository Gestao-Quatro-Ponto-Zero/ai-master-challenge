"""Quem sao os deals que nunca fecham ("zumbis")? Varia por vendedor/produto/conta? E o par vendedor x conta?"""
from common import *
from scipy import stats
d = load()
e = d[d.engage_date.notna() & (d.engage_date <= "2017-06-30")].copy()   # coortes resolvidas (prazo ja venceu)
e["zombie"] = (~e.closed).astype(int)
print("zumbis coortes ate jun:", e.zombie.mean().round(3), len(e))
def chi(col, df=e, y="zombie"):
    t = pd.crosstab(df[col], df[y]); c, p, dof, _ = stats.chi2_contingency(t)
    v = np.sqrt(c / (t.values.sum() * (min(t.shape) - 1)))
    return dict(col=col, niveis=t.shape[0], chi2=round(c, 1), p=round(p, 4), cramers_v=round(v, 3))
print(pd.DataFrame([chi(c) for c in ["sales_agent", "product", "manager", "regional_office"]]))
ea = e[e.account.notna()]
print("com conta:", pd.DataFrame([chi(c, ea) for c in ["account", "sector", "is_sub", "office_location"]]))
z = e.groupby("sales_agent").agg(n=("zombie", "size"), zr=("zombie", "mean")).sort_values("zr")
print(z.round(3).T.to_string())
# estabilidade no tempo do zumbi-rate por vendedor: coortes ate mar vs abr-jun vs jul-set
d["zombie"] = (~d.closed).astype(int)
co = {"ate_mar": d[d.engage_date <= "2017-03-31"], "abr_jun": d[(d.engage_date > "2017-03-31") & (d.engage_date <= "2017-06-30")],
      "jul_set": d[(d.engage_date > "2017-06-30") & (d.engage_date <= "2017-09-30")]}
zz = pd.DataFrame({k: v.groupby("sales_agent").zombie.mean() for k, v in co.items()})
zz["n_abr_jun"] = co["abr_jun"].groupby("sales_agent").size()
print(zz.round(3).to_string()); print(zz[["ate_mar", "abr_jun", "jul_set"]].corr(method="spearman").round(3))
for a, b in [("ate_mar", "abr_jun"), ("abr_jun", "jul_set"), ("ate_mar", "jul_set")]:
    x = zz[[a, b]].dropna(); print(a, b, stats.spearmanr(x[a], x[b]))
# vendedores que sairam? ultimo engage por vendedor
ag = d.groupby("sales_agent").agg(first=("engage_date", "min"), last=("engage_date", "max"), lastclose=("close_date", "max"), n=("zombie", "size"), z=("zombie", "sum"))
print(ag.sort_values("z").to_string())
# par vendedor x conta: zumbis com conta tem par ja visto entre fechados?
cl = d[d.closed]; pairs = cl.groupby(["sales_agent", "account"]).size()
print("pares distintos vendedor x conta entre fechados:", len(pairs), "de", cl.sales_agent.nunique() * cl.account.nunique())
print("contas por vendedor (fechados):", cl.groupby("sales_agent").account.nunique().describe().round(1).to_dict())
op = d[(d.deal_stage == "Engaging") & d.account.notna()]
seen = [(a, c) in pairs.index for a, c in zip(op.sales_agent, op.account)]
print("Engaging abertos com conta: par ja visto entre fechados:", np.mean(seen).round(3), len(op))
pr = d[(d.deal_stage == "Prospecting") & d.account.notna()]
print("Prospecting com conta: par ja visto:", np.mean([(a, c) in pairs.index for a, c in zip(pr.sales_agent, pr.account)]).round(3), len(pr))
# para fechados: leave-one-out, par aparece em outro deal fechado?
print("fechados: par aparece em outro fechado:", (cl.groupby(["sales_agent", "account"]).opportunity_id.transform("size") > 1).mean().round(3))
# distribuicao de contas: abertos x fechados
t = pd.DataFrame({"fechados": cl.account.value_counts(normalize=True), "abertos": op.account.value_counts(normalize=True)}).fillna(0)
print(t.sort_values("fechados", ascending=False).head(12).round(4)); print(stats.spearmanr(t.fechados, t.abertos))
print(pd.crosstab(d.deal_stage, d["product"], normalize="index").round(3))
