"""Emissão e validação de token de sessão assinado no servidor.

Sem senha — identificação, não autenticação (ver
docs/decisions-log.md, entrada 2026-08-19). O que é real: o segredo de
assinatura nunca é exposto ao cliente, e o papel/escopo do token é sempre
derivado dos dados no momento da identificação, nunca aceito do cliente.
"""

from __future__ import annotations

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

TOKEN_SALT = "lead-scorer-session-v1"
DEFAULT_MAX_AGE_SECONDS = 4 * 60 * 60  # 4 horas


class InvalidTokenError(Exception):
    pass


class ExpiredTokenError(Exception):
    pass


def _serializer(secret: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(secret, salt=TOKEN_SALT)


def issue_token(secret: str, role: str, identity: str) -> str:
    payload = {"role": role, "identity": identity}
    return _serializer(secret).dumps(payload)


def verify_token(
    secret: str, token: str, max_age: int = DEFAULT_MAX_AGE_SECONDS
) -> dict:
    try:
        return _serializer(secret).loads(token, max_age=max_age)
    except SignatureExpired as exc:
        raise ExpiredTokenError() from exc
    except BadSignature as exc:
        raise InvalidTokenError() from exc
