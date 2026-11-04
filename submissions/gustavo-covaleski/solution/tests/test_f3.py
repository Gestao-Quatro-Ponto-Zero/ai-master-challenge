import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comum import wilson  # noqa: E402
from f3_faixas import e_ponderado, faixas  # noqa: E402
from f3_llm import validar  # noqa: E402


def test_wilson_a_mao():
    # k=8, n=10, z=1,96: centro = (0,8 + 0,19208)/1,38416 = 0,71676; meia = 1,96·√(0,016 + 0,009604)/1,38416 = 0,22657
    li, ls = wilson(8, 10)
    assert li == pytest.approx(0.4902, abs=1e-3)
    assert ls == pytest.approx(0.9433, abs=1e-3)


def _curva(lis):
    return pd.DataFrame({"limiar": [0.5, 0.6, 0.7, 0.8, 0.9], "li": lis})


def test_faixas_tres_preenchidas():
    # meta decide = 1 - 0,03 = 0,97; meta sugere = 1 - 0,06 = 0,94
    assert faixas(_curva([0.90, 0.93, 0.95, 0.975, 0.99]), 0.03, 0.06) == (0.8, 0.7)


def test_faixas_ia_decide_vazia():
    t_dec, t_sug = faixas(_curva([0.90, 0.93, 0.95, 0.96, 0.965]), 0.03, 0.06)
    assert t_dec is None and t_sug == 0.7


def test_e_ponderado():
    adj = pd.DataFrame({"rotulo_original": ["A", "A", "B", "B", "B", "B"], "errado": [1, 0, 1, 1, 0, 0]})
    pesos = pd.Series({"A": 0.8, "B": 0.2})
    # taxas A = 0,5 e B = 0,5 → 0,8·0,5 + 0,2·0,5 = 0,5
    assert e_ponderado(adj, pesos) == pytest.approx(0.5)
    # taxas A = 1 e B = 0 → 0,8·1 + 0,2·0 = 0,8
    adj2 = pd.DataFrame({"rotulo_original": ["A", "A", "B", "B"], "errado": [1, 1, 0, 0]})
    assert e_ponderado(adj2, pesos) == pytest.approx(0.8)


@pytest.mark.parametrize("texto,ok", [
    ('{"categoria": "Hardware", "confianca": 0.9}', True),
    ('  {"categoria": "Storage", "confianca": 1}\n', True),
    ('{"categoria": "Printer", "confianca": 0.9}', False),
    ('{"categoria": "Hardware", "confianca": 0.9', False),
    ('Resposta: {"categoria": "Hardware", "confianca": 0.9}', False),
    ('{"categoria": "Hardware", "confianca": 1.5}', False),
])
def test_validador_json(texto, ok):
    assert (validar(texto) is not None) == ok
