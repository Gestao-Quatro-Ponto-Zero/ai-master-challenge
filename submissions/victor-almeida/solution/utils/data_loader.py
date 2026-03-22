"""
Carregamento e preparacao dos dados do Lead Scorer.

Carrega os 4 CSVs do dataset CRM Sales Predictive Analytics,
aplica normalizacoes e enriquece o pipeline com LEFT JOINs.
"""

import os

import pandas as pd

from utils.constants import ACTIVE_STAGES, REFERENCE_DATE


# ---------------------------------------------------------------------------
# Funcoes de carregamento individual
# ---------------------------------------------------------------------------


def load_accounts(data_dir: str = "data") -> pd.DataFrame:
    """Carrega accounts.csv e normaliza typo de setor.

    Normaliza 'technolgy' -> 'technology' na coluna sector.
    """
    path = os.path.join(data_dir, "accounts.csv")
    df = pd.read_csv(path)
    df["sector"] = df["sector"].replace("technolgy", "technology")
    return df


def load_products(data_dir: str = "data") -> pd.DataFrame:
    """Carrega products.csv sem transformacoes."""
    path = os.path.join(data_dir, "products.csv")
    return pd.read_csv(path)


def load_sales_teams(data_dir: str = "data") -> pd.DataFrame:
    """Carrega sales_teams.csv sem transformacoes."""
    path = os.path.join(data_dir, "sales_teams.csv")
    return pd.read_csv(path)


def load_pipeline(data_dir: str = "data") -> pd.DataFrame:
    """Carrega sales_pipeline.csv com normalizacoes.

    Transformacoes aplicadas:
    - Normaliza produto: 'GTXPro' -> 'GTX Pro'
    - Converte engage_date e close_date para datetime64
    - Adiciona coluna is_active (True para Prospecting/Engaging)
    - Adiciona coluna days_in_stage (dias desde engage_date ate REFERENCE_DATE)
    """
    path = os.path.join(data_dir, "sales_pipeline.csv")
    df = pd.read_csv(path)

    # Normalizar produto
    df["product"] = df["product"].replace("GTXPro", "GTX Pro")

    # Converter datas
    df["engage_date"] = pd.to_datetime(df["engage_date"])
    df["close_date"] = pd.to_datetime(df["close_date"])

    # Colunas derivadas
    df["is_active"] = df["deal_stage"].isin(ACTIVE_STAGES)
    df["days_in_stage"] = (REFERENCE_DATE - df["engage_date"]).dt.days

    return df


# ---------------------------------------------------------------------------
# Funcao principal
# ---------------------------------------------------------------------------


def load_data(data_dir: str = "data") -> dict[str, pd.DataFrame]:
    """Carrega e prepara todos os DataFrames do Lead Scorer.

    Etapas:
    1. Carrega os 4 CSVs
    2. Aplica normalizacoes (produto, setor)
    3. Converte datas e calcula colunas derivadas
    4. Enriquece pipeline com LEFT JOINs (products, accounts, sales_teams)

    Args:
        data_dir: Caminho para o diretorio com os CSVs.

    Returns:
        Dicionario com chaves: 'pipeline', 'accounts', 'products', 'sales_teams'.
    """
    accounts = load_accounts(data_dir)
    products = load_products(data_dir)
    sales_teams = load_sales_teams(data_dir)
    pipeline = load_pipeline(data_dir)

    # LEFT JOIN pipeline <- products ON product
    pipeline = pd.merge(
        pipeline,
        products[["product", "sales_price", "series"]],
        on="product",
        how="left",
    )

    # LEFT JOIN pipeline <- accounts ON account
    pipeline = pd.merge(
        pipeline,
        accounts[["account", "sector", "revenue", "employees", "office_location"]],
        on="account",
        how="left",
    )

    # LEFT JOIN pipeline <- sales_teams ON sales_agent
    pipeline = pd.merge(
        pipeline,
        sales_teams[["sales_agent", "manager", "regional_office"]],
        on="sales_agent",
        how="left",
    )

    return {
        "pipeline": pipeline,
        "accounts": accounts,
        "products": products,
        "sales_teams": sales_teams,
    }


# ---------------------------------------------------------------------------
# Funcoes auxiliares
# ---------------------------------------------------------------------------


def get_active_deals(pipeline) -> pd.DataFrame:
    """Retorna apenas deals ativos (Prospecting + Engaging).

    Args:
        pipeline: DataFrame do pipeline ou dict retornado por load_data().
    """
    if isinstance(pipeline, dict):
        pipeline = pipeline["pipeline"]
    return pipeline[pipeline["is_active"]].copy()


def get_reference_date() -> pd.Timestamp:
    """Retorna a data de referencia fixa: 2017-12-31."""
    return REFERENCE_DATE
