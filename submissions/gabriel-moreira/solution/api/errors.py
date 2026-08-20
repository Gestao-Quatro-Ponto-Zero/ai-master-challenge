"""Handlers de erro — nunca vazam rastreamento de pilha nem caminho de
arquivo (Requirement "Postura de segurança")."""

from __future__ import annotations

import logging

from auth.identity import UnknownIdentityError
from auth.scope import OutOfScopeError
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("lead_scorer.api")


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(OutOfScopeError)
    async def _out_of_scope(request: Request, exc: OutOfScopeError):
        return JSONResponse(
            status_code=403,
            content={"detail": f"{exc.field} fora do escopo do token"},
        )

    @app.exception_handler(UnknownIdentityError)
    async def _unknown_identity(request: Request, exc: UnknownIdentityError):
        return JSONResponse(
            status_code=422,
            content={"detail": "identidade desconhecida — verifique a lista em /identities"},
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        logger.exception("erro não tratado")
        return JSONResponse(
            status_code=500,
            content={"detail": "erro interno — tente novamente mais tarde"},
        )
