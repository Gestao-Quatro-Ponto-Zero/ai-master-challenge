"""Ciclo completo da API sem identificação prévia e consistência entre
camadas. Substitui os antigos casos de isolamento por papel (Requirement
"Isolamento de dados por papel de acesso", removido) por testes de que os
endpoints respondem sem `Authorization` e de que os filtros de
organização restringem corretamente por conta própria."""

import csv
import io


def test_deals_responds_without_authorization_header(client):
    resp = client.get("/deals")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2089
    assert len(body["items"]) == 100  # page_size padrão


def test_filter_by_sales_agent_restricts_without_session(client):
    resp = client.get("/deals", params={"sales_agent": "Anna Snelling"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert items
    assert all(row["sales_agent"] == "Anna Snelling" for row in items)


def test_filter_by_manager_restricts_to_team(client):
    resp = client.get("/deals", params={"manager": "Dustin Brinkmann"})
    assert resp.status_code == 200
    agentes_no_time = {
        "Anna Snelling", "Cecily Lampkin", "Versie Hillebrand", "Lajuana Vencill", "Moses Frase",
    }
    vistos = {row["sales_agent"] for row in resp.json()["items"]}
    assert vistos.issubset(agentes_no_time)


def test_filter_by_regional_office_restricts(client):
    resp = client.get("/deals", params={"regional_office": "Central"})
    assert resp.status_code == 200
    offices_vistos = {row["regional_office"] for row in resp.json()["items"]}
    assert offices_vistos.issubset({"Central"})


def test_rollup_open_to_any_client_no_role_required(client):
    resp = client.get("/rollup")
    assert resp.status_code == 200
    niveis = {linha["nivel"] for linha in resp.json()["linhas"]}
    assert niveis == {"sales_agent", "manager", "regional_office"}


def test_export_csv_open_to_any_client_no_role_required(client):
    resp = client.get("/export/csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")


def test_priority_identical_across_api_and_exported_csv(client):
    resp = client.get("/deals", params={"regional_office": "Central"})
    deals = resp.json()["items"]
    assert deals

    amostra = deals[0]
    detalhe = client.get(f"/deals/{amostra['opportunity_id']}").json()

    csv_resp = client.get("/export/csv")
    reader = csv.DictReader(io.StringIO(csv_resp.text))
    linhas_csv = {row["opportunity_id"]: row for row in reader}

    linha_csv = linhas_csv[amostra["opportunity_id"]]
    assert round(float(linha_csv["prioridade"]), 2) == round(detalhe["prioridade"], 2)
    assert round(float(linha_csv["score"]), 1) == round(amostra["score"], 1)
    assert linha_csv["estado"] == amostra["estado"]
    assert float(linha_csv["confianca"]) == amostra["confianca"]
    assert float(linha_csv["completude"]) == amostra["completude"]
    assert float(linha_csv["suporte"]) == amostra["suporte"]
