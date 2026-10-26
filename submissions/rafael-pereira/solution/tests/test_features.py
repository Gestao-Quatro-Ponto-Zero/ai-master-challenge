"""Testes de `features.py`: reconstrução do estado em T, fotos de treino e a mutação do futuro."""

import numpy as np
import pandas as pd
import pytest

from scorer import clean, config, features, score

END = pd.Timestamp(config.DEFAULT_REFERENCE_DATE)
CUTS = [pd.Timestamp(c) for c in config.BACKTEST_CUTS]
SCORE_COLUMNS = ["opportunity_id", "age_days", "p_win", "expected_value", "score", "category",
                 "days_to_knot", "days_to_limpe"]


@pytest.fixture(scope="module")
def deals():
    return clean.load_deals()


def toy_deals() -> pd.DataFrame:
    """Sete deals à mão, para conferir o resultado exato sem depender do dataset."""
    rows = [
        # id, estágio final, engajamento, fechamento, valor
        ("A", "Won", "2017-01-10", "2017-02-15", 100.0),
        ("B", "Lost", "2017-01-20", "2017-05-10", 0.0),  # fecha depois de T = 30/04
        ("C", "Engaging", "2017-02-01", None, np.nan),
        ("D", "Won", "2017-03-05", "2017-04-01", 80.0),
        ("E", "Prospecting", None, None, np.nan),
        ("F", "Won", "2017-06-15", "2017-07-01", 90.0),  # engajado depois de T
        ("G", "Won", "2017-03-20", "2017-05-10", 70.0),  # fecha depois de T
    ]
    df = pd.DataFrame(rows, columns=["opportunity_id", "deal_stage", "engage_date", "close_date", "close_value"])
    df["engage_date"] = pd.to_datetime(df["engage_date"])
    df["close_date"] = pd.to_datetime(df["close_date"])
    df["sales_price"] = 100
    attributes = {"account": "x", "product": "p", "regional_office": "West", "sector": "retail", "employees": 10.0}
    return clean.add_derived(df.assign(**attributes), "2017-12-31")


def test_as_of_hides_every_event_after_T(deals):
    for T in CUTS:
        view = features.as_of(deals, T)
        assert (view["engage_date"] <= T).all()
        assert view["close_date"].dropna().le(T).all(), "há fechamento depois de T"
        closed = view["deal_stage"].isin(["Won", "Lost"])
        assert view.loc[closed, "close_date"].notna().all()
        assert view.loc[~closed, ["close_date", "close_value"]].isna().all().all()
        assert set(view["deal_stage"]) <= {"Won", "Lost", "Engaging"}


def test_as_of_on_a_toy_example():
    view = features.as_of(toy_deals(), "2017-04-30").set_index("opportunity_id")
    assert list(view.index) == ["A", "B", "C", "D", "G"]  # E é Prospecting; F engaja só em junho
    assert view["deal_stage"].to_dict() == {"A": "Won", "B": "Engaging", "C": "Engaging", "D": "Won", "G": "Engaging"}
    assert view["close_date"].isna().to_dict() == {"A": False, "B": True, "C": True, "D": False, "G": True}
    assert view["close_value"].isna().to_dict() == {"A": False, "B": True, "C": True, "D": False, "G": True}


def test_as_of_excludes_prospecting_and_future_engagements(deals):
    view = features.as_of(deals, "2017-06-30")
    prospecting_ids = set(deals.loc[deals["deal_stage"] == "Prospecting", "opportunity_id"])
    assert not prospecting_ids & set(view["opportunity_id"])
    later = deals.loc[deals["engage_date"] > "2017-06-30", "opportunity_id"]
    assert len(later) > 0 and not set(later) & set(view["opportunity_id"])


def test_as_of_recomputes_age_and_cycle_from_dates(deals):
    T = pd.Timestamp("2017-06-30")
    view = features.as_of(deals, T)
    # a idade do arquivo usa 31/12/2017; a da visão usa T
    open_ = view["is_open"]
    assert open_.any() and (view.loc[open_, "age_days"] == (T - view.loc[open_, "engage_date"]).dt.days).all()
    assert view.loc[~open_, "age_days"].isna().all()
    # o ciclo existe só para quem fechou até T (no arquivo, também existe para quem fechou depois)
    assert view.loc[open_, "cycle_days"].isna().all()
    done = view.loc[~open_]
    assert (done["cycle_days"] == (done["close_date"] - done["engage_date"]).dt.days).all()
    assert deals.loc[deals["opportunity_id"].isin(view.loc[open_, "opportunity_id"]), "cycle_days"].notna().any()


