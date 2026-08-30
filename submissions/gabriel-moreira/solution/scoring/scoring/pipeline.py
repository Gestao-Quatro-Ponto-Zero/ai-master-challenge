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


def fechados(dataset: Dataset) -> pd.DataFrame:
    """Os 6.711 negócios com desfecho OBSERVADO — toda linha `Won`/`Lost`
    do CSV. População única de calibração: alimenta a taxa de vitória por
    produto, o prior de encolhimento de p̂_produto, os priors de fit, as
    curvas de idade (`p_ganho`, `risco`) e a censura em 138 dias.

    Era duas funções (`fechados_organicos` / `fechados_calibracao`) enquanto
    o expurgo de 200 dias existia: as curvas de idade tinham de ser
    protegidas dos 653 rótulos que nós mesmos atribuíamos por idade, sob
    pena de o sistema aprender "negócio velho perde" da própria régua. Sem
    desfecho inventado, a separação perde a razão de existir — não há
    subconjunto a proteger de nada (docs/decisions-log.md, 2026-08-29).
    """
    return dataset.pipeline[dataset.pipeline["deal_stage"].isin(constants.DEAL_STAGES_FECHADOS)]


def build_scoring_context(dataset: Dataset) -> model.ScoringContext:
    closed = fechados(dataset)
    counts = shrinkage.product_group_counts(closed)
    produto_stats = shrinkage.level_stats(counts, constants.GLOBAL_WIN_RATE)
    p_hat_by_product = {
        produto: shrinkage.p_hat_produto(produto, counts, k=produto_stats.k)
        for produto in constants.PRECO_TABELA
    }
    product_closed_counts = {
        produto: group.n for produto, group in counts.items()
    }
    return model.ScoringContext(
        p_hat_by_product=p_hat_by_product,
        ages_won_ordenadas=_won_ages(dataset),
        product_closed_counts=product_closed_counts,
    )


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
    has_sector: bool = False,
    has_team: bool = False,
) -> dict:
    """Pontua uma única oportunidade — usado tanto no lote quanto na
    pontuação avulsa (endpoint /score).

    `has_sector`/`has_team` alimentam apenas a completude de CONFIANÇA —
    o VALOR do setor não entra em lugar nenhum do score desde a remoção de
    `mult_setor` (2026-08-29, ver `constants.py`). A pontuação avulsa não
    tem conta nem vendedor reais, então usa o padrão (ausentes/None), o
    que é a leitura honesta de um "e se" sem cadastro.
    """
    componentes = model.score_componentes(ctx, product, stage, age_days, porte)
    score = ref.percentil(componentes.prioridade)

    completude_valor, campos_ausentes = confianca_mod.completude(
        stage=stage,
        has_account=has_account,
        has_employees=(porte is not None),
        has_sector=has_sector,
        has_team=has_team,
    )
    suporte_valor = confianca_mod.suporte(ctx, product, age_days)
    confianca_valor = confianca_mod.confianca(completude_valor, suporte_valor)
    sem_precedente_flag = confianca_mod.sem_precedente(ctx, age_days)
    razao = confianca_mod.razao_confianca(
        completude_valor, campos_ausentes, suporte_valor, sem_precedente_flag
    )

    estado_key = estado_mod.estado(score, confianca_valor, sem_precedente_flag)
    plano = explicacao.plano_de_acao(
        estado_key, razao, age_days, componentes, campos_ausentes, ages_won_ordenadas
    )
    passos = explicacao.plano_de_acao_passos(estado_key, has_account, campos_ausentes)
    fatores = explicacao.fatores_score(
        componentes, product, porte, has_account, stage, age_days
    )

    return {
        "p_hat": componentes.p_hat,
        "preco_tabela": componentes.preco_tabela,
        "valor": componentes.valor,
        "urgencia": componentes.urgencia,
        "prioridade": componentes.prioridade,
        "score": score,
        "confianca": confianca_valor,
        "completude": completude_valor,
        "suporte": suporte_valor,
        "sem_precedente": sem_precedente_flag,
        "razao_confianca": razao,
        "estado": estado_key,
        "estado_label": estado_mod.estado_label(estado_key),
        "plano_de_acao": plano,
        "plano_de_acao_passos": passos,
        "score_fatores": fatores,
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
        has_sector = has_account and not pd.isna(row.get("sector"))
        has_team = not pd.isna(row.get("manager"))

        result = score_row(
            ctx, ref, ages_won_ordenadas,
            product=row["product"],
            stage=row["deal_stage"],
            age_days=age_days,
            has_account=has_account,
            porte=porte,
            has_sector=has_sector,
            has_team=has_team,
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
