"""
models/schemas.py
-----------------
Contratos da API em Pydantic.
Garante que o frontend receba sempre a mesma estrutura,
independente do que mudar internamente no scoring.
"""

from pydantic import BaseModel
from typing import Optional


class FactorBreakdown(BaseModel):
    """Um fator de scoring com pontuação e explicação."""
    label:      str
    points:     float
    max_points: int
    reason:     str
    signal:     str   # "positive" | "warning" | "neutral"


class DealScore(BaseModel):
    """Score completo de uma oportunidade."""
    opportunity_id:  str
    account:         Optional[str]
    product:         Optional[str]
    sales_agent:     Optional[str]
    manager:         Optional[str]
    regional_office: Optional[str]
    deal_stage:      Optional[str]
    close_value:     Optional[float]
    days_in_pipeline: Optional[int]
    sector:          Optional[str]
    revenue:         Optional[float]
    employees:       Optional[float]

    # Scoring
    score:          int
    tier:           str   # "hot" | "warm" | "cold"
    action:         str
    action_urgency: str   # "high" | "medium" | "low"
    factors:        list[FactorBreakdown]


class PipelineResponse(BaseModel):
    """Resposta da rota GET /api/pipeline."""
    total:   int
    deals:   list[DealScore]


class AgentInfo(BaseModel):
    """Info de um vendedor."""
    sales_agent:     str
    manager:         Optional[str]
    regional_office: Optional[str]


class FiltersResponse(BaseModel):
    """Opções disponíveis para filtros no frontend."""
    agents:   list[str]
    managers: list[str]
    regions:  list[str]
    stages:   list[str]
    products: list[str]


class HealthResponse(BaseModel):
    status:            str
    total_deals:       int
    active_deals:      int
    global_win_rate:   float