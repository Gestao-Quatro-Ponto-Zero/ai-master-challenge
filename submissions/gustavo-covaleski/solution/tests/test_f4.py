import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from f4_politica import faixa_efetiva, politica_categoria  # noqa: E402

E_INF, E_SUP = 0.03, 0.05  # metas sintéticas: 0,97 (decide) e 0,95 (sugere)


@pytest.mark.parametrize("li,esperado", [(0.98, "IA decide"), (0.96, "IA sugere"), (0.94, "humano decide"),
                                         (None, "humano decide")])
def test_politica_por_categoria(li, esperado):
    assert politica_categoria(li, E_INF, E_SUP) == esperado


def test_politica_e_teto_da_faixa():
    assert faixa_efetiva(0.95, "IA sugere", 0.74, 0.66) == "IA sugere"      # rebaixa
    assert faixa_efetiva(0.60, "IA decide", 0.74, 0.66) == "humano decide"  # nunca promove
    assert faixa_efetiva(0.95, "humano decide", 0.74, 0.66) == "humano decide"
