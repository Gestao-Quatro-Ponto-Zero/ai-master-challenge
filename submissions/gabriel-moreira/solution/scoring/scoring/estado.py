"""Atribuição de ESTADO — árvore de decisão sobre SCORE e CONFIANÇA.

Avaliada nesta ordem exata:
1. sem precedente histórico  -> revisao_lote
2. SCORE >= corte            -> prioritize
3. CONFIANÇA < corte         -> qualificar
4. caso contrário            -> acompanhar

Ausência de precedente é lida diretamente (não derivada de um corte sobre
CONFIANÇA): oportunidades novas sem cadastro e antigas sem precedente se
aglomeram em valores adjacentes de CONFIANÇA, em ordem invertida — nenhum
corte único separa as duas populações (design.md, decisão "roteamento por
condição nomeada").
"""

from __future__ import annotations

from . import constants


def estado(score: float, confianca_valor: float, sem_precedente: bool) -> str:
    if sem_precedente:
        return "revisao_lote"
    if score >= constants.SCORE_CORTE_PRIORITIZE:
        return "prioritize"
    if confianca_valor < constants.CONFIANCA_CORTE_QUALIFICAR:
        return "qualificar"
    return "acompanhar"


def estado_label(estado_key: str) -> str:
    return constants.ESTADO_LABELS[estado_key]
