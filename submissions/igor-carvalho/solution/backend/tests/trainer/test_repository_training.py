import shutil

import numpy as np
import pandas as pd
import pytest

from lead_trainer.repository import CsvDealRepository, DataValidationError
from lead_trainer.training import build_test, build_train, fit_gbm, train_start

T = pd.Timestamp("2017-09-15")


@pytest.fixture(scope="module")
def df(synthetic_dir):
    return CsvDealRepository(synthetic_dir).load()


# ------------------------------------------------------------------ repositório
def test_load_merges_and_labels(df):
    assert {"price", "series", "manager", "regional_office", "won"} <= set(df.columns)
    assert set(df.loc[df["won"].notna(), "deal_stage"]) == {"Won", "Lost"}
    assert df.loc[df["deal_stage"].isin(["Engaging", "Prospecting"]), "won"].isna().all()


def test_missing_file_fails(tmp_path, synthetic_dir):
    shutil.copytree(synthetic_dir, tmp_path / "d")
    (tmp_path / "d" / "products.csv").unlink()
    with pytest.raises(DataValidationError, match="ausente"):
        CsvDealRepository(tmp_path / "d").load()


def test_missing_column_fails(tmp_path, synthetic_dir):
    shutil.copytree(synthetic_dir, tmp_path / "d")
    pd.read_csv(tmp_path / "d" / "products.csv").drop(columns=["sales_price"]).to_csv(tmp_path / "d" / "products.csv", index=False)
    with pytest.raises(DataValidationError, match="faltam colunas"):
        CsvDealRepository(tmp_path / "d").load()


def test_unknown_product_fails(tmp_path, synthetic_dir):
    shutil.copytree(synthetic_dir, tmp_path / "d")
    p = pd.read_csv(tmp_path / "d" / "sales_pipeline.csv")
    p.loc[0, "product"] = "Produto Fantasma"
    p.to_csv(tmp_path / "d" / "sales_pipeline.csv", index=False)
    with pytest.raises(DataValidationError, match="sem preço"):
        CsvDealRepository(tmp_path / "d").load()


def test_close_before_engage_fails(tmp_path, synthetic_dir):
    shutil.copytree(synthetic_dir, tmp_path / "d")
    p = pd.read_csv(tmp_path / "d" / "sales_pipeline.csv")
    p.loc[1, "close_date"] = "2000-01-01"
    p.loc[1, "deal_stage"] = "Won"
    p.to_csv(tmp_path / "d" / "sales_pipeline.csv", index=False)
    with pytest.raises(DataValidationError, match="anterior"):
        CsvDealRepository(tmp_path / "d").load()


def test_typo_product_name_is_normalized(tmp_path, synthetic_dir):
    shutil.copytree(synthetic_dir, tmp_path / "d")
    pd.DataFrame([("GTX Pro", "G", 4821)], columns=["product", "series", "sales_price"]).to_csv(tmp_path / "d" / "products.csv", index=False)
    p = pd.read_csv(tmp_path / "d" / "sales_pipeline.csv")
    p["product"] = "GTXPro"
    p.to_csv(tmp_path / "d" / "sales_pipeline.csv", index=False)
    assert set(CsvDealRepository(tmp_path / "d").load()["product"]) == {"GTX Pro"}


# ------------------------------------------------------------------ bases de treino/teste
def test_train_has_no_label_from_the_future(df):
    train = build_train(df, T)
    assert len(train) > 500
    assert (train["snapshot"] <= T - pd.Timedelta(days=30)).all(), "fotos de treino respeitam o horizonte de 30 dias"
    assert train["won_30d"].isin([0, 1]).all()


def test_train_never_uses_deal_duration_as_feature(df):
    from lead_core.constants import CAT_FEATURES, NUM_FEATURES
    banned = {"close_date", "close_value", "duration", "won", "engage_date"}
    assert banned.isdisjoint(NUM_FEATURES + CAT_FEATURES)


def test_test_set_is_open_at_T_and_closes_after(df):
    test = build_test(df, T)
    assert len(test) > 30
    assert (test["engage_date"] <= T).all()
    assert ((test["close_date"] > T) | test["close_date"].isna()).all()
    assert test["won_30d"].isin([0, 1]).all() and (test.loc[test["won_30d"] == 0, "realized_30d"] == 0).all()


def test_changing_future_labels_does_not_change_training_set(df):
    base = build_train(df, T)
    changed = df.copy()
    m = changed["close_date"] > T
    changed.loc[m, "won"] = 1.0 - changed.loc[m, "won"]
    again = build_train(changed, T)
    assert len(base) == len(again)
    cols = ["agent_wr", "agent_product_wr", "age_days"]
    pd.testing.assert_frame_equal(base[cols], again[cols])


def test_train_start_is_two_weeks_after_first_close(df):
    assert train_start(df) == df["close_date"].min() + pd.Timedelta(days=14)


def test_fit_gbm_predicts_probabilities(df):
    train, test = build_train(df, T), build_test(df, T)
    fit = fit_gbm(train)
    p = fit.predict(test)
    assert p.shape == (len(test),) and ((p > 0) & (p < 1)).all()
    assert fit.best_iteration >= 20
    assert set(fit.cats["product"]) <= set(df["product"])


def test_fit_gbm_rejects_single_class():
    bad = pd.DataFrame({"won": [1.0] * 50})
    with pytest.raises(ValueError):
        fit_gbm(bad)
    with pytest.raises(ValueError):
        fit_gbm(pd.DataFrame())


def test_fit_is_deterministic(df):
    train, test = build_train(df, T), build_test(df, T)
    np.testing.assert_allclose(fit_gbm(train).predict(test), fit_gbm(train).predict(test))
