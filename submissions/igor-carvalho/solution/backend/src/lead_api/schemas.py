"""Modelos Pydantic = contrato da API (docs/PLANO_APLICACAO.md seção 4.3)."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Band = Literal["focus", "follow_up", "low", "stale_risk", "review", "prospecting"]
Direction = Literal["positive", "negative"]


class LoginIn(BaseModel):
    user_key: str = Field(min_length=1, max_length=80)


class UserOut(BaseModel):
    user_key: str
    full_name: str
    role: Literal["seller", "manager", "revops"]
    manager: Optional[str] = None
    regional_office: Optional[str] = None


class LoginOut(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserOut


class MeOut(UserOut):
    scope: dict


class Reason(BaseModel):
    code: str
    label: str
    value: Optional[str] = None
    direction: Direction
    impact: float


class MissingField(BaseModel):
    field: str
    label: str
    affects_prediction: bool


class DataQuality(BaseModel):
    status: Literal["complete", "incomplete"]
    summary: str
    missing: list[MissingField]


class ExplainedReason(Reason):
    factor: str
    observed: Optional[str] = None
    reference: Optional[str] = None


class DealSummary(BaseModel):
    opportunity_id: str
    seller: str
    manager: str
    office: str
    stage: Literal["Engaging", "Prospecting"]
    product: str
    series: str
    account: Optional[str] = None
    account_missing: bool
    list_price: float
    engage_date: Optional[str] = None
    age_days: Optional[int] = None
    score: Optional[int] = None
    priority_level: Optional[Literal["Alta", "Média", "Baixa"]] = None
    band: Band
    view: Literal["focus", "decide", "follow", "prospecting", "review"]
    expected_value: float
    p_win: Optional[float] = None
    confidence: Literal["low", "medium", "high"]
    confidence_reason: Optional[str] = None
    data_quality: DataQuality
    suggested_action: str
    flags: list[str]
    reasons: list[Reason]


class DealPage(BaseModel):
    items: list[DealSummary]
    page: int
    page_size: int
    total: int


class Explanation(BaseModel):
    base_label: str
    contributions: list[ExplainedReason]
    disclaimer: str


class DealDetail(DealSummary):
    explanation: Explanation
    context: dict


class WhatIfIn(BaseModel):
    product: str = Field(min_length=1)
    seller: str = Field(min_length=1)
    age_days: int = Field(ge=0, le=400)


class WhatIfOut(BaseModel):
    score: Optional[int]
    band: Band
    priority_level: Optional[str]
    expected_value: float
    p_win: Optional[float]
    reasons: list[Reason]
    model_version: str


class FeedbackIn(BaseModel):
    action: Literal["worked", "disagree", "ignore"]
    comment: Optional[str] = Field(default=None, max_length=280)


class FeedbackCreated(BaseModel):
    id: int
    created_at: str


class FeedbackItem(BaseModel):
    id: int
    opportunity_id: str
    user_key: str
    action: str
    comment: Optional[str]
    model_version: Optional[str]
    created_at: str


class FeedbackList(BaseModel):
    items: list[FeedbackItem]


class JobOut(BaseModel):
    job_id: str
    kind: str
    status: Literal["queued", "running", "succeeded", "failed"]
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
