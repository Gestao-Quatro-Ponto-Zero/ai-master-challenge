"""Concentração de PRIORIDADE — Requirement "Concentração de prioridade".

Reporta a fração do total de PRIORIDADE capturada pelos 10% e 30% de
oportunidades abertas mais bem pontuadas, comparada lado a lado com a
mesma métrica usando ordenação por preço de tabela puro. Concentração,
não validação preditiva — `p̂` varia só entre 0,60 e 0,75, a diferenciação
vem de VALOR e URGÊNCIA.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from scoring import constants


@dataclass(frozen=True)
class ConcentrationReport:
    top10_prioridade: float
    top30_prioridade: float
    top10_preco_bruto: float
    top30_preco_bruto: float


def _capture_fraction(values: pd.Series, fraction: float) -> float:
    n = max(1, round(len(values) * fraction))
    ordered = values.sort_values(ascending=False)
    return float(ordered.iloc[:n].sum() / ordered.sum())


def build_report(scored: pd.DataFrame) -> ConcentrationReport:
    prioridade = scored["prioridade"]
    preco_bruto = scored["product"].map(constants.PRECO_TABELA)

    return ConcentrationReport(
        top10_prioridade=_capture_fraction(prioridade, 0.10),
        top30_prioridade=_capture_fraction(prioridade, 0.30),
        top10_preco_bruto=_capture_fraction(preco_bruto, 0.10),
        top30_preco_bruto=_capture_fraction(preco_bruto, 0.30),
    )
