"""Feedback do vendedor (somente acrescenta). Regras de escopo aqui; persistência no repositório."""
from __future__ import annotations

from lead_core.persistence import FeedbackRepository

from ..errors import deal_not_found
from ..security import Principal
from ..store import LoadedModel
from .deals import scoped


class FeedbackService:
    def __init__(self, feedback: FeedbackRepository):
        self.feedback = feedback

    def add(self, model: LoadedModel, user: Principal, opportunity_id: str, action: str, comment: str | None) -> dict:
        df = scoped(model, user)
        if opportunity_id not in df.index:
            raise deal_not_found()
        deal = df.loc[opportunity_id]
        score = None if deal["score"] is None or deal["score"] != deal["score"] else int(deal["score"])
        return self.feedback.add(opportunity_id=opportunity_id, user_key=user.user_key, action=action,
                                 comment=comment, model_version=model.bundle.version, score=score,
                                 band=deal["band"])

    def history(self, model: LoadedModel, user: Principal, opportunity_id: str) -> list[dict]:
        if opportunity_id not in scoped(model, user).index:
            raise deal_not_found()
        return self.feedback.history(opportunity_id)
