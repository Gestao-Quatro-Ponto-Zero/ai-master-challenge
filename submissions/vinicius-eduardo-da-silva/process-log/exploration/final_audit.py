"""Try to break the main result before submitting.

Questions: is the gain only from removing stale deals? Does it depend on a few
huge deals? Does it hold per rep and for other list sizes?

Usage: python final_audit.py <data_dir> <scoring_dir>
"""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, sys.argv[2])
import backtest as bt  # noqa: E402
import lead_scorer as ls  # noqa: E402

pd.set_option("display.width", 200)
deals = ls.load_deals(sys.argv[1])
mondays = pd.date_range(bt.FIRST_MONDAY, bt.LAST_MONDAY, freq="W-MON")
rows, rep_rows = [], []

for monday in mondays:
    snapshot, rates = bt.monday_snapshot(deals, monday)
    live = snapshot[snapshot["age"] <= rates.max_cycle]
    score_all = ls.ranking_value(snapshot["probability"], snapshot["sales_price"])
    score_live = ls.ranking_value(live["probability"], live["sales_price"])
    # Strongest simple rival: a rep who already ignores stale deals and sorts by value.
    lists = {
        "score": (snapshot, score_all),
        "maior_valor": (snapshot, snapshot["sales_price"].to_numpy()),
        "maior_valor_sem_parados": (live, live["sales_price"].to_numpy()),
        "so_momento": (live, live["probability"].to_numpy()),
    }
    for name, (pool, score) in lists.items():
        ranked = pool.assign(_s=score).sort_values(["_s", "opportunity_id"], ascending=[False, True])
        for k in (5, 10, 20):
            top = ranked.groupby("sales_agent").head(k)
            no_big = top[top["product"] != "GTK 500"]
            rows.append(
                {
                    "monday": monday,
                    "strategy": name,
                    "k": k,
                    "revenue": top["realized"].sum(),
                    "revenue_sem_gtk": no_big["realized"].sum(),
                    "wins": top["won_window"].sum(),
                    "listed": len(top),
                }
            )
            if k == 10:
                totals = top.groupby("sales_agent")["realized"].sum()
                rep_rows.extend({"monday": monday, "strategy": name, "agent": a, "revenue": v} for a, v in totals.items())

r = pd.DataFrame(rows)
table = r.groupby(["k", "strategy"])[["revenue", "revenue_sem_gtk", "wins", "listed"]].mean()
table["win_rate"] = table["wins"] / table["listed"]
print(table.round(3).to_string())

ten = r[r["k"] == 10].pivot(index="monday", columns="strategy", values="revenue")
for rival in ("maior_valor", "maior_valor_sem_parados"):
    diff = ten["score"] - ten[rival]
    print(f"\nscore vs {rival}: {ten['score'].mean() / ten[rival].mean() - 1:+.1%}; better on {(diff > 0).sum()}/{len(diff)} Mondays")
    print("  every 5th Monday:", (diff.iloc[::5] > 0).sum(), "of", len(diff.iloc[::5]), "| mean", round(diff.iloc[::5].mean()))
    period = ten.index < bt.HOLDOUT_START
    print(f"  Jul-Sep {ten.loc[period, 'score'].mean() / ten.loc[period, rival].mean() - 1:+.1%} | Oct-Nov {ten.loc[~period, 'score'].mean() / ten.loc[~period, rival].mean() - 1:+.1%}")

no_gtk = r[r["k"] == 10].pivot(index="monday", columns="strategy", values="revenue_sem_gtk")
print(f"\nWithout GTK 500 revenue: score vs maior_valor_sem_parados {no_gtk['score'].mean() / no_gtk['maior_valor_sem_parados'].mean() - 1:+.1%}")

reps = pd.DataFrame(rep_rows).groupby(["agent", "strategy"])["revenue"].sum().unstack()
for rival in ("maior_valor", "maior_valor_sem_parados"):
    print(f"Reps where score beat {rival}: {(reps['score'] > reps[rival]).sum()} of {len(reps)}")

gtk = deals[deals["product"] == "GTK 500"]
print("\nGTK 500 won revenue share:", round(gtk["close_value"].sum() / deals["close_value"].sum(), 3))

# Fixed value list for one rep, to see how much each list differs.
overlap = []
for monday in mondays:
    snapshot, rates = bt.monday_snapshot(deals, monday)
    live = snapshot[snapshot["age"] <= rates.max_cycle]
    a = bt.top_k(live, ls.ranking_value(live["probability"], live["sales_price"]))
    b = bt.top_k(live, live["sales_price"].to_numpy())
    overlap.append(len(set(a["opportunity_id"]) & set(b["opportunity_id"])) / max(1, len(a)))
print("Overlap between score list and live value list:", round(float(np.mean(overlap)), 3))
