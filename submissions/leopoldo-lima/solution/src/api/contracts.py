from __future__ import annotations

from pydantic import BaseModel, Field


class ApiError(BaseModel):
    detail: str


class ScoreExplanationResponse(BaseModel):
    score: int
    priority_band: str
    positive_factors: list[str]
    negative_factors: list[str]
    risk_flags: list[str]
    next_action: str


class OpportunityListItemResponse(BaseModel):
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
    nextBestAction: str
    # CRP-REAL-05: campos explícitos do dataset (além de aliases legados seller/region/amount)
    account: str = ""
    product: str = ""
    sales_agent: str = ""
    regional_office: str = ""
    close_value: float = 0.0


class OpportunitiesListResponse(BaseModel):
    total: int
    items: list[OpportunityListItemResponse]


class OpportunityDetailResponse(BaseModel):
    id: str
    title: str
    seller: str
    manager: str
    region: str
    deal_stage: str
    amount: float
    scoreExplanation: ScoreExplanationResponse
    account: str = ""
    product: str = ""
    sales_agent: str = ""
    regional_office: str = ""
    close_value: float = 0.0
    engage_date: str = ""
    close_date: str | None = None
    product_series: str = ""


class DashboardKpisResponse(BaseModel):
    total_opportunities: int
    open_opportunities: int
    won_opportunities: int
    lost_opportunities: int
    avg_score: float


class DashboardFilterOptionsResponse(BaseModel):
    """Opções para filtros do dashboard (CRP-CBX-01: ordenadas, sem duplicados)."""

    regional_offices: list[str] = Field(default_factory=list)
    managers: list[str] = Field(default_factory=list)
    deal_stages: list[str] = Field(default_factory=list)
    regions: list[str] = Field(
        default_factory=list,
        description="Espelho de regional_offices para compatibilidade com clientes legados.",
    )
