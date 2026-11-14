"""Regra de proximidade da assistência e leitura de CEP e sim/não (funções puras)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from assistencias import (ASSISTENCIAS, CADASTROS, cep_valido, mais_proxima, mascarar_cep,  # noqa: E402
                          resposta_sim_nao)
from dados_pessoais import cpf_valido  # noqa: E402


def test_cpfs_de_exemplo_sao_validos():
    assert all(cpf_valido(c) for c in CADASTROS)


def test_mais_proxima_pela_regiao_do_cep():
    assert mais_proxima("13025000").cidade == "Campinas"
    assert mais_proxima("05422000").cidade == "São Paulo"
    assert mais_proxima("22020001").cidade == "Rio de Janeiro"
    assert mais_proxima("51020000").cidade == "Recife"
    assert mais_proxima("88010000").cidade == "Curitiba"      # Florianópolis: mesma região postal 8
    assert mais_proxima("69000000").cidade in {a.cidade for a in ASSISTENCIAS}


def test_cadastro_de_cada_capital_cai_na_assistencia_da_mesma_cidade():
    for cad in CADASTROS.values():
        if cad.cidade != "Sorocaba":
            assert mais_proxima(cad.cep).cidade == cad.cidade


def test_cep_valido():
    assert cep_valido("13025-000") == "13025000"
    assert cep_valido("meu cep é 13.025-000") == "13025000"
    assert cep_valido("1302500") is None
    assert cep_valido("00000-000") is None
    assert mascarar_cep("13025000") == "13025-***"


def test_resposta_sim_nao():
    assert resposta_sim_nao("sim") is True
    assert resposta_sim_nao("Isso mesmo") is True
    assert resposta_sim_nao("não, estou no trabalho") is False
    assert resposta_sim_nao("nao") is False
    assert resposta_sim_nao("talvez") is None
