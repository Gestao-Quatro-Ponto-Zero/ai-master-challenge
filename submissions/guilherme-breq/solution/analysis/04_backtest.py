"""
Backtest temporal do scoring (sem vazamento de futuro).

Para cada data de snapshot S:
  - "treino"  = deals que já tinham FECHADO antes de S (é o que o vendedor saberia naquele dia)
  - "teste"   = deals que estavam ABERTOS em S (engage < S <= close) e fecharam depois
  - cada deal de teste é pontuado com a idade que tinha EM S, não com a duração final

Compara variantes de p(win) por AUC e Brier, e mede o valor capturado no topo do ranking.
Uso:  python 04_backtest.py
"""
import numpy as np
import pandas as pd

D = "../data/"
p = pd.read_csv(D + "sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
a = pd.read_csv(D + "accounts.csv")
pr = pd.read_csv(D + "products.csv")
p["product"] = p["product"].replace("GTXPro", "GTX Pro")
p = p.merge(a[["account", "sector"]], on="account", how="left").merge(pr, on="product", how="left")
closed = p[p.deal_stage.isin(["Won", "Lost"])].copy()
closed["won"] = (closed.deal_stage == "Won").astype(int)
closed["days"] = (closed.close_date - closed.engage_date).dt.days

K = 50  # força do shrinkage bayesiano (pseudo-contagem)


def auc(y, s):
    r = pd.Series(s).rank().values
    n1 = y.sum(); n0 = len(y) - n1
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def survival_curve(train):
    """p(win | deal ainda aberto com idade a) = win rate dos fechados com duração > a."""
    ages = np.arange(0, train.days.max() + 1)
    rates = np.array([train.loc[train.days > x, "won"].mean() if (train.days > x).sum() >= 30 else np.nan for x in ages])
    return pd.Series(rates, index=ages).ffill()


def shrunk_ratio(train, col, glob):
    g = train.groupby(col).won.agg(["sum", "count"])
    return ((g["sum"] + K * glob) / (g["count"] + K)) / glob


rows, lift = [], []
for S in pd.to_datetime(["2017-05-01", "2017-06-01", "2017-07-01", "2017-08-01", "2017-09-01"]):
    train = closed[closed.close_date < S]
    test = closed[(closed.engage_date < S) & (closed.close_date >= S)].copy()
    test["age"] = (S - test.engage_date).dt.days
    test = test[test.age <= train.days.max()]  # zumbis ficam de fora do ranking, como no app
    glob = train.won.mean()
    curve = survival_curve(train)
    test["p_age"] = test.age.clip(upper=curve.index.max()).map(curve).fillna(glob)
    ag = shrunk_ratio(train, "sales_agent", glob)
    prod = shrunk_ratio(train, "product", glob)
    sec = shrunk_ratio(train, "sector", glob)
    test["p_agent"] = test.p_age * test.sales_agent.map(ag).fillna(1)
    test["p_prod"] = test.p_agent * test["product"].map(prod).fillna(1)
    test["p_sector"] = test.p_agent * test.sector.map(sec).fillna(1)
    y = test.won.values
    r = {"snapshot": S.date(), "n_teste": len(test), "win_rate": round(y.mean(), 3)}
    for m in ["p_age", "p_agent", "p_prod", "p_sector"]:
        r["AUC_" + m] = round(auc(y, test[m].values), 3)
        r["Brier_" + m] = round(((test[m] - y) ** 2).mean(), 4)
    r["Brier_global"] = round(((glob - y) ** 2).mean(), 4)
    rows.append(r)

    # Valor capturado: dos deals no top 20% do ranking, quanto da receita ganha eles trouxeram?
    test["ev"] = test.p_agent * test.sales_price
    won_rev = (test.close_value * test.won).sum()
    top = int(len(test) * 0.2)
    for name, key in [("só valor", "sales_price"), ("valor esperado", "ev"), ("só chance", "p_agent")]:
        sel = test.sort_values(key, ascending=False).head(top)
        lift.append({"snapshot": S.date(), "ranking": name,
                     "receita_ganha_no_top20%": round((sel.close_value * sel.won).sum() / won_rev, 3),
                     "win_rate_no_top20%": round(sel.won.mean(), 3)})

pd.set_option("display.width", 250)
res = pd.DataFrame(rows)
print(res.to_string(index=False))
print("\nMédia:\n", res.drop(columns=["snapshot"]).mean().round(4).to_string())
lf = pd.DataFrame(lift)
print("\n", lf.groupby("ranking")[["receita_ganha_no_top20%", "win_rate_no_top20%"]].mean().round(3))
