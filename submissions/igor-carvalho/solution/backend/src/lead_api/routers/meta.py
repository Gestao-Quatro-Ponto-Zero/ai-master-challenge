from __future__ import annotations

from fastapi import APIRouter, Depends

from lead_core.constants import LOW_CONFIDENCE_AGENT_N, PRIORITY_LEVELS, VIEWS

from ..errors import model_not_ready
from ..security import Principal, current_user, get_container
from ..services.deals import DealQueryService, probability_allowed

router = APIRouter(tags=["meta"])


@router.get("/meta")
def meta(_: Principal = Depends(current_user), container=Depends(get_container)):
    m = container.store.require()
    card = m.bundle.card
    return {
        "api_version": "v1", "reference_date": card["reference_date"], "model_version": card["version"],
        "engine": card["engine"], "trained_at": card["trained_at"],
        "show_probability": probability_allowed(container.settings.show_probability, m),
        "calibration_useful": card["calibration"]["useful"], "thresholds": card["thresholds"],
        "horizon_days": card.get("horizon_days"),       # o score ordena a receita esperada neste horizonte (None = versão antiga)
        "priority_levels": [{"key": k, "label": label, "min_score": lo, "max_score": hi}
                            for k, label, lo, hi in PRIORITY_LEVELS],
        "views": [{"key": k, "bands": list(v["bands"]), "default_sort": v["sort"]} for k, v in VIEWS.items()],
        "low_confidence_below_closed_deals": LOW_CONFIDENCE_AGENT_N,
    }


@router.get("/filters")
def filters(user: Principal = Depends(current_user), container=Depends(get_container)):
    return DealQueryService.filters(container.store.require(), user)


@router.get("/model")
def model_card(_: Principal = Depends(current_user), container=Depends(get_container)):
    return container.store.require().bundle.card


@router.get("/health/live", tags=["health"])
def live():
    return {"status": "ok"}


@router.get("/health/ready", tags=["health"])
def ready(container=Depends(get_container)):
    if not container.store.ready:
        raise model_not_ready()
    return {"status": "ok", "model_version": container.store.require().bundle.version}
