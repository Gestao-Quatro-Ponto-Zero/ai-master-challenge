"""ID, busca e motivo em linguagem de atendimento."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from registro import formatar_id, hora_brt, motivo_atendimento, normalizar_busca, proximo_id  # noqa: E402


def test_id_sequencial(tmp_path):
    arq = tmp_path / "c.jsonl"
    assert proximo_id(arq) == "ATD-00001"
    arq.write_text(json.dumps({"id": "ATD-00007"}) + "\n" + json.dumps({"id": "ATD-00003"}) + "\n")
    assert proximo_id(arq) == "ATD-00008"


@pytest.mark.parametrize("busca", ["ATD-00044", "atd-44", "44", " ATD44 "])
def test_busca_aceita_formas_diferentes(busca):
    assert normalizar_busca(busca) == "ATD-00044"


def test_busca_sem_numero():
    assert normalizar_busca("abc") is None


def test_hora_em_brasilia():
    assert hora_brt("2026-11-11T15:13:45+00:00") == "11/11/2026 12:13"


@pytest.mark.parametrize("destino, tecnico, esperado", [
    ("fila", "confiança 0.89 ≥ 0.8: vai direto para a fila de Hardware", "encaminhada ao time de Hardware"),
    ("pessoa executa", "reembolso: a IA registra o pedido", "Pedido de reembolso"),
    ("pessoa executa", "alteração de cobrança: a IA registra", "Pedido de alteração de cobrança"),
    ("triagem humana", "IA conversacional indisponível (Timeout): uma pessoa assume", "fora do ar"),
    ("triagem humana", "problema não descrito depois de 3 perguntas: uma pessoa assume", "não explicou o problema"),
    ("triagem humana", "confiança 0.46 < 0.8 depois de 3 perguntas: uma pessoa assume", "não ficou claro"),
    ("cliente desistiu", "o cliente desistiu durante a coleta de contato", "durante a coleta"),
    ("cliente desistiu", "o cliente desistiu durante a coleta dos detalhes do pedido", "detalhes do pedido"),
    ("IA atendendo", "a IA segue o atendimento (assunto previsto: Hardware, confiança 0.91)", "ainda está atendendo"),
    ("resolvida pela IA", "o cliente confirmou que resolveu (assunto previsto: Hardware)", "Resolvida pela IA"),
    ("triagem humana", "atendimento sem IA: uma pessoa assume", "sem IA"),
    ("assistência técnica", "defeito de aparelho: o cliente é encaminhado", "assistência técnica autorizada"),
])
def test_motivo_sem_jargao_tecnico(destino, tecnico, esperado):
    m = motivo_atendimento(destino, tecnico, "Hardware", "notebook não liga")
    assert esperado in m
    for jargao in ("confiança", "0.8", "≥", "IA registra", "Timeout"):
        assert jargao not in m


def test_formatar_id():
    assert formatar_id(68) == "ATD-00068"


def test_motivo_de_cobranca_traz_valor_e_pedido():
    m = motivo_atendimento("pessoa executa", "cobrança duplicada: a IA registra", "Diversos", "cobrança em dobro",
                           {"valor": "R$ 189,90", "pedido": "pedido 4602"})
    assert m.startswith("Pedido sobre cobrança duplicada") and "Valor: R$ 189,90" in m and "Pedido: pedido 4602" in m


def test_sem_link_desarma_imagem_e_link_do_markdown():
    from registro import sem_link
    assert sem_link("veja ![x](https://mal.example/p.png)") == "veja !\\[x]\\(https://mal.example/p.png)"
    assert sem_link("[clique](https://mal.example)") == "[clique]\\(https://mal.example)"
    assert sem_link("1. Reinicie o computador.") == "1. Reinicie o computador."
    assert sem_link(None) == ""


def test_literal_mostra_a_mascara_sem_virar_italico():
    from registro import literal
    assert literal("***.***.003-88") == "\\*\\*\\*.\\*\\*\\*.003-88"
    assert literal("(11) *****-6804") == "(11) \\*\\*\\*\\*\\*-6804"
    assert literal("a_b@x.com") == "a\\_b@x.com"
    assert literal("![x](y)") == "!\\[x]\\(y)"
    assert literal(None) == ""
