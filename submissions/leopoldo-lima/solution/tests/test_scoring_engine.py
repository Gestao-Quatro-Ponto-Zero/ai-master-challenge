from __future__ import annotations

from src.scoring.engine import load_rules, score_opportunity


def test_scoring_is_deterministic_for_same_input() -> None:
    rules = load_rules()
    opportunity = {
        "deal_stage": "Engaging",
        "close_value": "12000",
        "account": "Acme Corp",
    }

    first = score_opportunity(opportunity, rules)
    second = score_opportunity(opportunity, rules)

    assert first == second
    assert first.score >= 0
    assert first.score <= 100


def test_scoring_flags_missing_account_as_risk() -> None:
    rules = load_rules()
    opportunity = {
        "deal_stage": "Prospecting",
        "close_value": "900",
        "account": "",
    }

    result = score_opportunity(opportunity, rules)

    assert result.score < 50
    assert any("account ausente" in n for n in result.negatives)
    assert any("Registro sem account" in r for r in result.risks)
    assert result.next_best_action
