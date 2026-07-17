"""Build the centralized datalake for the Lead Scorer.

Reads the 4 raw CRM extracts from data/raw/, applies cleaning rules,
and writes a single centralized store to data/lake/:

  - crm.db          SQLite database (dim_accounts, dim_products,
                    dim_sales_teams, fact_deals)
  - fact_deals.csv  The enriched, analysis-ready deals table
  - dim_*.csv       Cleaned dimension tables

Cleaning rules are documented inline and in docs/DATA_DICTIONARY.md.
Run:  python src/build_datalake.py
"""

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
LAKE = ROOT / "data" / "lake"

# The dataset is historical (2016-10 -> 2017-12). All "age" metrics are
# computed against this snapshot date instead of the real clock.
# It is derived below as max(engage_date, close_date) across the pipeline.


def load_raw():
    accounts = pd.read_csv(RAW / "accounts.csv")
    products = pd.read_csv(RAW / "products.csv")
    teams = pd.read_csv(RAW / "sales_teams.csv")
    pipeline = pd.read_csv(RAW / "sales_pipeline.csv")
    return accounts, products, teams, pipeline


def clean_accounts(accounts: pd.DataFrame) -> pd.DataFrame:
    acc = accounts.copy()
    acc["sector"] = acc["sector"].replace({"technolgy": "technology"})
    acc["office_location"] = acc["office_location"].replace(
        {"Philipines": "Philippines"}
    )
    acc = acc.rename(columns={"revenue": "revenue_musd"})
    return acc


def clean_pipeline(pipeline: pd.DataFrame) -> pd.DataFrame:
    pipe = pipeline.copy()
    # Product name mismatch between pipeline and catalog (2,000+ rows).
    pipe["product"] = pipe["product"].replace({"GTXPro": "GTX Pro"})
    pipe["engage_date"] = pd.to_datetime(pipe["engage_date"], errors="coerce")
    pipe["close_date"] = pd.to_datetime(pipe["close_date"], errors="coerce")
    # 1,425 open deals have no account in the CRM. Keep them, flag them.
    pipe["account_known"] = pipe["account"].notna()
    return pipe


def build_fact_deals(pipe, accounts, products, teams) -> pd.DataFrame:
    snapshot = max(pipe["engage_date"].max(), pipe["close_date"].max())

    fact = (
        pipe.merge(teams, on="sales_agent", how="left")
        .merge(products, on="product", how="left")
        .merge(accounts, on="account", how="left")
    )

    fact["is_open"] = fact["deal_stage"].isin(["Prospecting", "Engaging"])
    fact["is_won"] = fact["deal_stage"] == "Won"

    # Closed deals: how long the deal took. Open deals: how old it is now.
    fact["cycle_days"] = (fact["close_date"] - fact["engage_date"]).dt.days
    fact["age_days"] = (snapshot - fact["engage_date"]).dt.days.where(fact["is_open"])

    # Won deals close at ~list price (ratio 0.99-1.00 across all products),
    # so list price is the expected value for open deals.
    fact["expected_value"] = fact["close_value"].where(
        ~fact["is_open"], fact["sales_price"]
    )

    fact.attrs["snapshot_date"] = snapshot
    return fact


def write_lake(accounts, products, teams, fact):
    LAKE.mkdir(parents=True, exist_ok=True)

    accounts.to_csv(LAKE / "dim_accounts.csv", index=False)
    products.to_csv(LAKE / "dim_products.csv", index=False)
    teams.to_csv(LAKE / "dim_sales_teams.csv", index=False)
    fact.to_csv(LAKE / "fact_deals.csv", index=False)

    with sqlite3.connect(LAKE / "crm.db") as con:
        accounts.to_sql("dim_accounts", con, if_exists="replace", index=False)
        products.to_sql("dim_products", con, if_exists="replace", index=False)
        teams.to_sql("dim_sales_teams", con, if_exists="replace", index=False)
        fact_sql = fact.copy()
        for col in ["engage_date", "close_date"]:
            fact_sql[col] = fact_sql[col].dt.strftime("%Y-%m-%d")
        fact_sql.to_sql("fact_deals", con, if_exists="replace", index=False)


def validate(fact, products):
    assert fact["opportunity_id"].is_unique, "duplicate opportunity_id"
    assert len(fact) == 8800, f"expected 8800 deals, got {len(fact)}"
    unmatched = fact["sales_price"].isna().sum()
    assert unmatched == 0, f"{unmatched} deals with product not in catalog"
    no_team = fact["manager"].isna().sum()
    assert no_team == 0, f"{no_team} deals with agent not in sales_teams"
    open_deals = fact["is_open"].sum()
    won = fact["is_won"].sum()
    print(f"OK  {len(fact)} deals | {open_deals} open | {won} won")
    print(f"OK  snapshot date: {fact.attrs['snapshot_date'].date()}")


def main():
    accounts, products, teams, pipeline = load_raw()
    accounts = clean_accounts(accounts)
    pipe = clean_pipeline(pipeline)
    fact = build_fact_deals(pipe, accounts, products, teams)
    validate(fact, products)
    write_lake(accounts, products, teams, fact)
    print(f"OK  lake written to {LAKE}")


if __name__ == "__main__":
    main()
