"""Autenticação do MVP e sincronização de usuários (usa o repositório; sem SQL aqui)."""
from __future__ import annotations

from lead_core.persistence import UserRepository

from ..errors import unauthenticated


class AuthService:
    def __init__(self, users: UserRepository):
        self.users = users

    def login(self, user_key: str) -> dict:
        user = self.users.get_active(user_key)
        if user is None:
            raise unauthenticated("Usuário desconhecido.")
        return user

    def find_active(self, user_key: str) -> dict | None:
        return self.users.get_active(user_key)

    def sync_users(self, tables: dict | None) -> int:
        """Cria os usuários que faltam a partir das tabelas do modelo ativo."""
        return self.users.seed_from_tables(tables)
