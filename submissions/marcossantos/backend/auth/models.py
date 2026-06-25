"""
auth/models.py
--------------
Schemas Pydantic para autenticação.
Separado do models/schemas.py principal para manter coesão.
"""

from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos


class UserInfo(BaseModel):
    """Dados do usuário logado — retornados em /auth/me"""
    id: str
    name: str
    email: str
    role: str                        # "admin" | "manager" | "agent"
    sales_agent: Optional[str]       # preenchido se role == agent
    manager: Optional[str]           # preenchido se role == manager/agent
    regional_office: Optional[str]


class TokenPayload(BaseModel):
    """Payload decodificado do JWT"""
    sub: str           # user id
    role: str
    sales_agent: Optional[str]
    manager: Optional[str]
    regional_office: Optional[str]
    exp: int           # timestamp de expiração
