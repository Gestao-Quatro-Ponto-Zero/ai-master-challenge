from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from src.api.explanation_narrative import humanize_score_explanations
from src.scoring.engine import ScoreResult


@dataclass(frozen=True)
class ScoreExplanationView:
    score: int
    priority_band: str
    positive_factors: list[str]
    negative_factors: list[str]
    risk_flags: list[str]
    next_action: str


@dataclass(frozen=True)
class OpportunityListItemView:
    id: str
    title: str
    seller: str
    manager: str
    region: str
    deal_stage: str
    amount: float
    score: int
    priority_band: str
    next_action: str


@dataclass(frozen=True)
class OpportunityDetailView:
    id: str
    title: str
    seller: str
    manager: str
    region: str
    deal_stage: str
    amount: float
    explanation: ScoreExplanationView


def _priority_band(score: int) -> str:
    if score >= 75:
        return "high"
    if score >= 45:
        return "medium"
    return "low"


def _to_float(value: object) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return 0.0


def build_explanation_view(
    result: ScoreResult,
    *,
    opportunity_id: str = "",
    deal_stage: str = "",
) -> ScoreExplanationView:
    pos, neg, risks = humanize_score_explanations(
        result, deal_stage=deal_stage, opportunity_id=opportunity_id
    )
    return ScoreExplanationView(
        score=result.score,
        priority_band=_priority_band(result.score),
        positive_factors=pos,
        negative_factors=neg,
        risk_flags=risks,
        next_action=result.next_best_action,
    )


def build_list_item_view(base: dict[str, object], result: ScoreResult) -> OpportunityListItemView:
    return OpportunityListItemView(
        id=str(base["id"]),
        title=str(base["title"]),
        seller=str(base["seller"]),
        manager=str(base["manager"]),
        region=str(base["region"]),
        deal_stage=str(base["deal_stage"]),
        amount=_to_float(base["amount"]),
        score=result.score,
        priority_band=_priority_band(result.score),
        next_action=result.next_best_action,
    )


def build_detail_view(base: dict[str, object], result: ScoreResult) -> OpportunityDetailView:
    return OpportunityDetailView(
        id=str(base["id"]),
        title=str(base["title"]),
        seller=str(base["seller"]),
        manager=str(base["manager"]),
        region=str(base["region"]),
        deal_stage=str(base["deal_stage"]),
        amount=_to_float(base["amount"]),
        explanation=build_explanation_view(
            result,
            opportunity_id=str(base["id"]),
            deal_stage=str(base["deal_stage"]),
        ),
    )


def to_dict(view: Any) -> dict[str, Any]:
    return asdict(view)
