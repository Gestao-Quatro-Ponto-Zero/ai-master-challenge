"""Serving HTTP com dataset oficial (CRP-REAL-01): padrão `real_dataset`."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.app import app

client = TestClient(app)


def test_real_dataset_ranking_has_many_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LEAD_SCORER_DATA_SOURCE_MODE", raising=False)
    response = client.get("/api/ranking?limit=10")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 8000
    assert len(payload["items"]) == 10
    assert payload["items"][0]["id"] != "OPP-001"


def test_real_dataset_detail_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LEAD_SCORER_DATA_SOURCE_MODE", raising=False)
    listing = client.get("/api/opportunities?limit=1")
    oid = listing.json()["items"][0]["id"]
    detail = client.get(f"/api/opportunities/{oid}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["id"] == oid
    assert "scoreExplanation" in body


def test_real_dataset_filter_options_non_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LEAD_SCORER_DATA_SOURCE_MODE", raising=False)
    r = client.get("/api/dashboard/filter-options")
    assert r.status_code == 200
    data = r.json()
    assert data["regional_offices"]
    assert data["regions"] == data["regional_offices"]
    assert data["managers"]
    assert set(data["deal_stages"]).issubset({"Prospecting", "Engaging", "Won", "Lost"})


def test_demo_mode_still_loads_json_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LEAD_SCORER_DATA_SOURCE_MODE", "demo_dataset")
    r = client.get("/api/opportunities/OPP-001")
    assert r.status_code == 200
    assert r.json()["id"] == "OPP-001"
