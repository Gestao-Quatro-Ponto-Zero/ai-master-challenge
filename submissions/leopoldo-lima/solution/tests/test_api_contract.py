from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.app import app

client = TestClient(app)


def test_ranking_endpoint_returns_sorted_items() -> None:
    response = client.get("/api/ranking?limit=3")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 3
    assert len(payload["items"]) == 3
    assert payload["items"][0]["score"] >= payload["items"][1]["score"]
    assert "priority_band" in payload["items"][0]
    assert "nextBestAction" in payload["items"][0]


def test_opportunities_endpoint_matches_contract() -> None:
    response = client.get("/api/opportunities?limit=2")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 2
    assert "priority_band" in payload["items"][0]
    item0 = payload["items"][0]
    for key in ("account", "product", "sales_agent", "regional_office", "close_value"):
        assert key in item0


def test_detail_endpoint_returns_opportunity_or_404() -> None:
    ok_response = client.get("/api/opportunities/OPP-001")
    assert ok_response.status_code == 200
    body = ok_response.json()
    assert body["id"] == "OPP-001"
    assert body["deal_stage"] == "Engaging"
    assert "account" in body
    assert "product" in body
    assert "sales_agent" in body
    assert "regional_office" in body
    assert "close_value" in body
    assert "scoreExplanation" in body
    assert "priority_band" in ok_response.json()["scoreExplanation"]

    missing_response = client.get("/api/opportunities/NOPE")
    assert missing_response.status_code == 404
    assert missing_response.json() == {"detail": "Opportunity not found"}


def test_ranking_filters_apply_consistently() -> None:
    response = client.get("/api/ranking?region=Core&manager=Marcos&deal_stage=Engaging")
    assert response.status_code == 200
    payload = response.json()
    assert payload["items"]
    for item in payload["items"]:
        assert item["region"] == "Core"
        assert item["manager"] == "Marcos"
        assert item["deal_stage"] == "Engaging"


def test_opportunities_search_and_sort_on_server_side() -> None:
    response = client.get("/api/opportunities?q=expansion&sort_by=title&sort_order=asc&limit=5")
    assert response.status_code == 200
    payload = response.json()
    titles = [item["title"] for item in payload["items"]]
    assert titles == sorted(titles, key=lambda value: value.lower())
    for item in payload["items"]:
        assert "expansion" in item["title"].lower()


def test_request_id_header_and_metrics_endpoint() -> None:
    response = client.get("/api/ranking?limit=1", headers={"x-request-id": "req-123"})
    assert response.status_code == 200
    assert response.headers.get("x-request-id") == "req-123"

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    metrics = metrics_response.json()
    assert metrics["requests_total"] >= 1
    assert metrics["ranking_requests"] >= 1
    assert "status_404_total" in metrics
    assert "status_422_total" in metrics
    assert "status_500_total" in metrics


def test_dashboard_endpoints_return_expected_shapes() -> None:
    kpis_response = client.get("/api/dashboard/kpis")
    assert kpis_response.status_code == 200
    kpis = kpis_response.json()
    assert "total_opportunities" in kpis
    assert "avg_score" in kpis

    options_response = client.get("/api/dashboard/filter-options")
    assert options_response.status_code == 200
    options = options_response.json()
    assert "regional_offices" in options
    assert "regions" in options
    assert options["regions"] == options["regional_offices"]
    assert "managers" in options
    assert "deal_stages" in options
    allowed = {"Prospecting", "Engaging", "Won", "Lost"}
    assert set(options["deal_stages"]).issubset(allowed)


def test_invalid_query_returns_422_and_propagates_request_id() -> None:
    response = client.get(
        "/api/opportunities?sort_by=invalid",
        headers={"x-request-id": "req-422"},
    )
    assert response.status_code == 422
    assert response.headers.get("x-request-id") == "req-422"
