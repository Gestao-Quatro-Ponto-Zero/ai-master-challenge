"""
alerts/models.py
----------------
Schemas Pydantic para o sistema de alertas.
"""

from pydantic import BaseModel
from typing import Optional
from enum import Enum


class AlertSeverity(str, Enum):
    critical = "critical"   # ação urgente — deal muito acima da média, alto valor
    warning  = "warning"    # atenção — deal esfriando
    info     = "info"       # informativo — deal parado mas de baixo score


class AlertType(str, Enum):
    deal_stale         = "deal_stale"          # deal parado acima da média do produto
    deal_critical_stale = "deal_critical_stale" # deal parado 2x+ acima da média
    high_value_at_risk  = "high_value_at_risk"  # deal de alto valor esfriando
    agent_pipeline_cold = "agent_pipeline_cold" # vendedor com muitos deals frios
    no_engaging_deals   = "no_engaging_deals"   # vendedor sem nenhum deal em Engaging


class Alert(BaseModel):
    id: str
    type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    opportunity_id: Optional[str]
    account: Optional[str]
    sales_agent: Optional[str]
    manager: Optional[str]
    regional_office: Optional[str]
    score: Optional[int]
    close_value: Optional[float]
    days_in_pipeline: Optional[int]
    created_at: str        # ISO timestamp
    dismissed: bool = False
    dismissed_at: Optional[str] = None
    dismissed_by: Optional[str] = None


class AlertsResponse(BaseModel):
    total: int
    unseen: int
    alerts: list[Alert]


class DismissRequest(BaseModel):
    user_id: str
