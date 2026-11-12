"""Carga, normalização, relatório de qualidade e recorte temporal do dataset de vendas."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

_TYPOS_SETOR = {"technolgy": "technology"}
_TYPOS_PAIS = {"Philipines": "Philippines"}


@dataclass
class Dados:
    pipeline: pd.DataFrame
    contas: pd.DataFrame
    produtos: pd.DataFrame
    times: pd.DataFrame
    qualidade: dict = field(default_factory=dict)


def carregar(pasta: str | Path) -> Dados:
    d = Path(pasta)

    p = pd.read_csv(d / "sales_pipeline.csv", parse_dates=["engage_date", "close_date"])
    pr = pd.read_csv(d / "products.csv")
    t = pd.read_csv(d / "sales_teams.csv")
    a = pd.read_csv(d / "accounts.csv")

    # corrige typos nas tabelas de referência
    contas = a.copy()
    setores_corrigidos = {}
    for typo, correto in _TYPOS_SETOR.items():
        if (contas["sector"] == typo).any():
            contas["sector"] = contas["sector"].replace(typo, correto)
            setores_corrigidos[typo] = correto

    paises_corrigidos = {}
    for typo, correto in _TYPOS_PAIS.items():
        if (contas["office_location"] == typo).any():
            contas["office_location"] = contas["office_location"].replace(typo, correto)
            paises_corrigidos[typo] = correto

    # resolução de apelidos de produto: chave sem espaços, caixa baixa
    pr["_k"] = pr["product"].str.replace(" ", "").str.lower()
    p["_k"] = p["product"].str.replace(" ", "").str.lower()

    pm = p.merge(
        pr[["_k", "product", "sales_price"]].rename(
            columns={"product": "_prod_cat", "sales_price": "valor_tabela"}
        ),
        on="_k",
        how="left",
    )
    pm["produto_crm"] = pm["product"]
    pm["produto"] = pm["_prod_cat"].fillna(pm["product"])

    # enriquece com gerente, região e setor
    pm = pm.merge(
        t[["sales_agent", "manager", "regional_office"]].rename(
            columns={"manager": "gerente", "regional_office": "regiao"}
        ),
        on="sales_agent",
        how="left",
    )
    pm = pm.merge(
        contas[["account", "sector"]].rename(columns={"sector": "setor"}),
        on="account",
        how="left",
    )

    alias_mask = pm["produto_crm"] != pm["_prod_cat"].fillna(pm["produto_crm"])
    apelidos = {
        r["produto_crm"]: r["_prod_cat"]
        for _, r in pm[alias_mask].drop_duplicates("produto_crm").iterrows()
    }
    sem_par = sorted(pm[pm["_prod_cat"].isna()]["produto_crm"].unique().tolist())

    pipeline = pm.drop(columns=["_k", "_prod_cat"])

    abertos = p[p["deal_stage"].isin(["Engaging", "Prospecting"])]
    qualidade = {
        "apelidos_de_produto": apelidos,
        "produtos_sem_par": sem_par,
        "setores_corrigidos": setores_corrigidos,
        "paises_corrigidos": paises_corrigidos,
        "total_linhas": len(pipeline),
        "abertos_sem_conta": int(abertos["account"].isna().sum()),
        "prospecting_sem_data": int(
            p[p["deal_stage"] == "Prospecting"]["engage_date"].isna().sum()
        ),
        "maior_data": str(p["close_date"].max().date()),
        "primeiro_fechamento": str(p["close_date"].min().date()),
        "vendedores_cadastro": int(t["sales_agent"].nunique()),
        "vendedores_com_deal": int(p["sales_agent"].nunique()),
        "vendedores_com_deal_aberto": int(abertos["sales_agent"].nunique()),
    }

    return Dados(pipeline=pipeline, contas=contas, produtos=pr.drop(columns=["_k"]), times=t, qualidade=qualidade)


def recortar(dados: Dados, hoje: pd.Timestamp) -> Dados:
    """Devolve o export que existiria em `hoje`: sem engajamentos nem fechamentos futuros."""
    p = dados.pipeline
    d = p[p["engage_date"].isna() | (p["engage_date"] < hoje)].copy()

    futuro = d["close_date"].notna() & (d["close_date"] >= hoje)
    d.loc[futuro, ["close_date", "close_value"]] = [pd.NaT, np.nan]
    d.loc[futuro, "deal_stage"] = "Engaging"

    # Prospecting sem data de engajamento não pode ser datado no passado
    if hoje <= p["close_date"].max():
        d = d[d["engage_date"].notna()]

    return Dados(
        pipeline=d.reset_index(drop=True),
        contas=dados.contas,
        produtos=dados.produtos,
        times=dados.times,
        qualidade=dados.qualidade,
    )