def test_as_of_does_not_modify_its_input(deals):
    before = deals.copy(deep=True)
    features.as_of(deals, "2017-06-30")
    pd.testing.assert_frame_equal(before, deals)


def test_open_at_on_a_toy_example():
    view = features.as_of(toy_deals(), "2017-04-30")
    feb = features.open_at(view, "2017-02-28").set_index("opportunity_id")
    assert set(feb.index) == {"B", "C"}  # A fechou em 15/02; D só engaja em 05/03
    assert feb["age_days"].to_dict() == {"B": 39, "C": 27}
    assert feb["age_days"].dtype == np.int64
    closing_day = features.open_at(view, "2017-04-01")
    assert "D" not in set(closing_day["opportunity_id"])  # fechado em 01/04: não está aberto no fim do dia
    assert "D" in set(features.open_at(view, "2017-03-31")["opportunity_id"])


def test_open_at_refuses_snapshots_after_the_as_of_date(deals):
    view = features.as_of(deals, "2017-06-30")
    features.open_at(view, "2017-06-30")  # o próprio T pode
    with pytest.raises(AssertionError):
        features.open_at(view, "2017-07-31")


def test_training_set_labels_on_a_toy_example():
    view = features.as_of(toy_deals(), "2017-04-30")
    train = features.training_set(view, "2017-04-30", horizon_days=30, first_snapshot="2017-01-31")
    key = train.assign(snapshot_date=train["snapshot_date"].dt.strftime("%m-%d")).set_index(
        ["snapshot_date", "opportunity_id"]
    )["y"]
    # 30/04 fica de fora: 30/04 + 30 dias passa de T
    assert sorted(set(train["snapshot_date"].dt.strftime("%m-%d"))) == ["01-31", "02-28", "03-31"]
    assert key.to_dict() == {
        ("01-31", "A"): 1, ("01-31", "B"): 0,
        ("02-28", "B"): 0, ("02-28", "C"): 0,
        ("03-31", "B"): 0, ("03-31", "C"): 0, ("03-31", "D"): 1, ("03-31", "G"): 0,
    }  # G ganho em 10/05 e B perdido em 10/05 são futuros: o rótulo não os vê


def test_training_set_respects_the_horizon_for_every_cut(deals):
    horizon = pd.Timedelta(days=config.HORIZON_DAYS)
    for T in CUTS + [END]:
        train = features.training_set(features.as_of(deals, T), T, config.HORIZON_DAYS, config.FIRST_SNAPSHOT)
        assert len(train) > 0
        assert (train["snapshot_date"] + horizon <= T).all()
        assert train["snapshot_date"].min() == pd.Timestamp(config.FIRST_SNAPSHOT)
        assert set(train["y"]) == {0, 1}


def test_training_set_returns_empty_when_no_snapshot_closes_the_horizon(deals):
    train = features.training_set(features.as_of(deals, "2017-05-31"), "2017-05-31")
    assert train.empty and list(train.columns) == features.TRAINING_COLUMNS


def test_training_set_sizes_match_the_planner_prototype(deals):
    expected = {"2017-06-30": 1330, "2017-07-31": 2948, "2017-08-31": 4483, "2017-09-30": 6169, "2017-12-31": 13100}
    for T, rows in expected.items():
        train = features.training_set(features.as_of(deals, T), T)
        assert abs(len(train) - rows) <= 0.02 * rows, (T, len(train), rows)
    assert train["snapshot_date"].nunique() == 7  # hoje: 31/03 a 30/09


def test_training_set_has_no_seller_columns(deals):
    train = features.training_set(features.as_of(deals, "2017-09-30"), "2017-09-30")
    forbidden = {"sales_agent", "manager", "close_date", "close_value", "deal_stage"}
    assert not forbidden & set(train.columns)
    assert list(train.columns) == features.TRAINING_COLUMNS


