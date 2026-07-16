"""SPEC-11.6: Health check endpoint."""

from __future__ import annotations

import time
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from churn_platform import __version__
from churn_platform.api import get_state

router = APIRouter()

_start_time = time.time()


@router.get("/")
async def root():
    return RedirectResponse(url="/docs")


@router.get("/health")
async def health():
    state = get_state()
    last_run = "never"
    if state["runs"]:
        run_ids = sorted(state["runs"].keys())
        last_run = state["runs"][run_ids[-1]].get("completed_at", "running")

    return {
        "status": "ok",
        "version": __version__,
        "spec_version": "1.0",
        "last_run": last_run,
        "uptime_seconds": int(time.time() - _start_time),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
