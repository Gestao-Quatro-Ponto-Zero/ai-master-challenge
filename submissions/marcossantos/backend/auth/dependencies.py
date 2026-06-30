"""
auth/dependencies.py
--------------------
Dependências injetáveis do FastAPI para proteger rotas.

Uso nas rotas:
    @app.get("/api/pipeline")
    def get_pipeline(user = Depends(get_current_user)):
        ...

    @app.get("/api/admin/something")
    def admin_route(user = Depends(require_role("admin"))):
        ...
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .service import decode_token, get_user_by_id
from .models import TokenPayload

# Extrai o Bearer token do header Authorization
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """
    Dependência base — valida o JWT e retorna o usuário.
    Injete em qualquer rota que precise de autenticação.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido. Faça login em /auth/login.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado. Faça login novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_id(payload["sub"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado.",
        )

    return user


def require_role(*roles: str):
    """
    Factory de dependência — restringe rota a roles específicas.

    Uso:
        Depends(require_role("admin"))
        Depends(require_role("admin", "manager"))
    """
    def _check(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Requer perfil: {' ou '.join(roles)}.",
            )
        return user
    return _check


def get_pipeline_filters_for_user(user: dict) -> dict:
    """
    Retorna os filtros de pipeline baseados no role do usuário.

    - admin   → sem filtros (vê tudo)
    - manager → filtra pelo próprio manager (vê o time)
    - agent   → filtra pelo próprio sales_agent (vê só os seus)
    """
    role = user["role"]

    if role == "admin":
        return {}

    if role == "manager":
        return {"manager": user.get("manager")}

    if role == "agent":
        return {"agent": user.get("sales_agent")}

    return {}
