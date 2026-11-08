import time

import jwt
import pytest

from tests.api.conftest import SECRET, login, make_settings

API = "/api/v1"
DEAL_FIELDS = {"opportunity_id", "seller", "manager", "office", "stage", "product", "series", "account",
               "account_missing", "list_price", "engage_date", "age_days", "score", "priority_level", "band",
               "expected_value", "p_win", "confidence", "flags", "reasons",
               "view", "confidence_reason", "suggested_action", "data_quality"}


def test_login_ok_and_unknown_user(ro_client):
    r = ro_client.post(f"{API}/auth/login", json={"user_key": "agent-1"})
    body = r.json()
    assert r.status_code == 200 and body["token_type"] == "bearer" and body["user"]["role"] == "seller"
    bad = ro_client.post(f"{API}/auth/login", json={"user_key": "ninguem"})
    assert bad.status_code == 401 and bad.json()["error"]["code"] == "UNAUTHENTICATED"


def test_login_validation(ro_client):
    r = ro_client.post(f"{API}/auth/login", json={})
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer lixo"}, {"Authorization": "Basic abc"}])
def test_protected_routes_need_valid_token(ro_client, headers):
    for path in ("/me", "/deals", "/meta", "/filters", "/summary", "/model"):
        r = ro_client.get(API + path, headers=headers)
        assert r.status_code == 401, path
        assert r.json()["error"]["code"] == "UNAUTHENTICATED"


def test_expired_and_forged_tokens_are_rejected(ro_client):
    expired = jwt.encode({"sub": "agent-1", "exp": int(time.time()) - 10}, SECRET, algorithm="HS256")
    forged = jwt.encode({"sub": "revops", "exp": int(time.time()) + 600}, "outra-chave-" + "y" * 30, algorithm="HS256")
    for tok in (expired, forged):
        assert ro_client.get(f"{API}/me", headers={"Authorization": f"Bearer {tok}"}).status_code == 401


def test_me_scopes(ro_client, seller, manager, revops):
    s = ro_client.get(f"{API}/me", headers=seller).json()
    m = ro_client.get(f"{API}/me", headers=manager).json()
    r = ro_client.get(f"{API}/me", headers=revops).json()
    assert s["scope"] == {"type": "seller", "sellers": ["Agent 1"]}
    assert m["scope"]["type"] == "team" and m["scope"]["sellers"] == ["Agent 0", "Agent 1", "Agent 2"]
    assert r["scope"]["type"] == "all"


def test_error_format_and_request_id(ro_client, seller):
    r = ro_client.get(f"{API}/deals/NAO_EXISTE", headers=seller)
    err = r.json()["error"]
    assert r.status_code == 404 and set(err) == {"code", "message", "request_id", "details"}
    assert err["code"] == "DEAL_NOT_FOUND" and err["request_id"] == r.headers["X-Request-ID"]


def test_unknown_route_uses_standard_error(ro_client):
    r = ro_client.get(f"{API}/nao-existe")
    assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND"


def test_deal_summary_matches_contract(ro_client, seller):
    item = ro_client.get(f"{API}/deals?page_size=1", headers=seller).json()["items"][0]
    assert set(item) == DEAL_FIELDS
    assert item["p_win"] is None                     # oculto por padrão (flag)
    assert len(item["reasons"]) <= 3
    assert {"code", "label", "direction", "impact"} <= set(item["reasons"][0])


def test_probability_visible_only_with_flag(trained_copy):
    from fastapi.testclient import TestClient

    from lead_api.main import create_app
    settings = make_settings(trained_copy["artifact_dir"], trained_copy["db_path"], show_probability=True)
    with TestClient(create_app(settings)) as c:
        h = login(c, "agent-1")
        assert c.get(f"{API}/deals?page_size=1", headers=h).json()["items"][0]["p_win"] is not None
        assert c.get(f"{API}/meta", headers=h).json()["show_probability"] is True     # independe da calibração
        assert c.post(f"{API}/score/what-if", headers=h,
                      json={"product": "Prod Pro", "seller": "Agent 1", "age_days": 10}).json()["p_win"] is not None
    hidden = make_settings(trained_copy["artifact_dir"], trained_copy["db_path"], show_probability=False)
    with TestClient(create_app(hidden)) as c:                  # a flag desligada esconde sempre
        h = login(c, "agent-1")
        assert c.get(f"{API}/deals?page_size=1", headers=h).json()["items"][0]["p_win"] is None
