"""Replay past Mondays and measure each prioritization strategy.

Every Monday from July to November 2017, each rep's top 10 is built using only
what was known that day, then checked against wins in the following 30 days.

Usage: python backtest.py [--data DIR] [--out FILE]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import lead_scorer as ls

HERE = Path(__file__).resolve().parent
FIRST_MONDAY = "2017-07-03"
LAST_MONDAY = "2017-11-27"
HOLDOUT_START = pd.Timestamp("2017-10-01")
RANDOM_DRAWS = 20


def top_k_outcome(snapshot: pd.DataFrame, score: np.ndarray, max_cycle: int) -> dict:
    top = snapshot.assign(_score=score).sort_values("_score", ascending=False).groupby("sales_agent").head(ls.TOP_K)
    return {
        "revenue": float(top["realized"].sum()),
        "wins": int(top["won_window"].sum()),
        "listed": len(top),
        "stale": int((top["age"] > max_cycle).sum()),
    }


def replay(deals: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    calibration = []
    rng = np.random.default_rng(0)
    for monday in pd.date_range(FIRST_MONDAY, LAST_MONDAY, freq="W-MON"):
        rates = ls.learn_rates(deals, monday, use_quarter=True)
        week = ls.quarter_week(monday)
        snapshot = ls.open_deals_at(deals, monday)
        window_end = monday + pd.Timedelta(days=ls.HORIZON_DAYS)
        won = (snapshot["deal_stage"] == "Won") & (snapshot["close_date"] >= monday) & (snapshot["close_date"] < window_end)
        snapshot["realized"] = np.where(won, snapshot["close_value"], 0.0)
        snapshot["won_window"] = won.astype(int)
        snapshot["probability"] = [rates.probability(age, week) for age in snapshot["age"]]

        strategies = {
            "score": ls.ranking_value(snapshot["probability"], snapshot["sales_price"]),
            "maior_valor": snapshot["sales_price"].to_numpy(),
            "mais_novo": -snapshot["age"].to_numpy(),
            "mais_antigo": snapshot["age"].to_numpy(),
        }
        for name, score in strategies.items():
            rows.append({"monday": monday, "strategy": name, **top_k_outcome(snapshot, score, rates.max_cycle)})

        draws = [top_k_outcome(snapshot, rng.random(len(snapshot)), rates.max_cycle) for _ in range(RANDOM_DRAWS)]
        rows.append({"monday": monday, "strategy": "aleatorio", **pd.DataFrame(draws).mean().to_dict()})
        calibration.append(snapshot[["probability", "won_window"]].assign(monday=monday))
    return pd.DataFrame(rows), pd.concat(calibration, ignore_index=True)


def summarize(results: pd.DataFrame, calibration: pd.DataFrame) -> dict:
    def table(frame: pd.DataFrame) -> dict:
        grouped = frame.groupby("strategy")[["revenue", "wins", "listed", "stale"]].mean()
        grouped["win_rate"] = grouped["wins"] / grouped["listed"]
        return grouped.round(4).to_dict("index")

    wide = results.pivot(index="monday", columns="strategy", values="revenue")
    diff = wide["score"] - wide["maior_valor"]
    # Consecutive Mondays share most of their 30-day window, so a stricter check
    # keeps only Mondays whose windows do not overlap.
    independent = diff.iloc[::5]

    live = calibration[calibration["probability"] > 0].copy()
    live["band"] = pd.cut(live["probability"], [0, 0.05, 0.1, 0.2, 0.3, 1], labels=["até 5%", "5–10%", "10–20%", "20–30%", "acima de 30%"])
    bands = live.groupby("band", observed=True).agg(deals=("won_window", "size"), previsto=("probability", "mean"), real=("won_window", "mean"))

    return {
        "mondays": int(results["monday"].nunique()),
        "top_k": ls.TOP_K,
        "horizon_days": ls.HORIZON_DAYS,
        "all": table(results),
        "selection_jul_sep": table(results[results["monday"] < HOLDOUT_START]),
        "holdout_oct_nov": table(results[results["monday"] >= HOLDOUT_START]),
        "score_vs_value": {
            "mean_gain": round(float(diff.mean())),
            "better_mondays": int((diff > 0).sum()),
            "independent_mondays": len(independent),
            "independent_better": int((independent > 0).sum()),
            "independent_mean_gain": round(float(independent.mean())),
        },
        "calibration": bands.round(4).reset_index().to_dict("records"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=HERE.parent / "data", type=Path)
    parser.add_argument("--out", default=HERE / "backtest_results.json", type=Path)
    args = parser.parse_args()

    results, calibration = replay(ls.load_deals(args.data))
    summary = summarize(results, calibration)
    args.out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
