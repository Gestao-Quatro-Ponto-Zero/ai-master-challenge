"""Carrega e limpa as 4 tabelas do CRM num único DataFrame de oportunidades."""
from pathlib import Path

import pandas as pd

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "data"

# Problemas de qualidade encontrados na exploração (ver process-log/analysis)
PRODUCT_FIXES = {"GTXPro": "GTX Pro"}  # pipeline usa "GTXPro", catálogo usa "GTX Pro"
SECTOR_FIXES = {"technolgy": "technology"}


def load(data_dir=DEFAULT_DATA_DIR):
    data_dir = Path(data_dir)
    pipeline = pd.read_csv(data_dir / "sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
    accounts = pd.read_csv(data_dir / "accounts.csv")
    products = pd.read_csv(data_dir / "products.csv")
    teams = pd.read_csv(data_dir / "sales_teams.csv")

    pipeline["product"] = pipeline["product"].replace(PRODUCT_FIXES)
    accounts["sector"] = accounts["sector"].replace(SECTOR_FIXES)

    deals = (
        pipeline.merge(teams, on="sales_agent", how="left")
        .merge(products, on="product", how="left")
        .merge(accounts, on="account", how="left")
    )
    missing_price = deals["sales_price"].isna()
    if missing_price.any():
        unknown = sorted(deals.loc[missing_price, "product"].unique())
        raise ValueError(f"Produtos sem preço no catálogo: {unknown}")
    return deals, teams


def reference_date(deals):
    """Último evento registrado no CRM — usado como 'hoje' por padrão."""
    return max(deals["close_date"].max(), deals["engage_date"].max())
