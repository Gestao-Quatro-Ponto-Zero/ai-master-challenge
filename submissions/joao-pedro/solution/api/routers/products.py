"""
Router: /products
"""

from typing import Optional, List
from fastapi import APIRouter, Query
import pandas as pd

from api.dependencies import get_benchmarks, get_raw_data

router = APIRouter()


@router.get("")
def list_products(
    series: Optional[str] = Query(None, description="GTX | MG"),
    sort_by: Optional[str] = Query("win_rate", description="win_rate | active_deals | avg_ticket | avg_cycle_days"),
) -> List[dict]:
    """Lista produtos com métricas calculadas do pipeline."""
    benchmarks = get_benchmarks()
    pipeline_df, _, products_df, _ = get_raw_data()

    deal_counts = pipeline_df["product"].value_counts().rename("total_deals").rename_axis("product").reset_index()
    closed_df = pipeline_df[pipeline_df["deal_stage"].isin(["Won", "Lost"])]
    closed_counts = closed_df["product"].value_counts().rename("closed_deals").rename_axis("product").reset_index()
    won_df = pipeline_df[pipeline_df["deal_stage"] == "Won"]
    won_counts = won_df["product"].value_counts().rename("won_deals").rename_axis("product").reset_index()
    avg_ticket = won_df.groupby("product")["close_value"].mean().rename("avg_ticket").reset_index()

    won_dates = won_df.copy()
    won_dates["days_in_pipeline"] = (
        pd.to_datetime(won_dates["close_date"]) - pd.to_datetime(won_dates["engage_date"])
    ).dt.days
    avg_cycle = won_dates.groupby("product")["days_in_pipeline"].mean().rename("avg_cycle_days").reset_index()

    active_df = pipeline_df[pipeline_df["deal_stage"].isin(["Engaging", "Prospecting"])]
    active_counts = active_df["product"].value_counts().rename("active_deals").rename_axis("product").reset_index()

    df = products_df.copy()
    for right in [deal_counts, closed_counts, won_counts, avg_ticket, avg_cycle, active_counts]:
        df = df.merge(right, on="product", how="left")

    for col in ["total_deals", "closed_deals", "won_deals", "active_deals"]:
        df[col] = df[col].fillna(0).astype(int)
    for col in ["avg_ticket", "avg_cycle_days"]:
        df[col] = df[col].fillna(0).round(1)

    df["win_rate"] = df["product"].map(benchmarks["product_wr"]).fillna(0).round(1)

    if series:
        df = df[df["series"] == series]

    sort_map = {
        "win_rate": "win_rate",
        "active_deals": "active_deals",
        "avg_ticket": "avg_ticket",
        "avg_cycle_days": "avg_cycle_days",
    }
    df = df.sort_values(sort_map.get(sort_by, "win_rate"), ascending=False)

    return df.to_dict("records")
