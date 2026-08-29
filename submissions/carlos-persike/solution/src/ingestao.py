"""Carrega e limpa os 4 CSVs do CRM (accounts, products, sales_teams, sales_pipeline)."""
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

# Bug de dado real: o pipeline grafa "GTXPro" sem espaço, o catálogo usa "GTX Pro".
# Sem essa correção o join de preço perde 1.147 oportunidades silenciosamente.
CORRECAO_NOME_PRODUTO = {"GTXPro": "GTX Pro"}


def carregar_pipeline() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
    df["product"] = df["product"].replace(CORRECAO_NOME_PRODUTO)
    return df


def carregar_contas() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "accounts.csv")


def carregar_produtos() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "products.csv")


def carregar_time_vendas() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "sales_teams.csv")


def carregar_pipeline_enriquecido() -> pd.DataFrame:
    """Pipeline + conta + produto + time, já com os merges corrigidos."""
    pipeline = carregar_pipeline()
    contas = carregar_contas()
    produtos = carregar_produtos()
    time_vendas = carregar_time_vendas()

    df = (
        pipeline.merge(contas, on="account", how="left")
        .merge(produtos, on="product", how="left")
        .merge(time_vendas, on="sales_agent", how="left")
    )
    df["conta_desconhecida"] = df["account"].isna() | (df["account"] == "")
    return df
