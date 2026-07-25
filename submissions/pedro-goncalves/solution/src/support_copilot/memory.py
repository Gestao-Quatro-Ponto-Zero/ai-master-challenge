from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from src.support_copilot.privacy import mask_pii


MEMORY_SCHEMA_VERSION = "1.1.0"
VALID_LESSON_STATUSES = {"candidate", "approved", "retired"}
SECRET_PATTERN = re.compile(
    r"(?i)(password|passwd|api[_ -]?key|secret|token|bearer|sk-[a-z0-9_-]+)"
)


def _connect(path: str | Path) -> sqlite3.Connection:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(destination)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize(value: str) -> str:
    without_accents = "".join(
        character
        for character in unicodedata.normalize("NFKD", value.lower())
        if not unicodedata.combining(character)
    )
    return re.sub(r"\s+", " ", without_accents).strip()


def _normalize_terms(trigger_terms: list[str]) -> list[str]:
    normalized_terms = set()
    for term in trigger_terms:
        clean_term = term.strip()
        if not clean_term:
            continue
        _validate_safe_text(clean_term, field="termo", max_length=40)
        normalized = _normalize(clean_term)
        if len(normalized) < 3:
            raise ValueError("Cada termo precisa ter pelo menos 3 caracteres.")
        if not re.fullmatch(r"[a-z0-9 -]+", normalized):
            raise ValueError("Termos podem conter apenas letras, números, espaço e hífen.")
        normalized_terms.add(normalized)
    if len(normalized_terms) > 5:
        raise ValueError("Use no máximo 5 termos gerais por aprendizado.")
    return sorted(normalized_terms)


def _validate_safe_text(value: str, *, field: str, max_length: int) -> str:
    clean_value = value.strip()
    if not clean_value:
        raise ValueError(f"{field.capitalize()} não pode ficar vazio.")
    if len(clean_value) > max_length:
        raise ValueError(
            f"{field.capitalize()} excede o limite de {max_length} caracteres."
        )
    if SECRET_PATTERN.search(clean_value):
        raise ValueError(f"{field.capitalize()} contém possível credencial ou segredo.")
    _, counts = mask_pii(clean_value)
    if any(counts.values()):
        raise ValueError(
            f"{field.capitalize()} contém um padrão de dado pessoal não permitido."
        )
    return clean_value


def initialize_memory(path: str | Path) -> None:
    with _connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS feedback_events (
                event_id TEXT PRIMARY KEY,
                decision_id TEXT NOT NULL UNIQUE,
                predicted_category TEXT NOT NULL,
                corrected_category TEXT NOT NULL,
                confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
                was_correct INTEGER NOT NULL CHECK(was_correct IN (0, 1)),
                model_version TEXT NOT NULL,
                policy_version TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS lessons (
                lesson_id TEXT PRIMARY KEY,
                predicted_category TEXT NOT NULL,
                recommended_category TEXT NOT NULL,
                trigger_terms_json TEXT NOT NULL,
                instruction TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('candidate', 'approved', 'retired')),
                evidence_count INTEGER NOT NULL DEFAULT 1,
                version INTEGER NOT NULL DEFAULT 1,
                created_by TEXT NOT NULL DEFAULT 'legacy',
                approved_by TEXT,
                approved_at TEXT,
                approval_reason TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS lesson_evidence (
                lesson_id TEXT NOT NULL REFERENCES lessons(lesson_id),
                event_id TEXT NOT NULL REFERENCES feedback_events(event_id),
                PRIMARY KEY (lesson_id, event_id)
            );

            CREATE TRIGGER IF NOT EXISTS feedback_events_no_update
            BEFORE UPDATE ON feedback_events
            BEGIN
                SELECT RAISE(ABORT, 'feedback_events is append-only');
            END;

            CREATE TRIGGER IF NOT EXISTS feedback_events_no_delete
            BEFORE DELETE ON feedback_events
            BEGIN
                SELECT RAISE(ABORT, 'feedback_events is append-only');
            END;
            """
        )
        lesson_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(lessons)").fetchall()
        }
        migrations = {
            "created_by": "ALTER TABLE lessons ADD COLUMN created_by TEXT NOT NULL DEFAULT 'legacy'",
            "approved_by": "ALTER TABLE lessons ADD COLUMN approved_by TEXT",
            "approved_at": "ALTER TABLE lessons ADD COLUMN approved_at TEXT",
            "approval_reason": "ALTER TABLE lessons ADD COLUMN approval_reason TEXT",
        }
        for column, statement in migrations.items():
            if column not in lesson_columns:
                connection.execute(statement)


def record_feedback(
    path: str | Path,
    *,
    decision_id: str,
    predicted_category: str,
    corrected_category: str,
    confidence: float,
    model_version: str,
    policy_version: str,
    created_by: str,
    trigger_terms: list[str] | None = None,
) -> dict:
    initialize_memory(path)
    was_correct = predicted_category == corrected_category
    event_id = str(uuid4())
    created_at = _now()
    normalized_terms = _normalize_terms(trigger_terms or [])
    created_by = _validate_safe_text(
        created_by, field="identificador do autor", max_length=60
    )
    lesson_instruction = (
        f"Quando aparecerem os termos {', '.join(normalized_terms)}, revisar "
        f"a sugestão {predicted_category} e considerar {corrected_category}."
        if normalized_terms and not was_correct
        else ""
    )

    with _connect(path) as connection:
        connection.execute(
            """
            INSERT INTO feedback_events (
                event_id, decision_id, predicted_category, corrected_category,
                confidence, was_correct, model_version,
                policy_version, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                decision_id,
                predicted_category,
                corrected_category,
                confidence,
                int(was_correct),
                model_version,
                policy_version,
                created_at,
            ),
        )

        lesson_id = None
        if not was_correct and normalized_terms and lesson_instruction:
            terms_json = json.dumps(normalized_terms, ensure_ascii=True)
            existing = connection.execute(
                """
                SELECT lesson_id, evidence_count
                FROM lessons
                WHERE predicted_category = ?
                  AND recommended_category = ?
                  AND trigger_terms_json = ?
                  AND instruction = ?
                  AND status != 'retired'
                """,
                (
                    predicted_category,
                    corrected_category,
                    terms_json,
                    lesson_instruction,
                ),
            ).fetchone()

            if existing:
                lesson_id = existing["lesson_id"]
                connection.execute(
                    """
                    UPDATE lessons
                    SET evidence_count = ?, updated_at = ?
                    WHERE lesson_id = ?
                    """,
                    (existing["evidence_count"] + 1, created_at, lesson_id),
                )
            else:
                lesson_id = str(uuid4())
                connection.execute(
                    """
                    INSERT INTO lessons (
                        lesson_id, predicted_category, recommended_category,
                        trigger_terms_json, instruction, status, created_by,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, 'candidate', ?, ?, ?)
                    """,
                    (
                        lesson_id,
                        predicted_category,
                        corrected_category,
                        terms_json,
                        lesson_instruction,
                        created_by,
                        created_at,
                        created_at,
                    ),
                )

            connection.execute(
                """
                INSERT OR IGNORE INTO lesson_evidence (lesson_id, event_id)
                VALUES (?, ?)
                """,
                (lesson_id, event_id),
            )

    return {
        "event_id": event_id,
        "lesson_id": lesson_id,
        "was_correct": was_correct,
    }


