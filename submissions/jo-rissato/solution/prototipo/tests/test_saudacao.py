"""Saudação, nome da atendente e frase de espera da ligação (pedido do Jó em 2026-11-16 21:16 BRT).

Na ligação ATD-00442 o cliente disse só "Oi, tudo bem?" e a atendente respondeu "Já anotei o que você contou":
"tudo" e "bem" contavam como palavras úteis e o cumprimento virava relato."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

import conversa as cv  # noqa: E402
import ligacao  # noqa: E402
import voz  # noqa: E402
from config import NOME_ATENDENTE  # noqa: E402
from modelo import carregar  # noqa: E402
from roteador import palavras_uteis  # noqa: E402


@pytest.fixture(scope="module")
def modelo():
    return carregar()


@pytest.fixture
def sem_rede(monkeypatch, tmp_path):
    def proibido(*_a, **_k):
        raise AssertionError("cumprimento não pode chamar a IA externa")
    monkeypatch.setattr(cv.requests, "post", proibido)
    monkeypatch.setattr(cv, "chave_deepseek", lambda: "chave-de-teste")
    monkeypatch.setattr(cv, "CONVERSAS", tmp_path / "conversas.jsonl")


@pytest.mark.parametrize("texto", ["Oi, tudo bem?", "Olá, tudo bom?", "Oi, boa noite, como vai você?",
                                   "E aí, beleza?", "Alô, tudo certo?"])
def test_cumprimento_nao_e_relato(texto):
    assert palavras_uteis(texto) < 2


@pytest.mark.parametrize("texto", ["Oi, tudo bem?", "Boa noite! Tudo bem com você?"])
def test_atd_00442_cumprimento_nao_vira_anotado(modelo, sem_rede, texto):
    c = cv.Conversa(modelo, canal="telefone")
    r = c.receber(texto)
    assert c.relato == []
    assert "anotei" not in r.resposta.lower() and "Vou te ajudar com isso" not in r.resposta
    assert "Tudo bem, sim, obrigada." in r.resposta and NOME_ATENDENTE in r.resposta
    assert c.etapa == "nome"


def test_relato_na_primeira_fala_e_reconhecido(modelo, sem_rede):
    c = cv.Conversa(modelo, canal="chat")
    r = c.receber("Meu pedido não chegou e já passou da data prevista.")
    assert c.relato and "Vou te ajudar com isso. Antes, como posso te chamar?" in r.resposta
    assert NOME_ATENDENTE in r.resposta


def test_ligacao_nao_se_apresenta_duas_vezes(modelo, sem_rede):
    assert NOME_ATENDENTE in voz.SAUDACAO
    c = cv.Conversa(modelo, canal="telefone")
    c.voz = True
    r = c.receber("Oi, tudo bem?")
    assert r.resposta == "Tudo bem, sim, obrigada. Como posso te chamar?"
    c2 = cv.Conversa(modelo, canal="telefone")
    c2.voz = True
    assert c2.receber("Oi").resposta == "Oi! Como posso te chamar?"


def test_nome_no_prompt_e_na_assinatura():
    assert f"Você é a {NOME_ATENDENTE}" in cv.SISTEMA
    assert NOME_ATENDENTE in cv.ASSINATURA


def test_espera_intercalada_e_variada():
    # Jó, 2026-11-16 23:08 BRT: duas respostas sem a frase de espera, a terceira com.
    assert ligacao.ESPERA_A_CADA == 3 and ligacao.ESPERA_MS <= 1500
    assert len(set(ligacao.FRASES_ESPERA)) >= 3 and "Um instante." not in ligacao.FRASES_ESPERA
    fonte = Path(ligacao.__file__).read_text(encoding="utf-8")
    assert "S.enviado % S.cfg.esperaACada !== 0" in fonte   # o navegador toca só na 3ª, 6ª, 9ª fala
    assert "ultimaEspera" not in fonte


def test_devolve_bom_dia(modelo, sem_rede):
    c = cv.Conversa(modelo, canal="chat")
    assert c.receber("Boa noite!").resposta.startswith(f"Boa noite! Aqui é a {NOME_ATENDENTE}")
    c2 = cv.Conversa(modelo, canal="telefone")
    c2.voz = True
    assert c2.receber("Oi, bom dia.").resposta == "Bom dia! Como posso te chamar?"
