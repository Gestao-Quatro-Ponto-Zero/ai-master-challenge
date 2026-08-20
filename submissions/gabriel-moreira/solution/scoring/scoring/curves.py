"""Curvas de aging em degraus: p_ganho(t) e risco(t).

Ambas são lidas como função em degraus (step function): para um t entre
dois pontos calibrados, usa-se o maior ponto calibrado <= t. Consistente
com a natureza de uma regressão isotônica, que produz uma função constante
por partes.
"""

from __future__ import annotations

from . import constants


def _step_lookup(breakpoints: list[tuple[int, float]], t: float) -> float:
    """Maior breakpoint <= t; usa o primeiro ponto para t negativo/abaixo."""
    value = breakpoints[0][1]
    for threshold, v in breakpoints:
        if t >= threshold:
            value = v
        else:
            break
    return value


def p_ganho(t: float) -> float:
    """p_ganho(t), congelado em p_ganho(120) para t > 120.

    O chamador é responsável por aplicar `min(idade, 120)` antes de chamar
    esta função quando a idade estiver dentro da janela de censura (<=138);
    acima de 138, ver a regra de censura em model.py, que não passa por
    esta curva.
    """
    capped = min(t, constants.CURVA_LIMITE_CONFIAVEL_DIAS)
    return _step_lookup(constants.P_GANHO_BREAKPOINTS, capped)


def risco(t: float) -> float:
    """risco(t) = P(resolve em 30 dias | idade t), congelado em risco(120)."""
    capped = min(t, constants.CURVA_LIMITE_CONFIAVEL_DIAS)
    return _step_lookup(constants.RISCO_BREAKPOINTS, capped)
