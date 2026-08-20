"""Aplicação HTTP — importa `scoring/`, carrega a base na inicialização."""

from __future__ import annotations

from contextlib import asynccontextmanager

from config import settings
from errors import register_error_handlers
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import deals, export, kpis, management, scoring
from state import build_app_state


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.app_state = build_app_state(settings)
    yield


app = FastAPI(
    title="Lead Scorer API",
    description=(
        "Pipeline priorizado por valor em risco. Sem autenticação — dataset público de "
        "demonstração, sem informação real de cliente (ver Requirement 'Postura de segurança')."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS: origens enumeradas, nunca "*" (Requirement "Postura de segurança").
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

register_error_handlers(app)

app.include_router(deals.router)
app.include_router(kpis.router)
app.include_router(management.router)
app.include_router(scoring.router)
app.include_router(export.router)


@app.get("/health", tags=["saúde"])
def health():
    return {"status": "ok"}
