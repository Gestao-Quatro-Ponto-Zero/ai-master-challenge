from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from src.domain.deal_stage import normalize_deal_stage


class OpportunityListItemDTO(BaseModel):
    id: str = "unknown"
    title: str = ""
    seller: str = ""
    manager: str = ""
    region: str = ""
    deal_stage: str = ""
    amount: float = 0.0
    score: int = 0
    priority_band: str = "low"
    next_action: str = ""
    nextBestAction: str = ""
    account: str = ""
    product: str = ""
    sales_agent: str = ""
    regional_office: str = ""
    close_value: float = 0.0

    @classmethod
    def from_wire(cls, payload: dict) -> "OpportunityListItemDTO":
        data = dict(payload)
        if "deal_stage" not in data and "status" in data:
            data["deal_stage"] = normalize_deal_stage(str(data.pop("status", "")))
        next_action = str(data.get("next_action", "")).strip()
        if not next_action:
            next_action = str(data.get("nextBestAction", "")).strip()
        data["next_action"] = next_action
        data["nextBestAction"] = str(data.get("nextBestAction", next_action)).strip()
        return cls.model_validate(data)


class ScoreExplanationDTO(BaseModel):
    score: int = 0
    priority_band: str = "low"
    positive_factors: list[str] = Field(default_factory=list)
    negative_factors: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    next_action: str = ""


class OpportunityDetailDTO(BaseModel):
    id: str
    title: str
    seller: str
    manager: str
    region: str
    deal_stage: str
    amount: float
    scoreExplanation: ScoreExplanationDTO
    account: str = ""
    product: str = ""
    sales_agent: str = ""
    regional_office: str = ""
    close_value: float = 0.0
    engage_date: str = ""
    close_date: str | None = None
    product_series: str = ""

    @model_validator(mode="before")
    @classmethod
    def _coerce_legacy_status(cls, data: object) -> object:
        if isinstance(data, dict):
            d = dict(data)
            if "deal_stage" not in d and "status" in d:
                d["deal_stage"] = normalize_deal_stage(str(d.pop("status", "")))
            return d
        return data
