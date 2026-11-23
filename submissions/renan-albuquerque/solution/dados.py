"""Carrega os 4 CSVs do CRM, corrige problemas conhecidos e junta tudo numa tabela só."""

from pathlib import Path

import pandas as pd

PASTA_DADOS = Path(__file__).parent / "data"

# Os dados vão de out/2016 a dez/2017. Se usarmos a data de hoje, todo deal
# parece ter 8+ anos. Então "hoje", para a ferramenta, é o último dia do dataset.
DATA_REFERENCIA = pd.Timestamp("2017-12-31")

ESTAGIOS_ABERTOS = ["Prospecting", "Engaging"]
ESTAGIOS_FECHADOS = ["Won", "Lost"]


def carregar_dados(pasta: Path = PASTA_DADOS) -> pd.DataFrame:
    accounts = pd.read_csv(pasta / "accounts.csv")
    products = pd.read_csv(pasta / "products.csv")
    teams = pd.read_csv(pasta / "sales_teams.csv")
    pipeline = pd.read_csv(
        pasta / "sales_pipeline.csv", parse_dates=["engage_date", "close_date"]
    )

    # Correção 1: o pipeline escreve "GTXPro", o catálogo escreve "GTX Pro".
    # Sem isso, o join perde o preço desses deals sem dar erro nenhum.
    pipeline["product"] = pipeline["product"].replace({"GTXPro": "GTX Pro"})

    # Correção 2: erros de digitação no cadastro de contas.
    accounts["sector"] = accounts["sector"].replace({"technolgy": "technology"})
    accounts["office_location"] = accounts["office_location"].replace(
        {"Philipines": "Philippines"}
    )

    # validate= faz o pandas reclamar se algum join duplicar linhas.
    df = (
        pipeline.merge(products, on="product", how="left", validate="many_to_one")
        .merge(teams, on="sales_agent", how="left", validate="many_to_one")
        .merge(accounts, on="account", how="left", validate="many_to_one")
    )

    # Checagem: todo deal precisa ter preço e vendedor depois dos joins.
    sem_preco = df["sales_price"].isna().sum()
    sem_vendedor = df["manager"].isna().sum()
    if sem_preco or sem_vendedor:
        raise ValueError(
            f"Join incompleto: {sem_preco} deals sem preço, {sem_vendedor} sem vendedor"
        )

    # Dias desde que o deal entrou em Engaging (vazio para Prospecting).
    df["idade_dias"] = (DATA_REFERENCIA - df["engage_date"]).dt.days
    # Quanto tempo os deals fechados levaram para fechar.
    df["duracao_dias"] = (df["close_date"] - df["engage_date"]).dt.days
    return df


def separar(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devolve (histórico de deals fechados, pipeline aberto)."""
    fechados = df[df["deal_stage"].isin(ESTAGIOS_FECHADOS)].copy()
    abertos = df[df["deal_stage"].isin(ESTAGIOS_ABERTOS)].copy()
    return fechados, abertos


if __name__ == "__main__":
    # Rode `python dados.py` para conferir se os dados carregaram certo.
    df = carregar_dados()
    fechados, abertos = separar(df)
    print(f"Total de deals: {len(df)}")
    print(f"Fechados (histórico): {len(fechados)} | Abertos (pipeline): {len(abertos)}")
    print(f"Abertos por estágio: {abertos['deal_stage'].value_counts().to_dict()}")
    print(f"Abertos sem conta: {abertos['account'].isna().sum()}")
    print(f"Maior duração de um deal fechado: {fechados['duracao_dias'].max()} dias")
    print(f"Produtos: {sorted(df['product'].unique())}")
