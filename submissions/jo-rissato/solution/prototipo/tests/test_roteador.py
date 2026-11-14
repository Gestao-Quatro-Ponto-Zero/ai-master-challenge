"""Testes das regras do roteador (sem rede, sem modelo)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from modelo import preparar  # noqa: E402
from roteador import (ATENDENDO, ENCERRADA, EXECUCAO, FILA, RESOLVIDA, TRIAGEM, acao_sensivel, decidir,  # noqa: E402
                      decidir_lote, desistiu, palavras_uteis)


@pytest.mark.parametrize("texto, esperado", [
    ("Quero o reembolso do meu pedido", "reembolso"),
    ("please refund my order", "reembolso"),
    ("preciso cancelar a assinatura", "cancelamento"),
    ("quero cancelar", "cancelamento"),
    ("I want to cancel my subscription", "cancelamento"),
    ("fui cobrado duas vezes no cartão", "cobrança duplicada"),
    ("veio uma cobrança duplicada na fatura", "cobrança duplicada"),
    ("there is a wrong charge on my invoice", "cobrança indevida"),
    ("fui cobrado a mais esse mês", "cobrança indevida"),
    ("meu notebook não liga", None),
    ("como funciona a cobrança do plano?", None),
    ("cliquei em cancelar e a janela fechou", None),
    ("my laptop screen is broken", None),
])
def test_acao_sensivel(texto, esperado):
    assert acao_sensivel(texto) == esperado


def test_sem_pedido_de_dinheiro_a_ia_segue_atendendo():
    assert decidir("Hardware", 0.95, None).destino == ATENDENDO
    assert decidir("Storage", 0.2, None).destino == ATENDENDO


def test_so_reembolso_e_cancelamento_passam_para_o_time():
    for tipo in ("reembolso", "cancelamento", "cobrança duplicada", "cobrança indevida"):
        d = decidir("Purchase", 0.3, tipo)
        assert d.destino == EXECUCAO and d.motivo.startswith(tipo)


def test_resolvido_encerra_como_resolvida_pela_ia():
    assert decidir("Access", 0.9, None, resolvido=True).destino == RESOLVIDA


def test_pedido_de_dinheiro_vale_mais_que_resolvido():
    assert decidir("Access", 0.9, "reembolso", resolvido=True).destino == EXECUCAO


def test_desistencia_encerra():
    assert desistiu("não quero mais, pode esquecer")
    assert desistiu("deixa pra lá")
    assert not desistiu("meu notebook não liga")
    assert not desistiu("não quero mais esperar, meu notebook não liga")
    assert not desistiu("esqueci minha senha")
    assert decidir("Storage", 0.9, "reembolso", desistencia=True).destino == ENCERRADA


def test_lote():
    assert decidir_lote(0.81) == FILA
    assert decidir_lote(0.79) == TRIAGEM


def test_preparar_fica_no_formato_do_dataset2():
    assert preparar("Meu Laptop #42 não liga!!") == "meu laptop n o liga"


def test_saudacao_nao_e_problema():
    assert palavras_uteis("hello i need help") == 0
    assert palavras_uteis("olá, bom dia, preciso de ajuda") == 0
    assert palavras_uteis("my laptop screen is broken") >= 2


def test_defeito_de_aparelho_vai_para_assistencia_mesmo_se_aliviou():
    from roteador import ASSISTENCIA
    assert decidir("Hardware", 0.9, None, resolvido=True, assistencia=True).destino == ASSISTENCIA
    assert decidir("Hardware", 0.9, "reembolso", assistencia=True).destino == EXECUCAO
