"""Atribuição de ESTADO — tabela de decisão 4x2, CONFIANÇA x SCORE.

| CONFIANÇA | SCORE >= 50   | SCORE < 50  |
|-----------|---------------|-------------|
| A         | Foco urgente  | Acompanhar  |
| B         | Acompanhar    | Engajar     |
| C         | Engajar       | Qualificar  |
| D         | Desistir      | Desistir    |

CONFIANÇA D força Desistir independentemente de SCORE.
"""

from __future__ import annotations

from . import constants

_TABELA: dict[str, dict[bool, str]] = {
    "A": {True: "foco_urgente", False: "acompanhar"},
    "B": {True: "acompanhar", False: "engajar"},
    "C": {True: "engajar", False: "qualificar"},
    "D": {True: "desistir", False: "desistir"},
}


def estado(confianca_nivel: str, score: float) -> str:
    if confianca_nivel not in _TABELA:
        raise ValueError(f"nível de confiança inválido: {confianca_nivel!r}")
    acima_do_corte = score >= constants.SCORE_CORTE_ESTADO
    return _TABELA[confianca_nivel][acima_do_corte]


def estado_label(estado_key: str) -> str:
    return constants.ESTADO_LABELS[estado_key]
