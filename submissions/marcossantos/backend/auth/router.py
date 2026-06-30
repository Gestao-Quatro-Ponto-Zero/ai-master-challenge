"""
auth/router.py
--------------
Rotas de autenticação:
  POST /auth/login  → recebe credenciais, retorna JWT
  GET  /auth/me     → retorna dados do usuário logado
  POST /auth/logout → instrução pro cliente descartar o token
"""

from fastapi import APIRouter, HTTPException, status, Depends

from .models import LoginRequest, TokenResponse, UserInfo
from .service import authenticate_user, create_access_token, get_user_info, EXPIRES_IN
from .dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    """
    Autentica o usuário e retorna um JWT.

    O token deve ser enviado em todas as requisições protegidas:
        Authorization: Bearer <token>
    """
    user = authenticate_user(body.email, body.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos.",
        )

    token = create_access_token(user)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=EXPIRES_IN,
    )


@router.get("/me", response_model=UserInfo)
def me(current_user: dict = Depends(get_current_user)):
    """
    Retorna os dados do usuário autenticado.
    Útil para o frontend saber o role e personalizar a UI.
    """
    return get_user_info(current_user)


@router.post("/logout")
def logout():
    """
    JWT é stateless — logout é feito no cliente descartando o token.
    Esta rota existe para o frontend ter um endpoint semântico.
    """
    return {"message": "Logout realizado. Descarte o token no cliente."}
