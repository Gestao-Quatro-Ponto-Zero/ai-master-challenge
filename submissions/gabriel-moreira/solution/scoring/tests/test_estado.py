"""Task 2.12 — tabela de decisão ESTADO, os cinco valores."""

import pytest

from scoring.estado import estado


@pytest.mark.parametrize(
    "confianca_nivel,score,esperado",
    [
        ("A", 82.0, "foco_urgente"),
        ("A", 30.0, "acompanhar"),
        ("B", 82.0, "acompanhar"),
        ("B", 30.0, "engajar"),
        ("C", 65.0, "engajar"),
        ("C", 20.0, "qualificar"),
        ("D", 99.9, "desistir"),
        ("D", 0.0, "desistir"),
    ],
)
def test_estado_table(confianca_nivel, score, esperado):
    assert estado(confianca_nivel, score) == esperado


def test_estado_boundary_at_50_is_inclusive():
    assert estado("A", 50.0) == "foco_urgente"
    assert estado("A", 49.9) == "acompanhar"


def test_estado_invalid_confianca_raises():
    with pytest.raises(ValueError):
        estado("Z", 50.0)
