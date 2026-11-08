from __future__ import annotations

from fastapi import APIRouter, Depends

from lead_core.db import utc_now

from ..errors import ApiError
from ..schemas import JobOut
from ..security import Principal, get_container, require_revops

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/refresh")
def refresh(_: Principal = Depends(require_revops), container=Depends(get_container)):
    """Recarrega o modelo ativo (ponteiro CURRENT) sem reiniciar a API."""
    version = container.store.reload()
    if version is None:
        raise ApiError(503, "MODEL_NOT_READY", "Nenhum modelo promovido (arquivo CURRENT ausente).")
    container.auth.sync_users(container.store.require().bundle.tables)
    return {"model_version": version, "loaded_at": utc_now()}


@router.post("/retrain", status_code=202)
def retrain(user: Principal = Depends(require_revops), container=Depends(get_container)):
    """Dispara o treinamento (processo separado, assíncrono). Só um retreino por vez."""
    job_id = container.jobs.create_retrain(user.user_key)
    container.runner.start(job_id)
    return {"job_id": job_id, "status": "queued"}


@router.get("/jobs/{job_id}", response_model=JobOut)
def job_status(job_id: str, _: Principal = Depends(require_revops), container=Depends(get_container)):
    return container.jobs.get(job_id)