def find_approved_lessons(
    path: str | Path,
    *,
    text: str,
    predicted_category: str,
) -> list[dict]:
    initialize_memory(path)
    normalized_text = _normalize(text)
    with _connect(path) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM lessons
            WHERE status = 'approved'
              AND predicted_category = ?
            ORDER BY evidence_count DESC, updated_at DESC
            """,
            (predicted_category,),
        ).fetchall()

    matches = []
    for row in rows:
        terms = json.loads(row["trigger_terms_json"])
        if terms and all(term in normalized_text for term in terms):
            lesson = dict(row)
            lesson["trigger_terms"] = terms
            lesson.pop("trigger_terms_json")
            matches.append(lesson)
    return matches


def list_lessons(path: str | Path, *, limit: int = 100) -> list[dict]:
    initialize_memory(path)
    with _connect(path) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM lessons
            ORDER BY
                CASE status WHEN 'candidate' THEN 0 WHEN 'approved' THEN 1 ELSE 2 END,
                updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    lessons = []
    for row in rows:
        lesson = dict(row)
        lesson["trigger_terms"] = json.loads(lesson.pop("trigger_terms_json"))
        lessons.append(lesson)
    return lessons


def set_lesson_status(
    path: str | Path,
    *,
    lesson_id: str,
    status: str,
    actor_id: str,
    reason: str,
) -> None:
    if status not in VALID_LESSON_STATUSES:
        raise ValueError(f"Status inválido: {status}")
    initialize_memory(path)
    actor_id = _validate_safe_text(
        actor_id, field="identificador do revisor", max_length=60
    )
    reason = _validate_safe_text(reason, field="justificativa", max_length=240)
    with _connect(path) as connection:
        lesson = connection.execute(
            "SELECT * FROM lessons WHERE lesson_id = ?",
            (lesson_id,),
        ).fetchone()
        if lesson is None:
            raise KeyError(f"Aprendizado não encontrado: {lesson_id}")
        if status == "approved" and lesson["created_by"] == actor_id:
            raise PermissionError(
                "Quem criou o aprendizado não pode aprová-lo."
            )
        if status == "approved":
            conflict = connection.execute(
                """
                SELECT lesson_id
                FROM lessons
                WHERE lesson_id != ?
                  AND predicted_category = ?
                  AND trigger_terms_json = ?
                  AND recommended_category != ?
                  AND status = 'approved'
                """,
                (
                    lesson_id,
                    lesson["predicted_category"],
                    lesson["trigger_terms_json"],
                    lesson["recommended_category"],
                ),
            ).fetchone()
            if conflict:
                raise ValueError(
                    "Existe um aprendizado aprovado conflitante para os mesmos termos."
                )
        approved_by = actor_id if status == "approved" else lesson["approved_by"]
        approved_at = _now() if status == "approved" else lesson["approved_at"]
        result = connection.execute(
            """
            UPDATE lessons
            SET status = ?, approved_by = ?, approved_at = ?,
                approval_reason = ?, updated_at = ?
            WHERE lesson_id = ?
            """,
            (status, approved_by, approved_at, reason, _now(), lesson_id),
        )
        if result.rowcount != 1:
            raise KeyError(f"Aprendizado não encontrado: {lesson_id}")
