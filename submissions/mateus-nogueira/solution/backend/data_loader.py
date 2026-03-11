"""
Data loader: reads CSVs, cleans, enriches, and pre-computes lookup tables.
All data is held in memory (dataset < 1MB total).
"""

import pandas as pd
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field


DATA_DIR = Path(__file__).parent.parent / "data"


@dataclass
class DataStore:
    """Singleton holding all processed data and pre-computed stats."""

    # Raw DataFrames
    df_accounts: pd.DataFrame = field(default_factory=pd.DataFrame)
    df_products: pd.DataFrame = field(default_factory=pd.DataFrame)
    df_teams: pd.DataFrame = field(default_factory=pd.DataFrame)
    df_pipeline: pd.DataFrame = field(default_factory=pd.DataFrame)

    # Enriched pipeline (joined with accounts, teams, products)
    df_enriched: pd.DataFrame = field(default_factory=pd.DataFrame)

    # Pre-computed lookup tables
    product_winrate: dict = field(default_factory=dict)
    product_sector_winrate: dict = field(default_factory=dict)
    agent_stats: dict = field(default_factory=dict)
    account_stats: dict = field(default_factory=dict)
    overall_winrate: float = 0.0
    avg_days_won: float = 0.0
    avg_days_lost: float = 0.0
    reference_date: pd.Timestamp = None

    # Revenue/employee percentiles for normalization
    revenue_min: float = 0.0
    revenue_max: float = 0.0
    employees_min: float = 0.0
    employees_max: float = 0.0

    # Agent stats ranges for normalization
    agent_wr_min: float = 0.0
    agent_wr_max: float = 0.0
    agent_avg_val_min: float = 0.0
    agent_avg_val_max: float = 0.0
    agent_volume_max: float = 0.0

    # Product price lookup
    product_prices: dict = field(default_factory=dict)

    # Filter options for the UI
    filter_agents: list = field(default_factory=list)
    filter_managers: list = field(default_factory=list)
    filter_regions: list = field(default_factory=list)


# Global singleton
store = DataStore()


def load_data():
    """Load all CSVs, clean, enrich, and pre-compute everything."""
    global store

    # --- 1. Read CSVs ---
    store.df_accounts = pd.read_csv(DATA_DIR / "accounts.csv")
    store.df_products = pd.read_csv(DATA_DIR / "products.csv")
    store.df_teams = pd.read_csv(DATA_DIR / "sales_teams.csv")
    store.df_pipeline = pd.read_csv(DATA_DIR / "sales_pipeline.csv")

    # --- 2. Clean data ---
    df_pipe = store.df_pipeline.copy()

    # Normalize product name: "GTXPro" -> "GTX Pro" (both pipeline and products)
    df_pipe["product"] = df_pipe["product"].replace("GTXPro", "GTX Pro")
    store.df_products["product"] = store.df_products["product"].replace("GTXPro", "GTX Pro")

    # Parse dates
    df_pipe["engage_date"] = pd.to_datetime(df_pipe["engage_date"], errors="coerce")
    df_pipe["close_date"] = pd.to_datetime(df_pipe["close_date"], errors="coerce")

    # Reference date = max close_date across all closed deals
    closed = df_pipe.dropna(subset=["close_date"])
    store.reference_date = closed["close_date"].max()

    # Compute days in pipeline for all deals
    df_pipe["days_in_pipeline"] = np.nan

    # For closed deals: close_date - engage_date
    mask_closed = df_pipe["close_date"].notna() & df_pipe["engage_date"].notna()
    df_pipe.loc[mask_closed, "days_in_pipeline"] = (
        df_pipe.loc[mask_closed, "close_date"] - df_pipe.loc[mask_closed, "engage_date"]
    ).dt.days

    # For active deals: reference_date - engage_date
    mask_active = df_pipe["close_date"].isna() & df_pipe["engage_date"].notna()
    df_pipe.loc[mask_active, "days_in_pipeline"] = (
        store.reference_date - df_pipe.loc[mask_active, "engage_date"]
    ).dt.days

    store.df_pipeline = df_pipe

    # --- 3. Enrich pipeline with joins ---
    df = df_pipe.copy()

    # Join with accounts
    df = df.merge(
        store.df_accounts[["account", "sector", "revenue", "employees", "office_location", "subsidiary_of"]],
        on="account",
        how="left",
    )

    # Join with sales teams
    df = df.merge(
        store.df_teams[["sales_agent", "manager", "regional_office"]],
        on="sales_agent",
        how="left",
    )

    # Join with products
    df = df.merge(
        store.df_products[["product", "series", "sales_price"]],
        on="product",
        how="left",
    )

    store.df_enriched = df

    # --- 4. Pre-compute lookup tables ---
    _compute_lookups()

    # --- 5. Store filter options ---
    store.filter_agents = sorted(store.df_teams["sales_agent"].unique().tolist())
    store.filter_managers = sorted(store.df_teams["manager"].unique().tolist())
    store.filter_regions = sorted(store.df_teams["regional_office"].unique().tolist())

    # Product prices
    store.product_prices = dict(
        zip(store.df_products["product"], store.df_products["sales_price"])
    )

    print(f"[DataLoader] Loaded {len(store.df_pipeline)} deals, "
          f"{len(store.df_accounts)} accounts, "
          f"{len(store.df_products)} products, "
          f"{len(store.df_teams)} agents")
    print(f"[DataLoader] Reference date: {store.reference_date.date()}")


