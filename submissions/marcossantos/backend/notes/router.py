"""
notes/router.py
---------------
Rotas para o sistema de notas de deals:

  GET    /api/deal/{id}/notes          → lista notas do deal
  POST   /api/deal/{id}/notes          → adiciona nota
  DELETE /api/deal/{id}/notes/{note_id} → remove nota (autor ou admin)
"""

from fastapi import APIRouter, HTTPException, Depends

from .models import NoteCreate, Note, NotesResponse
from .store import add_note, get_notes, delete_note
from auth.dependencies import get_current_user

router = APIRouter(tags=["Notas"])


@router.get("/api/deal/{opportunity_id}/notes", response_model=NotesResponse)
def list_notes(
    opportunity_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Retorna todas as notas de um deal, da mais recente para a mais antiga.
    Inclui dias desde a última nota (usado pelo frontend para exibir alerta).
    """
    return get_notes(opportunity_id)


@router.post("/api/deal/{opportunity_id}/notes", response_model=Note)
def create_note(
    opportunity_id: str,
    body: NoteCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Adiciona uma nova nota ao deal.
    Qualquer usuário autenticado pode adicionar notas.
    """
    if not body.content or not body.content.strip():
        raise HTTPException(status_code=400, detail="Conteúdo da nota não pode ser vazio.")

    if len(body.content) > 1000:
        raise HTTPException(status_code=400, detail="Nota muito longa. Máximo: 1000 caracteres.")

    return add_note(opportunity_id, body.content, current_user)


@router.delete("/api/deal/{opportunity_id}/notes/{note_id}")
def remove_note(
    opportunity_id: str,
    note_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Remove uma nota. Apenas o autor ou um admin pode deletar.
    """
    removed = delete_note(opportunity_id, note_id, current_user)

    if not removed:
        raise HTTPException(
            status_code=404,
            detail="Nota não encontrada ou sem permissão para deletar.",
        )

    return {"message": "Nota removida.", "note_id": note_id}
