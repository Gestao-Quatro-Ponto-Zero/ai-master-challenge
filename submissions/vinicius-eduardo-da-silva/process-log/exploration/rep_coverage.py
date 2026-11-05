"""Why do only 17 reps have live deals? Usage: python rep_coverage.py <data_dir> <scoring_dir>"""
import sys

import pandas as pd

sys.path.insert(0, sys.argv[2])
import lead_scorer as ls  # noqa: E402

pd.set_option("display.width", 200)
pd.set_option("display.max_rows", 50)
deals = ls.load_deals(sys.argv[1])
scored, _ = ls.score_pipeline(deals)

rep = deals.groupby("sales_agent").agg(
    manager=("manager", "first"),
    region=("regional_office", "first"),
    last_engage=("engage_date", "max"),
    last_close=("close_date", "max"),
    closed_q4=("close_date", lambda s: (s >= "2017-10-01").sum()),
    prospecting=("deal_stage", lambda s: (s == "Prospecting").sum()),
)
rep["foco"] = scored[scored["queue"] == "foco"].groupby("sales_agent").size()
rep["decidir"] = scored[scored["queue"] == "decidir"].groupby("sales_agent").size()
rep = rep.fillna({"foco": 0, "decidir": 0}).astype({"foco": int, "decidir": int})
print(rep.sort_values(["foco", "decidir"]).to_string())

print("\nBy manager")
print(rep.groupby(["region", "manager"])[["foco", "decidir", "prospecting", "closed_q4"]].sum().to_string())

print("\nEngaged per month by manager")
print(deals.pivot_table(index=deals["engage_date"].dt.to_period("M"), columns="manager", values="opportunity_id", aggfunc="count").fillna(0).astype(int).to_string())

print("\nReps with no live deal: last engagement date")
print(rep[rep["foco"] == 0][["manager", "last_engage", "closed_q4", "decidir", "prospecting"]].to_string())

print("\nOpen Engaging share still missing account, by age band")
open_deals = scored.assign(no_account=scored["account"].isna())
print(open_deals.groupby("zone")["no_account"].agg(["mean", "size"]).round(3).to_string())
