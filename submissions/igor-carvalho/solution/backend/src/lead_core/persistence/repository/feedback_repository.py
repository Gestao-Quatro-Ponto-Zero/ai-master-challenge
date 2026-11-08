"""Repositório da entidade DealFeedback."""
from __future__ import annotations

from sqlalchemy import select

from ...db import utc_now
from ..database import Database
from ..models import DealFeedback
from ._common import as_dict


class FeedbackRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, *, opportunity_id: str, user_key: str, action: str, comment: str | None, model_version: str | None,
            score: int | None, band: str | None) -> dict:
        created = utc_now()
        with self.db.session() as s:
            row = DealFeedback(opportunity_id=opportunity_id, user_key=user_key, action=action, comment=comment,
                               model_version=model_version, score_at_feedback=score, band_at_feedback=band,
                               created_at=created)
            s.add(row)
            s.flush()
            return {"id": int(row.id), "created_at": created}

    def history(self, opportunity_id: str) -> list[dict]:
        with self.db.session() as s:
            rows = s.execute(select(DealFeedback).where(DealFeedback.opportunity_id == opportunity_id)
                             .order_by(DealFeedback.created_at.desc(), DealFeedback.id.desc())).scalars()
            return [as_dict(r, exclude=("score_at_feedback", "band_at_feedback")) for r in rows]

    def all(self) -> list[dict]:
        with self.db.session() as s:
            return [as_dict(r) for r in s.execute(select(DealFeedback).order_by(DealFeedback.id)).scalars()]
