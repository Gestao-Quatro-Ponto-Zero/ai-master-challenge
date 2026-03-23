"""
Win rate por faixa de dias no pipeline (deals fechados Won/Lost).

Mesma lógica de faixas usada em `streamlit_app/pages/Deals_Analysis.py`.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

# Ordem fixa das faixas (rótulos exibidos no eixo X)
BUCKET_ORDER: List[str] = [
    "< 28d",
    "28–57d",
    "57–85d",
    "85–165d",
    "165–200d",
    "> 200d",
]


def assign_bucket(days: float) -> str:
    """Classifica `days_in_pipeline` na faixa correspondente."""
    if days < 28:
        return "< 28d"
    if days < 57:
        return "28–57d"
    if days < 85:
        return "57–85d"
    if days < 165:
        return "85–165d"
    if days < 200:
        return "165–200d"
    return "> 200d"


def compute_win_rate_by_pipeline_time_bucket(
    pipeline_df: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Agrega win rate por faixa de tempo para deals fechados (Won ou Lost).

    Returns:
        buckets: lista ordenada (todas as faixas), cada item com bucket, total, won, win_rate.
        closed_deals_count: número de deals fechados considerados.
        scoped_closed_win_rate: win rate global dos fechados neste recorte (%), ou None se vazio.
    """
    closed_df = pipeline_df[pipeline_df["deal_stage"].isin(["Won", "Lost"])].copy()
    closed_df = closed_df[
        closed_df["days_in_pipeline"].notna() & (closed_df["days_in_pipeline"] >= 0)
    ]

    if closed_df.empty:
        return {
            "buckets": [
                {
                    "bucket": b,
                    "total": 0,
                    "won": 0,
                    "win_rate": None,
                }
                for b in BUCKET_ORDER
            ],
            "closed_deals_count": 0,
            "scoped_closed_win_rate": None,
        }

    closed_df["bucket"] = closed_df["days_in_pipeline"].apply(assign_bucket)
    closed_df["is_won"] = (closed_df["deal_stage"] == "Won").astype(int)

    agg = (
        closed_df.groupby("bucket", observed=False)
        .agg(total=("is_won", "count"), won=("is_won", "sum"))
        .reindex(BUCKET_ORDER)
        .fillna(0)
    )
    agg["total"] = agg["total"].astype(int)
    agg["won"] = agg["won"].astype(int)

    scoped_closed_win_rate = round(float(closed_df["is_won"].mean()) * 100, 2)

    buckets: List[Dict[str, Any]] = []
    for b in BUCKET_ORDER:
        row = agg.loc[b]
        total = int(row["total"])
        won = int(row["won"])
        win_rate: Optional[float]
        if total > 0:
            win_rate = round(won / total * 100, 2)
        else:
            win_rate = None
        buckets.append(
            {
                "bucket": b,
                "total": total,
                "won": won,
                "win_rate": win_rate,
            }
        )

    return {
        "buckets": buckets,
        "closed_deals_count": int(len(closed_df)),
        "scoped_closed_win_rate": scoped_closed_win_rate,
    }
