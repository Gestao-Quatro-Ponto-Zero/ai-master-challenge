"""Atribuição de CONFIANÇA (A-D) — quanto se sabe sobre a oportunidade.

Avaliada nesta ordem exata: censura primeiro, depois conta+Engaging, depois
conta OU Engaging, depois o restante. Independente de PRIORIDADE/SCORE.
"""

from __future__ import annotations

from . import constants


def confianca(
    stage: str,
    has_account: bool,
    age_days: float | None,
) -> str:
    censurado = stage == "Engaging" and age_days is not None and age_days > constants.CENSURA_DIAS
    if censurado:
        return "D"

    engaging = stage == "Engaging"
    if has_account and engaging:
        return "A"

    if has_account or engaging:
        return "B"

    return "C"


_RAZAO_TEMPLATES: dict[str, str] = {
    "A": "confiança A: conta conhecida, negócio em Engaging, dentro da janela histórica",
    "B_conta": "confiança B: conta conhecida, mas negócio ainda em Prospecting — falta engajamento",
    "B_engaging": "confiança B: negócio em Engaging dentro da janela histórica, mas sem conta vinculada",
    "C": "confiança C: sem conta vinculada e negócio ainda em Prospecting",
    "D": "confiança D: idade acima de 138 dias, fora de qualquer precedente histórico de fechamento",
}


def razao_confianca(stage: str, has_account: bool, age_days: float | None) -> str:
    """Texto que justifica o nível de CONFIANÇA atribuído (para explicabilidade)."""
    nivel = confianca(stage, has_account, age_days)
    if nivel == "D":
        return _RAZAO_TEMPLATES["D"]
    if nivel == "A":
        return _RAZAO_TEMPLATES["A"]
    if nivel == "C":
        return _RAZAO_TEMPLATES["C"]
    # B: distinguish which single condition was met
    if has_account:
        return _RAZAO_TEMPLATES["B_conta"]
    return _RAZAO_TEMPLATES["B_engaging"]
