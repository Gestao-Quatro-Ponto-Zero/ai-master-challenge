import pandas as pd

from motor.carregar import recortar
from motor.janela import aprender_janela, estado, prazo_do_deal


def test_janela_aprendida_no_fim_do_export(dados, config, hoje):
    j = aprender_janela(recortar(dados, hoje), config)
    assert j.ciclo_max == 138 and j.n_fechamentos == 6711
    assert j.fechamentos_apos_prazo == 1 and j.usa_prazo_trimestre is True


def test_regra_do_trimestre_ja_valia_no_passado(dados, config):
    for d, n in [("2017-07-01", 2679), ("2017-10-01", 4726)]:
        j = aprender_janela(recortar(dados, pd.Timestamp(d)), config)
        assert j.ciclo_max == 138 and j.n_fechamentos == n
        assert j.fechamentos_apos_prazo == 0 and j.usa_prazo_trimestre is True


def test_estado_em_2018_01_01(dados, config, hoje):
    r = recortar(dados, hoje)
    j = aprender_janela(r, config)
    e = estado(r.pipeline, j, hoje)
    assert (e == "vivo").sum() == 115 and (e == "sem_data").sum() == 500
    venc = r.pipeline[e == "vencido"]
    idade = (hoje - venc.engage_date).dt.days
    assert len(venc) == 1474 and (idade > 138).sum() == 1301 and (idade <= 138).sum() == 173


def test_prazo_do_deal_pega_o_limite_mais_curto(dados, config, hoje):
    r = recortar(dados, hoje)
    j = aprender_janela(r, config)
    # prazo_do_deal opera sobre engage_dates válidos; NaT (Prospecting) são excluídos
    engage = r.pipeline.engage_date.dropna()
    p = prazo_do_deal(engage, j)
    por_idade = engage + pd.Timedelta(days=138)
    assert (p <= por_idade).all() and (p < por_idade).sum() > 0


def test_sem_fechamentos_suficientes_desliga_a_regra(dados, config):
    j = aprender_janela(recortar(dados, pd.Timestamp("2017-03-15")), config)
    assert j.usa_prazo_trimestre is False
