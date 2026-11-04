import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comum import OUT_DIR  # noqa: E402
from f9_confirmacao import confirmar, mais_restritiva  # noqa: E402

E_INF, E_SUP = 0.032, 0.0455  # metas 0,968 e 0,9545


@pytest.mark.parametrize("li,oof,esperado", [
    (0.975, "IA decide", "IA decide"),
    (0.960, "IA decide", "IA sugere"),
    (0.897, "IA decide", "humano decide"),
    (float("nan"), "IA sugere", "IA sugere"),   # sem tickets em IA decide no holdout: mantém a OOF
])
def test_confirmacao_no_holdout(li, oof, esperado):
    assert confirmar(li, oof, E_INF, E_SUP) == esperado


def test_implantada_so_rebaixa():
    assert mais_restritiva("IA sugere", "IA decide") == "IA sugere"   # holdout melhor não promove
    assert mais_restritiva("IA decide", "humano decide") == "humano decide"


def test_politica_implantada_nunca_acima_da_oof():
    ordem = ["humano decide", "IA sugere", "IA decide"]
    tab = pd.read_csv(OUT_DIR / "f8_politica_por_categoria.csv")
    assert all(ordem.index(i) <= ordem.index(o) for i, o in zip(tab["politica_implantada"], tab["politica"]))
