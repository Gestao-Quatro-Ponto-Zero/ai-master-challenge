"""Fonte de dados. Hoje CSV; amanhã CRM (Salesforce/HubSpot) trocando só esta classe (interface DealRepository)."""
from __future__ import annotations

from pathlib import Path
from typing import Protocol

import pandas as pd


class DataValidationError(ValueError):
    pass


class DealRepository(Protocol):
    def load(self) -> pd.DataFrame: ...


REQUIRED = {
    "sales_pipeline.csv": {"opportunity_id", "sales_agent", "product", "deal_stage", "engage_date", "close_date",
                           "close_value"},
    "sales_teams.csv": {"sales_agent", "manager", "regional_office"},
    "products.csv": {"product", "series", "sales_price"},
}


class CsvDealRepository:
    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)

    def _read(self, name: str, **kw) -> pd.DataFrame:
        path = self.data_dir / name
        if not path.exists():
            raise DataValidationError(f"Arquivo ausente: {path}")
        df = pd.read_csv(path, **kw)
        missing = REQUIRED[name] - set(df.columns)
        if missing:
            raise DataValidationError(f"{name}: faltam colunas {sorted(missing)}")
        return df

    def load(self) -> pd.DataFrame:
        pipe = self._read("sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
        teams, prods = self._read("sales_teams.csv"), self._read("products.csv")

        pipe["product"] = pipe["product"].replace({"GTXPro": "GTX Pro"})  # nome diferente entre tabelas
        df = (pipe.merge(teams, on="sales_agent", how="left")
                  .merge(prods.rename(columns={"sales_price": "price"}), on="product", how="left"))
        df["won"] = df["deal_stage"].map({"Won": 1.0, "Lost": 0.0})  # NaN = ainda aberto
        self.validate(df)
        return df

    @staticmethod
    def validate(df: pd.DataFrame) -> None:
        if df["manager"].isna().any():
            raise DataValidationError("Há vendedores sem time em sales_teams.csv")
        if df["price"].isna().any():
            raise DataValidationError("Há produtos sem preço em products.csv")
        bad = df["engage_date"].notna() & df["close_date"].notna() & (df["close_date"] < df["engage_date"])
        if bad.any():
            raise DataValidationError(f"{int(bad.sum())} deals com close_date anterior a engage_date")
        closed = df["deal_stage"].isin(["Won", "Lost"])
        if (closed & df["close_date"].isna()).any():
            raise DataValidationError("Deals Won/Lost sem close_date")
        if not closed.any():
            raise DataValidationError("Sem deals fechados: impossível treinar")
