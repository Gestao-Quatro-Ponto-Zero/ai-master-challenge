from __future__ import annotations

import os

import pandas as pd
import pytest

from src.data_loader import DatasetNotFoundError, get_data_dir
from src.scoring import load_data, score_open_pipeline


def _real_data_or_skip():
    try:
        return load_data(get_data_dir())
    except DatasetNotFoundError as exc:
        pytest.skip(f"Local Kaggle dataset not available: {exc}")


def test_open_pipeline_count_and_no_closed_deals():
    data = _real_data_or_skip()
    scored = score_open_pipeline(data["enriched"])
    assert len(scored) == 2089
    assert set(scored["deal_stage"].unique()) <= {"Prospecting", "Engaging"}


def test_priority_scores_are_bounded():
    data = _real_data_or_skip()
    scored = score_open_pipeline(data["enriched"])
    assert scored["priority_score"].between(0, 100).all()
    assert scored["historical_fit"].between(0, 100).all()


def test_close_fields_do_not_drive_open_score():
    data = _real_data_or_skip()
    original = score_open_pipeline(data["enriched"])[["opportunity_id", "priority_score"]].set_index("opportunity_id")

    mutated = data["enriched"].copy()
    mask = mutated["deal_stage"].isin(["Prospecting", "Engaging"])
    mutated.loc[mask, "close_value"] = 999999999
    mutated.loc[mask, "close_date"] = pd.Timestamp("2099-01-01")
    rescored = score_open_pipeline(mutated)[["opportunity_id", "priority_score"]].set_index("opportunity_id")

    pd.testing.assert_series_equal(original["priority_score"], rescored["priority_score"])


def test_missing_account_does_not_break_scoring():
    data = _real_data_or_skip()
    scored = score_open_pipeline(data["enriched"])
    missing = scored[scored["account"].isna()]
    assert not missing.empty
    assert missing["historical_fit"].notna().all()
    assert missing["priority_score"].notna().all()


def test_no_local_dataset_is_committed_inside_solution():
    solution_dir = os.path.dirname(os.path.dirname(__file__))
    assert not os.path.isdir(os.path.join(solution_dir, "data"))
