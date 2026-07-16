"""Data access and metric reconciliation for the dashboard."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "dashboard" / "assets" / "dashboard_posts.parquet"

FILTERS = ["platform", "content_type", "content_category", "creator_size", "is_sponsored"]


def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load the contract-approved analytical dataset."""
    frame = pd.read_parquet(path)
    if len(frame) != 52_214:
        raise ValueError(f"unexpected row count: {len(frame)}")
    return frame


def apply_filters(frame: pd.DataFrame, selected: dict[str, list[object]]) -> pd.DataFrame:
    """Apply explicit inclusive filters; an empty selection means all."""
    result = frame
    for column, values in selected.items():
        if column not in FILTERS:
            raise ValueError(f"unsupported filter: {column}")
        if values:
            result = result.loc[result[column].isin(values)]
    return result.copy()


def kpis(frame: pd.DataFrame) -> dict[str, float | int]:
    """Return only metrics defined in the metric registry."""
    if frame.empty:
        return {
            "posts": 0,
            "engagement_mean": float("nan"),
            "views_mean": float("nan"),
            "sponsored_share": float("nan"),
        }
    return {
        "posts": int(len(frame)),
        "engagement_mean": float(frame["engagement_rate_views"].mean()),
        "views_mean": float(frame["views"].mean()),
        "sponsored_share": float(frame["is_sponsored"].mean()),
    }


def performance_by(frame: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """Aggregate a supported dimension with visible sample size."""
    if dimension not in FILTERS[:-1] + ["audience_age_distribution", "audience_location"]:
        raise ValueError(f"unsupported dimension: {dimension}")
    return (
        frame.groupby(dimension, observed=True)
        .agg(
            n=("id", "size"),
            engagement_mean=("engagement_rate_views", "mean"),
            views_mean=("views", "mean"),
        )
        .reset_index()
        .sort_values("engagement_mean", ascending=False)
    )


def audience_cross(
    frame: pd.DataFrame, audience_dimension: str, context_dimension: str
) -> pd.DataFrame:
    """Cross audience composition with the context explicitly requested by the challenge."""
    allowed_audience = {
        "audience_age_distribution",
        "audience_gender_distribution",
        "audience_location",
    }
    allowed_context = {"platform", "content_type", "content_category"}
    if audience_dimension not in allowed_audience:
        raise ValueError(f"unsupported audience dimension: {audience_dimension}")
    if context_dimension not in allowed_context:
        raise ValueError(f"unsupported context dimension: {context_dimension}")
    return (
        frame.groupby([context_dimension, audience_dimension], observed=True)
        .agg(
            n=("id", "size"),
            engagement_mean=("engagement_rate_views", "mean"),
            engagement_median=("engagement_rate_views", "median"),
            views_mean=("views", "mean"),
        )
        .reset_index()
        .sort_values([context_dimension, "engagement_mean"], ascending=[True, False])
    )
