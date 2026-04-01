"""
Router: /accounts
"""

from typing import Optional, List
from fastapi import APIRouter, Query

from api.dependencies import get_benchmarks, get_raw_data

router = APIRouter()


@router.get("")
def list_accounts(
    sector: Optional[str] = Query(None),
    office_location: Optional[str] = Query(None),
    top20_only: bool = Query(False),
    min_deals: Optional[int] = Query(None),
    sort_by: Optional[str] = Query("total_deals", description="total_deals | win_rate | total_won_value | revenue"),
) -> List[dict]:
    """Lista contas com métricas de pipeline."""
    benchmarks = get_benchmarks()
    pipeline_df, accounts_df, _, _ = get_raw_data()

    closed = pipeline_df[pipeline_df["deal_stage"].isin(["Won", "Lost"])]
    won = pipeline_df[pipeline_df["deal_stage"] == "Won"]

    deal_counts = pipeline_df["account"].value_counts().rename("total_deals").rename_axis("account").reset_index()
    won_counts = won["account"].value_counts().rename("won_deals").rename_axis("account").reset_index()
    won_value = won.groupby("account")["close_value"].sum().rename("total_won_value").reset_index()

    df = accounts_df.copy()
    df = df.merge(deal_counts, on="account", how="left")
    df = df.merge(won_counts, on="account", how="left")
    df = df.merge(won_value, on="account", how="left")

    df["total_deals"] = df["total_deals"].fillna(0).astype(int)
    df["won_deals"] = df["won_deals"].fillna(0).astype(int)
    df["total_won_value"] = df["total_won_value"].fillna(0).round(2)

    df["win_rate"] = df["account"].map(benchmarks["account_wr"]).fillna(0).round(1)
    top20 = set(benchmarks["top_20_accounts"])
    df["is_top20"] = df["account"].isin(top20)

    if sector:
        df = df[df["sector"] == sector]
    if office_location:
        df = df[df["office_location"] == office_location]
    if top20_only:
        df = df[df["is_top20"]]
    if min_deals is not None:
        df = df[df["total_deals"] >= min_deals]

    sort_map = {
        "total_deals": "total_deals",
        "win_rate": "win_rate",
        "total_won_value": "total_won_value",
        "revenue": "revenue",
    }
    df = df.sort_values(sort_map.get(sort_by, "total_deals"), ascending=False)

    return df.to_dict("records")
