"""Confere dois pontos da auditoria: baseline justo e calibração por idade."""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3] / "solution"))
import scoring  # noqa: E402

pd.set_option("display.width", 220)
deals = scoring.load_pipeline()
REF = scoring.reference_date(deals)
TOP = 10


def snapshot(as_of):
    curve = scoring.win_chance_by_age(deals, as_of)
    snap = scoring.open_at(deals, as_of)
    snap["chance"] = [scoring.chance_for(curve, a) for a in snap["age"]]
    snap["ev"] = snap["chance"] * snap["sales_price"]
    snap["won"] = snap["deal_stage"] == "Won"
    snap["rev"] = snap["close_value"].fillna(0)
    # regras simples, sem modelo
    snap["preco"] = snap["sales_price"]
    snap["preco_ate_90d"] = snap["sales_price"].where(snap["age"] <= 90, 0)
    snap["preco_ate_60d"] = snap["sales_price"].where(snap["age"] <= 60, 0)
    snap["mais_novo"] = -snap["age"]
    return snap


def captured(snap, key):
    top = snap.sort_values([key, "sales_price"], ascending=False).groupby("sales_agent").head(TOP)
    return top["rev"].sum()


rows = []
for as_of in pd.date_range("2017-06-03", "2017-12-09", freq="7D"):
    snap = snapshot(as_of)
    row = {"data": as_of.date(), "tri": f"T{as_of.quarter}"}
    for key in ["ev", "preco", "preco_ate_90d", "preco_ate_60d", "mais_novo"]:
        row[key] = captured(snap, key)
    rows.append(row)
table = pd.DataFrame(rows)
keys = ["ev", "preco", "preco_ate_90d", "preco_ate_60d", "mais_novo"]
print("Receita capturada (top 10 por vendedor), soma por trimestre, em $ mil:")
print((table.groupby("tri")[keys].sum() / 1000).round(0).to_string())
print("\nSemanas em que a ferramenta (ev) ganha de cada regra:")
for key in keys[1:]:
    wins = (table["ev"] > table[key]).groupby(table["tri"]).agg(["sum", "size"])
    print(f"  {key:15s}", {tri: f"{int(r['sum'])}/{int(r['size'])}" for tri, r in wins.iterrows()})

print("\nCalibração por faixa de idade (previsto x real), datas de fim/meio de trimestre:")
for date in ["2017-06-30", "2017-08-15", "2017-09-30"]:
    snap = snapshot(pd.Timestamp(date))
    live = snap[snap["chance"] >= scoring.MIN_CHANCE]
    bands = pd.cut(live["age"], [-1, 15, 30, 45, 60, 75, 92])
    print(date)
    print(live.groupby(bands, observed=True).agg(n=("won", "size"), previsto=("chance", "mean"), real=("won", "mean")).round(3).to_string())

# A borda da base: quanto de cada trimestre ainda estava aberto no fim dele
print("\nDeals iniciados no trimestre que seguiam abertos no último dia do trimestre:")
for end in ["2017-06-30", "2017-09-30", "2017-12-31"]:
    end = pd.Timestamp(end)
    start = end - pd.offsets.QuarterBegin(startingMonth=1) if end.month != 12 else pd.Timestamp("2017-10-01")
    start = pd.Timestamp(year=end.year, month=end.month - 2, day=1)
    cohort = deals[(deals["engage_date"] >= start) & (deals["engage_date"] <= end)]
    still = cohort["close_date"].isna() | (cohort["close_date"] > end)
    print(f"  {end.date()}: iniciados {len(cohort)}, abertos {int(still.sum())} ({still.mean():.0%})")
