"""Task 1.5 — teste que verifica a carga dos dados."""

from scoring.repository import unmatched_products


def test_pipeline_row_count(dataset):
    assert len(dataset.pipeline) == 8800


def test_accounts_count(dataset):
    assert len(dataset.accounts) == 85


def test_products_count(dataset):
    assert len(dataset.products) == 7


def test_sales_agents_count(dataset):
    assert dataset.sales_teams["sales_agent"].nunique() == 35


def test_no_unmatched_products_after_normalization(dataset):
    assert unmatched_products(dataset) == []


def test_sector_typo_corrected(dataset):
    assert "technolgy" not in set(dataset.accounts["sector"].dropna())


def test_as_of_default_is_max_close_date(dataset):
    assert str(dataset.as_of_default.date()) == "2017-12-31"


def test_deal_stage_counts(dataset):
    counts = dataset.pipeline["deal_stage"].value_counts()
    assert counts["Won"] == 4238
    assert counts["Lost"] == 2473
    assert counts["Engaging"] == 1589
    assert counts["Prospecting"] == 500
