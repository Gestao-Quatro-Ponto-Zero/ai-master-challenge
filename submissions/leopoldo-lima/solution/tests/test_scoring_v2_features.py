"""Scoring enriquecido (CRP-REAL-04): features derivadas do payload / dataset."""

from __future__ import annotations

from datetime import date

import pytest

from src.features.engineering import feature_set_from_payload
from src.scoring.engine import load_rules, score_from_features


def test_feature_set_from_payload_maps_join_fields() -> None:
    payload = {
        "id": "X1",
        "deal_stage": "Engaging",
        "engage_date": "2026-01-01",
        "close_date": None,
        "amount": 5000,
        "account_name": "Acme",
        "account_revenue": "5000000",
        "account_employees": "800",
        "product_series": "GTX",
        "product_sales_price": 9000,
        "team_regional_office": "Central",
        "manager": "Dustin Brinkmann",
        "product": "GTX Pro",
    }
    fs = feature_set_from_payload(payload, reference_date=date(2026, 1, 10))
    assert fs.days_since_engage == 9
    assert fs.pipeline_age_bucket == "fresh"
    assert fs.stage_rank == 2
    assert fs.account_revenue_band == "mid"
    assert fs.employee_band == "medium"
    assert fs.product_series == "GTX"
    assert fs.regional_office == "Central"
    assert fs.manager_name == "Dustin Brinkmann"


def test_scoring_v2_includes_series_and_pipeline_explanations() -> None:
    rules = load_rules()
    assert rules.get("version") == 2
    payload = {
        "id": "Z1",
        "deal_stage": "Engaging",
        "engage_date": "2026-01-01",
        "amount": 15000,
        "account_name": "BigCo",
        "account_revenue": "20000000",
        "account_employees": "2000",
        "product_series": "GTX",
        "product_sales_price": 9000,
        "team_regional_office": "West",
        "manager": "Lead M",
        "product": "GTX Pro",
    }
    fs = feature_set_from_payload(payload, reference_date=date(2026, 1, 8))
    result = score_from_features(fs, rules)
    assert result.score >= 75
    assert any("serie de produto" in p for p in result.positives)
    assert any("idade no pipeline" in p for p in result.positives)


def test_scoring_penalizes_stale_open_pipeline() -> None:
    rules = load_rules()
    payload = {
        "id": "Stale",
        "deal_stage": "Prospecting",
        "engage_date": "2024-01-01",
        "amount": 100,
        "account_name": "Co",
        "account_revenue": "100",
        "account_employees": "5",
        "product_series": "MG",
        "team_regional_office": "East",
        "manager": "M",
    }
    fs = feature_set_from_payload(payload, reference_date=date(2026, 3, 1))
    result = score_from_features(fs, rules)
    assert any("stale" in n or "pipeline" in n for n in result.negatives)


def test_score_from_features_respects_version_1_rules_without_v2_blocks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rules_v1 = {
        "base_score": 50,
        "deal_stage_weights": {"Engaging": 5},
        "close_value": {
            "high_threshold": 10000,
            "high_weight": 10,
            "mid_threshold": 3000,
            "mid_weight": 5,
        },
        "missing_account_penalty": -8,
        "actions": {"high": "h", "medium": "m", "low": "l"},
    }
    fs = feature_set_from_payload(
        {"id": "v1", "deal_stage": "Engaging", "amount": 500, "title": "Acc"},
        reference_date=date(2026, 1, 15),
    )
    r = score_from_features(fs, rules_v1)
    assert r.score == 55  # base + Engaging; sem v2; com account
    assert r.next_best_action == "m"
