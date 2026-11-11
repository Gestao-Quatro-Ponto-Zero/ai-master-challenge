import pandas as pd

from motor.aprender import carga_referencia, datas_analogas, tabela_destino
from motor.carregar import recortar
from motor.janela import aprender_janela


def _ctx(dados, config, hoje):
    r = recortar(dados, hoje)
    return r, aprender_janela(r, config), config, hoje


def test_datas_analogas(dados, hoje):
    assert datas_analogas(recortar(dados, hoje), hoje) == [
        pd.Timestamp("2017-10-01"), pd.Timestamp("2017-07-01"), pd.Timestamp("2017-04-01")]


def test_relogio_do_trimestre(dados, config, hoje):
    t = tabela_destino(*_ctx(dados, config, hoje))
    assert t.loc["1-15", "n"] == 1117 and t.loc["1-15", "decidiram_28d"] == 395
    assert round(t.loc["1-15", "p_decide"], 3) == 0.354
    velhas = t.drop(index="1-15")
    assert velhas.n.sum() == 3618 and velhas.decidiram_28d.sum() == 0   # o achado central
    assert t.loc["16-30", "decidiram_trimestre"] == 691                  # mas no trimestre decidem


def test_probabilidades_sao_validas(dados, config, hoje):
    t = tabela_destino(*_ctx(dados, config, hoje))
    for c in ["p_decide", "p_ganha_28d", "p_ganha_trimestre"]:
        assert t[c].between(0, 1).all() and t[c].notna().all()
    assert (t.p_ganha_trimestre <= t.decidiram_trimestre / t.n + 1e-9).all()


def test_nao_ha_vies_de_sobrevivencia(dados, config, hoje):
    """A fórmula do v1 dava 100% aos 120 dias; a tabela com os abertos em risco dá quase zero."""
    t = tabela_destino(*_ctx(dados, config, hoje))
    assert t.loc["106-120", "p_decide"] < 0.05 and t.loc["121-138", "p_decide"] < 0.05


def test_faixa_rala_e_agrupada(dados, config, hoje):
    cfg = {**config, "n_min_faixa": 500}
    t = tabela_destino(*_ctx(dados, cfg, hoje))
    assert t.agrupada.any() and (t.n >= 500).all()


def test_carga_de_referencia(dados, config, hoje):
    c = carga_referencia(recortar(dados, hoje), hoje)
    assert len(c) == 30 and c.median() == 33.0 and c.min() == 12.0 and c.max() == 77.0


def test_sem_analoga_devolve_tabela_vazia(dados, config):
    d = pd.Timestamp("2017-04-15")
    t = tabela_destino(*_ctx(dados, config, d))
    assert len(t) > 0 and (t.p_decide == 0).all() and t.motivo.notna().all()
