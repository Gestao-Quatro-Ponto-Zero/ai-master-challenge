import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comum import ler_csv_excel  # noqa: E402
from f2_diagnostico import mde, n_para_mde, semanas_para_n  # noqa: E402


def test_mde_valor_de_referencia():
    assert mde(10, 100, 100) == pytest.approx(3.96, abs=0.01)


def test_semanas_a_mao():
    # 30.000/ano ÷ 52 = 576,92 tickets/semana; grupo com 10% → 57,69/semana; 123 ÷ 57,69 = 2,132 semanas
    assert semanas_para_n(123, 0.10) == pytest.approx(2.132, abs=0.001)


def test_n_para_mde_inverte_mde():
    n = n_para_mde(5.0, 2.0)
    assert mde(5.0, n, n) <= 2.0 < mde(5.0, n - 1, n - 1)


@pytest.mark.parametrize("sep,cod", [(";", "utf-8-sig"), (",", "utf-8"), (",", "cp1252")])
def test_ler_csv_excel_aceita_variantes(tmp_path, sep, cod):
    p = tmp_path / "x.csv"
    p.write_bytes((sep.join(["id", "observacao"]) + "\r\n" + sep.join(["1", "não"]) + "\r\n").encode(cod))
    df = ler_csv_excel(p)
    assert list(df.columns) == ["id", "observacao"]
    assert df.iloc[0].tolist() == ["1", "não"]
