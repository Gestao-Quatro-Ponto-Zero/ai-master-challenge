"""Task 4.13 — testes de contrato dos endpoints principais e casos de erro."""

from tests.conftest import auth_headers


def test_identities_no_auth_required(client):
    resp = client.get("/identities")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["sales_agents"]) == 35
    assert len(body["managers"]) == 3


def test_identify_unknown_name_returns_422(client):
    resp = client.post("/identify", json={"name": "Fulano Inexistente"})
    assert resp.status_code == 422


def test_deals_requires_token(client):
    resp = client.get("/deals")
    assert resp.status_code == 401


def test_deals_invalid_token_returns_401(client):
    resp = client.get("/deals", headers={"Authorization": "Bearer lixo-invalido"})
    assert resp.status_code == 401


def test_deals_invalid_estado_returns_422(client):
    headers = auth_headers(client, "Anna Snelling")
    resp = client.get("/deals", params={"estado": "inexistente"}, headers=headers)
    assert resp.status_code == 422
    assert "foco_urgente" in resp.text


def test_deals_no_estado_returns_all(client):
    headers = auth_headers(client, "Central")
    resp = client.get("/deals", headers=headers)
    assert resp.status_code == 200
    estados = {row["estado"] for row in resp.json()}
    assert estados.issubset(
        {"foco_urgente", "acompanhar", "engajar", "qualificar", "desistir"}
    )


def test_deals_unknown_product_filter_returns_empty_not_error(client):
    headers = auth_headers(client, "Central")
    resp = client.get("/deals", params={"product": "Produto Que Nao Existe"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_deals_sorted_by_score_desc(client):
    headers = auth_headers(client, "Central")
    resp = client.get("/deals", headers=headers)
    scores = [row["score"] for row in resp.json()]
    assert scores == sorted(scores, reverse=True)


def test_kpis_scoped_to_identity(client):
    headers = auth_headers(client, "Anna Snelling")
    resp = client.get("/kpis", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["identidade"] == "Anna Snelling"
    assert body["papel"] == "sales_agent"
    assert body["data_inicio"] and body["data_fim"]


def test_rollup_forbidden_for_sales_agent(client):
    headers = auth_headers(client, "Anna Snelling")
    resp = client.get("/rollup", headers=headers)
    assert resp.status_code == 403


def test_rollup_allowed_for_supervisor(client):
    headers = auth_headers(client, "Dustin Brinkmann")
    resp = client.get("/rollup", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["linhas"]) == 5  # 5 agentes no time


def test_score_avulsa_prospecting_without_age(client):
    headers = auth_headers(client, "Anna Snelling")
    resp = client.post("/score", json={"product": "GTX Basic"}, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["urgencia"] == 0.47
    assert body["age_days"] is None


def test_score_avulsa_negative_age_returns_422(client):
    headers = auth_headers(client, "Anna Snelling")
    resp = client.post(
        "/score", json={"product": "GTX Basic", "age_days": -5}, headers=headers
    )
    assert resp.status_code == 422


def test_score_avulsa_unknown_product_enumerates_valid(client):
    headers = auth_headers(client, "Anna Snelling")
    resp = client.post("/score", json={"product": "Inexistente"}, headers=headers)
    assert resp.status_code == 422
    assert "GTK 500" in resp.text


def test_export_requires_manager(client):
    headers = auth_headers(client, "Anna Snelling")
    resp = client.get("/export/csv", headers=headers)
    assert resp.status_code == 403


def test_as_of_propagates_to_age_dependent_routes(client):
    headers = auth_headers(client, "Central")
    resp_default = client.get("/deals", headers=headers)
    resp_early = client.get("/deals", params={"as_of": "2017-06-30"}, headers=headers)
    assert resp_default.status_code == resp_early.status_code == 200

    by_id_default = {row["opportunity_id"]: row for row in resp_default.json()}
    by_id_early = {row["opportunity_id"]: row for row in resp_early.json()}
    comuns = set(by_id_default) & set(by_id_early)
    algum_diferente = any(
        by_id_default[i]["age_days"] != by_id_early[i]["age_days"] for i in comuns
    )
    assert algum_diferente

    resp_kpis_early = client.get("/kpis", params={"as_of": "2017-06-30"}, headers=headers)
    assert resp_kpis_early.status_code == 200


def test_export_ok_for_manager(client):
    headers = auth_headers(client, "Central")
    resp = client.get("/export/csv", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
