"""Garantias da trilha UX (CRP-UX-09) — sem regressão para demo/JSON técnico na vitrine."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.app import app

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_app_js_does_not_stringify_raw_payload_for_detail() -> None:
    script = _read("public/app.js")
    assert "JSON.stringify" not in script


def test_index_exposes_cockpit_and_filter_toolbar() -> None:
    html = _read("public/index.html")
    assert "cockpit-grid" in html
    assert 'id="filters-clear"' in html
    assert 'id="result-count"' in html
    assert 'id="search-q"' in html
    assert 'id="priority-band"' in html
    assert 'id="filter-region"' in html
    assert 'id="filter-deal-stage"' in html
    assert 'id="manager-search"' in html
    assert 'id="manager-value"' in html
    assert 'id="manager-listbox"' in html
    assert 'id="manager-combobox-root"' in html
    assert "ver todos os gestores" in html.lower()
    assert "aria-busy" in html


def test_ranking_table_includes_band_and_next_action_headers() -> None:
    html = _read("public/index.html")
    assert ">Faixa<" in html
    assert "Próxima ação" in html


def test_api_repository_sends_priority_and_search_params() -> None:
    api_repo = _read("public/infrastructure/repositories/api-opportunity-repository.js")
    assert 'params.set("q"' in api_repo
    assert 'params.set("priority_band"' in api_repo
    assert "getDashboardFilterOptions" in api_repo
    assert "/dashboard/filter-options" in api_repo


def test_app_wires_filter_options_and_manager_combobox() -> None:
    script = _read("public/app.js")
    assert "getDashboardFilterOptions" in script
    assert "initFilterWidgets" in script
    assert "wireManagerCombobox" in script
    assert "normalizeSortDedupeStrings" in script
    assert "manager-combobox-root" in script
    assert "A carregar gestores" in script
    assert "listAllOrFilterManagers" in _read("public/shared/filter-options-utils.js")


def test_filter_options_utils_supports_manager_prefix_filter() -> None:
    util = _read("public/shared/filter-options-utils.js")
    assert "filterManagersByQuery" in util


def test_manager_combobox_widget_uses_shared_filter() -> None:
    widget = _read("public/presentation/widgets/manager-combobox.js")
    assert "listAllOrFilterManagers" in widget
    assert "rootEl" in widget
    assert "pointerdown" in widget
    assert "AbortController" in widget


def test_default_repository_mode_is_api() -> None:
    factory = _read("public/infrastructure/repositories/repository-factory.js")
    assert 'window.LEAD_SCORER_REPOSITORY_MODE || "api"' in factory


def test_real_dataset_ranking_total_large_without_band(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LEAD_SCORER_DATA_SOURCE_MODE", raising=False)
    client = TestClient(app)
    r = client.get("/api/opportunities", params={"limit": 3})
    assert r.status_code == 200
    assert r.json()["total"] >= 8000


def test_real_dataset_priority_band_high_filters_items(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LEAD_SCORER_DATA_SOURCE_MODE", raising=False)
    client = TestClient(app)
    r = client.get("/api/opportunities", params={"priority_band": "high", "limit": 8})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    for it in body["items"]:
        assert str(it.get("priority_band", "")).lower() == "high"


def test_invalid_priority_band_returns_422(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LEAD_SCORER_DATA_SOURCE_MODE", raising=False)
    client = TestClient(app)
    r = client.get("/api/opportunities", params={"priority_band": "nope"})
    assert r.status_code == 422
