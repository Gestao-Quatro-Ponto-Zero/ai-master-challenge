"""Carga e junção dos quatro CSVs em memória, atrás de um módulo repositório.

Correções de origem aplicadas no carregamento (não nos dados em disco):
`technolgy` -> `technology` em accounts.sector, e variantes de "GTXPro" ->
"GTX Pro" em sales_pipeline.product. Ver constants.SECTOR_CORRECTIONS /
PRODUCT_CORRECTIONS.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import constants


@dataclass(frozen=True)
class Dataset:
    """Snapshot imutável dos dados carregados e já unidos.

    `pipeline["reclassificado"]` marca as oportunidades que estavam em
    `Engaging` com idade >= `constants.IDADE_RECLASSIFICACAO_DIAS` em
    `as_of_default` e foram convertidas para `deal_stage = "Lost"` em
    memória (Requirement "Reclassificação de oportunidades com 200 dias ou
    mais"). `sales_pipeline.csv` no disco não é tocado — a coluna existe
    apenas neste DataFrame carregado.
    """

    pipeline: pd.DataFrame  # 8.800 linhas, uma por oportunidade
    accounts: pd.DataFrame
    products: pd.DataFrame
    sales_teams: pd.DataFrame
    as_of_default: pd.Timestamp

    @property
    def n_reclassificados(self) -> int:
        return int(self.pipeline["reclassificado"].sum())


def _clean_sector(sector: object) -> object:
    if not isinstance(sector, str):
        return sector
    return constants.SECTOR_CORRECTIONS.get(sector, sector)


def _clean_product(product: object) -> object:
    if not isinstance(product, str):
        return product
    normalized = constants.PRODUCT_CORRECTIONS.get(product, product)
    return normalized


def load_dataset(data_dir: str | Path) -> Dataset:
    """Carrega os quatro CSVs, aplica as correções de origem e junta tudo.

    `sales_pipeline` é o grão principal (uma linha por oportunidade); as
    demais tabelas entram por LEFT JOIN — uma oportunidade sem conta, ou um
    vendedor sem correspondência em sales_teams, continua presente com
    campos nulos, nunca é descartada.
    """
    data_dir = Path(data_dir)

    accounts = pd.read_csv(data_dir / "accounts.csv")
    accounts["sector"] = accounts["sector"].map(_clean_sector)

    products = pd.read_csv(data_dir / "products.csv")

    sales_teams = pd.read_csv(data_dir / "sales_teams.csv")

    pipeline = pd.read_csv(
        data_dir / "sales_pipeline.csv",
        parse_dates=["engage_date", "close_date"],
    )
    pipeline["product"] = pipeline["product"].map(_clean_product)

    merged = pipeline.merge(
        accounts, how="left", on="account", suffixes=("", "_account")
    )
    merged = merged.merge(
        products, how="left", on="product", suffixes=("", "_product")
    )
    merged = merged.merge(
        sales_teams, how="left", on="sales_agent", suffixes=("", "_team")
    )

    as_of_default = pd.Timestamp(merged["close_date"].max())
    merged = _reclassify_aged_deals(merged, as_of_default)

    return Dataset(
        pipeline=merged,
        accounts=accounts,
        products=products,
        sales_teams=sales_teams,
        as_of_default=as_of_default,
    )


def _reclassify_aged_deals(pipeline: pd.DataFrame, as_of_default: pd.Timestamp) -> pd.DataFrame:
    """Reclassifica como `Lost`, em memória, toda oportunidade `Engaging`
    com idade >= `constants.IDADE_RECLASSIFICACAO_DIAS` em `as_of_default`.

    A idade de reclassificação é fixada em `as_of_default` (a mesma data de
    referência usada para o funil aberto padrão) — não é recalculada por
    requisição, do mesmo modo que `as_of_default` em si não é. Oportunidade
    sem `engage_date` conhecida (Prospecting) nunca é reclassificada: idade
    desconhecida não é evidência de idade alta.
    """
    pipeline = pipeline.copy()
    idade_dias = (as_of_default - pipeline["engage_date"]).dt.days
    elegivel = pipeline["deal_stage"] == "Engaging"
    reclassificar = elegivel & idade_dias.notna() & (idade_dias >= constants.IDADE_RECLASSIFICACAO_DIAS)

    pipeline["reclassificado"] = reclassificar
    pipeline.loc[reclassificar, "deal_stage"] = "Lost"
    return pipeline


def unmatched_products(dataset: Dataset) -> list[str]:
    """Produtos em sales_pipeline sem correspondência em products.csv.

    Usado pelo teste de carga (task 1.5) — deve retornar lista vazia após
    a normalização de origem.
    """
    known = set(dataset.products["product"])
    seen = set(dataset.pipeline["product"].dropna().unique())
    return sorted(seen - known)
