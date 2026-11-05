"""What effect could a real pilot detect with this team?

Splits reps into fake treatment and control groups inside each manager, in a
period when nothing was treated. The spread of those placebo differences is the
noise a real pilot would have to beat.

Usage: python pilot_plan.py [--data DIR] [--out FILE]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import lead_scorer as ls

HERE = Path(__file__).resolve().parent
PLACEBO_SPLITS = 5000
POWER_FACTOR = 2.8  # 80% power at 5% two-sided significance


def period_totals(won: pd.DataFrame, reps: pd.Index, start: str, end: str, column: str) -> pd.Series:
    period = won[(won["close_date"] >= start) & (won["close_date"] < end)]
    if column == "wins":
        totals = period.groupby("sales_agent").size()
    else:
        totals = period.groupby("sales_agent")["close_value"].sum()
    return totals.reindex(reps, fill_value=0).astype(float)


def placebo_spread(outcome: pd.Series, managers: pd.Series, rng: np.random.Generator) -> float:
    """Standard deviation of treatment-minus-control means across fake splits."""
    groups = [np.flatnonzero(managers.to_numpy() == manager) for manager in managers.unique()]
    values = outcome.to_numpy()
    differences = np.empty(PLACEBO_SPLITS)
    for i in range(PLACEBO_SPLITS):
        treated = np.zeros(len(values), dtype=bool)
        for group in groups:
            treated[rng.permutation(group)[: (len(group) + rng.integers(0, 2)) // 2]] = True
        differences[i] = values[treated].mean() - values[~treated].mean()
    return float(differences.std())


def detectable_effect(outcome: pd.Series, baseline: pd.Series, managers: pd.Series, rng: np.random.Generator) -> dict:
    slope = np.polyfit(baseline, outcome, 1)[0]
    adjusted = outcome - slope * (baseline - baseline.mean())
    mean = outcome.mean()
    return {
        "correlation_with_baseline": round(float(np.corrcoef(baseline, outcome)[0, 1]), 3),
        "raw_percent": round(POWER_FACTOR * placebo_spread(outcome, managers, rng) / mean * 100, 1),
        "adjusted_percent": round(POWER_FACTOR * placebo_spread(adjusted, managers, rng) / mean * 100, 1),
        "mean_per_rep": round(float(mean), 1),
    }


def build_plan(deals: pd.DataFrame) -> dict:
    rng = np.random.default_rng(0)
    won = deals[deals["deal_stage"] == "Won"]
    team = deals.groupby("sales_agent")["manager"].first()
    reps, managers = team.index, team

    periods = {
        "um_mes_outubro": (("2017-07-01", "2017-08-01"), ("2017-10-01", "2017-11-01")),
        "um_trimestre_q4": (("2017-07-01", "2017-10-01"), ("2017-10-01", "2018-01-01")),
    }
    results = {}
    for name, (baseline_range, outcome_range) in periods.items():
        results[name] = {}
        for metric in ("revenue", "wins"):
            baseline = period_totals(won, reps, *baseline_range, metric)
            outcome = period_totals(won, reps, *outcome_range, metric)
            results[name][metric] = detectable_effect(outcome, baseline, managers, rng)

    return {
        "reps": len(reps),
        "managers": int(managers.nunique()),
        "placebo_splits": PLACEBO_SPLITS,
        "power": "80% de poder, 5% de significância",
        "periods": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=HERE.parent / "data", type=Path)
    parser.add_argument("--out", default=HERE / "pilot_plan.json", type=Path)
    args = parser.parse_args()
    plan = build_plan(ls.load_deals(args.data))
    args.out.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(plan, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
