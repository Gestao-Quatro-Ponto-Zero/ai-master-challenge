"""Tabela mapeada: Job."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Job(Base):
    __tablename__ = "jobs"
    job_id: Mapped[str] = mapped_column(Text, primary_key=True)
    kind: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    requested_by: Mapped[Optional[str]] = mapped_column(Text)
    params_json: Mapped[Optional[str]] = mapped_column(Text)
    result_json: Mapped[Optional[str]] = mapped_column(Text)
    error: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)
    started_at: Mapped[Optional[str]] = mapped_column(Text)
    finished_at: Mapped[Optional[str]] = mapped_column(Text)
