"""Integração do pipeline de serving com os CSVs oficiais (CRP-REAL-02)."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from src.api.app import app
from src.raw.reader import load_raw_rows
from src.serving.opportunity_pipeline import (
    build_serving_opportunities,
    clear_serving_cache,
    validate_referential_for_row,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_serving_cache() -> Generator[None, None, None]:
    clear_serving_cache()
    yield
    clear_serving_cache()


def test_pipeline_loads_all_pipeline_rows_with_valid_fks() -> None:
    ops = build_serving_opportunities(use_cache=False)
    pipeline = load_raw_rows("sales_pipeline.csv")
    with_id = [r for r in pipeline if (r.get("opportunity_id") or "").strip()]
    assert len(ops) == len(with_id)
    assert len(ops) >= 8000


def test_known_csv_opportunity_joins_product_and_account() -> None:
    ops = build_serving_opportunities(use_cache=False)
    by_id = {o.opportunity_id: o for o in ops}
    row = by_id["1C1I7A6R"]
    assert row.account_name == "Cancity"
    assert row.sales_agent == "Moses Frase"
    assert row.product_canonical == "GTX Plus Basic"
    assert row.product_series == "GTX"
    assert row.product_sales_price == 1096.0


def test_validate_referential_rejects_unknown_agent() -> None:
    teams = {"A"}
    products = {"P"}
    accounts = {"X"}
    assert not validate_referential_for_row(
        sales_agent="Nobody",
        product_raw="P",
        account_name=None,
        teams_set=teams,
        products_canonical_set=products,
        accounts_set=accounts,
    )


def test_api_detail_matches_sales_pipeline_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LEAD_SCORER_DATA_SOURCE_MODE", raising=False)
    response = client.get("/api/opportunities/1C1I7A6R")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "1C1I7A6R"
    assert body["title"] == "Cancity"
    assert body["seller"] == "Moses Frase"
