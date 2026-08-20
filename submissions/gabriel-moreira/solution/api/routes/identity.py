"""Requirement "Identificação por papel de acesso"."""

from __future__ import annotations

from auth.identity import list_available_identities, resolve_identity
from auth.tokens import issue_token
from deps import get_app_state
from fastapi import APIRouter, Depends
from schemas import IdentitiesOut, IdentifyIn, TokenOut
from state import AppState

router = APIRouter(tags=["identidade"])


@router.get("/identities", response_model=IdentitiesOut)
def get_identities(app_state: AppState = Depends(get_app_state)):
    return list_available_identities(app_state.dataset)


@router.post("/identify", response_model=TokenOut)
def identify(body: IdentifyIn, app_state: AppState = Depends(get_app_state)):
    identity = resolve_identity(app_state.dataset, body.name)
    token = issue_token(app_state.settings.session_secret, identity.role, identity.name)
    return TokenOut(token=token, role=identity.role, identity=identity.name)
