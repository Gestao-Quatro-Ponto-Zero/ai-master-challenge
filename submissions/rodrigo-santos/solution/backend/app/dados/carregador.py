"""
Carregamento e limpeza dos dados.

Este é o ÚNICO lugar que sabe de onde os dados vêm (hoje, CSVs na pasta
`dados/`). Para migrar para um banco de dados no futuro, basta reescrever
`carregar_deals()` mantendo as mesmas colunas de saída.

Estrutura das tabelas:

    accounts ←── sales_pipeline ──→ products
                       ↓
                  sales_teams
"""

from functools import lru_cache

import pandas as pd

from app import config

# Etapas do funil, como aparecem nos CSVs.
ETAPA_PROSPECCAO = "Prospecting"
ETAPA_NEGOCIACAO = "Engaging"
ETAPA_GANHO = "Won"
ETAPA_PERDIDO = "Lost"

ETAPAS_ABERTAS = [ETAPA_PROSPECCAO, ETAPA_NEGOCIACAO]
ETAPAS_FECHADAS = [ETAPA_GANHO, ETAPA_PERDIDO]

# Texto usado quando o deal não tem conta associada.
CONTA_NAO_INFORMADA = "Conta não informada"

# Correções de inconsistências conhecidas nos dados de origem.
CORRECOES_PRODUTO = {"GTXPro": "GTX Pro"}
CORRECOES_SETOR = {"technolgy": "technology"}


def _ler_csv(nome_arquivo: str, **kwargs) -> pd.DataFrame:
    """Lê um CSV da pasta de dados."""
    return pd.read_csv(config.PASTA_DADOS / nome_arquivo, **kwargs)


@lru_cache(maxsize=1)
def carregar_deals() -> pd.DataFrame:
    """
    Retorna todos os deals já limpos e enriquecidos com dados da conta,
    do produto e do time de vendas (uma linha por deal).

    O resultado fica em cache na memória: os CSVs são lidos só uma vez.
    """
    pipeline = _ler_csv("sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
    contas = _ler_csv("accounts.csv")
    produtos = _ler_csv("products.csv")
    times = _ler_csv("sales_teams.csv")

    # --- Limpeza -----------------------------------------------------------
    pipeline["product"] = pipeline["product"].replace(CORRECOES_PRODUTO)
    contas["sector"] = contas["sector"].replace(CORRECOES_SETOR)

    # --- Junção das tabelas -------------------------------------------------
    # "left" para não perder deals sem conta (muitos deals abertos não têm).
    deals = (
        pipeline
        .merge(contas[["account", "sector", "office_location", "revenue", "employees"]], on="account", how="left")
        .merge(produtos[["product", "series", "sales_price"]], on="product", how="left")
        .merge(times, on="sales_agent", how="left")
    )

    deals["account"] = deals["account"].fillna(CONTA_NAO_INFORMADA)
    deals["conta_informada"] = deals["account"] != CONTA_NAO_INFORMADA

    return deals


@lru_cache(maxsize=1)
def obter_data_referencia() -> pd.Timestamp:
    """
    Data considerada como "hoje" para calcular há quantos dias um deal está aberto.
    Usa config.DATA_REFERENCIA ou, se não definida, a maior data dos dados.
    """
    if config.DATA_REFERENCIA is not None:
        return pd.Timestamp(config.DATA_REFERENCIA)

    deals = carregar_deals()
    return max(deals["engage_date"].max(), deals["close_date"].max())
