import json
from types import SimpleNamespace

import pytest

import ia.briefing as briefing
from build import construir
from ia.briefing import MODELO_FIXO, gerar


@pytest.fixture
def scored(dados_dir, config, tmp_path):
    construir(dados_dir, config, saida=tmp_path, hoje="2018-01-01")
    return json.loads((tmp_path / "scored.json").read_text(encoding="utf-8"))


class ClienteFalso:
    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.chamadas = []
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.chamadas.append(kwargs)
        texto, stop, entrada, saida = self.respostas.pop(0) if len(self.respostas) > 1 else self.respostas[0]
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=texto)],
            stop_reason=stop,
            usage=SimpleNamespace(input_tokens=entrada, output_tokens=saida),
        )


def _sempre(texto, stop="end_turn", entrada=100, saida=20):
    return ClienteFalso([(texto, stop, entrada, saida)])


def test_modelo_e_fixo_e_outro_modelo_e_recusado(scored):
    with pytest.raises(ValueError):
        gerar(scored, modelo="claude-sonnet-5-5", sem_ia=True)


def test_resposta_valida_vira_ia_e_passa_no_validador(scored):
    cliente = _sempre("{nome}, semana {semana_do_trimestre} do trimestre. Você tem {n_fechar} deal(s).")
    b = gerar(scored, cliente=cliente)
    v = b["vendedores"]["Boris Faz"]
    assert v["origem"] == "ia" and "Boris Faz" in v["texto"] and "{" not in v["texto"]
    assert b["modelo"] == MODELO_FIXO


def test_limites_de_tokens_e_parametros_do_haiku(scored):
    cliente = _sempre("{nome}, semana {semana_do_trimestre} do trimestre.")
    gerar(scored, cliente=cliente)
    tamanhos = {c["max_tokens"] for c in cliente.chamadas}
    assert tamanhos == {briefing.LIMITE_TOKENS["vendedor"], briefing.LIMITE_TOKENS["gestor"]}
    for c in cliente.chamadas:
        assert c["model"] == MODELO_FIXO
        assert c["thinking"] == {"type": "disabled"}
        assert c["output_config"] == {"effort": "low"}
        assert "temperature" not in c


def test_resposta_invalida_repete_uma_vez_e_cai_no_template(scored):
    cliente = _sempre("Ligue para a Acme Corporation hoje.")
    b = gerar(scored, cliente=cliente)
    v = b["vendedores"]["Boris Faz"]
    assert v["origem"] == "template" and v["motivo"] is None
    assert any(r["item"] == "Boris Faz" for r in b["recusas"])
    chamadas_boris = [c for c in cliente.chamadas if "Boris Faz" in c["messages"][0]["content"]]
    assert len(chamadas_boris) == briefing.TENTATIVAS_POR_ITEM


def test_parada_incompleta_nao_e_aceita(scored):
    cliente = _sempre("{nome}, semana", stop="max_tokens")
    b = gerar(scored, cliente=cliente)
    assert all(v["origem"] == "template" for v in b["vendedores"].values())
    assert any("parada incompleta" in r["motivo"] for r in b["recusas"])


def test_teto_de_chamadas_limita_o_gasto(scored, monkeypatch):
    monkeypatch.setattr(briefing, "TETO_CHAMADAS", 3)
    cliente = _sempre("{nome}, semana {semana_do_trimestre} do trimestre.")
    b = gerar(scored, cliente=cliente)
    assert b["chamadas"] == 3 and len(cliente.chamadas) == 3
    assert any(v["origem"] == "template" for v in b["vendedores"].values())


def test_custo_segue_o_preco_do_haiku(scored):
    cliente = _sempre("{nome}, semana {semana_do_trimestre} do trimestre.", entrada=1000, saida=100)
    b = gerar(scored, cliente=cliente)
    esperado = round(b["tokens_entrada"] * 0.10 / 1e6 + b["tokens_saida"] * 0.50 / 1e6, 6)
    assert b["custo_estimado_usd"] == esperado and b["custo_estimado_usd"] > 0


def test_sem_chave_e_sem_cliente_vai_para_template(scored, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    b = gerar(scored)
    assert b["modelo"] == "template" and b["custo_estimado_usd"] == 0.0
    assert all(v["origem"] == "template" for v in b["vendedores"].values())
