"""Tabela mapeada: User."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class User(Base):
    __tablename__ = "users"
    user_key: Mapped[str] = mapped_column(Text, primary_key=True)
    full_name: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(Text)
    manager: Mapped[Optional[str]] = mapped_column(Text)
    regional_office: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[str] = mapped_column(Text)
