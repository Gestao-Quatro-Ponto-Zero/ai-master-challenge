import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3] / "solution"))
import numpy as np, pandas as pd
import scoring, backtest
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 200)
d = scoring.load_pipeline()
today = scoring.reference_date(d)

print("== account missing by stage"); print(pd.crosstab(d.deal_stage, d.account.isna()))
eng = d[d.engage_date.notna()].copy()
eng["zombie"] = eng.deal_stage == "Engaging"
print("zombie share by region", eng.groupby("regional_office").zombie.mean().round(3).to_dict())
print("zombie share by product", eng.groupby("product").zombie.mean().round(3).to_dict())
za = eng.groupby("sales_agent").zombie.agg(["size", "mean"]); print("zombie share by agent min/max", za["mean"].min().round(3), za["mean"].max().round(3))
from scipy.stats import chi2_contingency
for col in ["sales_agent", "product", "regional_office", "manager"]:
    print(col, "chi2 p (zombie vs closed):", chi2_contingency(pd.crosstab(eng[col], eng.zombie))[1])
    eng["wonflag"] = eng.deal_stage == "Won"
    print(col, "chi2 p (won among ALL engaged):", chi2_contingency(pd.crosstab(eng[col], eng.wonflag))[1])
wa = eng.groupby("sales_agent").wonflag.agg(["size", "mean"]); print("won/all-engaged by agent min/max:", wa["mean"].min().round(3), wa["mean"].max().round(3))
print(eng.groupby("regional_office").wonflag.mean().round(3).to_dict())

# ---- full date sweep
dates = pd.date_range("2017-04-15", "2017-12-15", freq="7D")
rows = []; cal = []
for as_of in dates:
    snap = backtest.snapshot_with_predictions(d, as_of)
    snap["as_of"] = as_of
    parked = snap[snap.chance < scoring.MIN_CHANCE]
    def cap(col):
        return snap.sort_values(col, ascending=False).groupby("sales_agent").head(10).revenue_after.sum()
    # naive baselines
    closed_hist = d[(d.close_date <= as_of)]
    cyc = (closed_hist.close_date - closed_hist.engage_date).dt.days
    maxc = cyc.max() if len(cyc) else 138
    snap["naive_alive_price"] = np.where(snap.age <= 138, snap.sales_price, 0) - snap.age * 1e-6
    snap["young_price"] = np.where(snap.age <= 90, snap.sales_price, 0) - snap.age * 1e-6
    # global age curve (no quarter analog), using only info at as_of: deals engaged >=138d before as_of... simple: all snapshots weekly before as_of-138d
    snap["neg_age"] = -snap.age
    oracle = snap.sort_values("revenue_after", ascending=False).groupby("sales_agent").head(10).revenue_after.sum()
    rows.append(dict(data=as_of.date(), abertos=len(snap), score=cap("valor_esperado"), preco=cap("sales_price"),
                     vivo_preco=cap("naive_alive_price"), jovem90_preco=cap("young_price"), mais_novo=cap("neg_age"), oraculo=oracle,
                     parados=len(parked), par_fech=int((parked.won_after | parked.lost_after).sum()), par_won=int(parked.won_after.sum()),
                     par_idade_min=parked.age.min() if len(parked) else None,
                     naoparados_zero_real=int(((snap.chance >= 0.01) & ~snap.won_after).sum())))
    cal.append(snap)
r = pd.DataFrame(rows)
print(r.to_string(index=False))
print("\nTotals: score", r.score.sum(), "preco", r.preco.sum(), "vivo_preco", r.vivo_preco.sum(), "jovem90", r.jovem90_preco.sum(), "mais_novo", r.mais_novo.sum(), "oraculo", r.oraculo.sum())
print("dates where score < vivo_preco:", (r.score < r.vivo_preco).sum(), "of", len(r), "; score<jovem90:", (r.score < r.jovem90_preco).sum(), "; score<preco:", (r.score < r.preco).sum())
print("parked that closed on any date:", r.par_fech.sum(), "won:", r.par_won.sum())

allc = pd.concat(cal)
allc["band"] = pd.cut(allc.chance, [-0.001, 0.0099, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 1])
print("\n== calibration all weekly dates")
print(allc.groupby("band", observed=True).agg(n=("chance", "size"), prev=("chance", "mean"), real=("won_after", "mean")).round(3))
print("\n== calibration per snapshot (official 5): overall predicted vs real for chance>=1%")
for s in backtest.SNAPSHOTS:
    snap = backtest.snapshot_with_predictions(d, pd.Timestamp(s))
    a = snap[snap.chance >= 0.01]
    n_analog = sum((pd.Timestamp(s) - pd.DateOffset(months=3 * q)) >= d.close_date.min() for q in (1, 2, 3))
    print(s, "analogs:", n_analog, "n", len(a), "prev", round(a.chance.mean(), 3), "real", round(a.won_after.mean(), 3),
          "| expected wins", round(a.chance.sum()), "actual", int(a.won_after.sum()))
# What does the 2017-09-30 snapshot (closest regime to today, quarter end) look like by age band
snap = backtest.snapshot_with_predictions(d, pd.Timestamp("2017-09-30"))
snap["ab"] = pd.cut(snap.age, [-1, 7, 15, 30, 45, 60, 75, 90, 97, 138, 1000])
snap["closed_after"] = snap.won_after | snap.lost_after  # a coluna saiu do backtest.py; recriada aqui
print(snap.groupby("ab", observed=True).agg(n=("age", "size"), prev=("chance", "mean"), won=("won_after", "mean"), closed=("closed_after", "mean")).round(3))
# missing-account as predictor within the snapshot
snap["noacc"] = snap.account.isna()
print("09-30 snapshot: won_after by account missing:", snap.groupby("noacc").won_after.agg(["size", "mean"]).round(3).to_dict())
print("09-30 snapshot by region:", snap.groupby("regional_office").agg(n=("age", "size"), prev=("chance", "mean"), won=("won_after", "mean")).round(3).to_dict("index"))
