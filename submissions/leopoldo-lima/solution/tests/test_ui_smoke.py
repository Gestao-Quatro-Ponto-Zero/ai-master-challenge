from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.api.app import app

ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


def test_ui_files_exist() -> None:
    assert (ROOT / "public" / "index.html").exists()
    assert (ROOT / "public" / "styles.css").exists()
    assert (ROOT / "public" / "app.js").exists()
    assert (ROOT / "public" / "application" / "contracts" / "opportunity-repository.js").exists()
    assert (ROOT / "public" / "infrastructure" / "repositories" / "repository-factory.js").exists()
    assert (
        ROOT / "public" / "infrastructure" / "mocks" / "fixtures" / "opportunity-list.js"
    ).exists()
    assert (
        ROOT / "public" / "infrastructure" / "mocks" / "fixtures" / "opportunity-detail.js"
    ).exists()
    assert (ROOT / "public" / "presentation" / "hooks" / "use-dashboard-data.js").exists()
    assert (ROOT / "public" / "shared" / "query" / "query-keys.js").exists()


def test_ui_app_integrates_with_api_routes() -> None:
    script = (ROOT / "public" / "app.js").read_text(encoding="utf-8")
    assert "createOpportunityRepository" in script
    assert "createDashboardDataHook" in script
    assert "keydown" in script
    assert "detail-retry" in script
    assert "detail-close" in script
    api_repository = (
        ROOT / "public" / "infrastructure" / "repositories" / "api-opportunity-repository.js"
    ).read_text(encoding="utf-8")
    assert "/opportunities" in api_repository
    mock_repository = (
        ROOT / "public" / "infrastructure" / "repositories" / "mock-opportunity-repository.js"
    ).read_text(encoding="utf-8")
    assert "../mocks/fixtures/" in mock_repository
    assert "mocks/fixtures" not in script
    dashboard_hook = (
        ROOT / "public" / "presentation" / "hooks" / "use-dashboard-data.js"
    ).read_text(encoding="utf-8")
    assert "AbortController" in dashboard_hook
    assert "DASHBOARD_QUERY_KEYS" in dashboard_hook


def test_ui_root_route_serves_main_page() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Focus Score Cockpit" in response.text
    assert "ranking-table" in response.text
    assert "kpi-strip" in response.text
    assert "detail-retry" in response.text
    assert "filters-clear" in response.text
    assert "result-count" in response.text
    assert "filter-region" in response.text
    assert "manager-search" in response.text


def test_missing_ui_route_returns_404() -> None:
    response = client.get("/ui/does-not-exist.js")
    assert response.status_code == 404