def test_month_ends_includes_both_extremes():
    dates = features.month_ends("2017-03-31", "2017-06-30")
    assert [d.strftime("%Y-%m-%d") for d in dates] == ["2017-03-31", "2017-04-30", "2017-05-31", "2017-06-30"]


# --- Mutação do futuro ----------------------------------------------------------------------------


def mutate_future(deals: pd.DataFrame, T, seed: int) -> pd.DataFrame:
    """Troca por valores aleatórios tudo o que acontece depois de T (o passado fica intacto)."""
    rng = np.random.default_rng(seed)
    T = pd.Timestamp(T)
    span = (END - T).days
    out = deals.copy()

    def random_dates(n):
        return (T + pd.to_timedelta(rng.integers(1, span + 1, n), unit="D")).to_numpy(dtype=out["close_date"].dtype)

    # 1) deals que fecham depois de T: desfecho, data, valor e ciclo sorteados; metade perde a conta
    after = (out["close_date"] > T).to_numpy()
    n_after = int(after.sum())
    won = rng.random(n_after) < 0.5
    out.loc[after, "deal_stage"] = np.where(won, "Won", "Lost")
    out.loc[after, "close_date"] = random_dates(n_after)
    out.loc[after, "close_value"] = np.where(won, rng.uniform(50, 30000, n_after), 0.0)
    out.loc[after, "cycle_days"] = rng.integers(0, 400, n_after).astype("float64")
    out.loc[after, "is_open"] = rng.random(n_after) < 0.5
    drop_account = after.copy()
    drop_account[after] = rng.random(n_after) < 0.5
    out.loc[drop_account, ["account", "sector", "year_established", "revenue", "employees", "office_location",
                           "subsidiary_of"]] = np.nan
    out.loc[drop_account, "account_display"] = config.NO_ACCOUNT_LABEL
    out.loc[drop_account, "has_account"] = False

    # 2) deals engajados depois de T: nova data, novo estágio; produto, preço e time embaralhados
    later = (out["engage_date"] > T).to_numpy()
    n_later = int(later.sum())
    out.loc[later, "engage_date"] = random_dates(n_later)
    new_stage = rng.choice(["Won", "Lost", "Engaging"], n_later)
    out.loc[later, "deal_stage"] = new_stage
    out.loc[later, "close_date"] = np.where(new_stage == "Engaging", np.datetime64("NaT"), random_dates(n_later))
    out.loc[later, "close_value"] = np.where(new_stage == "Won", rng.uniform(50, 30000, n_later), np.nan)
    unknowable = later | (out["deal_stage"] == "Prospecting").to_numpy()  # Prospecting não existe no passado
    for columns in (["product", "series", "sales_price"], ["sales_agent", "manager", "regional_office"]):
        order = rng.permutation(int(unknowable.sum()))  # o mesmo sorteio nas colunas do bloco: preço segue o produto
        for column in columns:
            out.loc[unknowable, column] = out.loc[unknowable, column].to_numpy()[order]
    return out


@pytest.mark.parametrize("T, seed", [("2017-06-30", 1), ("2017-06-30", 2), ("2017-09-30", 3)])
def test_future_mutation_leaves_model_and_scores_unchanged(deals, T, seed):
    mutated = mutate_future(deals, T, seed)

    changed = (mutated["deal_stage"] != deals["deal_stage"]).sum()
    assert changed > 500  # a mutação mexeu de verdade no futuro
    assert (mutated["close_value"].fillna(-1) != deals["close_value"].fillna(-1)).sum() > 500
    assert (mutated["has_account"] != deals["has_account"]).sum() > 100
    assert (mutated["product"] != deals["product"]).sum() > 100
    past = deals["engage_date"].notna() & (deals["engage_date"] <= T) & ~(deals["close_date"] > T)
    pd.testing.assert_frame_equal(  # o passado de T ficou intacto
        deals.loc[past, ["opportunity_id", "deal_stage", "close_date", "close_value", "product", "sales_agent"]],
        mutated.loc[past, ["opportunity_id", "deal_stage", "close_date", "close_value", "product", "sales_agent"]],
    )

    model, model_mutated = score.fit_model(deals, T), score.fit_model(mutated, T)
    assert model == model_mutated  # joelho, intercepto, inclinação, limite de Limpe, escala: idênticos

    train = features.training_set(features.as_of(deals, T), T)
    train_mutated = features.training_set(features.as_of(mutated, T), T)
    columns = ["snapshot_date", "opportunity_id", "age_days", "sales_price", "y"]
    pd.testing.assert_frame_equal(train[columns], train_mutated[columns])

    scores = score.score_deals(deals, T, model)
    scores_mutated = score.score_deals(mutated, T, model_mutated)
    assert len(scores) > 1000
    pd.testing.assert_frame_equal(
        scores[SCORE_COLUMNS].sort_values("opportunity_id").reset_index(drop=True),
        scores_mutated[SCORE_COLUMNS].sort_values("opportunity_id").reset_index(drop=True),
    )


