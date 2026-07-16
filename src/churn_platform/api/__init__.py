"""SPEC-10.3: FastAPI application factory."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from churn_platform import __version__

logger = logging.getLogger(__name__)

_run_state: dict = {
    "runs": {},
    "accounts_df": None,
    "scored_df": None,
    "analysis_data": None,
    "explainer": None,
}


def get_state() -> dict:
    return _run_state


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    logger.info("Churn Platform API iniciando v%s", __version__)
    output_dir = Path(app.state.output_dir or "output")
    output_dir.mkdir(parents=True, exist_ok=True)
    app.state.output_dir = str(output_dir)
    yield
    logger.info("Churn Platform API finalizando")


def create_app(output_dir: str = "output") -> FastAPI:
    from churn_platform.llm import LLMExplainer

    app = FastAPI(
        title="Churn Platform API",
        version=__version__,
        description="SPEC-Driven Churn Diagnostic Engine — REST API",
        lifespan=lifespan,
    )

    app.state.output_dir = output_dir

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from churn_platform.api.health import router as health_router
    from churn_platform.api.routes_runs import router as runs_router
    from churn_platform.api.routes_accounts import router as accounts_router

    app.include_router(health_router)
    app.include_router(runs_router, prefix="/api/v1")
    app.include_router(accounts_router, prefix="/api/v1")

    output_path = Path(output_dir)
    if output_path.exists():
        app.mount("/output", StaticFiles(directory=str(output_path)), name="output")

    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def dashboard():
        index_path = static_dir / "index.html"
        if index_path.exists():
            return index_path.read_text(encoding="utf-8")
        return "<h1>Churn Platform</h1><p>Dashboard not found.</p>"

    state = get_state()
    state["explainer"] = LLMExplainer(cache_dir=str(output_path / "cache"))

    return app
