from avaliacao.backtest import backtest, razao_com_ic
from avaliacao.permutacao import historico as _historico
from avaliacao.permutacao import permutacao


def test_backtest_as_of(dados, config):
    r = backtest(dados, config)
    assert len(r) == 6
    assert r.valor_relogio.sum() == 1097324 and r.valor_preco_prazo.sum() == 842462
    # aleatório: média de 200 rodadas de sorteio por deal; o protótipo sorteava uma vez por posição (334520)
    assert round(r.valor_aleatorio.sum()) == 318622 and r.valor_oraculo.sum() == 2666327


def test_relogio_bate_a_melhor_alternativa_honesta(dados, config):
    razao, lo, hi = razao_com_ic(backtest(dados, config, detalhado=True), "relogio", "preco_prazo")
    assert round(razao, 2) == 1.30 and lo > 1.0        # o IC não cruza 1
    assert (round(lo, 2), round(hi, 2)) == (1.13, 1.52)


def test_a_vantagem_nao_e_mistura_de_preco(dados, config):
    r = backtest(dados, config)
    assert round(r.acerto_relogio.mean(), 3) == 0.227
    assert round(r.acerto_preco_prazo.mean(), 3) == 0.154
    assert round(r.acerto_aleatorio.mean(), 3) == 0.147


def test_fracao_do_teto(dados, config):
    r = backtest(dados, config)
    assert round(r.valor_relogio.sum() / r.valor_oraculo.sum(), 3) == 0.412
    assert round(r.valor_preco_prazo.sum() / r.valor_oraculo.sum(), 3) == 0.316


def test_nenhum_vencido_ganhou(dados, config):
    assert (backtest(dados, config).vencidos_ganhos == 0).all()


def test_atributos_nao_predizem_o_ganho(dados, config):
    h = _historico(dados, config)
    for chave in ["conta", "vendedor", "porte"]:
        assert permutacao(h, chave, estratificar_por="mes_do_trimestre", n=1000)["p"] > 0.05
