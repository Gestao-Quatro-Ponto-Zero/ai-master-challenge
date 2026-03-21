from __future__ import annotations

from src.infrastructure.http.mappers import (
    map_wire_detail_to_contract,
    map_wire_list_item_to_contract,
)


def test_list_item_mapper_handles_legacy_and_defaults() -> None:
    payload = {
        "id": "OPP-1",
        "title": "Deal",
        "seller": "Ana",
        "manager": "Marcos",
        "region": "Core",
        "status": "Open",
        "amount": "1200.5",
        "score": "60",
        "priority_band": "medium",
        "nextBestAction": "ligar",
    }
    mapped = map_wire_list_item_to_contract(payload)
    assert mapped.amount == 1200.5
    assert mapped.score == 60
    assert mapped.deal_stage == "Engaging"
    assert mapped.next_action == "ligar"
    assert mapped.nextBestAction == "ligar"


def test_detail_mapper_validates_shape() -> None:
    payload = {
        "id": "OPP-1",
        "title": "Deal",
        "seller": "Ana",
        "manager": "Marcos",
        "region": "Core",
        "status": "Open",
        "amount": 1200.5,
        "scoreExplanation": {
            "score": 60,
            "priority_band": "medium",
            "positive_factors": ["f1"],
            "negative_factors": [],
            "risk_flags": [],
            "next_action": "ligar",
        },
    }
    mapped = map_wire_detail_to_contract(payload)
    assert mapped.id == "OPP-1"
    assert mapped.deal_stage == "Engaging"
    assert mapped.scoreExplanation.score == 60
