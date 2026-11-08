from __future__ import annotations

from fastapi import APIRouter, Depends

from ..schemas import LoginIn, LoginOut, MeOut
from ..security import Principal, create_token, current_user, get_container

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=LoginOut)
def login(body: LoginIn, container=Depends(get_container)):
    """MVP: troca user_key por JWT. Produção: OIDC/SSO."""
    row = container.auth.login(body.user_key)
    s = container.settings
    token, ttl = create_token(s.jwt_secret, s.jwt_ttl_minutes, row["user_key"], row["role"], row["full_name"])
    user = {k: row[k] for k in ("user_key", "full_name", "role", "manager", "regional_office")}
    return {"access_token": token, "token_type": "bearer", "expires_in": ttl, "user": user}


@router.get("/me", response_model=MeOut)
def me(user: Principal = Depends(current_user)):
    return {"user_key": user.user_key, "full_name": user.full_name, "role": user.role, "manager": user.manager,
            "regional_office": user.regional_office, "scope": user.scope_info()}
