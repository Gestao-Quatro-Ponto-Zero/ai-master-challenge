import pytest

from motor.aprender import carga_referencia, tabela_destino
from motor.carregar import recortar
from motor.explicar import explicar, resumo_vendedor
from motor.janela import aprender_janela


@pytest.fixture(scope="session")
def ctx(dados, config, hoje):
    r = recortar(dados, hoje)
    j = aprender_janela(r, config)
    t = tabela_destino(r, j, config, hoje)
    c = carga_referencia(r, hoje)
    return j, t, c


def _explica(s, linha, j, t):
    return explicar(linha, j, t, s[s.vendedor == linha.vendedor])


def test_cartao_valor_formatado(s, ctx):
    j, t, _ = ctx
    linha = s[s.opportunity_id == "RDHTQLNI"].iloc[0]
    assert "US$ 5.482" in _explica(s, linha, j, t)["cartoes"]["valor"]


def test_momento_preparar_fala_do_fim_do_trimestre(s, ctx):
    j, t, _ = ctx
    linha = s[s.fila == "preparar"].iloc[0]
    m = _explica(s, linha, j, t)["cartoes"]["momento"]
    assert "até o fim" in m and "quatro semanas seguintes" not in m


def test_momento_fechar_usa_taxa_medida(s, ctx):
    j, t, _ = ctx
    linha = s[s.fila == "fechar"].iloc[0]
    assert "35 em cada 100" in _explica(s, linha, j, t)["cartoes"]["momento"]


def test_momento_encerrar_por_trimestre_nomeia_o_trimestre(s, ctx):
    j, t, _ = ctx
    linha = s[(s.fila == "encerrar") & (s.idade <= j.ciclo_max)].iloc[0]
    m = _explica(s, linha, j, t)["cartoes"]["momento"]
    assert "trimestre" in m and str(j.ciclo_max) not in m


def test_momento_encerrar_por_idade_nomeia_o_ciclo(s, ctx):
    j, t, _ = ctx
    linha = s[(s.fila == "encerrar") & (s.idade > j.ciclo_max)].iloc[0]
    assert str(j.ciclo_max) in _explica(s, linha, j, t)["cartoes"]["momento"]


def test_momento_iniciar_nao_estima(s, ctx):
    j, t, _ = ctx
    linha = s[s.fila == "iniciar"].iloc[0]
    assert "não há como estimar" in _explica(s, linha, j, t)["cartoes"]["momento"]


def test_nao_sabe_tem_quatro_itens_sem_conta(s, ctx):
    j, t, _ = ctx
    com_conta = s[(s.fila == "fechar") & s.conta.notna()].iloc[0]
    sem_conta = s[s.conta.isna()].iloc[0]
    assert len(_explica(s, com_conta, j, t)["nao_sabe"]) == 3
    assert len(_explica(s, sem_conta, j, t)["nao_sabe"]) == 4


def test_resumo_vendedor_sem_deal(s, ctx):
    _, _, c = ctx
    r = resumo_vendedor("Carl Lin", s[s.vendedor == "Carl Lin"], c)
    assert r["vivos"] == 0 and r["carga_referencia"] == 0.0
    assert all(v["n"] == 0 and v["valor"] == 0 for v in r["por_fila"].values())
    assert isinstance(r["frase_vazio"], str) and r["frase_vazio"]


def test_resumo_vendedor_com_deal_nao_tem_frase_de_vazio(s, ctx):
    _, _, c = ctx
    sub = s[s.vendedor == "Boris Faz"]
    r = resumo_vendedor("Boris Faz", sub, c)
    assert r["vivos"] > 0 and r["frase_vazio"] is None
