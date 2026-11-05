"""Generate app/data.js, which lets the page open directly with no server.

Usage: python build_app_data.py [--data DIR] [--backtest FILE] [--out FILE]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

import lead_scorer as ls

HERE = Path(__file__).resolve().parent


def text_or_none(value):
    return None if pd.isna(value) else value


def int_or_zero(value) -> int:
    return 0 if pd.isna(value) else int(value)


def engaged_row(deal) -> dict:
    return {
        "id": deal.opportunity_id,
        "agent": deal.sales_agent,
        "product": deal.product,
        "account": text_or_none(deal.account),
        "sector": text_or_none(deal.sector),
        "price": int(deal.sales_price),
        "age": int(deal.age),
        "score": int(deal.score),
        "valuePts": round(deal.value_points),
        "timingPts": round(deal.timing_points),
        "probability": round(deal.probability, 4),
        "expected": round(deal.expected_revenue),
        "zone": deal.zone,
        "queue": deal.queue,
        "action": deal.action,
        "pastDeals": int_or_zero(deal.past_deals),
        "pastWins": int_or_zero(deal.past_wins),
    }


def prospecting_rows(deals: pd.DataFrame, as_of: pd.Timestamp) -> list[dict]:
    prospects = deals[deals["deal_stage"] == "Prospecting"].merge(ls.account_history(deals, as_of), on="account", how="left")
    prospects = prospects.sort_values("sales_price", ascending=False)
    return [
        {
            "id": deal.opportunity_id,
            "agent": deal.sales_agent,
            "product": deal.product,
            "account": text_or_none(deal.account),
            "sector": text_or_none(deal.sector),
            "price": int(deal.sales_price),
            "pastDeals": int_or_zero(deal.past_deals),
            "pastWins": int_or_zero(deal.past_wins),
        }
        for deal in prospects.itertuples()
    ]


def build_payload(deals: pd.DataFrame, team: pd.DataFrame, backtest: dict, as_of: pd.Timestamp = ls.AS_OF) -> dict:
    scored, rates = ls.score_pipeline(deals, as_of)
    team = team.sort_values("sales_agent")  # includes reps with no deals in the pipeline
    return {
        "asOf": as_of.strftime("%Y-%m-%d"),
        "quarterPosition": int(ls.quarter_position(pd.DatetimeIndex([as_of]))[0]),
        "maxCycle": rates.max_cycle,
        "topK": ls.TOP_K,
        "team": [{"agent": r.sales_agent, "manager": r.manager, "region": r.regional_office} for r in team.itertuples()],
        "engaged": [engaged_row(deal) for deal in scored.itertuples()],
        "prospecting": prospecting_rows(deals, as_of),
        "backtest": backtest,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=HERE.parent / "data", type=Path)
    parser.add_argument("--backtest", default=HERE / "backtest_results.json", type=Path)
    parser.add_argument("--out", default=HERE.parent / "app" / "data.js", type=Path)
    args = parser.parse_args()

    backtest = json.loads(args.backtest.read_text(encoding="utf-8"))
    team = pd.read_csv(args.data / "sales_teams.csv")
    payload = build_payload(ls.load_deals(args.data), team, backtest)
    args.out.write_text("window.LEAD_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n", encoding="utf-8")

    engaged = pd.DataFrame(payload["engaged"])
    print("foco", (engaged["queue"] == "foco").sum(), "decidir", (engaged["queue"] == "decidir").sum(), "prospecting", len(payload["prospecting"]))
    print(engaged.groupby("queue").agg(price=("price", "sum"), expected=("expected", "sum"), no_account=("account", lambda s: s.isna().mean())).round(3))
    print(engaged[engaged["queue"] == "foco"].groupby("zone").size().to_dict())
    print("per rep foco", engaged[engaged["queue"] == "foco"].groupby("agent").size().describe().round(1).to_dict())
    print(engaged.head(5)[["id", "agent", "product", "account", "age", "score", "valuePts", "timingPts", "probability", "expected"]].to_string())


if __name__ == "__main__":
    main()
