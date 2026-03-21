"""Fluxo principal HTTP com CSVs reais (CRP-REAL-08).

Cobre ranking/listagem, detalhe, filtros, pesquisa `q`, KPIs e estrutura de explainability
usando dados do pipeline oficial — sem depender do snapshot `demo-opportunities.json`.
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.serving.opportunity_pipeline import clear_serving_cache

client = TestClient(app)

KNOWN_PIPELINE_ID = "1C1I7A6R"


@pytest.fixture(autouse=True)
def _real_dataset_and_clean_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[None, None, None]:
    monkeypatch.delenv("LEAD_SCORER_DATA_SOURCE_MODE", raising=False)
    clear_serving_cache()
    yield
    clear_serving_cache()


def test_real_opportunities_and_ranking_filters_match_row_slice() -> None:
    """Filtros `region` / `manager` / `deal_stage` aplicados sobre o dataset real."""
    sample = client.get("/api/opportunities", params={"limit": 1})
    assert sample.status_code == 200
    one = sample.json()["items"][0]
    region = one["region"]
    manager = one["manager"]
    stage = one["deal_stage"]
    params = {"region": region, "manager": manager, "deal_stage": stage, "limit": 25}
    for path in ("/api/opportunities", "/api/ranking"):
        r = client.get(path, params=params)
        assert r.status_code == 200, path
        payload = r.json()
        assert payload["total"] >= 1, path
        for item in payload["items"]:
            assert item["region"] == region
            assert item["manager"] == manager
            assert item["deal_stage"] == stage


def test_real_opportunities_q_filters_by_title_substring() -> None:
    """Pesquisa server-side `q` sobre títulos reais (amostra derivada do listing)."""
    listing = client.get(
        "/api/opportunities",
        params={"limit": 80, "sort_by": "title", "sort_order": "asc"},
    )
    assert listing.status_code == 200
    needle: str | None = None
    for item in listing.json()["items"]:
        title = str(item.get("title", ""))
        for raw in title.replace(",", " ").split():
            token = "".join(c for c in raw if c.isalnum())
            if len(token) >= 4:
                needle = token.lower()
                break
        if needle:
            break
    assert needle is not None, "expected at least one title token with len>=4 in sample"
    filtered = client.get("/api/opportunities", params={"q": needle, "limit": 30})
    assert filtered.status_code == 200
    body = filtered.json()
    assert body["total"] >= 1
    for item in body["items"]:
        assert needle in str(item["title"]).lower()


def test_real_detail_known_id_explainability_shape() -> None:
    """Detalhe + `scoreExplanation` com listas e campos esperados (explicabilidade)."""
    r = client.get(f"/api/opportunities/{KNOWN_PIPELINE_ID}")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == KNOWN_PIPELINE_ID
    exp = body["scoreExplanation"]
    assert isinstance(exp["score"], int)
    assert exp["priority_band"] in {"high", "medium", "low"}
    assert isinstance(exp["positive_factors"], list)
    assert isinstance(exp["negative_factors"], list)
    assert isinstance(exp["risk_flags"], list)
    assert isinstance(exp["next_action"], str)


def test_real_dashboard_kpis_sum_stages_equals_total() -> None:
    """KPIs agregados coerentes com o mesmo universo de linhas do serving real."""
    r = client.get("/api/dashboard/kpis")
    assert r.status_code == 200
    k = r.json()
    assert k["total_opportunities"] >= 8000
    assert (
        k["open_opportunities"] + k["won_opportunities"] + k["lost_opportunities"]
        == k["total_opportunities"]
    )
    assert isinstance(k["avg_score"], (int, float))
    assert 0 <= float(k["avg_score"]) <= 100
