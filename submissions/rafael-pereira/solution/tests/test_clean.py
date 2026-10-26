"""Testes da curadoria: join, nomes normalizados, colunas derivadas e pureza das funções."""

import csv
import datetime as dt

import pandas as pd
import pytest

from scorer import clean, config


@pytest.fixture(scope="module")
def raw():
    return clean.load_raw(config.RAW_DIR)


@pytest.fixture(scope="module")
def deals(raw):
    return clean.build_deals(raw, config.DEFAULT_REFERENCE_DATE)


def test_join_keeps_all_8800_rows(raw, deals):
    assert len(raw["pipeline"]) == 8800
    assert len(deals) == 8800
    assert deals["opportunity_id"].is_unique
    assert deals["sales_price"].notna().all()
    assert deals["manager"].notna().all()


def test_wrong_names_are_gone_but_existed_in_the_raw_data(raw, deals):
    assert (raw["pipeline"]["product"] == "GTXPro").sum() == 1480  # o problema existe no bruto
    assert (raw["accounts"]["sector"] == "technolgy").any()
    assert "GTXPro" not in set(deals["product"])
    assert "technolgy" not in set(deals["sector"].dropna())
    assert (deals["product"] == "GTX Pro").sum() == 1480
    assert "technology" in set(deals["sector"])


def test_age_days_matches_an_independent_calculation_for_a_chosen_engaging_deal():
    with open(config.RAW_DIR / "sales_pipeline.csv", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    deal = next(r for r in rows if r["deal_stage"] == "Engaging")
    expected = (dt.date.fromisoformat("2017-12-31") - dt.date.fromisoformat(deal["engage_date"])).days

    built = clean.build_deals(clean.load_raw(config.RAW_DIR), "2017-12-31").set_index("opportunity_id")
    assert built.loc[deal["opportunity_id"], "age_days"] == expected


def test_age_days_is_defined_exactly_for_open_deals_with_engage_date(deals):
    has_age = deals["age_days"].notna()
    assert has_age.sum() == (deals["deal_stage"] == "Engaging").sum()
    assert set(deals.loc[has_age, "deal_stage"]) == {"Engaging"}
    assert (deals.loc[has_age, "age_days"] >= 0).all()


def test_age_days_follows_the_reference_date_and_ignores_future_engagements(raw):
    later = clean.build_deals(raw, "2017-12-31").set_index("opportunity_id")["age_days"]
    earlier = clean.build_deals(raw, "2017-09-30").set_index("opportunity_id")["age_days"]
    both = later.notna() & earlier.notna()
    assert both.any()
    assert ((later[both] - earlier[both]) == 92).all()  # 30/09 -> 31/12 são 92 dias
    assert earlier.isna().sum() > later.isna().sum()  # engajados depois de 30/09 ficam sem idade


def test_cycle_days_only_for_closed_deals(deals):
    closed = deals["deal_stage"].isin(["Won", "Lost"])
    assert deals.loc[closed, "cycle_days"].notna().all()
    assert deals.loc[~closed, "cycle_days"].isna().all()
    assert (deals.loc[closed, "cycle_days"] >= 0).all()


def test_close_value_is_zero_for_lost_and_positive_for_won(deals):
    won, lost = deals[deals["deal_stage"] == "Won"], deals[deals["deal_stage"] == "Lost"]
    assert len(won) == 4238 and len(lost) == 2473
    assert (won["close_value"] > 0).all()
    assert (lost["close_value"] == 0).all()


def test_prospecting_has_no_engage_date_and_open_flags_are_consistent(deals):
    prospecting = deals[deals["deal_stage"] == "Prospecting"]
    assert len(prospecting) == 500
    assert prospecting["engage_date"].isna().all()
    assert (deals["is_open"] == deals["deal_stage"].isin(["Engaging", "Prospecting"])).all()


def test_missing_account_is_labelled_and_never_closed(deals):
    no_account = deals[~deals["has_account"]]
    assert len(no_account) == 1425
    assert (no_account["account_display"] == config.NO_ACCOUNT_LABEL).all()
    assert no_account["is_open"].all()  # o risco de vazamento descrito no DATA_QUALITY
    assert (deals.loc[deals["has_account"], "account_display"] == deals.loc[deals["has_account"], "account"]).all()


def test_normalize_products_rejects_a_product_missing_from_the_catalog(raw):
    pipeline = raw["pipeline"].copy()
    pipeline.loc[0, "product"] = "Produto Fantasma"
    with pytest.raises(AssertionError):
        clean.normalize_products(pipeline, raw["products"])


def test_functions_do_not_modify_their_input(raw):
    def unchanged(func, *frames):
        before = [f.copy(deep=True) for f in frames]
        func(*frames)
        for original, after in zip(before, frames):
            pd.testing.assert_frame_equal(original, after)

    products = raw["products"]
    normalized = clean.normalize_products(raw["pipeline"], products)
    accounts = clean.normalize_sectors(raw["accounts"])
    joined = clean.join_all(normalized, products, raw["sales_teams"], accounts)

    unchanged(lambda p, c: clean.normalize_products(p, c), raw["pipeline"], products)
    unchanged(clean.normalize_sectors, raw["accounts"])
    unchanged(clean.join_all, normalized, products, raw["sales_teams"], accounts)
    unchanged(lambda d: clean.add_derived(d, "2017-12-31"), joined)


def test_cli_output_is_reproducible_and_matches_the_committed_files(tmp_path):
    assert clean.main(["--out-dir", str(tmp_path)]) == 0
    assert len(pd.read_csv(tmp_path / "deals.csv")) == 8800
    for name in ["deals.csv", "facts.json"]:
        assert (tmp_path / name).read_bytes() == (config.PROCESSED_DIR / name).read_bytes(), (
            f"{name} está desatualizado: rode `python -m scorer.clean`"
        )
