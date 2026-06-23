#!/usr/bin/env python3
"""Generate seller-level diagnostics for the Lead Scorer challenge."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"


def fmt_pct(value: float | int | None) -> str:
    if pd.isna(value):
        return "n/a"
    return f"{float(value) * 100:.1f}%"


def fmt_money(value: float | int | None) -> str:
    if pd.isna(value):
        return "n/a"
    return f"US$ {float(value):,.0f}"


def mode_with_share(series: pd.Series) -> tuple[object, float]:
    values = series.dropna()
    if values.empty:
        return pd.NA, np.nan
    counts = values.value_counts()
    mode_value = counts.sort_values(ascending=False).index[0]
    return mode_value, float(counts.iloc[0] / counts.sum())


def maturity_band(closed_count: int) -> str:
    if closed_count == 0:
        return "no_history"
    if closed_count < 100:
        return "thin_history"
    if closed_count < 150:
        return "limited_history"
    return "consolidated"


def performance_band(win_rate: float | None, closed_count: int, global_win_rate: float) -> str:
    if closed_count == 0 or pd.isna(win_rate):
        return "no_history"
    if closed_count < 100:
        return "insufficient_sample"
    delta = win_rate - global_win_rate
    if delta >= 0.04:
        return "top_performer"
    if delta >= 0.01:
        return "above_average"
    if delta > -0.03:
        return "around_average"
    return "underperformer"


def portfolio_risk(row: pd.Series) -> str:
    if row["open_deals"] == 0:
        return "no_open_pipeline"
    if row["open_value"] >= 200_000 and row["win_rate"] < 0.62:
        return "high_value_low_conversion"
    if row["old_engaging_deals"] >= 75:
        return "large_stale_backlog"
    if row["open_account_known_pct"] < 0.4:
        return "low_data_confidence"
    return "normal"


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    teams = pd.read_csv(PROCESSED_DIR / "dim_sales_teams.csv")
    enriched = pd.read_csv(
        PROCESSED_DIR / "opportunities_enriched.csv",
        parse_dates=["engage_date", "close_date", "snapshot_date"],
    )
    open_pipeline = pd.read_csv(
        PROCESSED_DIR / "open_pipeline_for_scoring.csv",
        parse_dates=["engage_date", "snapshot_date"],
    )
    return teams, enriched, open_pipeline


def aggregate_sellers(
    teams: pd.DataFrame,
    enriched: pd.DataFrame,
    open_pipeline: pd.DataFrame,
) -> pd.DataFrame:
    closed = enriched[enriched["is_closed"]].copy()
    won = enriched[enriched["is_won"]].copy()
    global_win_rate = float(closed["is_won"].mean())

    rows: list[dict[str, object]] = []
    for _, seller in teams.sort_values("sales_agent").iterrows():
        seller_id = seller["sales_agent_id"]
        seller_all = enriched[enriched["sales_agent_id"] == seller_id].copy()
        seller_closed = closed[closed["sales_agent_id"] == seller_id].copy()
        seller_won = won[won["sales_agent_id"] == seller_id].copy()
        seller_open = open_pipeline[open_pipeline["sales_agent_id"] == seller_id].copy()

        closed_count = int(len(seller_closed))
        won_count = int(seller_closed["is_won"].sum()) if closed_count else 0
        lost_count = int(seller_closed["is_lost"].sum()) if closed_count else 0
        win_rate = (won_count / closed_count) if closed_count else np.nan

        closed_product_mode, closed_product_mode_share = mode_with_share(seller_closed["product"])
        closed_sector_mode, closed_sector_mode_share = mode_with_share(seller_closed["sector"])
        open_product_mode, open_product_mode_share = mode_with_share(seller_open["product"])
        open_stage_mode, open_stage_mode_share = mode_with_share(seller_open["deal_stage"])
        open_sector_mode, open_sector_mode_share = mode_with_share(seller_open["sector"])

        open_deals = int(len(seller_open))
        open_value = float(seller_open["estimated_deal_value"].sum()) if open_deals else 0.0
        engaging_open = int((seller_open["deal_stage"] == "engaging").sum()) if open_deals else 0
        prospecting_open = int((seller_open["deal_stage"] == "prospecting").sum()) if open_deals else 0
        old_engaging = seller_open[
            (seller_open["deal_stage"] == "engaging")
            & (seller_open["days_open_as_of_snapshot"] > 90)
        ]

        row = {
            "sales_agent_id": seller_id,
            "sales_agent": seller["sales_agent"],
            "manager": seller["manager"],
            "regional_office": seller["regional_office"],
            "total_opportunities": int(len(seller_all)),
            "closed_opportunities": closed_count,
            "won_opportunities": won_count,
            "lost_opportunities": lost_count,
            "win_rate": win_rate,
            "won_revenue_total": float(seller_won["close_value"].sum()) if len(seller_won) else 0.0,
            "won_value_median": float(seller_won["close_value"].median()) if len(seller_won) else np.nan,
            "won_value_std": float(seller_won["close_value"].std()) if len(seller_won) > 1 else np.nan,
            "days_to_close_median": float(seller_closed["days_to_close"].median()) if closed_count else np.nan,
            "days_to_close_std": float(seller_closed["days_to_close"].std()) if closed_count > 1 else np.nan,
            "closed_product_mode": closed_product_mode,
            "closed_product_mode_share": closed_product_mode_share,
            "closed_sector_mode": closed_sector_mode,
            "closed_sector_mode_share": closed_sector_mode_share,
            "open_deals": open_deals,
            "open_value": open_value,
            "open_engaging_deals": engaging_open,
            "open_prospecting_deals": prospecting_open,
            "open_stage_mode": open_stage_mode,
            "open_stage_mode_share": open_stage_mode_share,
            "open_product_mode": open_product_mode,
            "open_product_mode_share": open_product_mode_share,
            "open_sector_mode": open_sector_mode,
            "open_sector_mode_share": open_sector_mode_share,
            "open_account_known_pct": float(seller_open["account_known"].mean()) if open_deals else np.nan,
            "open_days_median": float(seller_open["days_open_as_of_snapshot"].median()) if open_deals else np.nan,
            "old_engaging_deals": int(len(old_engaging)),
            "old_engaging_value": float(old_engaging["estimated_deal_value"].sum()) if len(old_engaging) else 0.0,
        }
        row["history_maturity"] = maturity_band(closed_count)
        row["performance_band"] = performance_band(win_rate, closed_count, global_win_rate)
        row["portfolio_risk"] = portfolio_risk(pd.Series(row))
        rows.append(row)

    return pd.DataFrame(rows)


def markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    out = df[columns].copy()
    for col in out.columns:
        if col.endswith("_rate") or col.endswith("_pct") or col.endswith("_share"):
            out[col] = out[col].map(fmt_pct)
        elif (
            col.endswith("_value")
            or col.endswith("_revenue_total")
            or (col.endswith("_median") and "value" in col)
        ):
            out[col] = out[col].map(fmt_money)
        elif col.endswith("_std") and "value" in col:
            out[col] = out[col].map(fmt_money)
        elif col in {"open_value", "won_revenue_total", "old_engaging_value"}:
            out[col] = out[col].map(fmt_money)
        elif col in {"days_to_close_median", "days_to_close_std", "open_days_median"}:
            out[col] = out[col].map(lambda x: "n/a" if pd.isna(x) else f"{float(x):.1f}")
    out = out.fillna("n/a").astype(str)
    header = "| " + " | ".join(out.columns) + " |"
    separator = "| " + " | ".join(["---"] * len(out.columns)) + " |"
    body = ["| " + " | ".join(row) + " |" for row in out.to_numpy()]
    return "\n".join([header, separator, *body])


def build_report(sellers: pd.DataFrame) -> str:
    active = sellers[sellers["closed_opportunities"] > 0].copy()
    inactive = sellers[sellers["closed_opportunities"] == 0].copy()
    global_win_rate = (
        active["won_opportunities"].sum() / active["closed_opportunities"].sum()
        if active["closed_opportunities"].sum()
        else np.nan
    )

    top = active[active["closed_opportunities"] >= 150].sort_values(
        ["win_rate", "closed_opportunities"], ascending=[False, False]
    ).head(8)
    bottom = active[active["closed_opportunities"] >= 150].sort_values(
        ["win_rate", "open_value"], ascending=[True, False]
    ).head(8)
    high_risk = active.sort_values(
        ["portfolio_risk", "open_value"], ascending=[True, False]
    )
    high_risk = high_risk[
        high_risk["portfolio_risk"].isin(["high_value_low_conversion", "large_stale_backlog"])
    ].sort_values("open_value", ascending=False).head(10)
    limited = sellers[sellers["history_maturity"].isin(["no_history", "thin_history", "limited_history"])]
    largest_portfolios = active.sort_values("open_value", ascending=False).head(10)

    lines = [
        "# Seller X-Ray",
        "",
        "Generated from standardized CSVs in `data/processed`.",
        "",
        "## Metric Definitions",
        "",
        "- `win_rate`: won / closed opportunities.",
        "- `won_value_median` and `won_value_std`: median and sample standard deviation of won deal values.",
        "- `days_to_close_median` and `days_to_close_std`: median and sample standard deviation of lifecycle days for closed opportunities.",
        "- `closed_product_mode`, `closed_sector_mode`, `open_product_mode`, and `open_stage_mode`: categorical modes for historical/current portfolio composition.",
        "- `history_maturity`: `no_history`, `thin_history` (<100 closed), `limited_history` (100-149 closed), or `consolidated` (150+ closed).",
        "",
        "## Portfolio Summary",
        "",
        f"- Active sellers with closed history: {len(active)}.",
        f"- Sellers on roster with no opportunity history: {len(inactive)}.",
        f"- Global closed win rate: {fmt_pct(global_win_rate)}.",
        f"- Open pipeline value across active sellers: {fmt_money(sellers['open_value'].sum())}.",
        "",
        "## Top Historical Performers",
        "",
        markdown_table(
            top,
            [
                "sales_agent",
                "manager",
                "regional_office",
                "closed_opportunities",
                "win_rate",
                "won_revenue_total",
                "won_value_median",
                "days_to_close_median",
                "open_deals",
                "open_value",
            ],
        ),
        "",
        "## Underperforming Historical Conversion",
        "",
        markdown_table(
            bottom,
            [
                "sales_agent",
                "manager",
                "regional_office",
                "closed_opportunities",
                "win_rate",
                "won_revenue_total",
                "won_value_median",
                "days_to_close_median",
                "open_deals",
                "open_value",
            ],
        ),
        "",
        "## Current Portfolio Watchlist",
        "",
        markdown_table(
            high_risk,
            [
                "sales_agent",
                "manager",
                "regional_office",
                "win_rate",
                "open_deals",
                "open_value",
                "old_engaging_deals",
                "old_engaging_value",
                "open_account_known_pct",
                "portfolio_risk",
            ],
        ),
        "",
        "## Largest Open Portfolios",
        "",
        markdown_table(
            largest_portfolios,
            [
                "sales_agent",
                "manager",
                "regional_office",
                "win_rate",
                "open_deals",
                "open_value",
                "old_engaging_deals",
                "open_product_mode",
                "open_product_mode_share",
                "portfolio_risk",
            ],
        ),
        "",
        "## Sellers Requiring Different Interpretation",
        "",
        markdown_table(
            limited,
            [
                "sales_agent",
                "manager",
                "regional_office",
                "closed_opportunities",
                "open_deals",
                "open_value",
                "history_maturity",
                "performance_band",
            ],
        ),
        "",
        "## Full Detail",
        "",
        "See `data/processed/seller_xray.csv` for the complete seller-level table.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    teams, enriched, open_pipeline = load_data()
    sellers = aggregate_sellers(teams, enriched, open_pipeline)
    sellers = sellers.sort_values(["history_maturity", "win_rate"], ascending=[True, False])

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    sellers.to_csv(PROCESSED_DIR / "seller_xray.csv", index=False)
    (REPORTS_DIR / "seller_xray.md").write_text(build_report(sellers), encoding="utf-8")

    print(f"Wrote {PROCESSED_DIR / 'seller_xray.csv'}")
    print(f"Wrote {REPORTS_DIR / 'seller_xray.md'}")
    print(f"Rows: {len(sellers)}")


if __name__ == "__main__":
    main()
