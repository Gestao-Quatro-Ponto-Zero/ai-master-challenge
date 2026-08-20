"""Distribuição de referência de SCORE: PRIORIDADE sobre os negócios ganhos.

SCORE = percentil de PRIORIDADE de uma oportunidade contra a distribuição de
PRIORIDADE calculada sobre os 4.238 negócios historicamente "Won", usando a
idade real de cada um no fechamento como entrada das mesmas fórmulas de p̂,
VALOR e URGÊNCIA — nunca contra o funil aberto corrente.

Essa população é histórica e fixa: recalculada apenas no ciclo trimestral de
recalibração (`build_reference_distribution`), nunca por requisição.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass

import pandas as pd

from . import constants, model
from .repository import Dataset


@dataclass(frozen=True)
class ReferenceDistribution:
    """PRIORIDADE ordenada dos negócios ganhos — população fixa de referência."""

    prioridades_ordenadas: list[float]

    @property
    def n(self) -> int:
        return len(self.prioridades_ordenadas)

    @property
    def mediana(self) -> float:
        if not self.prioridades_ordenadas:
            return 0.0
        mid = self.n // 2
        if self.n % 2 == 1:
            return self.prioridades_ordenadas[mid]
        return (self.prioridades_ordenadas[mid - 1] + self.prioridades_ordenadas[mid]) / 2

    def percentil(self, prioridade_valor: float) -> float:
        """Percentil (0-100) de `prioridade_valor` nesta distribuição.

        Usa a definição de posto médio: metade do peso das observações
        empatadas conta a favor, metade contra — evita que um valor exato
        no meio de um platô de empates seja arredondado sempre para cima
        ou sempre para baixo.
        """
        if self.n == 0:
            return 0.0
        menores = bisect.bisect_left(self.prioridades_ordenadas, prioridade_valor)
        nao_maiores = bisect.bisect_right(self.prioridades_ordenadas, prioridade_valor)
        posto_medio = (menores + nao_maiores) / 2
        return round((posto_medio / self.n) * 100, 1)


def _age_at_close_days(row: pd.Series) -> float:
    return (row["close_date"] - row["engage_date"]).days


def build_reference_distribution(
    dataset: Dataset, ctx: model.ScoringContext
) -> ReferenceDistribution:
    """Recalcula PRIORIDADE para todos os negócios Won, na idade real do fechamento.

    Todo negócio Won tem `engage_date` na base (nenhum fechado veio direto
    de Prospecting) — por isso é tratado como Engaging aqui, mesmo já
    fechado; nenhum excede 138 dias (verificado em validation/), então a
    regra de censura nunca é acionada nesta população.
    """
    won = dataset.pipeline[dataset.pipeline["deal_stage"] == "Won"].copy()
    won["age_at_close"] = won.apply(_age_at_close_days, axis=1)

    prioridades: list[float] = []
    for _, row in won.iterrows():
        porte = constants.classificar_porte(row.get("employees"))
        componentes = model.score_componentes(
            ctx,
            product=row["product"],
            stage="Engaging",
            age_days=row["age_at_close"],
            porte=porte,
        )
        prioridades.append(componentes.prioridade)

    prioridades.sort()
    return ReferenceDistribution(prioridades_ordenadas=prioridades)
