"""Login por código pessoal e tokens assinados (HMAC) com o papel do usuário."""

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

from fastapi import Header, HTTPException

from api import db

TOKEN_TTL = 12 * 3600


def hash_code(code: str, iterations: int = 200_000) -> str:
    salt = secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", code.encode(), salt.encode(), iterations).hex()
    return f"pbkdf2_sha256${iterations}${salt}${digest}"


def verify_code(code: str, stored: str) -> bool:
    _, iterations, salt, digest = stored.split("$")
    test = hashlib.pbkdf2_hmac("sha256", code.encode(), salt.encode(), int(iterations)).hex()
    return hmac.compare_digest(test, digest)


def _secret() -> bytes:
    if db.settings.auth_secret is None:
        raise HTTPException(status_code=503, detail="AUTH_SECRET não configurado")
    return db.settings.auth_secret.get_secret_value().encode()


def issue_token(user: dict[str, Any]) -> str:
    payload = {"email": user["email"], "role": user["role"], "exp": int(time.time()) + TOKEN_TTL}
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    sig = hmac.new(_secret(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def login(email: str, code: str) -> dict[str, Any]:
    found = db.rows(
        """select u.email, u.name, u.role, u.code_hash, r.label, r.profile_slug, r.tabs, r.can_edit
             from app.users u join app.roles r using (role) where u.email = %s and u.active""",
        (email.strip().lower(),),
    )
    if not found or not verify_code(code, found[0]["code_hash"]):
        raise HTTPException(status_code=401, detail="e-mail ou código inválido")
    user = found[0]
    db.execute("update app.users set last_login = now() where email = %s", (user["email"],))
    user.pop("code_hash")
    return {"token": issue_token(user), "user": user}


def current_user(authorization: str | None = Header(None)) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="faça login")
    try:
        body, sig = authorization[7:].split(".")
        expected = hmac.new(_secret(), body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            raise ValueError
        payload = json.loads(base64.urlsafe_b64decode(body))
        if payload["exp"] < time.time():
            raise ValueError
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=401, detail="sessão inválida ou expirada") from exc
    found = db.rows(
        """select u.email, u.name, u.role, r.label, r.profile_slug, r.tabs, r.can_edit
             from app.users u join app.roles r using (role) where u.email = %s and u.active""",
        (payload["email"],),
    )
    if not found:
        raise HTTPException(status_code=401, detail="usuário inativo")
    return found[0]
