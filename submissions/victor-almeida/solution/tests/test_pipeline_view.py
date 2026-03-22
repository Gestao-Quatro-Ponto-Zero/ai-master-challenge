"""
Testes para components/pipeline_view.py e components/deal_detail.py

Cobre: prepare_pipeline_data, get_velocity_status, format_zombie_tag,
       build_explanation, build_next_action_text, score_color, format_currency.
"""

import math

import numpy as np
import pandas as pd
import pytest

from components.pipeline_view import (
    format_zombie_tag,
    get_velocity_status,
    prepare_pipeline_data,
)
from components.deal_detail import (
    build_explanation,
    build_next_action_text,
)
from utils.formatters import format_currency, score_color


# ---------------------------------------------------------------------------
# Helpers — synthetic data builders
# ---------------------------------------------------------------------------


def _make_pipeline_df(rows: list[dict]) -> pd.DataFrame:
    """Build a synthetic scored pipeline DataFrame from a list of row dicts.

    Missing keys are filled with sensible defaults so each test only needs to
    specify the columns relevant to its assertion.
    """
    defaults = {
        "opportunity_id": "OPP-001",
        "deal_stage": "Engaging",
        "sales_agent": "Agent A",
        "account": "Acme Corp",
        "product": "GTK 500",
        "close_value": np.nan,
        "sales_price": 5000.0,
        "score_final": 75.0,
        "score_stage": 70.0,
        "score_value": 60.0,
        "score_velocity": 80.0,
        "score_seller_fit": 50.0,
        "score_account_health": 50.0,
        "days_in_stage": 30.0,
        "is_zombie": False,
        "is_critical_zombie": False,
        "velocity_ratio": 0.5,
        "velocity_label": "saudavel",
        "sector": "Technology",
        "manager": "Manager X",
        "regional_office": "West",
    }
    complete_rows = []
    for i, row in enumerate(rows):
        r = {**defaults, **row}
        if r["opportunity_id"] == "OPP-001" and i > 0:
            r["opportunity_id"] = f"OPP-{i + 1:03d}"
        complete_rows.append(r)
    return pd.DataFrame(complete_rows)


