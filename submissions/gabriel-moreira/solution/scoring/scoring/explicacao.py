"""Explicabilidade: decomposição do score + plano de ação determinístico.

Gerado por template a partir dos componentes já calculados — nunca por um
modelo não determinístico nem por chamada a serviço externo, para
preservar a auditabilidade (Requirement "Explicabilidade do score e plano
de ação").
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass

from . import constants
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


_PLANOS: dict[str, str] = {
    "prioritize": (
        "{razao}. {fracao}% das vitórias históricas já ocorreram nesta idade — "
        "priorize contato esta semana."
    ),
    "acompanhar": (
        "{razao}. Nada falta saber sobre esta oportunidade — mantenha follow-up "
        "regular, o valor em jogo ainda não justifica agir com urgência agora."
    ),
    "qualificar": (
        "{razao}. Faltam {campos} — obtenha essa informação antes de tratar "
        "como tarefa priorizada."
    ),
    "revisao_lote": (
        "{razao}. Fora de qualquer precedente histórico de fechamento — "
        "recomenda-se revisão em lote com o gestor: fechar ou descartar, não "
        "trabalhar individualmente."
    ),
}


def plano_de_acao(
    estado_key: str,
    razao: str,
    age_days: float | None,
    componentes: Componentes,
    campos_ausentes: list[str] | None = None,
    ages_won_ordenadas: list[float] | None = None,
) -> str:
    """Texto de plano de ação específico do ESTADO, a partir da razão de
    CONFIANÇA já computada (qual metade governou o mínimo e o que falta)."""
    template = _PLANOS[estado_key]

    fracao = 0.0
    if estado_key == "prioritize" and age_days is not None and ages_won_ordenadas:
        fracao = fracao_vitorias_ate(ages_won_ordenadas, age_days)

    campos = ", ".join(campos_ausentes) if campos_ausentes else "dados de cadastro"

    return template.format(razao=razao, fracao=fracao, campos=campos)


_PASSOS_BASE: dict[str, tuple[str, ...]] = {
    "prioritize": (
        "Entre em contato com o cliente esta semana para avançar a negociação.",
        "Confirme o próximo marco e a data de decisão combinada.",
    ),
    "acompanhar": (
        "Mantenha follow-up regular — nada falta saber e o valor ainda não "
        "justifica agir com urgência agora.",
        "Reavalie a prioridade se o valor aumentar ou o SCORE subir.",
    ),
    "qualificar": (
        "Confirme os dados ausentes — {campos} — antes de tratar como tarefa "
        "priorizada.",
        "Reavalie a prioridade assim que o cadastro estiver completo.",
    ),
    "revisao_lote": (
        "Não trabalhe a oportunidade individualmente — está fora de qualquer "
        "precedente histórico de fechamento.",
        "Inclua no lote de revisão com o gestor: fechar ou descartar, não "
        "trabalhar individualmente.",
    ),
}

_PASSO_ENRIQUECIMENTO = (
    "Enriqueça o cadastro da conta — sem ela, o valor usa o prior neutro de porte."
)


_TIER_VALOR_FRASES: dict[str, str] = {
    "alto": (
        "Valor do produto: {product} está entre os produtos de maior valor de "
        "tabela do catálogo — isso puxa a prioridade para cima."
    ),
    "médio": (
        "Valor do produto: {product} tem valor de tabela mediano no catálogo — "
        "efeito neutro na prioridade."
    ),
    "baixo": (
        "Valor do produto: {product} está entre os produtos de menor valor de "
        "tabela do catálogo — sozinho, isso não empurra a prioridade para cima."
    ),
}


def _tier_valor(product: str) -> str:
    """Classifica o preço de tabela do produto em tercis sobre os preços
    distintos do catálogo (7 produtos) — não sobre volume de negócios."""
    precos_ordenados = sorted(set(constants.PRECO_TABELA.values()))
    preco = constants.PRECO_TABELA[product]
    pos = precos_ordenados.index(preco)
    pct = pos / (len(precos_ordenados) - 1) if len(precos_ordenados) > 1 else 1.0
    if pct >= 0.66:
        return "alto"
    if pct >= 0.33:
        return "médio"
    return "baixo"


def _fator_valor(product: str) -> str:
    return _TIER_VALOR_FRASES[_tier_valor(product)].format(product=product)


def _fator_chance(p_hat: float, stage: str, age_days: float | None) -> str:
    """Chance de fechamento em linguagem simples, incluindo o achado
    contraintuitivo de que negócios mais velhos (dentro da janela de
    censura) têm chance histórica igual ou maior de fechar, não menor."""
    pct = round(p_hat * 100)
    if p_hat >= 0.70:
        nivel = "alta"
    elif p_hat >= 0.60:
        nivel = "dentro da média histórica"
    else:
        nivel = "um pouco abaixo da média histórica"

    base = f"Chance de fechamento: {nivel} ({pct}%), baseada no histórico deste produto"

    if (
        stage == "Engaging"
        and age_days is not None
        and 14 <= age_days <= constants.CENSURA_DIAS
    ):
        return (
            f"{base} e no tempo já decorrido — negócios que chegam aos "
            f"{round(age_days)} dias sem fechar historicamente têm chance igual "
            "ou maior de fechar do que negócios recém-abertos."
        )
    return f"{base}."


def _fator_urgencia(urgencia: float) -> str:
    if urgencia >= 0.7:
        return (
            "Urgência: tende a se resolver (fechar ou ser perdido) nos "
            "próximos 30 dias — é hora de agir."
        )
    if urgencia >= 0.3:
        return "Urgência: pode se resolver nas próximas semanas, mas ainda sem pressa extrema."
    return "Urgência: nada indica que vá se resolver logo — o tempo não é o fator crítico agora."


def _fator_conta(has_account: bool, porte: str | None) -> str:
    if not has_account or porte is None:
        return (
            "Dados da conta: sem conta vinculada — o cálculo usa o valor médio "
            "de mercado, sem favorecer nem penalizar."
        )
    mult = constants.MULT_PORTE.get(porte, constants.MULT_PORTE_DESCONHECIDO)
    if mult > 1.0:
        return (
            f"Dados da conta indicam porte {porte} — isso eleva o valor "
            "considerado em relação à média do mercado."
        )
    if mult < 1.0:
        return (
            f"Dados da conta indicam porte {porte} — isso reduz um pouco o "
            "valor considerado em relação à média do mercado."
        )
    return f"Dados da conta indicam porte {porte} — efeito neutro no valor considerado."


def fatores_score(
    componentes: Componentes,
    product: str,
    porte: str | None,
    has_account: bool,
    stage: str,
    age_days: float | None,
) -> list[str]:
    """Decompõe PRIORIDADE (p̂, VALOR, URGÊNCIA) e o efeito do porte da conta
    em frases de negócio, sem jargão técnico — geradas por template a partir
    dos mesmos componentes já calculados, com a mesma garantia de
    auditabilidade do plano de ação (Requirement "Explicabilidade do score e
    plano de ação")."""
    return [
        _fator_valor(product),
        _fator_chance(componentes.p_hat, stage, age_days),
        _fator_urgencia(componentes.urgencia),
        _fator_conta(has_account, porte),
    ]


def plano_de_acao_passos(
    estado_key: str,
    has_account: bool,
    campos_ausentes: list[str],
) -> tuple[str, ...]:
    """Plano de ação em 2 a 4 passos, derivado de ESTADO e das duas metades
    de CONFIANÇA (via `campos_ausentes`, produto da completude).

    O passo de enriquecimento de conta entra primeiro quando falta conta,
    independentemente do estado — é a mesma ausência em qualquer estado.
    O total é truncado em 4.
    """
    campos = ", ".join(campos_ausentes) if campos_ausentes else "o cadastro"
    passos = [passo.format(campos=campos) for passo in _PASSOS_BASE[estado_key]]

    if not has_account:
        passos.insert(0, _PASSO_ENRIQUECIMENTO)

    return tuple(passos[:4])
