from __future__ import annotations

from fastapi import APIRouter, Depends

from ..schemas import WhatIfIn, WhatIfOut
from ..security import Principal, current_user, get_container

router = APIRouter(tags=["scoring"])


@router.post("/score/what-if", response_model=WhatIfOut)
def what_if(body: WhatIfIn, user: Principal = Depends(current_user), container=Depends(get_container)):
    """Score de um deal hipotético com o modelo já treinado (sem treinar)."""
    container.limiter.check(f"whatif:{user.user_key}")
    return container.whatif.score(container.store.require(), body.product, body.seller, body.age_days)


@router.get("/summary")
def summary(group_by: str = "seller", user: Principal = Depends(current_user), container=Depends(get_container)):
    return container.summary.summarize(container.store.require(), user, group_by)
