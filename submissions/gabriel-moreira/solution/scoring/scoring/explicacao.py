"""Explicabilidade: decomposição do score + plano de ação determinístico.

Gerado por template a partir dos componentes já calculados — nunca por um
modelo não determinístico nem por chamada a serviço externo, para
preservar a auditabilidade (Requirement "Explicabilidade do score e plano
de ação").
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass

from .confianca import razao_confianca
from .model import Componentes


@dataclass(frozen=True)
class Decomposicao:
    p_hat: float
    valor: float
    urgencia: float
    prioridade: float


def decompor(componentes: Componentes) -> Decomposicao:
    return Decomposicao(
        p_hat=componentes.p_hat,
        valor=componentes.valor,
        urgencia=componentes.urgencia,
        prioridade=componentes.prioridade,
    )


def fracao_vitorias_ate(ages_won_ordenadas: list[float], age_days: float) -> float:
    """Fração (0-100) dos negócios ganhos históricos com idade <= age_days."""
    if not ages_won_ordenadas:
        return 0.0
    pos = bisect.bisect_right(ages_won_ordenadas, age_days)
    return round(100 * pos / len(ages_won_ordenadas), 1)


def _fmt_usd(value: float) -> str:
    return f"US$ {value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


_PLANOS: dict[str, str] = {
    "foco_urgente": (
        "{razao}. {fracao}% das vitórias históricas já ocorreram nesta idade — "
        "priorize contato esta semana."
    ),
    "acompanhar": (
        "{razao}. Mantenha follow-up regular: o valor em jogo ou a confiança "
        "ainda não justificam agir com urgência agora."
    ),
    "engajar": (
        "{razao}. O valor potencial ({valor}) justifica buscar a informação que "
        "falta — conta ou engajamento pleno — antes de descartar."
    ),
    "qualificar": (
        "{razao}. Faltam dados de conta e o valor aparente é baixo — enriqueça "
        "o cadastro antes de tratar como tarefa priorizada."
    ),
    "desistir": (
        "{razao}. A idade está fora de qualquer precedente histórico de "
        "fechamento — recomenda-se revisão em lote com o gestor: fechar ou "
        "descartar, não trabalhar individualmente."
    ),
}


def plano_de_acao(
    estado_key: str,
    stage: str,
    has_account: bool,
    age_days: float | None,
    confianca_nivel: str,
    componentes: Componentes,
    ages_won_ordenadas: list[float] | None = None,
) -> str:
    """Texto de plano de ação específico do ESTADO, a partir dos componentes."""
    razao = razao_confianca(stage, has_account, age_days)
    template = _PLANOS[estado_key]

    fracao = 0.0
    if estado_key == "foco_urgente" and age_days is not None and ages_won_ordenadas:
        fracao = fracao_vitorias_ate(ages_won_ordenadas, age_days)

    return template.format(
        razao=razao,
        fracao=fracao,
        valor=_fmt_usd(componentes.valor),
    )
