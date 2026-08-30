"""Handlers de erro — nunca vazam rastreamento de pilha nem caminho de
arquivo (Requirement "Postura de segurança")."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("lead_scorer.api")


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        logger.exception("erro não tratado")
        return JSONResponse(
            status_code=500,
            content={"detail": "erro interno — tente novamente mais tarde"},
        )
