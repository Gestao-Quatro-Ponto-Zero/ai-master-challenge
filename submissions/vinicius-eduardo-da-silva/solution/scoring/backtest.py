"""Replay past Mondays and measure each prioritization strategy.

Every Monday from July to November 2017, each rep's top 10 is built using only
what was known that day, then checked against wins in the following 30 days.
Also writes the data behind the app's time machine.

Usage: python backtest.py [--data DIR] [--out FILE] [--replay-out FILE]
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


def monday_snapshot(deals: pd.DataFrame, monday: pd.Timestamp) -> tuple[pd.DataFrame, ls.TimingRates]:
    """Open deals on a Monday, their score inputs, and what happened in 30 days."""
    rates = ls.learn_rates(deals, monday, use_quarter=True)
    week = ls.quarter_week(monday)
    snapshot = ls.open_deals_at(deals, monday)
    window_end = monday + pd.Timedelta(days=ls.HORIZON_DAYS)
    closed_in_window = (snapshot["close_date"] >= monday) & (snapshot["close_date"] < window_end)
    won = closed_in_window & (snapshot["deal_stage"] == "Won")
    snapshot["realized"] = np.where(won, snapshot["close_value"], 0.0)
    snapshot["won_window"] = won.astype(int)
    snapshot["outcome"] = np.select([won, closed_in_window], ["won", "lost"], default="open")
    snapshot["days_to_close"] = (snapshot["close_date"] - monday).dt.days
    snapshot["probability"] = [rates.probability(age, week) for age in snapshot["age"]]
    return snapshot, rates


def top_k(snapshot: pd.DataFrame, score: np.ndarray, rng: np.random.Generator | None = None) -> pd.DataFrame:
    """Each rep's top deals. Ties break by ID, which is unrelated to the outcome.

    Many deals share a price, so file order would otherwise decide who gets in,
    and the file is ordered by date. Passing rng breaks ties at random instead.
    """
    ranked = snapshot.assign(_score=score)
    if rng is None:
        ranked = ranked.sort_values(["_score", "opportunity_id"], ascending=[False, True])
    else:
        ranked = ranked.iloc[rng.permutation(len(ranked))].sort_values("_score", ascending=False, kind="mergesort")
    return ranked.groupby("sales_agent").head(ls.TOP_K)


def outcome_summary(top: pd.DataFrame, max_cycle: int) -> dict:
    return {
        "revenue": float(top["realized"].sum()),
        "wins": int(top["won_window"].sum()),
        "listed": len(top),
        "stale": int((top["age"] > max_cycle).sum()),
    }


def strategy_scores(snapshot: pd.DataFrame) -> dict[str, np.ndarray]:
    return {
        "score": ls.ranking_value(snapshot["probability"], snapshot["sales_price"]),
        "maior_valor": snapshot["sales_price"].to_numpy(),
        "mais_novo": -snapshot["age"].to_numpy(),
        "mais_antigo": snapshot["age"].to_numpy(),
    }


def replay(deals: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, list[dict], dict]:
    rows = []
    calibration = []
    machine = []
    tie_checks = {"score": [], "maior_valor": []}
    rng = np.random.default_rng(0)
    for monday in pd.date_range(FIRST_MONDAY, LAST_MONDAY, freq="W-MON"):
        snapshot, rates = monday_snapshot(deals, monday)
        scores = strategy_scores(snapshot)
        for name, score in scores.items():
            rows.append({"monday": monday, "strategy": name, **outcome_summary(top_k(snapshot, score), rates.max_cycle)})
        for name in tie_checks:
            revenue = [top_k(snapshot, scores[name], rng)["realized"].sum() for _ in range(RANDOM_DRAWS)]
            tie_checks[name].append(float(np.mean(revenue)))

        draws = [outcome_summary(top_k(snapshot, rng.random(len(snapshot))), rates.max_cycle) for _ in range(RANDOM_DRAWS)]
        rows.append({"monday": monday, "strategy": "aleatorio", **pd.DataFrame(draws).mean().to_dict()})
        calibration.append(snapshot[["probability", "won_window"]].assign(monday=monday))
        machine.append(time_machine_entry(deals, monday, snapshot, scores))
    tie_means = {name: round(float(np.mean(values))) for name, values in tie_checks.items()}
    return pd.DataFrame(rows), pd.concat(calibration, ignore_index=True), machine, tie_means


def time_machine_entry(deals: pd.DataFrame, monday: pd.Timestamp, snapshot: pd.DataFrame, scores: dict) -> dict:
    """What each rep's list looked like that Monday, and what value-sorting would give."""
    price_min, price_max = float(deals["sales_price"].min()), float(deals["sales_price"].max())
    score_top = top_k(snapshot, scores["score"])
    value_top = top_k(snapshot, scores["maior_valor"])
    agents = {}
    for agent, group in score_top.groupby("sales_agent", sort=False):
        rows = []
        for deal in group.itertuples():
            value_points, timing_points = ls.score_points(deal.probability, deal.sales_price, price_min, price_max)
            rows.append(
                [
                    deal.opportunity_id,
                    deal.product,
                    None if pd.isna(deal.account) else deal.account,
                    int(deal.sales_price),
                    int(deal.age),
                    round(value_points + timing_points),
                    round(value_points),
                    round(timing_points),
                    deal.outcome,
                    int(deal.realized),
                    None if pd.isna(deal.days_to_close) or deal.outcome == "open" else int(deal.days_to_close),
                ]
            )
        rep_value = value_top[value_top["sales_agent"] == agent]
        rep_pool = snapshot[snapshot["sales_agent"] == agent]
        agents[agent] = {
            "deals": rows,
            "valueRevenue": int(rep_value["realized"].sum()),
            "valueWins": int(rep_value["won_window"].sum()),
            "poolRevenue": int(rep_pool["realized"].sum()),
        }
    return {"date": monday.strftime("%Y-%m-%d"), "week": ls.quarter_week(monday), "agents": agents}


def summarize(results: pd.DataFrame, calibration: pd.DataFrame, tie_means: dict) -> dict:
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
        "random_tie_break_revenue": tie_means,
        "calibration": bands.round(4).reset_index().to_dict("records"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=HERE.parent / "data", type=Path)
    parser.add_argument("--out", default=HERE / "backtest_results.json", type=Path)
    parser.add_argument("--replay-out", default=HERE.parent / "app" / "replay.js", type=Path)
    args = parser.parse_args()

    results, calibration, machine, tie_means = replay(ls.load_deals(args.data))
    summary = summarize(results, calibration, tie_means)
    args.out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    args.replay_out.write_text("window.LEAD_REPLAY = " + json.dumps(machine, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
