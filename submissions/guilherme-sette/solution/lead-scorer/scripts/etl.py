#!/usr/bin/env python3
"""Build standardized CSV layers for Challenge 003.

The script keeps raw files unchanged, writes canonicalized processed tables, and
creates modeling-ready cuts that avoid obvious target leakage.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


RAW_FILES = [
    "accounts.csv",
    "products.csv",
    "sales_teams.csv",
    "sales_pipeline.csv",
    "data_dictionary.csv",
]

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DIR = PROJECT_ROOT / "data" / "raw"
SNAPSHOT_DATE = pd.Timestamp("2017-12-31")


def slugify(value: object) -> object:
    if pd.isna(value):
        return pd.NA
    text = str(value)
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")
    return text if text else pd.NA


def normalize_strings(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.select_dtypes(include=["object"]).columns:
        out[col] = out[col].astype("string").str.strip()
        out[col] = out[col].replace({"": pd.NA})
    return out


def require_columns(df: pd.DataFrame, name: str, columns: Iterable[str]) -> None:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def copy_raw_files(source_dir: Path, raw_dir: Path) -> None:
    source_dir = source_dir.resolve()
    raw_dir = raw_dir.resolve()

    if source_dir == raw_dir:
        for file_name in RAW_FILES:
            source_file = source_dir / file_name
            if not source_file.exists():
                raise FileNotFoundError(f"Raw CSV missing from project data/raw: {source_file}")
        return

    raw_dir.mkdir(parents=True, exist_ok=True)
    for file_name in RAW_FILES:
        source_file = source_dir / file_name
        if not source_file.exists():
            raise FileNotFoundError(f"Raw source file not found: {source_file}")
        destination_file = raw_dir / file_name
        if source_file.resolve() != destination_file.resolve():
            shutil.copy2(source_file, destination_file)


def load_raw(raw_dir: Path) -> dict[str, pd.DataFrame]:
    frames = {
        "accounts": read_csv(raw_dir / "accounts.csv"),
        "products": read_csv(raw_dir / "products.csv"),
        "sales_teams": read_csv(raw_dir / "sales_teams.csv"),
        "sales_pipeline": read_csv(raw_dir / "sales_pipeline.csv"),
        "data_dictionary": read_csv(raw_dir / "data_dictionary.csv"),
    }
    require_columns(
        frames["accounts"],
        "accounts",
        [
            "account",
            "sector",
            "year_established",
            "revenue",
            "employees",
            "office_location",
            "subsidiary_of",
        ],
    )
    require_columns(frames["products"], "products", ["product", "series", "sales_price"])
    require_columns(
        frames["sales_teams"],
        "sales_teams",
        ["sales_agent", "manager", "regional_office"],
    )
    require_columns(
        frames["sales_pipeline"],
        "sales_pipeline",
        [
            "opportunity_id",
            "sales_agent",
            "product",
            "account",
            "deal_stage",
            "engage_date",
            "close_date",
            "close_value",
        ],
    )
    return frames


def standardize_accounts(accounts: pd.DataFrame) -> pd.DataFrame:
    out = normalize_strings(accounts)
    out["account"] = out["account"].astype("string")
    out["account_id"] = out["account"].map(slugify)
    out["sector"] = out["sector"].str.lower().replace({"technolgy": "technology"})
    out["year_established"] = pd.to_numeric(out["year_established"], errors="raise").astype("Int64")
    out["revenue"] = pd.to_numeric(out["revenue"], errors="raise").round(2)
    out["employees"] = pd.to_numeric(out["employees"], errors="raise").astype("Int64")
    out["is_subsidiary"] = out["subsidiary_of"].notna()
    out["account_age_years_as_of_snapshot"] = SNAPSHOT_DATE.year - out["year_established"]
    out["revenue_band"] = pd.cut(
        out["revenue"],
        bins=[-np.inf, 500, 1500, 3000, np.inf],
        labels=["under_500m", "500m_to_1_5b", "1_5b_to_3b", "over_3b"],
    ).astype("string")
    out["employee_band"] = pd.cut(
        out["employees"],
        bins=[-np.inf, 500, 2000, 10000, np.inf],
        labels=["under_500", "500_to_2k", "2k_to_10k", "over_10k"],
    ).astype("string")
    columns = [
        "account_id",
        "account",
        "sector",
        "year_established",
        "account_age_years_as_of_snapshot",
        "revenue",
        "revenue_band",
        "employees",
        "employee_band",
        "office_location",
        "subsidiary_of",
        "is_subsidiary",
    ]
    return out[columns].sort_values("account").reset_index(drop=True)


def canonical_product(product: object) -> object:
    if pd.isna(product):
        return pd.NA
    product_text = str(product).strip()
    return {"GTXPro": "GTX Pro"}.get(product_text, product_text)


def standardize_products(products: pd.DataFrame) -> pd.DataFrame:
    out = normalize_strings(products)
    out["product"] = out["product"].map(canonical_product).astype("string")
    out["product_id"] = out["product"].map(slugify)
    out["series"] = out["series"].str.upper()
    out["sales_price"] = pd.to_numeric(out["sales_price"], errors="raise").astype("Int64")
    columns = ["product_id", "product", "series", "sales_price"]
    return out[columns].drop_duplicates("product").sort_values("product").reset_index(drop=True)


def standardize_sales_teams(sales_teams: pd.DataFrame) -> pd.DataFrame:
    out = normalize_strings(sales_teams)
    out["sales_agent_id"] = out["sales_agent"].map(slugify)
    out["manager_id"] = out["manager"].map(slugify)
    out["regional_office"] = out["regional_office"].str.title()
    columns = [
        "sales_agent_id",
        "sales_agent",
        "manager_id",
        "manager",
        "regional_office",
    ]
    return out[columns].sort_values("sales_agent").reset_index(drop=True)


def standardize_pipeline(sales_pipeline: pd.DataFrame) -> pd.DataFrame:
    out = normalize_strings(sales_pipeline)
    out["opportunity_id"] = out["opportunity_id"].astype("string")
    out["sales_agent"] = out["sales_agent"].astype("string")
    out["sales_agent_id"] = out["sales_agent"].map(slugify)
    out["account_id"] = out["account"].map(slugify)
    out["product_raw"] = out["product"].astype("string")
    out["product"] = out["product"].map(canonical_product).astype("string")
    out["product_id"] = out["product"].map(slugify)
    out["deal_stage"] = out["deal_stage"].str.strip().str.lower()
    out["engage_date"] = pd.to_datetime(out["engage_date"], errors="coerce")
    out["close_date"] = pd.to_datetime(out["close_date"], errors="coerce")
    out["close_value"] = pd.to_numeric(out["close_value"], errors="coerce")

    out["is_won"] = out["deal_stage"].eq("won")
    out["is_lost"] = out["deal_stage"].eq("lost")
    out["is_closed"] = out["deal_stage"].isin(["won", "lost"])
    out["is_open"] = ~out["is_closed"]
    out["is_engaging"] = out["deal_stage"].eq("engaging")
    out["is_prospecting"] = out["deal_stage"].eq("prospecting")
    out["has_account"] = out["account"].notna()
    out["has_engage_date"] = out["engage_date"].notna()
    out["has_close_date"] = out["close_date"].notna()
    out["has_close_value"] = out["close_value"].notna()
    out["snapshot_date"] = SNAPSHOT_DATE
    out["days_to_close"] = np.where(
        out["is_closed"] & out["engage_date"].notna() & out["close_date"].notna(),
        (out["close_date"] - out["engage_date"]).dt.days,
        np.nan,
    )
    out["days_open_as_of_snapshot"] = np.where(
        out["is_open"] & out["engage_date"].notna(),
        (SNAPSHOT_DATE - out["engage_date"]).dt.days,
        np.nan,
    )
    out["training_closed"] = out["is_closed"]
    out["scoring_population"] = out["is_open"]
    out["target_won"] = np.where(out["is_closed"], out["is_won"].astype(int), np.nan)

    columns = [
        "opportunity_id",
        "sales_agent_id",
        "sales_agent",
        "product_id",
        "product",
        "product_raw",
        "account_id",
        "account",
        "deal_stage",
        "engage_date",
        "close_date",
        "close_value",
        "is_won",
        "is_lost",
        "is_closed",
        "is_open",
        "is_engaging",
        "is_prospecting",
        "has_account",
        "has_engage_date",
        "has_close_date",
        "has_close_value",
        "snapshot_date",
        "days_to_close",
        "days_open_as_of_snapshot",
        "training_closed",
        "scoring_population",
        "target_won",
    ]
    return out[columns].sort_values("opportunity_id").reset_index(drop=True)


def build_enriched(
    pipeline: pd.DataFrame,
    accounts: pd.DataFrame,
    products: pd.DataFrame,
    sales_teams: pd.DataFrame,
) -> pd.DataFrame:
    out = pipeline.merge(
        accounts.drop(columns=["account"]),
        on="account_id",
        how="left",
        validate="many_to_one",
    )
    out = out.merge(
        products.drop(columns=["product"]),
        on="product_id",
        how="left",
        validate="many_to_one",
    )
    out = out.merge(
        sales_teams.drop(columns=["sales_agent"]),
        on="sales_agent_id",
        how="left",
        validate="many_to_one",
    )
    out["estimated_deal_value"] = out["sales_price"]
    out["account_known"] = out["account_id"].notna() & out["sector"].notna()
    out["product_known"] = out["product_id"].notna() & out["sales_price"].notna()
    out["sales_agent_known"] = out["sales_agent_id"].notna() & out["manager"].notna()
    return out


def build_training_table(enriched: pd.DataFrame) -> pd.DataFrame:
    feature_columns = [
        "opportunity_id",
        "target_won",
        "sales_agent_id",
        "sales_agent",
        "manager_id",
        "manager",
        "regional_office",
        "product_id",
        "product",
        "series",
        "sales_price",
        "account_id",
        "account",
        "sector",
        "revenue",
        "revenue_band",
        "employees",
        "employee_band",
        "office_location",
        "is_subsidiary",
        "account_age_years_as_of_snapshot",
        "has_account",
        "account_known",
        "product_known",
        "sales_agent_known",
    ]
    out = enriched.loc[enriched["training_closed"], feature_columns].copy()
    out["target_won"] = out["target_won"].astype("Int64")
    return out.reset_index(drop=True)


def build_scoring_table(enriched: pd.DataFrame) -> pd.DataFrame:
    scoring_columns = [
        "opportunity_id",
        "deal_stage",
        "sales_agent_id",
        "sales_agent",
        "manager_id",
        "manager",
        "regional_office",
        "product_id",
        "product",
        "series",
        "sales_price",
        "estimated_deal_value",
        "account_id",
        "account",
        "sector",
        "revenue",
        "revenue_band",
        "employees",
        "employee_band",
        "office_location",
        "is_subsidiary",
        "account_age_years_as_of_snapshot",
        "engage_date",
        "snapshot_date",
        "days_open_as_of_snapshot",
        "has_account",
        "has_engage_date",
        "account_known",
        "product_known",
        "sales_agent_known",
    ]
    return enriched.loc[enriched["scoring_population"], scoring_columns].reset_index(drop=True)


def build_quality_report(
    raw: dict[str, pd.DataFrame],
    accounts: pd.DataFrame,
    products: pd.DataFrame,
    sales_teams: pd.DataFrame,
    pipeline: pd.DataFrame,
    enriched: pd.DataFrame,
    training: pd.DataFrame,
    scoring: pd.DataFrame,
) -> dict[str, object]:
    stage_counts = pipeline["deal_stage"].value_counts().sort_index().to_dict()
    report: dict[str, object] = {
        "snapshot_date": SNAPSHOT_DATE.strftime("%Y-%m-%d"),
        "raw_rows": {name: int(len(df)) for name, df in raw.items()},
        "processed_rows": {
            "dim_accounts": int(len(accounts)),
            "dim_products": int(len(products)),
            "dim_sales_teams": int(len(sales_teams)),
            "fact_sales_pipeline": int(len(pipeline)),
            "opportunities_enriched": int(len(enriched)),
            "training_closed_opportunities": int(len(training)),
            "open_pipeline_for_scoring": int(len(scoring)),
        },
        "deal_stage_counts": {str(k): int(v) for k, v in stage_counts.items()},
        "quality_checks": {
            "duplicate_accounts": int(accounts["account_id"].duplicated().sum()),
            "duplicate_products": int(products["product_id"].duplicated().sum()),
            "duplicate_sales_agents": int(sales_teams["sales_agent_id"].duplicated().sum()),
            "duplicate_opportunities": int(pipeline["opportunity_id"].duplicated().sum()),
            "unknown_product_after_canonicalization": int((~enriched["product_known"]).sum()),
            "unknown_sales_agent_after_join": int((~enriched["sales_agent_known"]).sum()),
            "open_rows_missing_account": int(scoring["account_known"].eq(False).sum()),
            "closed_rows_missing_account": int(
                enriched.loc[enriched["training_closed"], "account_known"].eq(False).sum()
            ),
        },
        "leakage_policy": {
            "training_table_excludes": ["deal_stage", "engage_date", "close_date", "close_value"],
            "scoring_table_excludes": ["close_date", "close_value", "target_won"],
            "allowed_status_for_scoring": ["prospecting", "engaging"],
        },
    }
    return report


def validate_outputs(
    accounts: pd.DataFrame,
    products: pd.DataFrame,
    sales_teams: pd.DataFrame,
    pipeline: pd.DataFrame,
    enriched: pd.DataFrame,
    training: pd.DataFrame,
    scoring: pd.DataFrame,
) -> None:
    if accounts["account_id"].duplicated().any():
        raise ValueError("Duplicate account_id found after ETL")
    if products["product_id"].duplicated().any():
        raise ValueError("Duplicate product_id found after ETL")
    if sales_teams["sales_agent_id"].duplicated().any():
        raise ValueError("Duplicate sales_agent_id found after ETL")
    if pipeline["opportunity_id"].duplicated().any():
        raise ValueError("Duplicate opportunity_id found after ETL")
    if len(enriched) != len(pipeline):
        raise ValueError("Enriched table row count changed during joins")
    if enriched["product_known"].eq(False).any():
        unknown = enriched.loc[~enriched["product_known"], "product"].dropna().unique().tolist()
        raise ValueError(f"Unknown products after canonicalization: {unknown}")
    if enriched["sales_agent_known"].eq(False).any():
        unknown = enriched.loc[~enriched["sales_agent_known"], "sales_agent"].dropna().unique().tolist()
        raise ValueError(f"Unknown sales agents after join: {unknown}")
    if len(training) != int(pipeline["training_closed"].sum()):
        raise ValueError("Training table row count does not match closed opportunities")
    if len(scoring) != int(pipeline["scoring_population"].sum()):
        raise ValueError("Scoring table row count does not match open opportunities")
    leakage_training_cols = {"deal_stage", "engage_date", "close_date", "close_value"}
    if leakage_training_cols.intersection(training.columns):
        raise ValueError("Training table contains leakage columns")
    leakage_scoring_cols = {"close_date", "close_value", "target_won"}
    if leakage_scoring_cols.intersection(scoring.columns):
        raise ValueError("Scoring table contains outcome columns")


def run_etl(source_dir: Path, raw_dir: Path, processed_dir: Path) -> dict[str, object]:
    copy_raw_files(source_dir, raw_dir)
    raw = load_raw(raw_dir)

    accounts = standardize_accounts(raw["accounts"])
    products = standardize_products(raw["products"])
    sales_teams = standardize_sales_teams(raw["sales_teams"])
    pipeline = standardize_pipeline(raw["sales_pipeline"])
    enriched = build_enriched(pipeline, accounts, products, sales_teams)
    training = build_training_table(enriched)
    scoring = build_scoring_table(enriched)

    validate_outputs(accounts, products, sales_teams, pipeline, enriched, training, scoring)
    report = build_quality_report(raw, accounts, products, sales_teams, pipeline, enriched, training, scoring)

    processed_dir.mkdir(parents=True, exist_ok=True)
    write_csv(accounts, processed_dir / "dim_accounts.csv")
    write_csv(products, processed_dir / "dim_products.csv")
    write_csv(sales_teams, processed_dir / "dim_sales_teams.csv")
    write_csv(pipeline, processed_dir / "fact_sales_pipeline.csv")
    write_csv(enriched, processed_dir / "opportunities_enriched.csv")
    write_csv(training, processed_dir / "training_closed_opportunities.csv")
    write_csv(scoring, processed_dir / "open_pipeline_for_scoring.csv")
    (processed_dir / "etl_quality_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Challenge 003 CSV ETL.")
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=DEFAULT_SOURCE_DIR,
        help="Directory containing raw Kaggle CSV files. Defaults to project data/raw.",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "raw",
        help="Destination directory for immutable raw copies.",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "processed",
        help="Destination directory for standardized outputs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = run_etl(
        source_dir=args.source_dir.resolve(),
        raw_dir=args.raw_dir.resolve(),
        processed_dir=args.processed_dir.resolve(),
    )
    print(json.dumps(report, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
