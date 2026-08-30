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
    """Contagens exatamente como o CSV as registra — a carga não reescreve
    desfecho. Até 2026-08-29, 653 oportunidades saíam de Engaging para Lost
    aqui; o expurgo foi removido (docs/decisions-log.md)."""
    counts = dataset.pipeline["deal_stage"].value_counts()
    assert counts["Won"] == 4238
    assert counts["Lost"] == 2473
    assert counts["Engaging"] == 1589
    assert counts["Prospecting"] == 500


def test_deal_stage_matches_source_csv(dataset, data_dir):
    """Nenhuma linha muda de estágio entre o CSV e o Dataset carregado —
    a garantia estrutural de que não há desfecho atribuído por nós."""
    import pandas as pd

    raw = pd.read_csv(data_dir / "sales_pipeline.csv")
    esperado = raw["deal_stage"].value_counts().to_dict()
    obtido = dataset.pipeline["deal_stage"].value_counts().to_dict()
    assert obtido == esperado


def test_aged_open_deals_stay_open(dataset):
    """As 653 oportunidades abertas há 200 dias ou mais continuam abertas e
    pontuáveis — envelhecer não é desfecho."""
    idade = (dataset.as_of_default - dataset.pipeline["engage_date"]).dt.days
    paradas = dataset.pipeline[
        (dataset.pipeline["deal_stage"] == "Engaging") & (idade >= 200)
    ]
    assert len(paradas) == 653
    assert (paradas["deal_stage"] == "Engaging").all()


def test_no_reclassification_column(dataset):
    """A coluna que marcava o expurgo não existe mais — se voltar, algum
    caminho de rotulagem automática voltou junto."""
    assert "reclassificado" not in dataset.pipeline.columns


def test_source_csv_untouched(data_dir):
    raw = data_dir / "sales_pipeline.csv"
    original = raw.read_bytes()
    load_dataset(data_dir)
    assert raw.read_bytes() == original
