#!/usr/bin/env python3
"""Reproducible structural and quality audit for the Challenge 003 dataset."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import pandas as pd


FILES = {
    "accounts": "accounts.csv",
    "products": "products.csv",
    "sales_teams": "sales_teams.csv",
    "sales_pipeline": "sales_pipeline.csv",
    "metadata": "metadata.csv",
}

PRIMARY_KEYS = {
    "accounts": "account",
    "products": "product",
    "sales_teams": "sales_agent",
    "sales_pipeline": "opportunity_id",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_key(value: object) -> str | None:
    if pd.isna(value):
        return None
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def json_value(value: object) -> object:
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value


def profile_table(name: str, frame: pd.DataFrame, path: Path) -> dict[str, object]:
    profile: dict[str, object] = {
        "file": path.name,
        "sha256": sha256(path),
        "rows": int(len(frame)),
        "columns": int(len(frame.columns)),
        "column_names": frame.columns.tolist(),
        "duplicate_rows": int(frame.duplicated().sum()),
        "nulls": {
            column: {
                "count": int(frame[column].isna().sum()),
                "rate": round(float(frame[column].isna().mean()), 6),
            }
            for column in frame.columns
        },
        "unique_values": {
            column: int(frame[column].nunique(dropna=True)) for column in frame.columns
        },
    }

    primary_key = PRIMARY_KEYS.get(name)
    if primary_key:
        profile["primary_key"] = {
            "column": primary_key,
            "nulls": int(frame[primary_key].isna().sum()),
            "duplicates": int(frame[primary_key].duplicated().sum()),
        }

    numeric = frame.select_dtypes(include="number")
    profile["numeric_summary"] = {
        column: {
            "min": json_value(numeric[column].min()),
            "median": json_value(numeric[column].median()),
            "max": json_value(numeric[column].max()),
        }
        for column in numeric.columns
    }
    return profile


def missing_references(
    source: pd.Series, target: pd.Series, allow_normalized_match: bool = False
) -> dict[str, object]:
    source_values = source.dropna().astype(str)
    target_values = set(target.dropna().astype(str))
    missing = sorted(set(source_values) - target_values)

    result: dict[str, object] = {
        "rows_with_null_reference": int(source.isna().sum()),
        "rows_with_unknown_exact_reference": int(source_values.isin(missing).sum()),
        "unknown_exact_values": missing,
    }

    if allow_normalized_match:
        normalized_targets = {normalize_key(value) for value in target_values}
        normalized_resolvable = [
            value for value in missing if normalize_key(value) in normalized_targets
        ]
        result["unknown_values_resolvable_by_normalization"] = normalized_resolvable
        result["rows_resolvable_by_normalization"] = int(
            source_values.isin(normalized_resolvable).sum()
        )
    return result


def grouped_outcome_summary(
    frame: pd.DataFrame, dimension: str
) -> dict[str, object]:
    grouped = (
        frame.groupby(dimension, dropna=False)
        .agg(
            deals=("opportunity_id", "size"),
            wins=("deal_stage", lambda values: int(values.eq("Won").sum())),
            won_value=(
                "close_value",
                lambda values: float(values.where(values.gt(0), 0).sum()),
            ),
        )
        .reset_index()
    )
    grouped["win_rate"] = grouped["wins"] / grouped["deals"]
    ranked = grouped.sort_values(["win_rate", "deals"], ascending=[False, False])
    return {
        "groups": int(len(grouped)),
        "deals_per_group": {
            "min": int(grouped["deals"].min()),
            "median": float(grouped["deals"].median()),
            "max": int(grouped["deals"].max()),
        },
        "win_rate_range": {
            "min": round(float(grouped["win_rate"].min()), 6),
            "median": round(float(grouped["win_rate"].median()), 6),
            "max": round(float(grouped["win_rate"].max()), 6),
        },
        "highest_win_rate": {
            "value": json_value(ranked.iloc[0][dimension]),
            "deals": int(ranked.iloc[0]["deals"]),
            "win_rate": round(float(ranked.iloc[0]["win_rate"]), 6),
        },
        "lowest_win_rate": {
            "value": json_value(ranked.iloc[-1][dimension]),
            "deals": int(ranked.iloc[-1]["deals"]),
            "win_rate": round(float(ranked.iloc[-1]["win_rate"]), 6),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    frames = {
        name: pd.read_csv(args.data_dir / filename)
        for name, filename in FILES.items()
    }

    pipeline = frames["sales_pipeline"].copy()
    for column in ["engage_date", "close_date"]:
        pipeline[column] = pd.to_datetime(pipeline[column], errors="coerce")

    closed = pipeline[pipeline["deal_stage"].isin(["Won", "Lost"])].copy()
    active = pipeline[pipeline["deal_stage"].isin(["Prospecting", "Engaging"])].copy()
    closed["sales_cycle_days"] = (closed["close_date"] - closed["engage_date"]).dt.days

    max_known_date = pd.concat(
        [pipeline["engage_date"], pipeline["close_date"]], ignore_index=True
    ).max()

    product_lookup = frames["products"].copy()
    product_lookup["product_normalized"] = product_lookup["product"].map(normalize_key)
    pipeline["product_normalized"] = pipeline["product"].map(normalize_key)
    pipeline_with_price = pipeline.merge(
        product_lookup[["product_normalized", "series", "sales_price"]],
        on="product_normalized",
        how="left",
        validate="many_to_one",
    )
    active_with_price = pipeline_with_price[
        pipeline_with_price["deal_stage"].isin(["Prospecting", "Engaging"])
    ].copy()
    active_with_price["age_days"] = (
        max_known_date - active_with_price["engage_date"]
    ).dt.days

    won_with_price = pipeline_with_price[
        pipeline_with_price["deal_stage"].eq("Won")
    ].copy()
    won_with_price["close_to_list_ratio"] = (
        won_with_price["close_value"] / won_with_price["sales_price"]
    )

    max_observed_cycle = int(closed["sales_cycle_days"].max())
    maturity_cutoff = max_known_date - pd.Timedelta(days=max_observed_cycle)
    active_engaging_ages = active_with_price.loc[
        active_with_price["deal_stage"].eq("Engaging"), "age_days"
    ].dropna()
    closed_agents = set(closed["sales_agent"].dropna())
    active_agents = set(active["sales_agent"].dropna())
    agents_without_closed_history = sorted(active_agents - closed_agents)

    stage_counts = pipeline["deal_stage"].value_counts(dropna=False)
    stage_quality: dict[str, object] = {}
    for stage, group in pipeline.groupby("deal_stage", dropna=False):
        stage_quality[str(stage)] = {
            "rows": int(len(group)),
            "share": round(float(len(group) / len(pipeline)), 6),
            "missing_account": int(group["account"].isna().sum()),
            "missing_engage_date": int(group["engage_date"].isna().sum()),
            "missing_close_date": int(group["close_date"].isna().sum()),
            "missing_close_value": int(group["close_value"].isna().sum()),
            "zero_close_value": int(group["close_value"].fillna(-1).eq(0).sum()),
        }

    cycle_summary: dict[str, object] = {}
    for stage, group in closed.groupby("deal_stage"):
        valid = group["sales_cycle_days"].dropna()
        cycle_summary[stage] = {
            "count": int(len(valid)),
            "min": json_value(valid.min()),
            "median": json_value(valid.median()),
            "p90": json_value(valid.quantile(0.9)),
            "max": json_value(valid.max()),
        }

    output = {
        "source": {
            "dataset": "CRM Sales Predictive Analytics",
            "url": "https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics",
            "license": "CC0",
        },
        "tables": {
            name: profile_table(name, frame, args.data_dir / FILES[name])
            for name, frame in frames.items()
        },
        "relationships": {
            "pipeline_to_accounts": missing_references(
                frames["sales_pipeline"]["account"], frames["accounts"]["account"]
            ),
            "pipeline_to_products": missing_references(
                frames["sales_pipeline"]["product"],
                frames["products"]["product"],
                allow_normalized_match=True,
            ),
            "pipeline_to_sales_teams": missing_references(
                frames["sales_pipeline"]["sales_agent"],
                frames["sales_teams"]["sales_agent"],
            ),
            "sales_team_agents_without_pipeline_rows": sorted(
                set(frames["sales_teams"]["sales_agent"])
                - set(frames["sales_pipeline"]["sales_agent"])
            ),
            "accounts_to_parent_accounts": missing_references(
                frames["accounts"]["subsidiary_of"], frames["accounts"]["account"]
            ),
        },
        "pipeline": {
            "stage_counts": {str(key): int(value) for key, value in stage_counts.items()},
            "stage_quality": stage_quality,
            "closed_rows": int(len(closed)),
            "active_rows": int(len(active)),
            "historical_win_rate": round(
                float(closed["deal_stage"].eq("Won").mean()), 6
            ),
            "max_known_date": json_value(max_known_date),
            "engage_date_range": {
                "min": json_value(pipeline["engage_date"].min()),
                "max": json_value(pipeline["engage_date"].max()),
            },
            "close_date_range": {
                "min": json_value(pipeline["close_date"].min()),
                "max": json_value(pipeline["close_date"].max()),
            },
            "invalid_close_before_engage": int(
                (closed["close_date"] < closed["engage_date"]).sum()
            ),
            "closed_missing_engage_date": int(closed["engage_date"].isna().sum()),
            "closed_missing_close_date": int(closed["close_date"].isna().sum()),
            "won_nonpositive_close_value": int(
                closed.loc[closed["deal_stage"].eq("Won"), "close_value"]
                .fillna(0)
                .le(0)
                .sum()
            ),
            "lost_nonzero_close_value": int(
                closed.loc[closed["deal_stage"].eq("Lost"), "close_value"]
                .fillna(0)
                .ne(0)
                .sum()
            ),
            "sales_cycle_days": cycle_summary,
            "active_by_stage": {
                str(key): int(value)
                for key, value in active["deal_stage"].value_counts().items()
            },
            "active_feature_coverage": {
                "account_known": int(active["account"].notna().sum()),
                "account_known_rate": round(float(active["account"].notna().mean()), 6),
                "engage_date_known": int(active["engage_date"].notna().sum()),
                "engage_date_known_rate": round(
                    float(active["engage_date"].notna().mean()), 6
                ),
                "catalog_price_known_after_product_normalization": int(
                    active_with_price["sales_price"].notna().sum()
                ),
                "catalog_price_known_rate": round(
                    float(active_with_price["sales_price"].notna().mean()), 6
                ),
                "sales_agents_present": int(active["sales_agent"].nunique()),
                "sales_agents_without_closed_history": agents_without_closed_history,
                "deals_owned_by_agents_without_closed_history": int(
                    active["sales_agent"].isin(agents_without_closed_history).sum()
                ),
            },
            "active_catalog_value": float(active_with_price["sales_price"].sum()),
            "active_engaging_age_days": {
                "count": int(len(active_engaging_ages)),
                "min": json_value(active_engaging_ages.min()),
                "median": json_value(active_engaging_ages.median()),
                "p90": json_value(active_engaging_ages.quantile(0.9)),
                "max": json_value(active_engaging_ages.max()),
            },
            "right_censoring_check": {
                "max_observed_closed_cycle_days": max_observed_cycle,
                "maturity_cutoff_if_using_max_cycle": json_value(maturity_cutoff),
                "active_engaging_older_than_cutoff": int(
                    (
                        active_with_price.loc[
                            active_with_price["deal_stage"].eq("Engaging"),
                            "engage_date",
                        ]
                        <= maturity_cutoff
                    ).sum()
                ),
            },
            "won_close_to_catalog_price_ratio": {
                "count": int(won_with_price["close_to_list_ratio"].notna().sum()),
                "p10": json_value(won_with_price["close_to_list_ratio"].quantile(0.1)),
                "median": json_value(won_with_price["close_to_list_ratio"].median()),
                "p90": json_value(won_with_price["close_to_list_ratio"].quantile(0.9)),
            },
            "historical_outcome_variation": {
                "sales_agent": grouped_outcome_summary(closed, "sales_agent"),
                "product": grouped_outcome_summary(closed, "product"),
                "account": grouped_outcome_summary(closed, "account"),
            },
        },
        "categorical_quality": {
            "account_sectors": frames["accounts"]["sector"].value_counts().to_dict(),
            "account_locations": frames["accounts"]["office_location"]
            .value_counts()
            .to_dict(),
            "regional_offices": frames["sales_teams"]["regional_office"]
            .value_counts()
            .to_dict(),
            "managers": frames["sales_teams"]["manager"].value_counts().to_dict(),
        },
        "modeling_guardrails": [
            "Use only Won/Lost rows as historical outcomes; active Prospecting/Engaging rows have no observed target.",
            "Do not use close_date or close_value as predictive features because they are only known after outcome.",
            "Treat deal_stage as workflow state for active prioritization, not as the prediction target and feature at the same time.",
            "Compute seller/account/product historical features inside each training fold or using time-aware history to avoid target leakage.",
            "Use product sales_price or another pre-outcome estimate for active deal value; close_value is unavailable before closing.",
            "Preserve missing account and engage_date as meaningful workflow states instead of silently dropping active deals.",
        ],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, indent=2, ensure_ascii=False, default=json_value) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
