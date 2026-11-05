"""Is the month-of-quarter signal too coarse at the very start of a quarter?

A rep opens the tool on January 1st, and that 30-day window stays inside month 1.
Usage: python quarter_start_check.py <data_dir> <scoring_dir>
"""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, sys.argv[2])
import lead_scorer as ls  # noqa: E402

pd.set_option("display.width", 200)
deals = ls.load_deals(sys.argv[1])


def snapshot_with_outcome(monday):
    snap = ls.open_deals_at(deals, monday)
    end = monday + pd.Timedelta(days=30)
    won = (snap["deal_stage"] == "Won") & (snap["close_date"] >= monday) & (snap["close_date"] < end)
    snap["won"] = won.astype(int)
    snap["realized"] = np.where(won, snap["close_value"], 0.0)
    return snap


print("== Win within 30 days, by age band and Monday")
bands = [0, 14, 44, 89, 119, 138, 1000]
for monday in pd.date_range("2017-03-06", "2017-11-27", freq="W-MON"):
    if monday.month % 3 != 1:
        continue
    snap = snapshot_with_outcome(monday)
    rate = snap.groupby(pd.cut(snap["age"], bands), observed=True)["won"].mean().round(3)
    print(monday.date(), "window ends", (monday + pd.Timedelta(days=30)).date(), rate.to_dict())


def half_month(date):
    """1 to 6: half of each month inside the quarter."""
    return (date.month - 1) % 3 * 2 + (1 if date.day <= 15 else 2)


def learn(as_of, key):
    """Age x key rates, learned only from windows already finished at as_of."""
    max_cycle = ls.known_max_cycle(deals, as_of)
    rows = []
    for monday in pd.date_range(ls.FIRST_RELIABLE_DATE, as_of - pd.Timedelta(days=30), freq="W-MON"):
        snap = snapshot_with_outcome(monday)
        rows.append(pd.DataFrame({"age": snap["age"].to_numpy(), "key": key(monday), "won": snap["won"].to_numpy()}))
    obs = pd.concat(rows)
    obs = obs[obs["age"] <= max_cycle]
    obs["bin"] = ls.age_bin(obs["age"])
    overall = obs["won"].mean()
    by_age = obs.groupby("bin")["won"].agg(["sum", "size"])
    by_age = (by_age["sum"] + ls.SMOOTHING * overall) / (by_age["size"] + ls.SMOOTHING)
    cells = obs.groupby(["bin", "key"])["won"].agg(["sum", "size"]).reset_index()
    table = {
        (r.bin, r.key): (r.sum + ls.SMOOTHING * by_age[r.bin]) / (r.size + ls.SMOOTHING)
        for r in cells.rename(columns={"sum": "sum", "size": "size"}).itertuples()
    }
    return table, by_age.to_dict(), max_cycle


month_key = lambda d: (d.month - 1) % 3 + 1  # noqa: E731
rows = []
for monday in pd.date_range("2017-07-03", "2017-11-27", freq="W-MON"):
    snap = snapshot_with_outcome(monday)
    for name, key in [("mes_do_trimestre", month_key), ("quinzena_do_trimestre", half_month)]:
        table, by_age, max_cycle = learn(monday, key)
        k = key(monday)
        p = [0.0 if a > max_cycle else table.get((a // 15 * 15, k), by_age.get(a // 15 * 15, 0.0)) for a in snap["age"]]
        rank = ls.ranking_value(np.array(p), snap["sales_price"])
        top = snap.assign(_r=rank).sort_values("_r", ascending=False).groupby("sales_agent").head(10)
        rows.append({"monday": monday, "variant": name, "revenue": top["realized"].sum(), "wins": top["won"].sum(), "listed": len(top), "first_half_m1": k == 1 or (name == "mes_do_trimestre" and monday.month % 3 == 1 and monday.day <= 15)})

r = pd.DataFrame(rows)
r["period"] = np.where(r["monday"] < "2017-10-01", "jul_set", "out_nov")
print("\n== Replay of the two variants")
print(r.groupby(["period", "variant"])[["revenue", "wins"]].mean().round(0).to_string())
wide = r.pivot(index="monday", columns="variant", values="revenue")
diff = wide["quinzena_do_trimestre"] - wide["mes_do_trimestre"]
print("quinzena better on", (diff > 0).sum(), "of", len(diff), "mean diff", round(diff.mean()))
print(diff.round(0).to_string())

print("\n== What each variant says for January 1st")
for name, key in [("mes_do_trimestre", month_key), ("quinzena_do_trimestre", half_month)]:
    table, by_age, _ = learn(ls.AS_OF, key)
    print(name, {b: round(table.get((b, key(ls.AS_OF)), by_age[b]), 3) for b in sorted(by_age)})
