"""Reprodução de `mult_setor` em si (task 5.2) e auditoria de consistência
entre o funil aberto e a reconstrução da distribuição de referência (task
5.3) — lead-scoring spec, Requirement "Ajuste de desempenho produto×setor
sobre p̂".

A reprodução recalcula `mult_setor` a partir de `fechados_calibracao`,
independentemente do `ScoringContext` de produção, e confirma: uma célula
de amostra grande não aciona o teto de ±15% (o encolhimento, não o teto,
faz o trabalho de calar ruído — design.md); uma célula de amostra ínfima
produz `mult_setor` próximo de 1,0; nenhuma célula produz um multiplicador
fora de [MULT_SETOR_MIN, MULT_SETOR_MAX] (o que garante, por construção,
que `p̂_produto × mult_setor` nunca sai de
[0,85×p̂_produto, 1,15×p̂_produto] para nenhum produto).

A auditoria de consistência (mesmo padrão de `circularity_check.py`:
recomputar da fonte e comparar, não confiar por construção) recalcula
`mult_setor` de forma independente e confirma que bate, célula a célula,
com o que o `ScoringContext` de produção — o mesmo objeto compartilhado
por `pipeline.score_open_pipeline` e `reference.build_reference_
distribution` — realmente retorna.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from scoring import constants, setor
from scoring.model import ScoringContext
from scoring.repository import Dataset
from scoring.shrinkage import level_stats, p_hat_produto, product_group_counts


@dataclass(frozen=True)
class MultSetorReproduction:
    celula_grande_produto: str
    celula_grande_setor: str
    celula_grande_n: int
    celula_grande_mult: float
    celula_grande_clip_acionado: bool
    celula_pequena_produto: str
    celula_pequena_setor: str
    celula_pequena_n: int
    celula_pequena_mult: float
    faixa_min: float
    faixa_max: float
    todos_dentro_do_teto: bool


def build_reproduction(closed: pd.DataFrame) -> MultSetorReproduction:
    prod_counts = product_group_counts(closed)
    produto_stats = level_stats(prod_counts, constants.GLOBAL_WIN_RATE_CALIBRACAO)
    p_hat_by_product = {
        produto: p_hat_produto(produto, prod_counts, k=produto_stats.k)
        for produto in constants.PRECO_TABELA
    }
    setor_ctx = setor.build_context(closed, p_hat_by_product)

    itens = sorted(setor_ctx.cell_counts.items(), key=lambda kv: kv[1].n)
    (menor_produto, menor_setor), menor_gc = itens[0]
    (maior_produto, maior_setor), maior_gc = itens[-1]

    mult_maior = setor.mult_setor(setor_ctx, maior_produto, maior_setor)
    mult_menor = setor.mult_setor(setor_ctx, menor_produto, menor_setor)

    multiplicadores = [
        setor.mult_setor(setor_ctx, produto, sector_) for produto, sector_ in setor_ctx.cell_counts
    ]

    return MultSetorReproduction(
        celula_grande_produto=maior_produto,
        celula_grande_setor=maior_setor,
        celula_grande_n=maior_gc.n,
        celula_grande_mult=mult_maior,
        celula_grande_clip_acionado=mult_maior
        in (constants.MULT_SETOR_MIN, constants.MULT_SETOR_MAX),
        celula_pequena_produto=menor_produto,
        celula_pequena_setor=menor_setor,
        celula_pequena_n=menor_gc.n,
        celula_pequena_mult=mult_menor,
        faixa_min=min(multiplicadores),
        faixa_max=max(multiplicadores),
        todos_dentro_do_teto=all(
            constants.MULT_SETOR_MIN <= m <= constants.MULT_SETOR_MAX for m in multiplicadores
        ),
    )


@dataclass(frozen=True)
class ConsistencyAudit:
    n_combinacoes_verificadas: int
    todas_consistentes: bool


def audit_reference_and_open_funnel_consistency(
    dataset: Dataset, ctx: ScoringContext
) -> ConsistencyAudit:
    """`ctx` é o `ScoringContext` de produção, compartilhado por
    `pipeline.score_open_pipeline` (funil aberto) e `reference.build_
    reference_distribution` (negócios Won) — as duas populações já
    consomem exatamente o mesmo `setor_ctx`/`K_SETOR` por construção
    (um único `ctx` é montado em `load_and_score` e passado a ambas). Esta
    auditoria recalcula `mult_setor` do zero, a partir de `fechados_
    calibracao`, e confirma que bate célula a célula com o que `ctx`
    realmente retorna — a mesma disciplina de "recomputar da fonte, não
    confiar por construção" já aplicada à circularidade de 138 dias."""
    from scoring.pipeline import fechados_calibracao

    closed = fechados_calibracao(dataset)
    prod_counts = product_group_counts(closed)
    produto_stats = level_stats(prod_counts, constants.GLOBAL_WIN_RATE_CALIBRACAO)
    p_hat_by_product_recalc = {
        produto: p_hat_produto(produto, prod_counts, k=produto_stats.k)
        for produto in constants.PRECO_TABELA
    }
    setor_ctx_recalc = setor.build_context(closed, p_hat_by_product_recalc)

    inconsistentes = [
        (produto, sector_)
        for produto, sector_ in setor_ctx_recalc.cell_counts
        if round(setor.mult_setor(setor_ctx_recalc, produto, sector_), 9)
        != round(ctx.mult_setor(produto, sector_), 9)
    ]

    return ConsistencyAudit(
        n_combinacoes_verificadas=len(setor_ctx_recalc.cell_counts),
        todas_consistentes=not inconsistentes,
    )
