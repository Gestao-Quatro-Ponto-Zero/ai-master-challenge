"""`mult_setor(produto, setor)` — ajuste de desempenho produto×setor sobre
p̂. lead-scoring spec, Requirement "Ajuste de desempenho produto×setor
sobre p̂".

O nível produto×setor tem variância em excesso ≤ 0 nos dados de calibração
(colapsa, k=∞ — ver `scoring/shrinkage.py` e `validation/shrinkage_check.py`):
a resposta estatisticamente correta seria mult_setor ≡ 1,000 para todas as
células. `constants.K_SETOR` é uma constante de POLÍTICA que sobrepõe esse
colapso deliberadamente — mesmo papel que `constants.K_FIT` já cumpre para
o fit de vendedor (`scoring/fit.py`), reaproveitando o mesmo valor por
consistência (design.md).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import constants
from .shrinkage import GroupCounts, product_sector_group_counts


def setor_desconhecido(sector: str | None) -> bool:
    """True quando o setor não é utilizável — ausente (`None`) ou NaN
    (pandas, quando a conta não está vinculada ou a conta não tem setor
    cadastrado)."""
    return sector is None or (isinstance(sector, float) and sector != sector)


@dataclass(frozen=True)
class MultSetorContext:
    """Pré-computado uma vez sobre `fechados_calibracao`: contagens por
    célula (produto, setor) e o p̂_produto já derivado de cada produto —
    o prior em direção ao qual cada célula é encolhida (não a taxa
    global)."""

    cell_counts: dict[tuple[str, str], GroupCounts]
    p_hat_by_product: dict[str, float]


def build_context(
    fechados_calibracao: pd.DataFrame, p_hat_by_product: dict[str, float]
) -> MultSetorContext:
    cell_counts = product_sector_group_counts(fechados_calibracao)
    return MultSetorContext(cell_counts=cell_counts, p_hat_by_product=p_hat_by_product)


def n_celula(ctx: MultSetorContext, product: str, sector: str | None) -> int:
    """Tamanho amostral (negócios fechados de calibração) da célula
    produto×setor — 0 quando o setor é desconhecido ou a célula não tem
    nenhum negócio fechado. Consumido por CONFIANÇA (`s_célula`) e por
    `explicacao.fatores_score` (frase do ajuste de setor)."""
    if setor_desconhecido(sector):
        return 0
    counts = ctx.cell_counts.get((product, sector))
    return counts.n if counts is not None else 0


def mult_setor(ctx: MultSetorContext, product: str, sector: str | None) -> float:
    """taxa_bruta_célula = vitórias_célula / total_célula
    taxa_encolhida = (n_célula×taxa_bruta_célula + K_SETOR×p̂_produto) / (n_célula+K_SETOR)
    mult_setor = taxa_encolhida / p̂_produto, limitado a [MULT_SETOR_MIN, MULT_SETOR_MAX]

    Setor desconhecido ou célula sem nenhum negócio fechado -> 1,0 (neutro)
    — nunca inventa dado a partir de uma célula vazia.
    """
    if setor_desconhecido(sector):
        return 1.0

    counts = ctx.cell_counts.get((product, sector))
    if counts is None or counts.n == 0:
        return 1.0

    p_hat_produto = ctx.p_hat_by_product.get(product, constants.GLOBAL_WIN_RATE_CALIBRACAO)
    taxa_encolhida = (
        counts.n * counts.rate + constants.K_SETOR * p_hat_produto
    ) / (counts.n + constants.K_SETOR)
    valor = taxa_encolhida / p_hat_produto
    return max(constants.MULT_SETOR_MIN, min(constants.MULT_SETOR_MAX, valor))
