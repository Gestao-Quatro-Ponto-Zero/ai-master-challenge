"""SPEC-2 REQ-2-004: Merge configurável entre tabelas."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def _aggregate_features(
    df: pd.DataFrame,
    agg_config: dict[str, Any],
    group_col: str,
) -> pd.DataFrame:
    agg_dict = {}
    for name, spec in agg_config.items():
        method = spec["method"]
        col = spec["column"]
        if method == "count":
            agg_dict[name] = pd.NamedAgg(column=col, aggfunc="count")
        elif method == "sum":
            agg_dict[name] = pd.NamedAgg(column=col, aggfunc="sum")
        elif method == "mean":
            agg_dict[name] = pd.NamedAgg(column=col, aggfunc="mean")
        elif method == "max":
            agg_dict[name] = pd.NamedAgg(column=col, aggfunc="max")
        elif method == "nunique":
            agg_dict[name] = pd.NamedAgg(column=col, aggfunc="nunique")
        elif method == "count_where":
            condition = spec.get("condition", "")
            if "in" in condition:
                vals = eval(condition.split("in")[1].strip())
                agg_dict[name] = pd.NamedAgg(
                    column=col,
                    aggfunc=lambda x, v=vals: x.isin(v).sum(),
                )
            else:
                agg_dict[name] = pd.NamedAgg(column=col, aggfunc="count")

    return df.groupby(group_col).agg(**agg_dict).reset_index() if agg_dict else pd.DataFrame()


def _latest_subscription(subscriptions: pd.DataFrame) -> pd.DataFrame:
    return (
        subscriptions.sort_values("start_date")
        .groupby("account_id")
        .last()
        .reset_index()
    )


def run(
    sources: dict[str, pd.DataFrame],
    merge_config: dict[str, Any],
) -> pd.DataFrame:
    logger.info("=== Merge de dados ===")

    steps = merge_config.get("main_view", {}).get("steps", [])
    result = None

    for step in steps:
        from_name = step.get("from")
        with_name = step["with"]
        strategy = step.get("strategy", "left")
        left_df = sources[from_name] if from_name and from_name in sources else result
        right_df = sources[with_name]

        logger.info("Merge: %s → %s (strategy=%s)", from_name or "result", with_name, strategy)

        if strategy == "latest_subscription":
            right_df = _latest_subscription(right_df)
            result = left_df.merge(
                right_df,
                on=step["on"],
                how="left",
                suffixes=tuple(step.get("suffix", ["_left", "_right"])),
            )

        elif strategy == "aggregate":
            agg_config = step.get("aggregations", {})
            on = step["on"]
            aggregated = _aggregate_features(right_df, agg_config, on)
            result = left_df.merge(aggregated, on=on, how="left")

        elif strategy == "left":
            result = left_df.merge(
                right_df,
                on=step["on"],
                how="left",
                suffixes=tuple(step.get("suffix", ["_left", "_right"])),
            )

        logger.info("  → %s linhas", len(result))

    if result is None:
        raise RuntimeError("Nenhum passo de merge foi executado")

    return result
