"""Curadoria dos dados: lê os CSVs brutos, corrige nomes, junta as tabelas e cria colunas derivadas.

Todas as funções são puras: devolvem um DataFrame novo e nunca alteram a entrada.
Uso: `python -m scorer.clean [--reference-date 2017-12-31]`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from . import config, facts

RAW_FILES = {
    "pipeline": "sales_pipeline.csv",
    "accounts": "accounts.csv",
    "products": "products.csv",
    "sales_teams": "sales_teams.csv",
}
DATE_COLUMNS = ["engage_date", "close_date"]
DEAL_COLUMNS = [
    "opportunity_id", "sales_agent", "manager", "regional_office", "product", "series", "sales_price",
    "account", "account_display", "has_account", "sector", "year_established", "revenue", "employees",
    "office_location", "subsidiary_of", "deal_stage", "is_open", "engage_date", "close_date",
    "close_value", "age_days", "cycle_days",
]


def load_raw(raw_dir) -> dict[str, pd.DataFrame]:
    """Lê os 4 CSVs brutos (pipeline com datas já convertidas)."""
    raw_dir = Path(raw_dir)
    raw = {name: pd.read_csv(raw_dir / file, encoding="utf-8") for name, file in RAW_FILES.items()}
    for column in DATE_COLUMNS:
        raw["pipeline"][column] = pd.to_datetime(raw["pipeline"][column])
    return raw


def normalize_products(pipeline: pd.DataFrame, catalog: pd.DataFrame) -> pd.DataFrame:
    """Troca o nome do produto pelo do catálogo ('GTXPro' -> 'GTX Pro') e exige que todos existam nele."""
    out = pipeline.copy()
    out["product"] = out["product"].replace(config.PRODUCT_NAME_MAP)
    missing = sorted(set(out["product"]) - set(catalog["product"]))
    assert not missing, f"produtos fora do catálogo: {missing}"
    return out


def normalize_sectors(accounts: pd.DataFrame) -> pd.DataFrame:
    """Corrige o setor com erro de digitação ('technolgy' -> 'technology')."""
    out = accounts.copy()
    out["sector"] = out["sector"].replace(config.SECTOR_MAP)
    return out


def join_all(
    pipeline: pd.DataFrame, products: pd.DataFrame, sales_teams: pd.DataFrame, accounts: pd.DataFrame
) -> pd.DataFrame:
    """Left joins do pipeline com produtos, times e contas; nenhuma linha pode ser perdida ou duplicada."""
    df = (
        pipeline.merge(products, on="product", how="left", validate="many_to_one")
        .merge(sales_teams, on="sales_agent", how="left", validate="many_to_one")
        .merge(accounts, on="account", how="left", validate="many_to_one")
    )
    assert len(df) == len(pipeline), f"o join mudou o número de linhas: {len(pipeline)} -> {len(df)}"
    assert df["sales_price"].notna().all(), "há deals sem sales_price (produto fora do catálogo)"
    assert df["manager"].notna().all(), "há deals sem manager (vendedor fora de sales_teams)"
    with_account = df["account"].notna()
    assert df.loc[with_account, "sector"].notna().all(), "há conta do pipeline ausente em accounts"
    return df


def add_derived(df: pd.DataFrame, reference_date) -> pd.DataFrame:
    """Acrescenta is_open, has_account, account_display, age_days e cycle_days.

    - `age_days`: dias entre `engage_date` e a data de referência, só para deal aberto com `engage_date`
      (NaN nos demais e quando o engajamento é posterior à referência).
    - `cycle_days`: dias entre engajamento e fechamento, só para Won e Lost.
    """
    ref = pd.Timestamp(reference_date)
    out = df.copy()
    out["is_open"] = out["deal_stage"].isin(config.OPEN_STAGES)
    out["has_account"] = out["account"].notna()
    out["account_display"] = out["account"].fillna(config.NO_ACCOUNT_LABEL)
    age = (ref - out["engage_date"]).dt.days.astype("float64")
    out["age_days"] = age.where(out["is_open"] & (age >= 0))
    cycle = (out["close_date"] - out["engage_date"]).dt.days.astype("float64")
    out["cycle_days"] = cycle.where(out["deal_stage"].isin(config.CLOSED_STAGES))
    return out


def build_deals(raw: dict[str, pd.DataFrame], reference_date) -> pd.DataFrame:
    """Pipeline completo: normaliza, junta e deriva. Entrada: saída de `load_raw`."""
    pipeline = normalize_products(raw["pipeline"], raw["products"])
    accounts = normalize_sectors(raw["accounts"])
    joined = join_all(pipeline, raw["products"], raw["sales_teams"], accounts)
    return add_derived(joined, reference_date)[DEAL_COLUMNS]


def save_deals(deals: pd.DataFrame, path) -> None:
    """Grava o CSV em UTF-8, com quebra de linha LF e datas ISO (bytes iguais a cada execução)."""
    deals.to_csv(path, index=False, encoding="utf-8", lineterminator="\n", date_format="%Y-%m-%d")


def load_deals(path=None) -> pd.DataFrame:
    """Lê o `deals.csv` gerado, devolvendo as datas como datetime."""
    return pd.read_csv(path or config.DEALS_CSV, encoding="utf-8", parse_dates=DATE_COLUMNS)


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Limpa os CSVs brutos e grava deals.csv e facts.json.")
    parser.add_argument("--reference-date", default=config.DEFAULT_REFERENCE_DATE)
    parser.add_argument("--raw-dir", default=config.RAW_DIR)
    parser.add_argument("--out-dir", default=config.PROCESSED_DIR)
    args = parser.parse_args(argv)

    raw = load_raw(args.raw_dir)
    deals = build_deals(raw, args.reference_date)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    save_deals(deals, out_dir / "deals.csv")
    facts_path = facts.write_facts(raw, deals, args.reference_date, out_dir / "facts.json")

    print(f"deals.csv: {len(deals)} linhas, {len(deals.columns)} colunas -> {out_dir / 'deals.csv'}")
    print(f"facts.json -> {facts_path}")
    print(f"data de referência: {args.reference_date}; deals abertos: {int(deals['is_open'].sum())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