def _compute_lookups():
    """Pre-compute win rates and stats from historical closed deals."""
    df = store.df_enriched
    closed = df[df["deal_stage"].isin(["Won", "Lost"])].copy()
    won = closed[closed["deal_stage"] == "Won"]
    lost = closed[closed["deal_stage"] == "Lost"]

    # Overall win rate
    store.overall_winrate = len(won) / len(closed) if len(closed) > 0 else 0.5

    # Avg days for Won and Lost
    won_days = won["days_in_pipeline"].dropna()
    lost_days = lost["days_in_pipeline"].dropna()
    store.avg_days_won = won_days.mean() if len(won_days) > 0 else 50
    store.avg_days_lost = lost_days.mean() if len(lost_days) > 0 else 40

    # --- Product win rate ---
    product_groups = closed.groupby("product")["deal_stage"].apply(
        lambda x: (x == "Won").sum() / len(x)
    )
    store.product_winrate = product_groups.to_dict()

    # --- Product × Sector win rate ---
    # Only compute for combos with enough data (>= 5 deals)
    combo = closed.dropna(subset=["sector"]).groupby(["product", "sector"])
    for (prod, sect), group in combo:
        if len(group) >= 5:
            wr = (group["deal_stage"] == "Won").sum() / len(group)
            store.product_sector_winrate[(prod, sect)] = wr

    # --- Agent stats ---
    agent_closed = closed.groupby("sales_agent")
    for agent, group in agent_closed:
        total = len(group)
        wins = (group["deal_stage"] == "Won").sum()
        won_values = group.loc[group["deal_stage"] == "Won", "close_value"]
        avg_val = won_values.mean() if len(won_values) > 0 else 0

        store.agent_stats[agent] = {
            "win_rate": wins / total if total > 0 else 0.5,
            "total_deals": total,
            "won_deals": wins,
            "avg_deal_value": avg_val,
            "total_won_value": won_values.sum(),
        }

    # Agent normalization ranges
    if store.agent_stats:
        wrs = [s["win_rate"] for s in store.agent_stats.values()]
        vals = [s["avg_deal_value"] for s in store.agent_stats.values() if s["avg_deal_value"] > 0]
        vols = [s["total_deals"] for s in store.agent_stats.values()]
        store.agent_wr_min = min(wrs) if wrs else 0.5
        store.agent_wr_max = max(wrs) if wrs else 0.7
        store.agent_avg_val_min = min(vals) if vals else 0
        store.agent_avg_val_max = max(vals) if vals else 1
        store.agent_volume_max = max(vols) if vols else 1

    # --- Account stats ---
    account_closed = closed.dropna(subset=["account"]).groupby("account")
    for acct, group in account_closed:
        total = len(group)
        wins = (group["deal_stage"] == "Won").sum()
        won_values = group.loc[group["deal_stage"] == "Won", "close_value"]

        store.account_stats[acct] = {
            "win_rate": wins / total if total > 0 else 0.5,
            "total_deals": total,
            "won_deals": wins,
            "avg_deal_value": won_values.mean() if len(won_values) > 0 else 0,
        }

    # Revenue/employee ranges from accounts
    store.revenue_min = store.df_accounts["revenue"].min()
    store.revenue_max = store.df_accounts["revenue"].max()
    store.employees_min = store.df_accounts["employees"].min()
    store.employees_max = store.df_accounts["employees"].max()
