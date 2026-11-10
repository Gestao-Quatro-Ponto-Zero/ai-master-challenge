"""Limpa e normaliza os 4 CSVs do CRM (data/raw/) e grava em data/clean/.

Rodar a partir de qualquer pasta:  python solution/data/clean.py
Depende só de pandas e numpy. Não há edição manual: toda correção está aqui.
As regras estão descritas em data/README.md.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
CLEAN = HERE / "clean"

# "Hoje" para o pipeline aberto: último dia com registro no dataset
# (último close_date = 2017-12-31; último engage_date = 2017-12-27).
REFERENCE_DATE = pd.Timestamp("2017-12-31")

PRODUCT_FIXES = {"GTXPro": "GTX Pro"}          # nome no pipeline ≠ catálogo
SECTOR_FIXES = {"technolgy": "technology"}     # erro de digitação na origem
SIZE_LABELS = ["pequena", "media", "grande"]   # tercis calculados sobre as 85 contas


def _strip(df: pd.DataFrame) -> pd.DataFrame:
    for c in df.columns:
        if df[c].dtype == object or pd.api.types.is_string_dtype(df[c]):
            df[c] = df[c].astype("string").str.strip()
    return df


def _terciles(s: pd.Series) -> tuple[pd.Series, list[float]]:
    cuts = s.quantile([1 / 3, 2 / 3]).tolist()
    band = pd.cut(s, [-np.inf, cuts[0], cuts[1], np.inf], labels=SIZE_LABELS)
    return band.astype("string"), cuts


def load_raw() -> dict[str, pd.DataFrame]:
    return {
        n: _strip(pd.read_csv(RAW / f"{n}.csv"))
        for n in ["accounts", "products", "sales_teams", "sales_pipeline"]
    }


def clean(raw: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], dict]:
    report: dict = {"reference_date": REFERENCE_DATE.date().isoformat(), "fixes": {}}

    # --- accounts ---------------------------------------------------------
    acc = raw["accounts"].copy()
    report["fixes"]["sector_renamed"] = int(acc["sector"].isin(SECTOR_FIXES).sum())
    acc["sector"] = acc["sector"].replace(SECTOR_FIXES)
    acc["parent_company"] = acc["subsidiary_of"].fillna(acc["account"])
    acc["revenue_band"], rev_cuts = _terciles(acc["revenue"])
    acc["employees_band"], emp_cuts = _terciles(acc["employees"])
    acc["company_age_years"] = REFERENCE_DATE.year - acc["year_established"]
    report["size_band_cuts"] = {
        "revenue_musd": [round(x, 2) for x in rev_cuts],
        "employees": [round(x, 1) for x in emp_cuts],
    }

    # --- products ---------------------------------------------------------
    prod = raw["products"].copy()

    # --- sales teams ------------------------------------------------------
    team = raw["sales_teams"].copy()

    # --- pipeline ---------------------------------------------------------
    pipe = raw["sales_pipeline"].copy()
    report["fixes"]["product_renamed"] = int(pipe["product"].isin(PRODUCT_FIXES).sum())
    pipe["product"] = pipe["product"].replace(PRODUCT_FIXES)
    for c in ["engage_date", "close_date"]:
        pipe[c] = pd.to_datetime(pipe[c], errors="raise")

    pipe["is_open"] = pipe["deal_stage"].isin(["Prospecting", "Engaging"])
    pipe["won"] = pd.Series(pd.NA, index=pipe.index, dtype="Int64")
    pipe.loc[pipe["deal_stage"] == "Won", "won"] = 1
    pipe.loc[pipe["deal_stage"] == "Lost", "won"] = 0
    pipe["has_account"] = pipe["account"].notna()
    pipe["cycle_days"] = (pipe["close_date"] - pipe["engage_date"]).dt.days.astype("Int64")
    pipe["days_since_engage"] = pd.Series(pd.NA, index=pipe.index, dtype="Int64")
    eng = pipe["deal_stage"] == "Engaging"
    pipe.loc[eng, "days_since_engage"] = (REFERENCE_DATE - pipe.loc[eng, "engage_date"]).dt.days

    # --- checagens de integridade (falha alto se a origem mudar) ----------
    assert pipe["opportunity_id"].is_unique, "opportunity_id duplicado"
    assert set(pipe["product"]) <= set(prod["product"]), "produto sem catálogo"
    assert set(pipe["sales_agent"]) <= set(team["sales_agent"]), "vendedor sem time"
    assert set(pipe["account"].dropna()) <= set(acc["account"]), "conta sem cadastro"
    closed = ~pipe["is_open"]
    assert pipe.loc[closed, ["account", "engage_date", "close_date"]].notna().all().all()
    assert (pipe.loc[closed, "close_date"] >= pipe.loc[closed, "engage_date"]).all()
    assert (pipe.loc[pipe["deal_stage"] == "Won", "close_value"] > 0).all()
    assert (pipe.loc[pipe["deal_stage"] == "Lost", "close_value"] == 0).all()
    assert pipe.loc[pipe["is_open"], ["close_date", "close_value"]].isna().all().all()
    assert pipe.loc[pipe["deal_stage"] == "Prospecting", "engage_date"].isna().all()
    assert pipe.loc[eng, "engage_date"].notna().all()
    assert pipe[["engage_date", "close_date"]].max().max() <= REFERENCE_DATE

    # --- tabela larga: 1 linha por oportunidade com tudo junto ------------
    deals = (
        pipe.merge(team, on="sales_agent", how="left", validate="m:1")
        .merge(prod, on="product", how="left", validate="m:1")
        .merge(
            acc[["account", "sector", "revenue", "employees", "revenue_band",
                 "employees_band", "office_location", "parent_company",
                 "year_established"]],
            on="account", how="left", validate="m:1",
        )
    )
    for c in ["employees", "year_established"]:
        deals[c] = deals[c].astype("Int64")
    deals["list_price"] = deals.pop("sales_price")
    won = deals["deal_stage"] == "Won"
    deals["price_ratio"] = np.where(won, deals["close_value"] / deals["list_price"], np.nan)
    deals["close_quarter"] = deals["close_date"].dt.to_period("Q").astype("string")

    report["counts"] = {
        "deals": int(len(deals)),
        "by_stage": deals["deal_stage"].value_counts().to_dict(),
        "open_without_account": int((deals["is_open"] & ~deals["has_account"]).sum()),
        "open": int(deals["is_open"].sum()),
        "agents_in_team": int(len(team)),
        "agents_with_deals": int(deals["sales_agent"].nunique()),
        "agents_without_deals": sorted(set(team["sales_agent"]) - set(deals["sales_agent"])),
        "accounts": int(len(acc)),
    }
    report["date_range"] = {
        "engage_min": deals["engage_date"].min().date().isoformat(),
        "engage_max": deals["engage_date"].max().date().isoformat(),
        "close_min": deals["close_date"].min().date().isoformat(),
        "close_max": deals["close_date"].max().date().isoformat(),
    }
    out = {"accounts": acc, "products": prod, "sales_teams": team,
           "sales_pipeline": pipe, "deals": deals}
    return out, report


def save(tables: dict[str, pd.DataFrame], report: dict) -> None:
    CLEAN.mkdir(exist_ok=True)
    for name, df in tables.items():
        df = df.copy()
        for c in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[c]):
                df[c] = df[c].dt.strftime("%Y-%m-%d")
        df.to_csv(CLEAN / f"{name}.csv", index=False, lineterminator="\n")
    (CLEAN / "cleaning_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    tables, rep = clean(load_raw())
    save(tables, rep)
    print(json.dumps(rep, indent=2, ensure_ascii=False))
