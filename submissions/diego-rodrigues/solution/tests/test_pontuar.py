import dataclasses

import pandas as pd

from motor.pontuar import pontuar_em


def _apagar_desfechos_depois_de(dados, data):
    """Reescreve os desfechos que ocorrem em `data` ou depois: inverte Won/Lost e muda a data."""
    p = dados.pipeline.copy()
    futuro = p.close_date >= data
    p.loc[futuro, "close_date"] = data + pd.Timedelta(days=10)
    trocado = p.loc[futuro, "deal_stage"].map({"Won": "Lost", "Lost": "Won"})
    p.loc[futuro, "deal_stage"] = trocado.fillna(p.loc[futuro, "deal_stage"])
    return dataclasses.replace(dados, pipeline=p)


def test_filas_em_2018_01_01(s):
    assert s.fila.value_counts().to_dict() == {
        "encerrar": 1474, "iniciar": 500, "preparar": 108, "fechar": 7}
    assert len(s) == 2089 and s.vendedor.nunique() == 27


def test_valor_por_fila(s):
    v = s.groupby("fila").valor_tabela.sum().round().astype(int).to_dict()
    assert v == {"encerrar": 3656299, "fechar": 16385, "iniciar": 1073986, "preparar": 219545}


def test_valor_esperado_total(s):
    assert round(s.ve_trimestre.sum(), 2) == 65482.05
    assert round(s.ve_28.sum(), 2) == 2699.05


def test_fila_fechar_e_so_deal_novo_na_virada_do_trimestre(s):
    f = s[s.fila == "fechar"]
    assert len(f) == 7 and f.idade.max() <= 15
    assert set(f.opportunity_id) == {"NGTVHTFH", "RDHTQLNI", "DB801ISB", "HB740BLB",
                                     "RTWE19SU", "T6MPH7JC", "HCQK8NQ8"}


def test_indice_monotono_com_a_ordem(s):
    viv = s[s.estado == "vivo"]
    assert viv.indice.between(1, 100).all()
    assert (s[s.estado == "vencido"].indice == 0).all()
    assert s[s.estado == "sem_data"].indice.isna().all()
    for _, x in viv.groupby("vendedor"):
        assert x.sort_values(["fila_ordem", "posicao"]).indice.diff().dropna().le(0).all()


def test_foco_cabe_e_ignora_encerrar(s, config):
    foco = s[s.em_foco]
    assert (foco.groupby("vendedor").size() <= config["foco_por_vendedor"]).all()
    assert (foco.fila != "encerrar").all() and len(foco) == 127


def test_ordem_dentro_do_vendedor(s):
    x = s[(s.vendedor == "Boris Faz") & s.em_foco].sort_values("indice", ascending=False)
    assert list(x.opportunity_id) == ["NGTVHTFH", "I5VHXAWW", "BREOLQD9", "EP5QRHID", "W4XB23IP"]


def test_vendedor_sem_deal(s, dados):
    assert "Carl Lin" not in set(s.vendedor)   # tratado na Tarefa 5, não aqui


def test_pontuacao_independe_do_futuro(dados, config):
    """A lista de uma data não muda quando o futuro é alterado."""
    d1 = pontuar_em(dados, config, pd.Timestamp("2017-08-28"))
    alterado = _apagar_desfechos_depois_de(dados, pd.Timestamp("2017-10-01"))
    d2 = pontuar_em(alterado, config, pd.Timestamp("2017-08-28"))
    assert d1.equals(d2)
