"""
auth/service.py
---------------
Toda a lógica de autenticação:
- Carregar usuários do users.json
- Validar credenciais com bcrypt
- Criar e decodificar JWT

Não há dependência de FastAPI aqui — só lógica pura.
"""

import json
import time
import hmac
import hashlib
import base64
import bcrypt
from pathlib import Path
from typing import Optional

from .models import UserInfo

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SECRET_KEY = "lead-scorer-secret-key-troque-em-producao-123"
EXPIRES_IN = 60 * 60 * 8  # 8 horas

USERS_FILE = Path(__file__).parent.parent / "users.json"


# ---------------------------------------------------------------------------
# JWT manual (hmac + sha256 — sem dependência de python-jose)
# ---------------------------------------------------------------------------

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def _b64url_decode(s: str) -> bytes:
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * pad)

def _sign(header_b64: str, payload_b64: str) -> str:
    msg = f"{header_b64}.{payload_b64}".encode()
    sig = hmac.new(SECRET_KEY.encode(), msg, hashlib.sha256).digest()
    return _b64url_encode(sig)

def create_token(payload: dict) -> str:
    import json as _json
    header  = _b64url_encode(_json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body    = _b64url_encode(_json.dumps(payload).encode())
    sig     = _sign(header, body)
    return f"{header}.{body}.{sig}"

def decode_token(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, sig = parts

        if not hmac.compare_digest(sig, _sign(header_b64, payload_b64)):
            return None

        import json as _json
        payload = _json.loads(_b64url_decode(payload_b64))

        if payload.get("exp", 0) < int(time.time()):
            return None

        return payload
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Bcrypt — hash e verificação de senha
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    """
    Gera o hash bcrypt de uma senha em texto plano.
    Work factor 12 — bom equilíbrio entre segurança e velocidade.
    """
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verifica se a senha em texto plano bate com o hash armazenado.
    bcrypt.checkpw é timing-safe por design.
    """
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def is_hashed(password: str) -> bool:
    """Detecta se o campo password já é um hash bcrypt ($2b$...)."""
    return password.startswith("$2b$") or password.startswith("$2a$")


# ---------------------------------------------------------------------------
# Usuários
# ---------------------------------------------------------------------------

def _load_users() -> list[dict]:
    if not USERS_FILE.exists():
        return []
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("users", [])


def _save_users(users: list[dict]) -> None:
    USERS_FILE.write_text(
        json.dumps({"users": users}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def migrate_plain_passwords() -> int:
    """
    Migração automática no startup:
    converte senhas em texto plano para hashes bcrypt no users.json.
    Roda uma vez — senhas já hasheadas são ignoradas.
    Retorna quantas senhas foram migradas.
    """
    users = _load_users()
    migrated = 0

    for user in users:
        pwd = user.get("password", "")
        if pwd and not is_hashed(pwd):
            user["password"] = hash_password(pwd)
            migrated += 1

    if migrated > 0:
        _save_users(users)

    return migrated


def authenticate_user(email: str, password: str) -> Optional[dict]:
    """
    Valida email + senha com bcrypt.
    Suporta hashes bcrypt ($2b$) e, como fallback seguro,
    texto plano ainda não migrado (raro após startup).
    """
    users = _load_users()
    for user in users:
        if user["email"].lower() != email.lower():
            continue

        stored = user.get("password", "")

        if is_hashed(stored):
            if verify_password(password, stored):
                return user
        else:
            # Fallback: compara texto plano e faz hash na hora
            if stored == password:
                user["password"] = hash_password(password)
                all_users = _load_users()
                for u in all_users:
                    if u["id"] == user["id"]:
                        u["password"] = user["password"]
                _save_users(all_users)
                return user

    return None


def get_user_by_id(user_id: str) -> Optional[dict]:
    users = _load_users()
    return next((u for u in users if u["id"] == user_id), None)


# ---------------------------------------------------------------------------
# Token de acesso
# ---------------------------------------------------------------------------

def create_access_token(user: dict) -> str:
    payload = {
        "sub":             user["id"],
        "role":            user["role"],
        "name":            user["name"],
        "email":           user["email"],
        "sales_agent":     user.get("sales_agent"),
        "manager":         user.get("manager"),
        "regional_office": user.get("regional_office"),
        "exp":             int(time.time()) + EXPIRES_IN,
    }
    return create_token(payload)


def get_user_info(user: dict) -> UserInfo:
    return UserInfo(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        role=user["role"],
        sales_agent=user.get("sales_agent"),
        manager=user.get("manager"),
        regional_office=user.get("regional_office"),
    )