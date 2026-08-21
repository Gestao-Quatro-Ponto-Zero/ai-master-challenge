"""Task 1.5 — teste que verifica a carga dos dados."""

from scoring.repository import load_dataset, unmatched_products


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
    """Contagens após a reclassificação de 200 dias (task 1.6): 653
    oportunidades saem de Engaging e entram em Lost — Won é intocado."""
    counts = dataset.pipeline["deal_stage"].value_counts()
    assert counts["Won"] == 4238
    assert counts["Lost"] == 3126
    assert counts["Engaging"] == 936
    assert counts["Prospecting"] == 500


def test_reclassification_count(dataset):
    assert dataset.n_reclassificados == 653


def test_reclassified_deals_have_age_at_least_200(dataset):
    reclass = dataset.pipeline[dataset.pipeline["reclassificado"]]
    idade = (dataset.as_of_default - reclass["engage_date"]).dt.days
    assert len(reclass) == 653
    assert idade.min() == 200
    assert (reclass["deal_stage"] == "Lost").all()


def test_source_csv_untouched_by_reclassification(data_dir):
    raw = data_dir / "sales_pipeline.csv"
    original = raw.read_bytes()
    load_dataset(data_dir)
    assert raw.read_bytes() == original


def test_reclassification_scenarios():
    """Task 1.6 — cenários exatos do spec (213d vira Lost, 199d permanece
    aberto, Prospecting sem engage_date nunca é reclassificado)."""
    import pandas as pd

    from scoring.repository import _reclassify_aged_deals

    as_of = pd.Timestamp("2017-12-31")
    pipeline = pd.DataFrame(
        {
            "opportunity_id": ["A", "B", "C"],
            "deal_stage": ["Engaging", "Engaging", "Prospecting"],
            "engage_date": [
                as_of - pd.Timedelta(days=213),
                as_of - pd.Timedelta(days=199),
                pd.NaT,
            ],
        }
    )
    result = _reclassify_aged_deals(pipeline, as_of)
    by_id = result.set_index("opportunity_id")

    assert by_id.loc["A", "deal_stage"] == "Lost"
    assert bool(by_id.loc["A", "reclassificado"]) is True

    assert by_id.loc["B", "deal_stage"] == "Engaging"
    assert bool(by_id.loc["B", "reclassificado"]) is False

    assert by_id.loc["C", "deal_stage"] == "Prospecting"
    assert bool(by_id.loc["C", "reclassificado"]) is False
