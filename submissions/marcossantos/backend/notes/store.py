"""
notes/store.py
--------------
Persistência das notas em notes.json.

Estrutura do arquivo:
{
  "opportunity_id_1": [
    { "id": "abc", "content": "...", "author_id": "1", ... },
    ...
  ],
  "opportunity_id_2": [...]
}

Em produção: trocar por SQLite/PostgreSQL.
"""

import json
import uuid
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from .models import Note, NotesResponse

logger = logging.getLogger(__name__)

NOTES_FILE = Path(__file__).parent.parent / "notes.json"


# ---------------------------------------------------------------------------
# I/O básico
# ---------------------------------------------------------------------------

def _load_raw() -> dict:
    if not NOTES_FILE.exists():
        return {}
    try:
        return json.loads(NOTES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_raw(data: dict) -> None:
    NOTES_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def add_note(opportunity_id: str, content: str, user: dict) -> Note:
    """
    Adiciona uma nota a um deal.
    Retorna a nota criada.
    """
    data = _load_raw()

    note = Note(
        id=str(uuid.uuid4())[:8],
        opportunity_id=opportunity_id,
        content=content.strip(),
        author_id=user["id"],
        author_name=user["name"],
        author_role=user["role"],
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    if opportunity_id not in data:
        data[opportunity_id] = []

    # Insere no início (mais recente primeiro no arquivo)
    data[opportunity_id].insert(0, note.model_dump())
    _save_raw(data)

    logger.info(f"Nota adicionada ao deal {opportunity_id} por {user['name']}.")
    return note


def get_notes(opportunity_id: str) -> NotesResponse:
    """
    Retorna todas as notas de um deal, ordenadas da mais recente para a mais antiga.
    Inclui metadados úteis para o scoring (days_since_last_note).
    """
    data = _load_raw()
    raw_notes = data.get(opportunity_id, [])

    notes = [Note(**n) for n in raw_notes]

    # Ordena mais recente primeiro (já deve estar assim, mas garante)
    notes.sort(key=lambda n: n.created_at, reverse=True)

    last_note_at = None
    days_since_last_note = None

    if notes:
        last_note_at = notes[0].created_at
        last_dt = datetime.fromisoformat(last_note_at)
        now = datetime.now(timezone.utc)
        # Garante timezone-aware
        if last_dt.tzinfo is None:
            last_dt = last_dt.replace(tzinfo=timezone.utc)
        days_since_last_note = (now - last_dt).days

    return NotesResponse(
        opportunity_id=opportunity_id,
        total=len(notes),
        last_note_at=last_note_at,
        days_since_last_note=days_since_last_note,
        notes=notes,
    )


def get_days_since_last_note(opportunity_id: str) -> Optional[int]:
    """
    Retorna quantos dias se passaram desde a última nota.
    None se não houver notas.
    Usado diretamente pelo scoring engine (factor_notes_activity).
    """
    data = _load_raw()
    raw_notes = data.get(str(opportunity_id), [])

    if not raw_notes:
        return None

    # Pega a nota mais recente
    most_recent = max(raw_notes, key=lambda n: n["created_at"])
    last_dt = datetime.fromisoformat(most_recent["created_at"])
    now = datetime.now(timezone.utc)

    if last_dt.tzinfo is None:
        last_dt = last_dt.replace(tzinfo=timezone.utc)

    return (now - last_dt).days


def delete_note(opportunity_id: str, note_id: str, user: dict) -> bool:
    """
    Remove uma nota. Só o autor ou um admin pode deletar.
    Retorna True se removida.
    """
    data = _load_raw()
    notes = data.get(opportunity_id, [])

    for i, note in enumerate(notes):
        if note["id"] == note_id:
            # Verifica permissão
            if note["author_id"] != user["id"] and user["role"] != "admin":
                return False
            notes.pop(i)
            data[opportunity_id] = notes
            _save_raw(data)
            logger.info(f"Nota {note_id} removida por {user['name']}.")
            return True

    return False