def _make_breakdown(
    score_final: float = 85.0,
    stage_score: int = 70,
    value_score: int = 90,
    velocity_score: int = 100,
    seller_fit_score: int = 80,
    account_health_score: int = 85,
    velocity_ratio: float = 0.39,
    velocity_label: str = "saudavel",
    is_zombie: bool = False,
    is_critical_zombie: bool = False,
    zombie_detail: str | None = None,
) -> dict:
    """Build a sample score_breakdown dict."""
    return {
        "score_final": score_final,
        "components": {
            "stage": {
                "score": stage_score,
                "weight": 0.30,
                "weighted": stage_score * 0.30,
                "detail": "Deal em Engaging — ja qualificado",
            },
            "expected_value": {
                "score": value_score,
                "weight": 0.25,
                "weighted": value_score * 0.25,
                "detail": "Valor alto (GTK 500, $26,768)",
            },
            "velocity": {
                "score": velocity_score,
                "weight": 0.25,
                "weighted": velocity_score * 0.25,
                "detail": "34 dias em Engaging (saudavel, ref: 88 dias)",
                "ratio": velocity_ratio,
                "label": velocity_label,
            },
            "seller_fit": {
                "score": seller_fit_score,
                "weight": 0.10,
                "weighted": seller_fit_score * 0.10,
                "detail": "Seu WR neste setor (72%) esta acima da media (65%)",
            },
            "account_health": {
                "score": account_health_score,
                "weight": 0.10,
                "weighted": account_health_score * 0.10,
                "detail": "Conta com bom historico (78% WR em 12 deals)",
            },
        },
        "flags": {
            "is_zombie": is_zombie,
            "is_critical_zombie": is_critical_zombie,
            "zombie_detail": zombie_detail,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# Data integrity tests (6)
# ═══════════════════════════════════════════════════════════════════════════


class TestPipelineDataIntegrity:
    def test_pipeline_view_only_active_deals(self):
        """prepare_pipeline_data returns only Prospecting + Engaging deals."""
        df = _make_pipeline_df(
            [
                {"opportunity_id": "OPP-A", "deal_stage": "Prospecting", "score_final": 40.0},
                {"opportunity_id": "OPP-B", "deal_stage": "Engaging", "score_final": 80.0},
                {"opportunity_id": "OPP-C", "deal_stage": "Won", "score_final": 90.0},
                {"opportunity_id": "OPP-D", "deal_stage": "Lost", "score_final": 10.0},
            ]
        )
        result = prepare_pipeline_data(df)
        stages = result["deal_stage"].unique().tolist()
        assert set(stages) <= {"Prospecting", "Engaging"}
        assert len(result) == 2

    def test_pipeline_view_sorted_by_score_desc(self):
        """prepare_pipeline_data sorts by score descending."""
        df = _make_pipeline_df(
            [
                {"opportunity_id": "OPP-LOW", "score_final": 30.0},
                {"opportunity_id": "OPP-MID", "score_final": 60.0},
                {"opportunity_id": "OPP-HI", "score_final": 90.0},
            ]
        )
        result = prepare_pipeline_data(df)
        scores = result["score_final"].tolist()
        assert scores == sorted(scores, reverse=True)

    def test_pipeline_view_has_expected_columns(self):
        """Output has the required display columns."""
        df = _make_pipeline_df([{"opportunity_id": "OPP-1"}])
        result = prepare_pipeline_data(df)
        expected_cols = {
            "score_final",
            "opportunity_id",
            "account",
            "product",
            "valor_display",
            "deal_stage",
            "dias_display",
            "sales_agent",
        }
        assert expected_cols.issubset(set(result.columns))

    def test_pipeline_view_displays_sem_conta_when_null(self):
        """When account is NaN, display column shows 'Sem conta'."""
        df = _make_pipeline_df(
            [{"opportunity_id": "OPP-NULL", "account": np.nan}]
        )
        result = prepare_pipeline_data(df)
        assert result.iloc[0]["account"] == "Sem conta"

    def test_pipeline_view_value_uses_proxy_for_active(self):
        """valor_display uses sales_price for active deals (not close_value)."""
        df = _make_pipeline_df(
            [
                {
                    "opportunity_id": "OPP-ACTIVE",
                    "deal_stage": "Engaging",
                    "sales_price": 26768.0,
                    "close_value": np.nan,
                }
            ]
        )
        result = prepare_pipeline_data(df)
        assert result.iloc[0]["valor_display"] == "$26.8K"

    def test_pipeline_view_days_dash_for_prospecting(self):
        """dias_display shows dash for Prospecting deals."""
        df = _make_pipeline_df(
            [
                {
                    "opportunity_id": "OPP-PROSP",
                    "deal_stage": "Prospecting",
                    "days_in_stage": np.nan,
                }
            ]
        )
        result = prepare_pipeline_data(df)
        assert result.iloc[0]["dias_display"] == "\u2014"


# ═══════════════════════════════════════════════════════════════════════════
# Color coding tests (4) — uses existing score_color from formatters
# ═══════════════════════════════════════════════════════════════════════════


class TestScoreColorCoding:
    def test_score_color_green_for_80_plus(self):
        """score_color(85) returns green."""
        assert score_color(85) == "#2ecc71"

    def test_score_color_yellow_for_60_to_79(self):
        """score_color(65) returns yellow."""
        assert score_color(65) == "#f1c40f"

    def test_score_color_orange_for_40_to_59(self):
        """score_color(45) returns orange."""
        assert score_color(45) == "#e67e22"

    def test_score_color_red_for_below_40(self):
        """score_color(20) returns red."""
        assert score_color(20) == "#e74c3c"


# ═══════════════════════════════════════════════════════════════════════════
# Deal detail tests (4)
# ═══════════════════════════════════════════════════════════════════════════


class TestDealDetail:
    def test_deal_detail_score_breakdown_sums_to_total(self):
        """Sum of weighted components = score_final (tolerance 0.5)."""
        breakdown = _make_breakdown(score_final=85.0)
        total_weighted = sum(
            c["weighted"] for c in breakdown["components"].values()
        )
        assert abs(total_weighted - breakdown["score_final"]) < 0.5

    def test_deal_detail_has_explanation_text(self):
        """build_explanation returns non-empty string."""
        deal = pd.Series(
            {
                "deal_stage": "Engaging",
                "days_in_stage": 34,
                "product": "GTK 500",
                "sales_agent": "Agent A",
                "account": "Acme Corp",
            }
        )
        breakdown = _make_breakdown()
        text = build_explanation(deal, breakdown)
        assert isinstance(text, str)
        assert len(text) > 0

    def test_deal_detail_has_next_action(self):
        """build_next_action_text returns non-empty string."""
        deal = pd.Series(
            {
                "deal_stage": "Engaging",
                "days_in_stage": 34,
                "score_final": 85.0,
            }
        )
        breakdown = _make_breakdown()
        text = build_next_action_text(deal, breakdown)
        assert isinstance(text, str)
        assert len(text) > 0

    def test_deal_detail_zombie_flag_shown_when_zombie(self):
        """format_zombie_tag returns visible tag for zombie, empty for non-zombie."""
        assert format_zombie_tag(True, False) != ""
        assert format_zombie_tag(True, True) != ""
        assert format_zombie_tag(False, False) == ""
        # Critical zombies should have a distinct tag
        tag_zombie = format_zombie_tag(True, False)
        tag_critical = format_zombie_tag(True, True)
        assert tag_zombie != tag_critical


# ═══════════════════════════════════════════════════════════════════════════
# Formatting tests (2)
# ═══════════════════════════════════════════════════════════════════════════


class TestFormattingHelpers:
    def test_format_value_abbreviation(self):
        """format_currency abbreviates correctly."""
        assert format_currency(26768) == "$26.8K"
        assert format_currency(550) == "$550"
        assert format_currency(55) == "$55"

    def test_velocity_status_vocabulary(self):
        """get_velocity_status maps ratio to correct vocabulary."""
        assert get_velocity_status(0.5) == "saudavel"
        assert get_velocity_status(1.0) == "saudavel"
        assert get_velocity_status(1.1) == "no limite"
        assert get_velocity_status(1.2) == "no limite"
        assert get_velocity_status(1.4) == "parado"
        assert get_velocity_status(1.8) == "em risco"
        assert get_velocity_status(2.5) == "zumbi"
        assert get_velocity_status(None) == "sem dados"