def test_future_mutation_control_changes_a_later_cut(deals):
    """Controle negativo: o mesmo embaralhamento TEM de mudar um modelo ajustado depois de T."""
    mutated = mutate_future(deals, "2017-06-30", seed=1)
    assert score.fit_model(deals, "2017-09-30") != score.fit_model(mutated, "2017-09-30")
    assert score.fit_model(deals, "2017-06-30") == score.fit_model(mutated, "2017-06-30")


def test_naive_choices_would_leak_and_the_mutation_exposes_them(deals):
    """As duas escolhas ingênuas que as guardas evitam mudariam com o futuro; as do código, não."""
    T = pd.Timestamp("2017-06-30")
    mutated = mutate_future(deals, T, seed=1)

    def naive_limpe(d):  # maior ciclo de todos os ganhos do arquivo, sem olhar a data T
        won = d[d["deal_stage"] == "Won"]
        return int((won["close_date"] - won["engage_date"]).dt.days.max())

    def naive_label(d):  # foto de 30/06 com horizonte de 90 dias, que passa de T, lida do estágio final
        opened = features.open_at(d[d["engage_date"].notna()], T)
        return int(((opened["deal_stage"] == "Won") & (opened["close_date"] <= T + pd.Timedelta(days=90))).sum())

    assert naive_limpe(deals) != naive_limpe(mutated)
    assert naive_label(deals) != naive_label(mutated)
    assert score.fit_model(deals, T).limpe_after_days == score.fit_model(mutated, T).limpe_after_days


# --- Curva v2: fotos da mesma fase do trimestre -----------------------------------------------------


def test_quarter_phase_and_same_phase_filter():
    assert [features.quarter_phase(d) for d in ("2017-01-31", "2017-02-28", "2017-03-31", "2017-04-30", "2017-12-31")] == [1, 2, 3, 1, 3]
    train = pd.DataFrame({"snapshot_date": pd.to_datetime(["2017-03-31", "2017-04-30", "2017-06-30", "2017-07-31"]), "y": [1, 0, 1, 0]})
    assert features.same_phase(train, 3)["y"].tolist() == [1, 1]
    assert features.same_phase(train, 1)["y"].tolist() == [0, 0]
    assert features.same_phase(train, 2).empty


@pytest.mark.parametrize("T", [pd.Timestamp(c) for c in [*config.BACKTEST_CUTS, config.DEFAULT_REFERENCE_DATE]])
def test_v2_model_is_the_isotonic_fit_of_the_same_phase_rows_only(deals, T):
    model = score.fit_model(deals, T)
    assert model.version == "v2"
    every = features.training_set(features.as_of(deals, T), T)
    same = features.same_phase(every, features.quarter_phase(T))
    assert (same["snapshot_date"] + pd.Timedelta(days=config.HORIZON_DAYS) <= T).all()
    assert model.curve.binned == score.fit_binned_curve(same["age_days"], same["y"], alpha=0)


def test_v2_ignores_the_outcomes_of_photos_from_other_phases(deals):
    T = pd.Timestamp(config.DEFAULT_REFERENCE_DATE)
    every = features.training_set(features.as_of(deals, T), T)
    other = features.quarter_phase_series(every["snapshot_date"]) != features.quarter_phase(T)
    assert other.any()
    scrambled = every.copy()
    scrambled.loc[other, "y"] = 1 - scrambled.loc[other, "y"]
    scrambled.loc[other, "age_days"] = 0
    assert score._fit_v2(every, T, score.FitConfig()) == score._fit_v2(scrambled, T, score.FitConfig())
