"""Auditoria da circularidade acima de 138 dias — Requirement "Auditoria
da circularidade acima de 138 dias".

Demonstra que a faixa >138d na população de calibração é composta
integralmente por reclassificados (não por desfechos observados), e
verifica que nenhum reclassificado entrou na calibração das curvas de
idade (`fechados_organicos`).
"""

from __future__ import annotations

from dataclasses import dataclass

from scoring.pipeline import fechados_organicos
from scoring.repository import Dataset


@dataclass(frozen=True)
class CircularityReport:
    idade_maxima_organica: int
    idade_minima_reclassificada: int
    populacoes_nao_se_sobrepoem: bool
    curvas_protegidas: bool


def build_report(dataset: Dataset) -> CircularityReport:
    organicos = fechados_organicos(dataset)
    idade_organica = (organicos["close_date"] - organicos["engage_date"]).dt.days
    idade_maxima_organica = int(idade_organica.max())

    reclassificados = dataset.pipeline[dataset.pipeline["reclassificado"]]
    idade_reclassificada = (dataset.as_of_default - reclassificados["engage_date"]).dt.days
    idade_minima_reclassificada = int(idade_reclassificada.min())

    return CircularityReport(
        idade_maxima_organica=idade_maxima_organica,
        idade_minima_reclassificada=idade_minima_reclassificada,
        populacoes_nao_se_sobrepoem=idade_maxima_organica < idade_minima_reclassificada,
        curvas_protegidas=not bool(organicos["reclassificado"].any()),
    )
