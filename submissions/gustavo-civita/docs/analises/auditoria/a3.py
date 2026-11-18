import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3] / "solution"))
import numpy as np, pandas as pd
import scoring, backtest
from scipy.stats import rankdata
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
d = scoring.load_pipeline()
today = scoring.reference_date(d)

def auc(score, y):
    y = np.asarray(y, bool); r = rankdata(score)
    n1, n0 = y.sum(), (~y).sum()
    return (r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0) if n1 and n0 else np.nan

def cap(snap, col, n=10):
    return snap.sort_values(col, ascending=False).groupby("sales_agent").head(n).revenue_after.sum()

rows = []
for as_of in pd.date_range("2017-07-01", "2017-12-09", freq="7D"):
    s = backtest.snapshot_with_predictions(d, as_of)
    s["j90"] = np.where(s.age <= 90, s.sales_price, 0) - s.age * 1e-6
    s["j60"] = np.where(s.age <= 60, s.sales_price, 0) - s.age * 1e-6
    s["acc_price"] = np.where(s.account.notna(), s.sales_price, 0)
    rows.append(dict(data=as_of.date(), q=as_of.quarter, score=cap(s, "valor_esperado"), preco=cap(s, "sales_price"), j90=cap(s, "j90"), j60=cap(s, "j60"),
                     acc_price=cap(s, "acc_price"),
                     auc_chance=auc(s.chance, s.won_after), auc_negage=auc(-s.age, s.won_after), auc_acc=auc(s.account.notna().astype(int), s.won_after)))
r = pd.DataFrame(rows)
print(r.round(3).to_string(index=False))
for q, g in r.groupby("q"):
    print("Q", q, "n", len(g), {c: int(g[c].sum()) for c in ["score", "preco", "j90", "j60", "acc_price"]},
          "score wins vs j90:", int((g.score > g.j90).sum()), "vs j60:", int((g.score > g.j60).sum()),
          "AUC chance", g.auc_chance.mean().round(3), "AUC -age", g.auc_negage.mean().round(3), "AUC account", g.auc_acc.mean().round(3))

sc, model = scoring.score_open_deals(d, today)
foco = sc[sc.lista == "foco"]
print("\nfoco today without account:", foco.account.isna().sum(), "of", len(foco))
print("reativar without account:", sc[sc.lista == "reativar"].account.isna().mean().round(3), "abordar without:", sc[sc.lista == "abordar"].account.isna().mean().round(3))
print("top-5 foco per seller without account share:", foco.sort_values("valor_esperado", ascending=False).groupby("sales_agent").head(5).account.isna().mean().round(3))
print("agents in sales_teams:", pd.read_csv(scoring.DATA_DIR / "sales_teams.csv").sales_agent.nunique(), "with open deals:", sc.sales_agent.nunique())
print("per-seller open counts by lista (describe):"); print(pd.crosstab(sc.sales_agent, sc.lista).describe().round(1))
print("today's chance curve at ages 30,45,60,65,75,90:", [round(model["chance_by_age"][a], 3) for a in (30, 45, 60, 65, 75, 90)])
# what did the 2017-09-30 quarter-end actually yield per age (the single most comparable realized point)
s = backtest.snapshot_with_predictions(d, pd.Timestamp("2017-09-30"))
for a in (30, 45, 60, 65, 75, 90):
    m = (s.age - a).abs() <= 7
    print("  09-30 actual won within +-7d of age", a, ":", round(s[m].won_after.mean(), 3), "n", int(m.sum()), "| predicted then", round(s[m].chance.mean(), 3))
# sample size behind today's curve
ages = []
for qb in (1, 2, 3):
    ad = today - pd.DateOffset(months=3 * qb); snap = scoring.open_at(d, ad); print("analog", ad.date(), "open", len(snap), "won by today", int(((snap.deal_stage == "Won")).sum()))
# 3 analogs individually at age 65
for qb in (1, 2, 3):
    ad = today - pd.DateOffset(months=3 * qb); snap = scoring.open_at(d, ad)
    for a in (0, 30, 65):
        m = (snap.age - a).abs() <= 7
        print("   analog", ad.date(), "age", a, "n", int(m.sum()), "won rate", round((snap[m].deal_stage == "Won").mean(), 3))
