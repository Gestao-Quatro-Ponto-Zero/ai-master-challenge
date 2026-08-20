"""Dependências FastAPI: estado da aplicação, escopo autenticado, data de
referência opcional — reutilizadas por toda rota de dados.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
from auth.identity import Identity
from auth.scope import Scope, build_scope
from auth.tokens import ExpiredTokenError, InvalidTokenError, verify_token
from fastapi import Header, HTTPException, Request

from state import AppState


class AuthError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=401, detail=detail)


def get_app_state(request: Request) -> AppState:
    return request.app.state.app_state


def get_scope(
    request: Request,
    authorization: Optional[str] = Header(default=None),
) -> Scope:
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthError("token de sessão ausente")

    token = authorization.removeprefix("Bearer ").strip()
    app_state: AppState = request.app.state.app_state

    try:
        payload = verify_token(
            app_state.settings.session_secret,
            token,
            max_age=app_state.settings.token_max_age_seconds,
        )
    except ExpiredTokenError:
        raise AuthError("token de sessão expirado — identifique-se novamente") from None
    except InvalidTokenError:
        raise AuthError("token de sessão inválido") from None

    identity = Identity(role=payload["role"], name=payload["identity"])
    return build_scope(app_state.dataset, identity)


def get_as_of(as_of: Optional[str] = None) -> Optional[pd.Timestamp]:
    if as_of is None:
        return None
    try:
        return pd.Timestamp(as_of)
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="data de referência inválida") from None
