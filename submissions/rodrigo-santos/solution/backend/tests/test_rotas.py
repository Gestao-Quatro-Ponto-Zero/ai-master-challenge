"""Testes das rotas da API."""

from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def test_pipeline_sem_filtros_retorna_todos_os_abertos():
    resposta = cliente.get("/api/pipeline")
    assert resposta.status_code == 200
    assert resposta.json()["total"] == 2089


def test_pipeline_filtra_por_vendedor():
    vendedor = cliente.get("/api/filtros").json()["vendedores"][0]
    deals = cliente.get("/api/pipeline", params={"vendedor": vendedor}).json()["deals"]
    assert deals
    assert all(d["vendedor"] == vendedor for d in deals)


def test_detalhe_do_deal():
    id_deal = cliente.get("/api/pipeline").json()["deals"][0]["id"]
    deal = cliente.get(f"/api/deals/{id_deal}").json()
    assert deal["id"] == id_deal
    assert deal["motivos"]
    assert deal["sugestao"]


def test_detalhe_mostra_pontos_que_somam_o_score():
    id_deal = cliente.get("/api/pipeline").json()["deals"][-1]["id"]
    deal = cliente.get(f"/api/deals/{id_deal}").json()
    assert sum(p["pontos"] for p in deal["partes"]) == deal["score"]


def test_detalhe_de_deal_inexistente_retorna_404():
    assert cliente.get("/api/deals/NAOEXISTE").status_code == 404


def test_resumo_bate_com_pipeline():
    resumo = cliente.get("/api/resumo", params={"prioridade": "Alta"}).json()
    pipeline = cliente.get("/api/pipeline", params={"prioridade": "Alta"}).json()
    assert resumo["total_abertos"] == pipeline["total"]
    assert resumo["qtd_prioridade_alta"] == pipeline["total"]
    assert resumo["qtd_parados"] == 0  # parado nunca é prioridade alta


def test_regras_de_pontuacao():
    regras = cliente.get("/api/regras").json()
    assert sum(regras["pontos_maximos"].values()) == 100
    assert regras["limite_alta"] > regras["limite_media"]
    assert regras["limite_dias"] == 138


def test_validacao():
    validacao = cliente.get("/api/validacao").json()
    assert validacao["parados_fechados_depois"] == 0
    assert len(validacao["atributos"]) >= 10


def test_tela_compilada_e_servida_pela_api():
    """A tela em frontend/dist precisa abrir em http://localhost:8000 (modo só Python)."""
    resposta = cliente.get("/")
    assert resposta.status_code == 200
    assert "Priorização de Deals" in resposta.text
