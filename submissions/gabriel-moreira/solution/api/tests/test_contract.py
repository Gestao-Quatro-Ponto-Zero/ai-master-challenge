"""Testes de contrato dos endpoints principais e casos de erro — sem
identificação prévia, já que o RBAC foi removido."""


def test_deals_no_auth_required(client):
    resp = client.get("/deals")
    assert resp.status_code == 200


def test_deals_invalid_estado_returns_422(client):
    resp = client.get("/deals", params={"estado": "inexistente"})
    assert resp.status_code == 422
    assert "foco_urgente" in resp.text


def test_deals_no_estado_returns_all(client):
    resp = client.get("/deals")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2089
    estados = {row["estado"] for row in body["items"]}
    assert estados.issubset(
        {"foco_urgente", "acompanhar", "engajar", "qualificar", "desistir"}
    )


def test_deals_unknown_product_filter_returns_empty_not_error(client):
    resp = client.get("/deals", params={"product": "Produto Que Nao Existe"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0


def test_deals_sorted_by_score_desc_by_default(client):
    resp = client.get("/deals")
    scores = [row["score"] for row in resp.json()["items"]]
    assert scores == sorted(scores, reverse=True)


def test_deals_invalid_sort_returns_422(client):
    resp = client.get("/deals", params={"sort": "inexistente"})
    assert resp.status_code == 422


def test_deals_invalid_order_returns_422(client):
    resp = client.get("/deals", params={"order": "inexistente"})
    assert resp.status_code == 422


def test_kpis_reflects_filter(client):
    resp = client.get("/kpis", params={"sales_agent": "Anna Snelling"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["data_inicio"] and body["data_fim"]
    assert body["indicadores_historicos"] == ["receita_ganha", "maior_negocio_fechado"]


def test_rollup_available_to_anyone(client):
    resp = client.get("/rollup")
    assert resp.status_code == 200
    assert len(resp.json()["linhas"]) > 0


def test_rollup_filtered_by_manager(client):
    resp = client.get("/rollup", params={"manager": "Dustin Brinkmann"})
    assert resp.status_code == 200
    linhas_agente = [linha for linha in resp.json()["linhas"] if linha["nivel"] == "sales_agent"]
    assert len(linhas_agente) == 5  # 5 agentes no time


def test_score_avulsa_prospecting_without_age(client):
    resp = client.post("/score", json={"product": "GTX Basic"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["urgencia"] == 0.47
    assert body["age_days"] is None
    assert body["confianca_label"]
    assert 2 <= len(body["plano_de_acao_passos"]) <= 4


def test_score_avulsa_negative_age_returns_422(client):
    resp = client.post("/score", json={"product": "GTX Basic", "age_days": -5})
    assert resp.status_code == 422


def test_score_avulsa_unknown_product_enumerates_valid(client):
    resp = client.post("/score", json={"product": "Inexistente"})
    assert resp.status_code == 422
    assert "GTK 500" in resp.text


def test_export_csv_open_to_anyone(client):
    resp = client.get("/export/csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")


def test_as_of_propagates_to_age_dependent_routes(client):
    resp_default = client.get("/deals")
    resp_early = client.get("/deals", params={"as_of": "2017-06-30"})
    assert resp_default.status_code == resp_early.status_code == 200

    by_id_default = {row["opportunity_id"]: row for row in resp_default.json()["items"]}
    by_id_early = {row["opportunity_id"]: row for row in resp_early.json()["items"]}
    comuns = set(by_id_default) & set(by_id_early)
    algum_diferente = any(
        by_id_default[i]["age_days"] != by_id_early[i]["age_days"] for i in comuns
    )
    assert algum_diferente

    resp_kpis_early = client.get("/kpis", params={"as_of": "2017-06-30"})
    assert resp_kpis_early.status_code == 200


def test_deals_page_size_respects_default_and_max(client):
    resp = client.get("/deals")
    assert resp.json()["page_size"] == 100

    resp_max = client.get("/deals", params={"page_size": 500})
    assert resp_max.status_code == 200

    resp_over = client.get("/deals", params={"page_size": 501})
    assert resp_over.status_code == 422
