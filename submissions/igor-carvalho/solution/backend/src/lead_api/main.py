"""create_app(): monta a API. Lifespan: cria o SQLite (esquema v1), carrega o modelo ativo, semeia usuários."""
from __future__ import annotations

import json
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from lead_core.persistence import Database, FeedbackRepository, JobRepository, UserRepository

from .container import Container
from .errors import install_error_handlers
from .limiter import RateLimiter
from .routers import admin, auth, deals, meta, scoring
from .services.deals import DealQueryService
from .services.auth import AuthService
from .services.feedback import FeedbackService
from .services.jobs import JobRunner, JobService, SubprocessJobRunner
from .services.summary import SummaryService
from .services.whatif import WhatIfService
from .settings import Settings
from .store import ScoreStore

log = logging.getLogger("lead_api")
API_PREFIX = "/api/v1"


def build_container(settings: Settings, runner: JobRunner | None = None) -> Container:
    store = ScoreStore(settings.artifact_dir)
    db = Database(settings.db_path)                       # cria o esquema v1 se faltar
    auth = AuthService(UserRepository(db))
    job_repo = JobRepository(db)
    return Container(
        settings=settings, store=store, deals=DealQueryService(settings.show_probability),
        whatif=WhatIfService(settings.show_probability), summary=SummaryService(),
        feedback=FeedbackService(FeedbackRepository(db)), jobs=JobService(job_repo), auth=auth,
        runner=runner or SubprocessJobRunner(settings, store, job_repo, auth),
        limiter=RateLimiter(settings.rate_limit_per_minute),
    )


def create_app(settings: Settings | None = None, runner: JobRunner | None = None) -> FastAPI:
    settings = settings or Settings()
    container = build_container(settings, runner)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        container.store.reload()
        container.auth.sync_users(container.store.tables)
        yield

    app = FastAPI(title="G4 Lead Scorer API", version="0.1.0", lifespan=lifespan)
    app.state.container = container
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"],
                       allow_headers=["*"])
    install_error_handlers(app)

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request.state.request_id = uuid.uuid4().hex
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        log.info(json.dumps({"request_id": request.state.request_id, "method": request.method,
                             "path": request.url.path, "status": response.status_code,
                             "ms": round((time.perf_counter() - start) * 1000, 1)}))
        return response

    for router in (auth.router, meta.router, deals.router, scoring.router, admin.router):
        app.include_router(router, prefix=API_PREFIX)
    return app
