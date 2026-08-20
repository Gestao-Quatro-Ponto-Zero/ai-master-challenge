"""Orquestração de ponta a ponta: carrega dados, calcula p̂_produto, a
distribuição de referência de SCORE, e pontua todas as oportunidades
abertas — o que a API, a exportação CSV e a validação consomem.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import confianca as confianca_mod
from . import constants, estado as estado_mod, explicacao, model, reference, shrinkage
from .repository import Dataset, load_dataset


@dataclass(frozen=True)
class ScoredPipeline:
    dataset: Dataset
    as_of: pd.Timestamp
    ctx: model.ScoringContext
    ref: reference.ReferenceDistribution
    ages_won_ordenadas: list[float]
    scored: pd.DataFrame


def build_scoring_context(dataset: Dataset) -> model.ScoringContext:
    closed = dataset.pipeline[
        dataset.pipeline["deal_stage"].isin(constants.DEAL_STAGES_FECHADOS)
    ]
    counts = shrinkage.product_group_counts(closed)
    p_hat_by_product = {
        produto: shrinkage.p_hat_produto(produto, counts)
        for produto in constants.PRECO_TABELA
    }
    return model.ScoringContext(p_hat_by_product=p_hat_by_product)


def _age_days(row: pd.Series, as_of: pd.Timestamp) -> float | None:
    if row["deal_stage"] != "Engaging" or pd.isna(row["engage_date"]):
        return None
    return float((as_of - row["engage_date"]).days)


def _won_ages(dataset: Dataset) -> list[float]:
    won = dataset.pipeline[dataset.pipeline["deal_stage"] == "Won"].copy()
    ages = (won["close_date"] - won["engage_date"]).dt.days.astype(float).tolist()
    ages.sort()
    return ages


def score_row(
    ctx: model.ScoringContext,
    ref: reference.ReferenceDistribution,
    ages_won_ordenadas: list[float],
    product: str,
    stage: str,
    age_days: float | None,
    has_account: bool,
    porte: str | None,
) -> dict:
    """Pontua uma única oportunidade — usado tanto no lote quanto na
    pontuação avulsa (endpoint /score)."""
    componentes = model.score_componentes(ctx, product, stage, age_days, porte)
    score = ref.percentil(componentes.prioridade)
    nivel_confianca = confianca_mod.confianca(stage, has_account, age_days)
    estado_key = estado_mod.estado(nivel_confianca, score)
    plano = explicacao.plano_de_acao(
        estado_key,
        stage,
        has_account,
        age_days,
        nivel_confianca,
        componentes,
        ages_won_ordenadas,
    )
    return {
        "p_hat": componentes.p_hat,
        "valor": componentes.valor,
        "urgencia": componentes.urgencia,
        "prioridade": componentes.prioridade,
        "score": score,
        "confianca": nivel_confianca,
        "confianca_label": confianca_mod.confianca_label(nivel_confianca),
        "razao_confianca": confianca_mod.razao_confianca(stage, has_account, age_days),
        "estado": estado_key,
        "estado_label": estado_mod.estado_label(estado_key),
        "plano_de_acao": plano,
        "plano_de_acao_passos": explicacao.plano_de_acao_passos(estado_key, has_account, age_days),
    }


def score_open_pipeline(
    dataset: Dataset,
    ctx: model.ScoringContext,
    ref: reference.ReferenceDistribution,
    ages_won_ordenadas: list[float],
    as_of: pd.Timestamp,
) -> pd.DataFrame:
    """Pontua as oportunidades abertas (Prospecting + Engaging)."""
    open_deals = dataset.pipeline[
        dataset.pipeline["deal_stage"].isin(constants.DEAL_STAGES_ABERTOS)
    ].copy()

    records: list[dict] = []
    for _, row in open_deals.iterrows():
        age_days = _age_days(row, as_of)
        has_account = bool(row.get("account")) and not pd.isna(row.get("account"))
        porte = constants.classificar_porte(row.get("employees"))

        result = score_row(
            ctx, ref, ages_won_ordenadas,
            product=row["product"],
            stage=row["deal_stage"],
            age_days=age_days,
            has_account=has_account,
            porte=porte,
        )

        records.append(
            {
                "opportunity_id": row["opportunity_id"],
                "sales_agent": row["sales_agent"],
                "manager": row.get("manager"),
                "regional_office": row.get("regional_office"),
                "product": row["product"],
                "account": row.get("account") if has_account else None,
                "sector": row.get("sector"),
                "employees": row.get("employees"),
                "porte": porte,
                "deal_stage": row["deal_stage"],
                "engage_date": row.get("engage_date"),
                "age_days": age_days,
                **result,
            }
        )

    return pd.DataFrame.from_records(records)


def load_and_score(data_dir: str, as_of: pd.Timestamp | None = None) -> ScoredPipeline:
    dataset = load_dataset(data_dir)
    resolved_as_of = as_of if as_of is not None else dataset.as_of_default

    ctx = build_scoring_context(dataset)
    ref = reference.build_reference_distribution(dataset, ctx)
    ages_won_ordenadas = _won_ages(dataset)

    scored = score_open_pipeline(dataset, ctx, ref, ages_won_ordenadas, resolved_as_of)

    return ScoredPipeline(
        dataset=dataset,
        as_of=resolved_as_of,
        ctx=ctx,
        ref=ref,
        ages_won_ordenadas=ages_won_ordenadas,
        scored=scored,
    )
