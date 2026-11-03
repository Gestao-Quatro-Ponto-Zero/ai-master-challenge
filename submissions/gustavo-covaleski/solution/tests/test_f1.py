import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comum import OUT_DIR, REVISAO_DIR, ler_csv_excel, ler_ds2, salvar_csv_excel  # noqa: E402
import f1_adjudicacao as adj  # noqa: E402

N_CLASSES = 8


@pytest.fixture(scope="module")
def splits():
    return pd.read_csv(OUT_DIR / "f1_splits.csv")


@pytest.fixture(scope="module")
def rotulos():
    return ler_ds2()[["id", "Topic_group"]]


def test_splits_ids_e_grupos(splits, rotulos):
    assert splits["id"].is_unique
    assert splits["id"].tolist() == list(range(len(rotulos)))
    g = splits.groupby("group_id")["split_grupo"].nunique()
    assert (g == 1).all(), "group_id em treino e holdout"


@pytest.mark.parametrize("col", ["split_grupo", "split_aleatorio"])
def test_holdouts_tamanho_e_classes(splits, rotulos, col):
    d = splits.merge(rotulos, on="id")
    h = d[d[col] == "holdout"]
    assert 0.18 <= len(h) / len(d) <= 0.22
    assert h["Topic_group"].nunique() == N_CLASSES


def test_planilha_revisao(splits):
    rev = ler_csv_excel(REVISAO_DIR / "revisao_rotulos.csv")
    gab = ler_csv_excel(REVISAO_DIR / "revisao_gabarito.csv")
    assert len(rev) == 60
    assert (rev["meu_rotulo"] == "").all() and (rev["rotulo_original"] == "").all()
    assert sorted(gab["id"]) == sorted(rev["id"])
    assert (gab["rotulo_original"].value_counts() >= 5).all()
    assert gab["rotulo_original"].nunique() == N_CLASSES
    ids = rev["id"].astype(int)
    s = splits.set_index("id").loc[ids]
    assert (s["split_grupo"] == "holdout").all()
    assert s["group_id"].is_unique


def _planilha(tmp_path, meus, gab):
    ids = [str(i) for i in range(len(meus))]
    salvar_csv_excel(pd.DataFrame({"id": ids, "texto": [f"t{i}" for i in ids], "rotulo_original": "",
                                   "meu_rotulo": meus, "ambiguo": "n", "observacao": ""}),
                     tmp_path / "revisao_rotulos.csv")
    salvar_csv_excel(pd.DataFrame({"id": ids, "rotulo_original": gab}), tmp_path / "revisao_gabarito.csv")


GAB = ["Access", "Hardware", "Storage", "Purchase"]


@pytest.mark.parametrize("meus", [["Access", "", "Storage", "Purchase"],
                                  ["Access", "Impressora", "Storage", "Purchase"]])
def test_preparar_recusa_rotulo_invalido(tmp_path, meus):
    _planilha(tmp_path, meus, GAB)
    with pytest.raises(SystemExit):
        adj.main(["preparar", "--dir-revisao", str(tmp_path)])


def test_preparar_lista_so_divergencias(tmp_path):
    _planilha(tmp_path, ["Access", "Storage", "Storage", "HR Support"], GAB)
    adj.main(["preparar", "--dir-revisao", str(tmp_path)])
    out = ler_csv_excel(tmp_path / "adjudicacao.csv")
    assert out["id"].tolist() == ["1", "3"]
    assert out["rotulo_original"].tolist() == ["Hardware", "Purchase"]


@pytest.mark.parametrize("valor", ["", "talvez"])
def test_consolidar_recusa_adjudicacao_invalida(tmp_path, valor):
    _planilha(tmp_path, ["Access", "Storage", "Storage", "HR Support"], GAB)
    adj.main(["preparar", "--dir-revisao", str(tmp_path)])
    a = ler_csv_excel(tmp_path / "adjudicacao.csv")
    a["adjudicacao"] = ["original errado", valor]
    salvar_csv_excel(a, tmp_path / "adjudicacao.csv")
    with pytest.raises(SystemExit):
        adj.main(["consolidar", "--dir-revisao", str(tmp_path), "--dir-saida", str(tmp_path)])


def test_consolidar_mantem_todas_as_linhas(tmp_path):
    _planilha(tmp_path, ["Access", "Storage", "Storage", "HR Support"], GAB)
    adj.main(["preparar", "--dir-revisao", str(tmp_path)])
    a = ler_csv_excel(tmp_path / "adjudicacao.csv")
    a["adjudicacao"] = ["original errado", "ambíguo"]
    salvar_csv_excel(a, tmp_path / "adjudicacao.csv")
    adj.main(["consolidar", "--dir-revisao", str(tmp_path), "--dir-saida", str(tmp_path)])
    final = ler_csv_excel(tmp_path / "revisao_rotulos_adjudicada.csv")
    assert len(final) == 4
    assert final["adjudicacao"].tolist() == ["", "original errado", "", "ambíguo"]
    assert final["rotulo_original"].tolist() == GAB
