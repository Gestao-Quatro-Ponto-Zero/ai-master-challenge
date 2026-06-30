"""
analytics/models.py
-------------------
Schemas Pydantic para as respostas de analytics.
"""

from pydantic import BaseModel
from typing import Optional


# ---------------------------------------------------------------------------
# GET /api/analytics/team
# ---------------------------------------------------------------------------

class AgentStats(BaseModel):
    """Métricas de um vendedor individual."""
    sales_agent:      str
    manager:          Optional[str]
    regional_office:  Optional[str]
    total_deals:      int           # total de deals fechados (Won + Lost)
    won_deals:        int
    lost_deals:       int
    win_rate:         float         # 0.0 a 1.0
    active_deals:     int           # Prospecting + Engaging ativos
    hot_deals:        int           # deals com tier "hot"
    pipeline_value:   float         # soma dos close_value ativos
    avg_deal_value:   float         # média dos deals Won
    status:           str           # "strong" | "average" | "needs_coaching"


class TeamAnalyticsResponse(BaseModel):
    """Resposta de GET /api/analytics/team."""
    manager:          Optional[str]
    regional_office:  Optional[str]
    team_win_rate:    float
    global_win_rate:  float
    total_agents:     int
    total_active:     int
    pipeline_value:   float
    agents:           list[AgentStats]


# ---------------------------------------------------------------------------
# GET /api/analytics/funnel
# ---------------------------------------------------------------------------

class StageCount(BaseModel):
    stage:   str
    count:   int
    pct:     float   # % do total ativo


class ProductFunnelStats(BaseModel):
    product:   str
    series:    Optional[str]
    won:       int
    lost:      int
    active:    int
    win_rate:  float
    avg_days_to_close: Optional[float]  # média de dias dos Won


class FunnelAnalyticsResponse(BaseModel):
    """Resposta de GET /api/analytics/funnel."""
    total_active:   int
    by_stage:       list[StageCount]
    by_product:     list[ProductFunnelStats]


# ---------------------------------------------------------------------------
# GET /api/analytics/at-risk
# ---------------------------------------------------------------------------

class RiskDeal(BaseModel):
    opportunity_id:   str
    account:          Optional[str]
    sales_agent:      Optional[str]
    product:          Optional[str]
    deal_stage:       Optional[str]
    close_value:      float
    days_in_pipeline: int
    days_above_avg:   int      # quantos dias acima da média do produto
    risk_ratio:       float    # days_in_pipeline / avg_days_produto
    score:            Optional[int]


class RegionRiskSummary(BaseModel):
    regional_office:  str
    total_at_risk:    int
    critical_count:   int    # ratio >= 2.0
    warning_count:    int    # ratio 1.5–2.0
    total_value_at_risk: float


class AtRiskResponse(BaseModel):
    """Resposta de GET /api/analytics/at-risk."""
    total_at_risk:    int
    critical_count:   int
    warning_count:    int
    total_value:      float
    by_region:        list[RegionRiskSummary]
    deals:            list[RiskDeal]