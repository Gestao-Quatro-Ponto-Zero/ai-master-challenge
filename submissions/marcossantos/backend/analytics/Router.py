"""
analytics/router.py
-------------------
Rotas de analytics — restritas a manager e admin.

  GET /api/analytics/team     → win rate e ranking por vendedor
  GET /api/analytics/funnel   → conversão por stage e produto
  GET /api/analytics/at-risk  → deals em risco agrupados por região
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional

from .models import TeamAnalyticsResponse, FunnelAnalyticsResponse, AtRiskResponse
from .service import compute_team_analytics, compute_funnel_analytics, compute_at_risk
from auth.dependencies import require_role, get_pipeline_filters_for_user

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


def _get_loader():
    """Importa o loader do main para evitar circular import."""
    from main import loader
    return loader


# ---------------------------------------------------------------------------
# Helpers para aplicar filtros de role automaticamente
# ---------------------------------------------------------------------------

def _resolve_filters(current_user: dict, manager: Optional[str], region: Optional[str]):
    """
    Managers só veem o próprio time.
    Admins podem ver qualquer manager/região.
    """
    role_filters = get_pipeline_filters_for_user(current_user)
    return (
        role_filters.get("manager") or manager,
        region,
    )


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------

@router.get("/team", response_model=TeamAnalyticsResponse)
def team_analytics(
    manager: Optional[str] = Query(None, description="Filtrar por manager (admin only)"),
    region:  Optional[str] = Query(None, description="Filtrar por região"),
    current_user: dict     = Depends(require_role("admin", "manager")),
):
    """
    Ranking de vendedores com win rate, deals ativos e status de coaching.
    Manager vê automaticamente apenas o seu time.
    Admin pode filtrar por qualquer manager.
    """
    loader = _get_loader()
    effective_manager, effective_region = _resolve_filters(current_user, manager, region)

    return compute_team_analytics(
        pipeline=loader.pipeline,
        metrics=loader.metrics,
        manager_filter=effective_manager,
        region_filter=effective_region,
    )


@router.get("/funnel", response_model=FunnelAnalyticsResponse)
def funnel_analytics(
    manager: Optional[str] = Query(None),
    region:  Optional[str] = Query(None),
    current_user: dict     = Depends(require_role("admin", "manager")),
):
    """
    Funil de conversão: distribuição por stage e win rate por produto.
    """
    loader = _get_loader()
    effective_manager, effective_region = _resolve_filters(current_user, manager, region)

    return compute_funnel_analytics(
        pipeline=loader.pipeline,
        metrics=loader.metrics,
        manager_filter=effective_manager,
        region_filter=effective_region,
    )


@router.get("/at-risk", response_model=AtRiskResponse)
def at_risk_analytics(
    manager:   Optional[str] = Query(None),
    region:    Optional[str] = Query(None),
    min_ratio: float          = Query(1.5, ge=1.0, le=5.0, description="Ratio mínimo para considerar em risco"),
    current_user: dict        = Depends(require_role("admin", "manager")),
):
    """
    Deals em risco: acima da média histórica do produto, agrupados por região.
    min_ratio: quantas vezes acima da média para considerar em risco (padrão: 1.5x).
    """
    loader = _get_loader()
    effective_manager, effective_region = _resolve_filters(current_user, manager, region)

    return compute_at_risk(
        pipeline=loader.pipeline,
        metrics=loader.metrics,
        manager_filter=effective_manager,
        region_filter=effective_region,
        min_ratio=min_ratio,
    )