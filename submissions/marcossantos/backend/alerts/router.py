"""
alerts/router.py
----------------
Rotas da API para o sistema de alertas:

  GET  /api/alerts                → lista alertas do usuário logado
  POST /api/alerts/{id}/dismiss   → marca alerta como visto
  POST /api/alerts/dismiss-all    → marca todos como vistos
  POST /api/alerts/refresh        → força nova rodada de detecção (admin)
"""

from fastapi import APIRouter, HTTPException, Depends, Query

from .models import AlertsResponse, AlertSeverity
from .queue import get_alerts_for_user, dismiss_alert, dismiss_all_for_user
from .scheduler import scheduler
from auth.dependencies import get_current_user, require_role

router = APIRouter(prefix="/api/alerts", tags=["Alertas"])


@router.get("", response_model=AlertsResponse)
def list_alerts(
    include_dismissed: bool = Query(False, description="Incluir alertas já vistos"),
    severity: str           = Query(None,  description="Filtrar por severidade: critical | warning | info"),
    current_user: dict      = Depends(get_current_user),
):
    """
    Retorna alertas do usuário logado, filtrados pelo seu role.
    Ordenados por severidade (critical primeiro).
    """
    alerts = get_alerts_for_user(current_user, include_dismissed=include_dismissed)

    # Filtro opcional por severidade
    if severity:
        alerts = [a for a in alerts if a.severity == severity]

    unseen = sum(1 for a in alerts if not a.dismissed)

    return AlertsResponse(
        total=len(alerts),
        unseen=unseen,
        alerts=alerts,
    )


@router.post("/{alert_id}/dismiss")
def dismiss(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Marca um alerta específico como visto."""
    found = dismiss_alert(alert_id, current_user)
    if not found:
        raise HTTPException(status_code=404, detail="Alerta não encontrado.")
    return {"message": "Alerta marcado como visto.", "alert_id": alert_id}


@router.post("/dismiss-all")
def dismiss_all(current_user: dict = Depends(get_current_user)):
    """Marca todos os alertas visíveis ao usuário como vistos."""
    count = dismiss_all_for_user(current_user)
    return {"message": f"{count} alertas marcados como vistos."}


@router.post("/refresh")
async def refresh_alerts(
    current_user: dict = Depends(require_role("admin", "manager")),
):
    """
    Força uma rodada de detecção imediata.
    Restrito a admin e managers.
    """
    added = await scheduler.run_now()
    return {
        "message": "Detecção concluída.",
        "new_alerts": added,
    }
