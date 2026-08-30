"""Auditoria de circularidade — Requirement "Auditoria da circularidade
acima de 138 dias".

A pergunta original era estreita: os rótulos que nós atribuíamos por idade
(o expurgo de 200 dias) estavam vazando para as curvas que aprendem o
efeito da idade? Removido o expurgo (2026-08-29), a pergunta vira a mais
forte que ela sempre foi um caso particular: **existe algum desfecho na
população de calibração que não veio do CRM?**

A resposta tem de ser não, por construção — `repository.load_dataset` não
escreve em `deal_stage`. Esta auditoria existe para que uma reintrodução
futura de qualquer regra de rotulagem automática quebre um teste em vez de
passar despercebida: se voltar a haver negócio "fechado" sem `close_date`,
ou aberto além da fronteira observada dentro da calibração, o backtest
falha.
"""

from __future__ import annotations

from dataclasses import dataclass

from scoring import constants
from scoring.pipeline import fechados
from scoring.repository import Dataset


@dataclass(frozen=True)
class CircularityReport:
    n_calibracao: int
    n_sem_close_date: int
    idade_maxima_observada: int
    fronteira_censura: int
    idade_maxima_aberta: int
    todos_desfechos_observados: bool
    censura_cobre_a_calibracao: bool


def build_report(dataset: Dataset) -> CircularityReport:
    closed = fechados(dataset)

    # Um negócio fechado sem data de fechamento seria um rótulo sem evento
    # — exatamente a assinatura de um desfecho atribuído por regra.
    n_sem_close_date = int(closed["close_date"].isna().sum())

    idade_fechada = (closed["close_date"] - closed["engage_date"]).dt.days
    idade_maxima_observada = int(idade_fechada.max())

    abertos = dataset.pipeline[
        dataset.pipeline["deal_stage"].isin(constants.DEAL_STAGES_ABERTOS)
    ]
    idade_aberta = (dataset.as_of_default - abertos["engage_date"]).dt.days

    return CircularityReport(
        n_calibracao=int(len(closed)),
        n_sem_close_date=n_sem_close_date,
        idade_maxima_observada=idade_maxima_observada,
        fronteira_censura=constants.CENSURA_DIAS,
        idade_maxima_aberta=int(idade_aberta.max()),
        todos_desfechos_observados=n_sem_close_date == 0,
        # A censura tem de cobrir tudo que a calibração viu: se um negócio
        # fechado levasse mais que CENSURA_DIAS, a curva estaria sendo lida
        # fora da faixa em que foi calibrada.
        censura_cobre_a_calibracao=idade_maxima_observada <= constants.CENSURA_DIAS,
    )
