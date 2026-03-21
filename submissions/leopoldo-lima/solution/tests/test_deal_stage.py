"""Domínio oficial de estágio (CRP-REAL-03)."""

from __future__ import annotations

import pytest

from src.domain.deal_stage import (
    OFFICIAL_DEAL_STAGES,
    is_official_deal_stage,
    is_pipeline_open_stage,
    normalize_deal_stage,
)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Prospecting", "Prospecting"),
        ("Engaging", "Engaging"),
        ("Won", "Won"),
        ("Lost", "Lost"),
        ("Open", "Engaging"),
        ("", "Engaging"),
        ("Unknown", "Engaging"),
    ],
)
def test_normalize_deal_stage(raw: str, expected: str) -> None:
    assert normalize_deal_stage(raw) == expected


def test_official_stages_tuple_is_challenge_taxonomy() -> None:
    assert OFFICIAL_DEAL_STAGES == ("Prospecting", "Engaging", "Won", "Lost")
    for s in OFFICIAL_DEAL_STAGES:
        assert is_official_deal_stage(s)


def test_pipeline_open_includes_prospecting_and_engaging() -> None:
    assert is_pipeline_open_stage("Prospecting")
    assert is_pipeline_open_stage("Engaging")
    assert not is_pipeline_open_stage("Won")
    assert not is_pipeline_open_stage("Lost")
