"""Decide with evidence which signals enter the score.

Replays past Mondays and compares scoring variants. Variants are compared on
Jul-Sep (selection) and then checked on Oct-Nov (holdout).

Usage: python variant_test.py <data_dir> <scoring_dir>
"""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, sys.argv[2])
import lead_scorer as ls  # noqa: E402

pd.set_option("display.width", 200)
deals = ls.load_deals(sys.argv[1])
mondays = pd.date_range("2017-07-03", "2017-11-27", freq="W-MON")
TOP_K = 10
rows = []


def shrunk_rates(closed, key, base):
    grouped = closed.groupby(key)["is_won"].agg(["sum", "size"])
    return ((grouped["sum"] + 20 * base) / (grouped["size"] + 20)).to_dict()


for monday in mondays:
    known = deals[deals["engage_date"] < monday]
    closed = known[known["close_date"] < monday].assign(is_won=lambda d: (d["deal_stage"] == "Won").astype(int))
    base = closed["is_won"].mean()
    age_rates = ls.learn_rates(deals, monday, use_quarter=False)
    quarter_rates = ls.learn_rates(deals, monday, use_quarter=True)
    position = ls.quarter_position(pd.DatetimeIndex([monday]))[0]

    snapshot = ls.open_deals_at(deals, monday)
    window_end = monday + pd.Timedelta(days=ls.HORIZON_DAYS)
    won = (snapshot["deal_stage"] == "Won") & (snapshot["close_date"] >= monday) & (snapshot["close_date"] < window_end)
    snapshot["realized"] = np.where(won, snapshot["close_value"], 0.0)
    snapshot["won_window"] = won.astype(int)

    p_age = snapshot["age"].map(lambda a: age_rates.probability(a, position))
    p_quarter = snapshot["age"].map(lambda a: quarter_rates.probability(a, position))
    agent = shrunk_rates(closed, "sales_agent", base)
    product = shrunk_rates(closed, "product", base)
    agent_lift = snapshot["sales_agent"].map(lambda v: agent.get(v, base) / base)
    product_lift = snapshot["product"].map(lambda v: product.get(v, base) / base)
    price = snapshot["sales_price"]

    variants = {
        "1_maior_valor": price,
        "2_valor_x_idade": p_age * price,
        "3_valor_x_idade_x_trimestre": p_quarter * price,
        "4_idade_+_vendedor": p_age * agent_lift * price,
        "5_idade_+_produto": p_age * product_lift * price,
    }
    for name, score in variants.items():
        top = snapshot.assign(_s=score).sort_values("_s", ascending=False).groupby("sales_agent").head(TOP_K)
        rows.append(
            {
                "monday": monday,
                "variant": name,
                "revenue": top["realized"].sum(),
                "wins": top["won_window"].sum(),
                "listed": len(top),
                "position": position,
                "period": "selecao_jul_set" if monday < pd.Timestamp("2017-10-01") else "holdout_out_nov",
            }
        )

r = pd.DataFrame(rows)
table = r.groupby(["period", "variant"]).agg(revenue=("revenue", "mean"), wins=("wins", "mean"), listed=("listed", "mean"), mondays=("monday", "nunique"))
table["win_rate_30d"] = table["wins"] / table["listed"]
print(table.round(3).to_string())
print("\nBy month of quarter")
print(r.pivot_table(index="position", columns="variant", values="revenue", aggfunc="mean").round(0).to_string())

wide = r.pivot(index="monday", columns="variant", values="revenue")
for name in wide.columns:
    if name != "2_valor_x_idade":
        diff = wide[name] - wide["2_valor_x_idade"]
        print(f"{name} vs 2_valor_x_idade: mean diff {diff.mean():,.0f}; better on {(diff > 0).sum()}/{len(diff)} Mondays")

print("\nRates learned at the dataset snapshot")
rates = ls.learn_rates(deals, ls.AS_OF, use_quarter=True)
grid = pd.DataFrame(
    {b: {pos: rates.by_age_position.get((b, pos)) for pos in (1, 2, 3)} for b in sorted(rates.by_age)}
).T
grid["todas"] = pd.Series(rates.by_age)
print(grid.round(3).to_string())
print("overall", round(rates.overall, 3), "max cycle", rates.max_cycle)
