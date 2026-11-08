"""Tabela mapeada: ModelVersion."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ModelVersion(Base):
    __tablename__ = "model_versions"
    version: Mapped[str] = mapped_column(Text, primary_key=True)
    engine: Mapped[str] = mapped_column(Text)
    trained_at: Mapped[str] = mapped_column(Text)
    reference_date: Mapped[str] = mapped_column(Text)
    artifact_path: Mapped[str] = mapped_column(Text)
    metrics_json: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    promoted_at: Mapped[Optional[str]] = mapped_column(Text)
    reject_reason: Mapped[Optional[str]] = mapped_column(Text)
