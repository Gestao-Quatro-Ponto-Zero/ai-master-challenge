from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import backtest
import lead_scorer as ls

DATA = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture(scope="module")
def deals():
    return ls.load_deals(DATA)


@pytest.fixture(scope="module")
def scored(deals):
    return ls.score_pipeline(deals)


def test_join_keeps_every_deal_and_fixes_known_errors(deals):
    assert len(deals) == 8800
    assert "GTXPro" not in set(deals["product"])
    assert deals["sales_price"].notna().all()
    assert "technolgy" not in set(deals["sector"].dropna())


def test_rates_ignore_outcomes_after_the_date(deals):
    """Rewriting everything that happened after a date must not change what was learned."""
    moment = pd.Timestamp("2017-09-04")
    before = ls.learn_rates(deals, moment, use_quarter=True)

    altered = deals.copy()
    future = altered["close_date"] >= moment
    altered.loc[future, "deal_stage"] = "Lost"
    altered.loc[future, "close_value"] = 0
    after = ls.learn_rates(altered, moment, use_quarter=True)

    assert after.by_age == before.by_age
    assert after.by_age_week == before.by_age_week
    assert after.max_cycle == before.max_cycle


def test_snapshot_only_contains_deals_open_at_that_moment(deals):
    moment = pd.Timestamp("2017-08-07")
    snapshot = ls.open_deals_at(deals, moment)
    assert (snapshot["engage_date"] < moment).all()
    assert (snapshot["close_date"].isna() | (snapshot["close_date"] >= moment)).all()
    assert (snapshot["age"] > 0).all()


def test_deals_older_than_any_closed_deal_go_to_the_decision_queue(scored):
    table, rates = scored
    stale = table[table["queue"] == "decidir"]
    assert len(stale) > 0
    assert (stale["age"] > rates.max_cycle).all()
    assert (stale["probability"] == 0).all()
    assert (table[table["queue"] == "foco"]["age"] <= rates.max_cycle).all()


def test_only_open_engaging_deals_are_scored(scored):
    assert set(scored[0]["deal_stage"]) == {"Engaging"}
    assert len(scored[0]) == 1589


@pytest.mark.parametrize("lo,hi", [(0.02, 0.2), (0.05, 0.3)])
def test_points_rank_exactly_like_expected_revenue(lo, hi):
    # The cheap, likely deal and the costly, unlikely one must order the same
    # way by points as by probability x price.
    cheap = ls.score_points(hi, 550, 55, 26768)
    costly = ls.score_points(lo, 5482, 55, 26768)
    assert (sum(cheap) > sum(costly)) == (hi * 550 > lo * 5482)


def test_score_stays_in_range(scored):
    assert scored[0]["score"].between(0, 100).all()


def test_visible_score_never_rises_down_the_list(scored):
    live = scored[0][scored[0]["queue"] == "foco"]
    assert np.all(np.diff(live["score"].to_numpy()) <= 0)


def test_stale_deals_rank_below_every_live_deal():
    values = ls.ranking_value(np.array([0.0, 0.002]), np.array([26768, 55]))
    assert values[0] == 0
    assert values[1] > 0


def test_tied_deals_do_not_depend_on_file_order(deals):
    snapshot = ls.open_deals_at(deals, pd.Timestamp("2017-08-07"))
    reversed_snapshot = snapshot.iloc[::-1]
    first = backtest.top_k(snapshot, snapshot["sales_price"].to_numpy())
    second = backtest.top_k(reversed_snapshot, reversed_snapshot["sales_price"].to_numpy())
    assert set(first["opportunity_id"]) == set(second["opportunity_id"])


def test_time_machine_outcomes_only_cover_the_30_day_window(deals):
    monday = pd.Timestamp("2017-08-07")
    snapshot, _ = backtest.monday_snapshot(deals, monday)
    won = snapshot[snapshot["outcome"] == "won"]
    assert (won["close_date"] < monday + pd.Timedelta(days=30)).all()
    later = snapshot[snapshot["close_date"] >= monday + pd.Timedelta(days=30)]
    assert (later["outcome"] == "open").all()
    assert (later["realized"] == 0).all()


@pytest.mark.parametrize(
    "moment,week",
    [("2018-01-01", 1), ("2017-07-03", 1), ("2017-10-02", 1), ("2017-04-10", 2), ("2017-09-25", 13)],
)
def test_quarter_week(moment, week):
    assert ls.quarter_week(pd.Timestamp(moment)) == week


def test_action_does_not_ask_for_a_decision_when_chance_is_low():
    assert ls.suggested_action(70, 138, 0.02).startswith("Prepare")
    assert ls.suggested_action(70, 138, 0.20).startswith("Peça")


@pytest.mark.parametrize(
    "age,zone",
    [(5, "novo"), (30, "intermediario"), (80, "janela"), (130, "prazo_final"), (139, "parado")],
)
def test_age_zones(age, zone):
    assert ls.age_zone(age, 138) == zone
