"""
notes/models.py
---------------
Schemas Pydantic para o sistema de notas de deals.
"""

from pydantic import BaseModel
from typing import Optional


class NoteCreate(BaseModel):
    """Payload para criar uma nova nota."""
    content: str


class Note(BaseModel):
    """Uma nota registrada em um deal."""
    id: str
    opportunity_id: str
    content: str
    author_id: str
    author_name: str
    author_role: str
    created_at: str         # ISO timestamp


class NotesResponse(BaseModel):
    """Resposta da rota GET /api/deal/{id}/notes."""
    opportunity_id: str
    total: int
    last_note_at: Optional[str]   # ISO timestamp da nota mais recente
    days_since_last_note: Optional[int]
    notes: list[Note]
