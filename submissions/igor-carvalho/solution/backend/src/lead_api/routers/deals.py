from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query

from ..schemas import DealDetail, DealPage, FeedbackCreated, FeedbackIn, FeedbackList
from ..security import Principal, current_user, get_container
from ..services.deals import DealFilters

router = APIRouter(tags=["deals"])


@router.get("/deals", response_model=DealPage)
def list_deals(
    seller: Optional[str] = None, manager: Optional[str] = None, office: Optional[str] = None,
    stage: Optional[Literal["Engaging", "Prospecting"]] = None,
    band: Optional[Literal["focus", "follow_up", "low", "stale_risk", "review", "prospecting"]] = None,
    product: Optional[str] = None, min_score: Optional[int] = Query(None, ge=0, le=100),
    max_score: Optional[int] = Query(None, ge=0, le=100),
    priority: Optional[Literal["high", "medium", "low"]] = None,
    view: Optional[Literal["focus", "decide", "follow", "prospecting", "review", "all", "ev"]] = None,
    q: Optional[str] = None,
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    sort: Optional[Literal["score", "expected_value", "age_days"]] = None, order: Literal["asc", "desc"] = "desc",
    user: Principal = Depends(current_user), container=Depends(get_container),
):
    filters = DealFilters(seller=seller, manager=manager, office=office, stage=stage, band=band, product=product,
                          min_score=min_score, max_score=max_score, priority=priority, view=view, q=q,
                          page=page, page_size=page_size, sort=sort, order=order)
    return container.deals.list(container.store.require(), user, filters)


@router.get("/deals/{opportunity_id}", response_model=DealDetail)
def deal_detail(opportunity_id: str, user: Principal = Depends(current_user), container=Depends(get_container)):
    return container.deals.get(container.store.require(), user, opportunity_id)


@router.post("/deals/{opportunity_id}/feedback", response_model=FeedbackCreated, status_code=201)
def add_feedback(opportunity_id: str, body: FeedbackIn, user: Principal = Depends(current_user),
                 container=Depends(get_container)):
    container.limiter.check(f"write:{user.user_key}")
    return container.feedback.add(container.store.require(), user, opportunity_id, body.action, body.comment)


@router.get("/deals/{opportunity_id}/feedback", response_model=FeedbackList)
def feedback_history(opportunity_id: str, user: Principal = Depends(current_user), container=Depends(get_container)):
    return {"items": container.feedback.history(container.store.require(), user, opportunity_id)}
