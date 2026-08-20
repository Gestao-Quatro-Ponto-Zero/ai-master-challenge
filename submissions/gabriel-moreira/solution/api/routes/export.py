"""Requirement "Download do dataset processado" — restrito a Manager."""

from __future__ import annotations

from auth.scope import Scope
from deps import get_app_state, get_scope
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from state import AppState

router = APIRouter(tags=["exportação"])


@router.get("/export/csv")
def download_processed_dataset(
    scope: Scope = Depends(get_scope),
    app_state: AppState = Depends(get_app_state),
):
    if scope.role != "manager":
        raise HTTPException(403, detail="download restrito a identidades Manager")

    return FileResponse(
        app_state.settings.export_path,
        media_type="text/csv",
        filename="pipeline_processado.csv",
    )
