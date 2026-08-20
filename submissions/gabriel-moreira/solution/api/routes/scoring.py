"""Requirement "Pontuação de oportunidade avulsa" — acessível sem identificação prévia."""

from __future__ import annotations

from deps import get_app_state
from fastapi import APIRouter, Depends, HTTPException
from schemas import ScoreAvulsaIn, ScoreAvulsaOut
from scoring import constants
from scoring.pipeline import score_row
from state import AppState

router = APIRouter(tags=["pontuação avulsa"])


@router.post("/score", response_model=ScoreAvulsaOut)
def score_avulsa(
    body: ScoreAvulsaIn,
    app_state: AppState = Depends(get_app_state),
):
    if body.product not in constants.PRECO_TABELA:
        raise HTTPException(
            422,
            detail=f"produto fora do catálogo; produtos válidos: {sorted(constants.PRECO_TABELA)}",
        )
    if body.porte is not None and body.porte not in constants.MULT_PORTE:
        raise HTTPException(
            422, detail=f"porte inválido; valores válidos: {sorted(constants.MULT_PORTE)}"
        )

    stage = "Engaging" if body.age_days is not None else "Prospecting"
    has_account = body.porte is not None

    result = score_row(
        app_state.ctx,
        app_state.ref,
        app_state.ages_won_ordenadas,
        product=body.product,
        stage=stage,
        age_days=body.age_days,
        has_account=has_account,
        porte=body.porte,
    )

    return ScoreAvulsaOut(
        product=body.product,
        porte=body.porte,
        age_days=body.age_days,
        **result,
    )
