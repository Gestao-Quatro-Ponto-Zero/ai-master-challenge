"""
Módulo de autenticação com JWT para o G4 IA - Inteligência de Suporte.
Gerencia login, tokens e validação de sessão.
"""

import hashlib
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import USERS, JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_HOURS

security = HTTPBearer(auto_error=False)


def _hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


class ContaDesativadaError(Exception):
    pass


def authenticate_user(email: str, password: str) -> dict | None:
    user = USERS.get(email.lower())
    if not user:
        return None
    if user["senha_hash"] != _hash_pw(password):
        return None
    if not user.get("ativo", True):
        raise ContaDesativadaError()
    return {
        "email": email.lower(),
        "nome": user["nome"],
        "perfil": user["perfil"],
    }


def create_token(user_data: dict) -> str:
    payload = {
        "sub": user_data["email"],
        "nome": user_data["nome"],
        "perfil": user_data["perfil"],
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="Token de autenticação não fornecido")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {
            "email": payload["sub"],
            "nome": payload["nome"],
            "perfil": payload["perfil"],
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")


def optional_verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict | None:
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {
            "email": payload["sub"],
            "nome": payload["nome"],
            "perfil": payload["perfil"],
        }
    except JWTError:
        return None
