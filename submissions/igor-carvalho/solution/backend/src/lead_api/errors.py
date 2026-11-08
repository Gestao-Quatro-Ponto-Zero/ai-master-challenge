"""Erro padrão do contrato: {"error": {"code", "message", "request_id", "details"}}."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str, details=None):
        super().__init__(message)
        self.status_code, self.code, self.message, self.details = status_code, code, message, details


def unauthenticated(msg: str = "Credenciais ausentes ou inválidas.") -> ApiError:
    return ApiError(401, "UNAUTHENTICATED", msg)


def forbidden_role() -> ApiError:
    return ApiError(403, "FORBIDDEN_ROLE", "Esta rota é restrita ao papel revops.")


def deal_not_found() -> ApiError:
    return ApiError(404, "DEAL_NOT_FOUND", "Deal não encontrado.")


def model_not_ready() -> ApiError:
    return ApiError(503, "MODEL_NOT_READY", "Nenhum modelo treinado está carregado.")


def _respond(request: Request, status: int, code: str, message: str, details=None) -> JSONResponse:
    rid = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "request_id": rid, "details": details}},
        headers={"X-Request-ID": rid} if rid else None,
    )


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api(request: Request, exc: ApiError):
        return _respond(request, exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        return _respond(request, 422, "VALIDATION_ERROR", "Dados de entrada inválidos.",
                        jsonable_encoder(exc.errors(), custom_encoder={Exception: str}))

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(exc.status_code, "HTTP_ERROR")
        return _respond(request, exc.status_code, code, str(exc.detail))

    @app.exception_handler(Exception)
    async def _unexpected(request: Request, exc: Exception):
        return _respond(request, 500, "INTERNAL_ERROR", "Erro interno.")
