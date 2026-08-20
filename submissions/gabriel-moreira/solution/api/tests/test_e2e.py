"""Tasks 8.3, 8.4 — ciclo completo da API e consistência entre camadas."""

import csv
import io
import time

from tests.conftest import auth_headers, token_for


def test_full_cycle_identify_token_scoped_listing_out_of_scope_no_token(client):
    # 1. identificação -> token
    token = token_for(client, "Anna Snelling")
    headers = {"Authorization": f"Bearer {token}"}

    # 2. listagem dentro do escopo
    resp = client.get("/deals", headers=headers)
    assert resp.status_code == 200
    assert all(row["sales_agent"] == "Anna Snelling" for row in resp.json())

    # 3. tentativa de acesso fora do escopo -> 403
    resp = client.get("/deals", params={"sales_agent": "Violet Mclelland"}, headers=headers)
    assert resp.status_code == 403

    # 4. requisição sem token -> 401
    resp = client.get("/deals")
    assert resp.status_code == 401

    # 5. rollup restrito por papel -> 403 para Sales Agent
    resp = client.get("/rollup", headers=headers)
    assert resp.status_code == 403

    # 6. download restrito a Manager -> 403 para Sales Agent
    resp = client.get("/export/csv", headers=headers)
    assert resp.status_code == 403

    # ... e 200 para Manager
    manager_headers = auth_headers(client, "Central")
    resp = client.get("/rollup", headers=manager_headers)
    assert resp.status_code == 200
    resp = client.get("/export/csv", headers=manager_headers)
    assert resp.status_code == 200


def test_supervisor_sees_only_own_team(client):
    headers = auth_headers(client, "Dustin Brinkmann")
    resp = client.get("/deals", headers=headers)
    assert resp.status_code == 200
    agentes_no_time = {
        "Anna Snelling", "Cecily Lampkin", "Versie Hillebrand", "Lajuana Vencill", "Moses Frase",
    }
    vistos = {row["sales_agent"] for row in resp.json()}
    assert vistos.issubset(agentes_no_time)


def test_manager_sees_only_own_office_even_with_same_named_supervisors_elsewhere(client):
    headers_central = auth_headers(client, "Central")
    resp = client.get("/deals", headers=headers_central)
    offices_vistos = {row["regional_office"] for row in resp.json()}
    assert offices_vistos.issubset({"Central"})


def test_expired_token_rejected_with_401(client):
    # itsdangerous mede idade em segundos inteiros — uma folga de só meio
    # segundo sobre max_age pode cair no mesmo segundo por arredondamento
    # (flaky). max_age=1 + sleep(2.2) garante diferença de >=2s inteiros.
    original = client.app.state.app_state.settings.token_max_age_seconds
    client.app.state.app_state.settings.token_max_age_seconds = 1
    try:
        token = token_for(client, "Anna Snelling")
        time.sleep(2.2)
        resp = client.get("/deals", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401
    finally:
        client.app.state.app_state.settings.token_max_age_seconds = original


def test_priority_identical_across_api_and_exported_csv(client):
    """Task 8.4 — a mesma oportunidade tem PRIORIDADE idêntica na API e no CSV."""
    manager_headers = auth_headers(client, "Central")
    resp = client.get("/deals", headers=manager_headers)
    deals = resp.json()
    assert deals

    amostra = deals[0]

    csv_resp = client.get("/export/csv", headers=manager_headers)
    reader = csv.DictReader(io.StringIO(csv_resp.text))
    linhas_csv = {row["opportunity_id"]: row for row in reader}

    linha_csv = linhas_csv[amostra["opportunity_id"]]
    assert round(float(linha_csv["prioridade"]), 2) == round(amostra["prioridade"], 2)
    assert round(float(linha_csv["score"]), 1) == round(amostra["score"], 1)
    assert linha_csv["estado"] == amostra["estado"]
    assert linha_csv["confianca"] == amostra["confianca"]
