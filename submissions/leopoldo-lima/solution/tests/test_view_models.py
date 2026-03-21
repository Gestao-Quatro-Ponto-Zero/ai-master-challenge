from __future__ import annotations

from src.api.view_models import (
    build_detail_view,
    build_explanation_view,
    build_list_item_view,
    to_dict,
)
from src.scoring.engine import ScoreResult


def _base() -> dict[str, object]:
    return {
        "id": "OPP-1",
        "title": "Deal",
        "seller": "Ana",
        "manager": "Marcos",
        "region": "Core",
        "deal_stage": "Engaging",
        "amount": 1000,
    }


def _score() -> ScoreResult:
    return ScoreResult(
        score=80,
        positives=["p1"],
        negatives=["n1"],
        risks=["r1"],
        next_best_action="follow-up",
    )


def test_view_model_serialization() -> None:
    item = to_dict(build_list_item_view(_base(), _score()))
    assert item["priority_band"] == "high"
    assert item["score"] == 80

    detail = to_dict(build_detail_view(_base(), _score()))
    assert detail["explanation"]["score"] == 80
    assert detail["explanation"]["next_action"] == "follow-up"

    expl = to_dict(build_explanation_view(_score()))
    assert expl["risk_flags"] == ["r1"]
