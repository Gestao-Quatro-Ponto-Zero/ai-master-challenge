"""Tabela mapeada: DealFeedback."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class DealFeedback(Base):
    __tablename__ = "deal_feedback"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    opportunity_id: Mapped[str] = mapped_column(Text)
    user_key: Mapped[str] = mapped_column(Text)
    action: Mapped[str] = mapped_column(Text)
    comment: Mapped[Optional[str]] = mapped_column(Text)
    model_version: Mapped[Optional[str]] = mapped_column(Text)
    score_at_feedback: Mapped[Optional[int]] = mapped_column(Integer)
    band_at_feedback: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)
