"""Task 6.5 — contrato de carga/sobrecarga e fit no detalhe."""


def test_carga_de_um_escritorio(client):
    resp = client.get("/carga", params={"regional_office": "Central"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["escritorios"]) == 1
    central = body["escritorios"][0]
    assert central["regional_office"] == "Central"

    qualificar = next(e for e in central["estados"] if e["estado"] == "qualificar")
    darcel = next(v for v in qualificar["vendedores"] if v["sales_agent"] == "Darcel Schlecht")
    assert darcel["contagem"] == 92
    assert round(qualificar["media_escritorio"], 2) == 44.30
    assert darcel["sobrecarregado"] is True


def test_carga_nunca_inclui_revisao_lote(client):
    resp = client.get("/carga")
    body = resp.json()
    for escritorio in body["escritorios"]:
        for estado in escritorio["estados"]:
            assert estado["estado"] != "revisao_lote"


def test_carga_com_data_de_referencia_recalcula(client):
    resp_default = client.get("/carga", params={"regional_office": "Central"})
    resp_early = client.get("/carga", params={"regional_office": "Central", "as_of": "2017-06-30"})
    assert resp_default.status_code == 200
    assert resp_early.status_code == 200
    assert resp_default.json() != resp_early.json()


def test_listagem_sobrecarregados_agrupavel_por_vendedor(client):
    resp = client.get("/deals/sobrecarregados", params={"page_size": 500})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 227
    for item in body["items"]:
        assert "sugestao" in item
        assert item["contagem"] >= 5


def test_listagem_geral_sem_vendedor_sugerido(client):
    resp = client.get("/deals", params={"sobrecarga": True, "page_size": 500})
    body = resp.json()
    assert body["total"] > 0
    for item in body["items"]:
        assert item["sobrecarregado"] is True
        assert "sugestao" not in item
        assert "vendedor_sugerido" not in item


def test_filtro_sobrecarga_restringe_listagem(client):
    resp_all = client.get("/deals", params={"page_size": 1})
    resp_filtered = client.get("/deals", params={"sobrecarga": True, "page_size": 1})
    assert resp_filtered.json()["total"] < resp_all.json()["total"]
    assert resp_filtered.json()["total"] == 227


def test_deal_detail_fit_do_vendedor_atual(client):
    resp = client.get("/deals", params={"sales_agent": "Darcel Schlecht", "estado": "qualificar", "page_size": 1})
    deal_id = resp.json()["items"][0]["opportunity_id"]

    detail = client.get(f"/deals/{deal_id}").json()
    assert detail["fit_produto"]["disponivel"] is True
    assert detail["fit_produto"]["n"] is not None
    assert "ressalva_fit" in detail
    assert detail["sobrecarregado"] is True
    assert detail["sugestao"]["disponivel"] is True
    assert detail["sugestao"]["sales_agent"] != "Darcel Schlecht"


def test_deal_detail_sem_conta_setor_indisponivel(client):
    page = 1
    while True:
        resp = client.get("/deals", params={"page_size": 500, "page": page})
        body = resp.json()
        candidato = next((r for r in body["items"] if r["account"] is None), None)
        if candidato is not None:
            break
        page += 1
        if page > body["total_pages"]:
            raise AssertionError("nenhuma oportunidade sem conta encontrada")

    detail = client.get(f"/deals/{candidato['opportunity_id']}").json()
    assert detail["fit_setor"]["disponivel"] is False
    assert detail["fit_setor"]["valor"] is None
    assert detail["fit_produto"]["disponivel"] is True


def test_deal_detail_sem_sobrecarga_nao_tem_sugestao(client):
    resp = client.get("/deals", params={"page_size": 500})
    body = resp.json()
    candidato = next(r for r in body["items"] if not r["sobrecarregado"])
    detail = client.get(f"/deals/{candidato['opportunity_id']}").json()
    assert detail["sugestao"] is None
