"""JWT, usuário atual e escopo (RBAC). Fora do escopo => 404, nunca revela existência."""
from __future__ import annotations

import time
from dataclasses import dataclass

import jwt
from fastapi import Depends, Request


from .errors import forbidden_role, unauthenticated

ALGORITHM = "HS256"


@dataclass(frozen=True)
class Principal:
    user_key: str
    full_name: str
    role: str
    manager: str | None
    regional_office: str | None
    sellers: frozenset[str] | None   # None = vê tudo (revops)

    def sees_seller(self, seller: str) -> bool:
        return self.sellers is None or seller in self.sellers

    def scope_info(self) -> dict:
        if self.sellers is None:
            return {"type": "all", "sellers": None}
        return {"type": "seller" if self.role == "seller" else "team", "sellers": sorted(self.sellers)}


def create_token(secret: str, ttl_minutes: int, user_key: str, role: str, name: str) -> tuple[str, int]:
    ttl = ttl_minutes * 60
    payload = {"sub": user_key, "role": role, "name": name, "exp": int(time.time()) + ttl}
    return jwt.encode(payload, secret, algorithm=ALGORITHM), ttl


def get_container(request: Request):
    return request.app.state.container


def current_user(request: Request, container=Depends(get_container)) -> Principal:
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise unauthenticated()
    try:
        claims = jwt.decode(token, container.settings.jwt_secret, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise unauthenticated("Token inválido ou expirado.")
    row = container.auth.find_active(claims["sub"])
    if row is None:
        raise unauthenticated("Usuário inexistente ou inativo.")
    if row["role"] == "revops":
        sellers = None
    elif row["role"] == "manager":
        sellers = container.store.sellers_of_manager(row["full_name"])
    else:
        sellers = frozenset({row["full_name"]})
    return Principal(row["user_key"], row["full_name"], row["role"], row["manager"], row["regional_office"], sellers)


def require_revops(user: Principal = Depends(current_user)) -> Principal:
    if user.role != "revops":
        raise forbidden_role()
    return user
