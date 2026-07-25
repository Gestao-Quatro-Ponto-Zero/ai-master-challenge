from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from src.support_copilot.privacy import mask_pii


MEMORY_SCHEMA_VERSION = "2.0.0"
VALID_LESSON_STATUSES = {"candidate", "approved", "retired"}
SECRET_PATTERN = re.compile(
    r"(?i)(password|passwd|api[_ -]?key|secret|token|bearer|sk-[a-z0-9_-]+)"
)
CASE_LESSONS = (
    {
        "lesson_key": "customer-repeat-contact-v1",
        "scope": "Atendimento ao cliente",
        "statement": (
            "Contato repetido sem solução exige cuidado humano, mesmo quando "
            "o registro aparece como encerrado."
        ),
        "evidence": (
            "460 relatos explícitos; 152 abertos, 156 pendentes e 152 encerrados."
        ),
        "control": "Forçar revisão humana e auditar encerramentos.",
        "source": "docs/gate-1/data-audit.md",
        "applied_in": "customer_care.py",
    },
    {
        "lesson_key": "domain-taxonomy-boundary-v1",
        "scope": "Fronteira entre bases",
        "statement": (
            "A taxonomia de TI não pode classificar a fila de clientes."
        ),
        "evidence": (
            "No teste cruzado, 85,1% das mensagens de clientes viraram Hardware."
        ),
        "control": "Manter filas e decisões separadas por contexto.",
        "source": "docs/gate-2/cross-dataset-validation.md",
        "applied_in": "batch.py",
    },
    {
        "lesson_key": "confidence-is-not-domain-fit-v1",
        "scope": "Política de decisão",
        "statement": (
            "Confiança alta não prova que o modelo serve para o contexto."
        ),
        "evidence": (
            "49,5% das previsões cruzadas superaram o limite, apesar da "
            "taxonomia incompatível."
        ),
        "control": "Validar domínio antes de considerar confiança.",
        "source": "docs/gate-2/cross-dataset-validation.md",
        "applied_in": "app.py",
    },
    {
        "lesson_key": "invalid-time-fields-v1",
        "scope": "Qualidade dos dados",
        "statement": (
            "Os horários disponíveis não sustentam tempo de resposta, "
            "resolução ou ROI observado."
        ),
        "evidence": (
            "1.365 de 2.769 pares registram resolução antes da primeira resposta."
        ),
        "control": "Tratar ROI apenas como cenário até corrigir a instrumentação.",
        "source": "docs/gate-1/data-audit.md",
        "applied_in": "roi.py",
    },
    {
        "lesson_key": "repetition-is-not-duplicate-v1",
        "scope": "Qualidade dos dados",
        "statement": (
            "Texto repetido não significa automaticamente ticket duplicado."
        ),
        "evidence": (
            "A base tem zero linhas idênticas, zero IDs repetidos e descrições "
            "normalizadas repetidas em registros distintos."
        ),
        "control": "Preservar a base e marcar repetições antes de consolidar.",
        "source": "docs/gate-1/data-audit.md",
        "applied_in": "case_test_matrix.csv",
    },
    {
        "lesson_key": "template-noise-v1",
        "scope": "Qualidade do texto",
        "statement": (
            "Texto ruidoso e com placeholders limita automação autônoma."
        ),
        "evidence": "As 8.469 descrições do Dataset 1 contêm placeholders.",
        "control": "Usar regras auditáveis e revisão humana no piloto.",
        "source": "docs/gate-1/data-audit.md",
        "applied_in": "customer_care.py",
    },
)


def _connect(path: str | Path) -> sqlite3.Connection:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(destination, timeout=10.0)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 10000")
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

            CREATE TABLE IF NOT EXISTS operational_lessons (
                lesson_key TEXT PRIMARY KEY,
                scope TEXT NOT NULL,
                statement TEXT NOT NULL,
                evidence TEXT NOT NULL,
                control TEXT NOT NULL,
                source TEXT NOT NULL,
                applied_in TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('approved', 'retired')),
                approved_by TEXT NOT NULL,
                approved_at TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS memory_revisions (
                revision_id TEXT PRIMARY KEY,
                memory_type TEXT NOT NULL,
                memory_key TEXT NOT NULL,
                version INTEGER NOT NULL,
                action TEXT NOT NULL CHECK(action IN ('created', 'updated', 'retired')),
                snapshot_json TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL
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

            CREATE TRIGGER IF NOT EXISTS lessons_no_delete
            BEFORE DELETE ON lessons
            BEGIN
                SELECT RAISE(ABORT, 'lessons cannot be deleted; retire instead');
            END;

            CREATE TRIGGER IF NOT EXISTS lesson_evidence_no_update
            BEFORE UPDATE ON lesson_evidence
            BEGIN
                SELECT RAISE(ABORT, 'lesson_evidence is append-only');
            END;

            CREATE TRIGGER IF NOT EXISTS lesson_evidence_no_delete
            BEFORE DELETE ON lesson_evidence
            BEGIN
                SELECT RAISE(ABORT, 'lesson_evidence is append-only');
            END;

            CREATE TRIGGER IF NOT EXISTS operational_lessons_no_delete
            BEFORE DELETE ON operational_lessons
            BEGIN
                SELECT RAISE(ABORT, 'operational_lessons cannot be deleted; retire instead');
            END;

            CREATE TRIGGER IF NOT EXISTS memory_revisions_no_update
            BEFORE UPDATE ON memory_revisions
            BEGIN
                SELECT RAISE(ABORT, 'memory_revisions is append-only');
            END;

            CREATE TRIGGER IF NOT EXISTS memory_revisions_no_delete
            BEFORE DELETE ON memory_revisions
            BEGIN
                SELECT RAISE(ABORT, 'memory_revisions is append-only');
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


def seed_case_memory(
    path: str | Path,
    *,
    model_version: str,
    policy_version: str,
) -> None:
    initialize_memory(path)
    approved_at = "2026-07-24T00:00:00+00:00"
    with _connect(path) as connection:
        for lesson in CASE_LESSONS:
            connection.execute(
                """
                INSERT OR IGNORE INTO operational_lessons (
                    lesson_key, scope, statement, evidence, control, source,
                    applied_in, status, approved_by, approved_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'approved', ?, ?, 1)
                """,
                (
                    lesson["lesson_key"],
                    lesson["scope"],
                    lesson["statement"],
                    lesson["evidence"],
                    lesson["control"],
                    lesson["source"],
                    lesson["applied_in"],
                    "revisao-independente",
                    approved_at,
                ),
            )

        event_id = "seed-event-purchase-monitor-v1"
        lesson_id = "seed-lesson-purchase-monitor-v1"
        connection.execute(
            """
            INSERT OR IGNORE INTO feedback_events (
                event_id, decision_id, predicted_category,
                corrected_category, confidence, was_correct, model_version,
                policy_version, created_at
            ) VALUES (?, ?, 'Hardware', 'Purchase', 0.854, 0, ?, ?, ?)
            """,
            (
                event_id,
                "case-matrix-it-purchase-v1",
                model_version,
                policy_version,
                approved_at,
            ),
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO lessons (
                lesson_id, predicted_category, recommended_category,
                trigger_terms_json, instruction, status, evidence_count,
                version, created_by, approved_by, approved_at,
                approval_reason, created_at, updated_at
            ) VALUES (
                ?, 'Hardware', 'Purchase', ?,
                ?, 'approved', 1, 1, 'teste-controlado',
                'revisao-independente', ?,
                'Erro reproduzido na matriz de testes e mantido sob revisão humana.',
                ?, ?
            )
            """,
            (
                lesson_id,
                json.dumps(["monitor", "order"], ensure_ascii=True),
                (
                    "Quando aparecerem os termos monitor, order, revisar a "
                    "sugestão Hardware e considerar Purchase."
                ),
                approved_at,
                approved_at,
                approved_at,
            ),
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO lesson_evidence (lesson_id, event_id)
            VALUES (?, ?)
            """,
            (lesson_id, event_id),
        )


def list_operational_lessons(
    path: str | Path,
    *,
    status: str | None = "approved",
) -> list[dict]:
    initialize_memory(path)
    with _connect(path) as connection:
        if status is None:
            rows = connection.execute(
                """
                SELECT *
                FROM operational_lessons
                ORDER BY scope, lesson_key
                """
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT *
                FROM operational_lessons
                WHERE status = ?
                ORDER BY scope, lesson_key
                """,
                (status,),
            ).fetchall()
    return [dict(row) for row in rows]


def list_feedback_events(path: str | Path, *, limit: int = 500) -> list[dict]:
    initialize_memory(path)
    with _connect(path) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM feedback_events
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def list_lesson_evidence(path: str | Path, *, limit: int = 500) -> list[dict]:
    initialize_memory(path)
    with _connect(path) as connection:
        rows = connection.execute(
            """
            SELECT lesson_id, event_id
            FROM lesson_evidence
            ORDER BY lesson_id, event_id
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def list_memory_revisions(path: str | Path, *, limit: int = 500) -> list[dict]:
    initialize_memory(path)
    with _connect(path) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM memory_revisions
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    revisions = []
    for row in rows:
        revision = dict(row)
        revision["snapshot"] = json.loads(revision.pop("snapshot_json"))
        revisions.append(revision)
    return revisions


def create_operational_memory(
    path: str | Path,
    *,
    scope: str,
    statement: str,
    evidence: str,
    control: str,
    source: str,
    applied_in: str,
    actor_id: str,
    reason: str,
) -> dict:
    initialize_memory(path)
    actor_id = _validate_safe_text(
        actor_id, field="identificador do autor", max_length=60
    )
    reason = _validate_safe_text(reason, field="justificativa", max_length=240)
    values = {
        "scope": _validate_safe_text(scope, field="escopo", max_length=100),
        "statement": _validate_safe_text(
            statement, field="aprendizado", max_length=500
        ),
        "evidence": _validate_safe_text(
            evidence, field="evidência", max_length=500
        ),
        "control": _validate_safe_text(
            control, field="controle", max_length=500
        ),
        "source": _validate_safe_text(source, field="fonte", max_length=240),
        "applied_in": _validate_safe_text(
            applied_in, field="aplicação", max_length=240
        ),
    }
    created_at = _now()
    lesson_key = f"manual-{uuid4()}"
    snapshot = {
        "lesson_key": lesson_key,
        **values,
        "status": "approved",
        "approved_by": actor_id,
        "approved_at": created_at,
        "version": 1,
    }
    with _connect(path) as connection:
        connection.execute(
            """
            INSERT INTO operational_lessons (
                lesson_key, scope, statement, evidence, control, source,
                applied_in, status, approved_by, approved_at, version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'approved', ?, ?, 1)
            """,
            (
                lesson_key,
                values["scope"],
                values["statement"],
                values["evidence"],
                values["control"],
                values["source"],
                values["applied_in"],
                actor_id,
                created_at,
            ),
        )
        connection.execute(
            """
            INSERT INTO memory_revisions (
                revision_id, memory_type, memory_key, version, action,
                snapshot_json, actor_id, reason, created_at
            ) VALUES (?, 'operational_lesson', ?, 1, 'created', ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                lesson_key,
                json.dumps(snapshot, ensure_ascii=False, sort_keys=True),
                actor_id,
                reason,
                created_at,
            ),
        )
    return snapshot


def update_operational_memory(
    path: str | Path,
    *,
    lesson_key: str,
    scope: str,
    statement: str,
    evidence: str,
    control: str,
    source: str,
    applied_in: str,
    status: str,
    actor_id: str,
    reason: str,
) -> dict:
    if status not in {"approved", "retired"}:
        raise ValueError("Status operacional inválido.")
    initialize_memory(path)
    actor_id = _validate_safe_text(
        actor_id, field="identificador do editor", max_length=60
    )
    reason = _validate_safe_text(reason, field="justificativa", max_length=240)
    values = {
        "scope": _validate_safe_text(scope, field="escopo", max_length=100),
        "statement": _validate_safe_text(
            statement, field="aprendizado", max_length=500
        ),
        "evidence": _validate_safe_text(
            evidence, field="evidência", max_length=500
        ),
        "control": _validate_safe_text(
            control, field="controle", max_length=500
        ),
        "source": _validate_safe_text(source, field="fonte", max_length=240),
        "applied_in": _validate_safe_text(
            applied_in, field="aplicação", max_length=240
        ),
    }
    updated_at = _now()
    with _connect(path) as connection:
        current = connection.execute(
            "SELECT * FROM operational_lessons WHERE lesson_key = ?",
            (lesson_key,),
        ).fetchone()
        if current is None:
            raise KeyError(f"Memória não encontrada: {lesson_key}")
        version = int(current["version"]) + 1
        connection.execute(
            """
            UPDATE operational_lessons
            SET scope = ?, statement = ?, evidence = ?, control = ?,
                source = ?, applied_in = ?, status = ?, approved_by = ?,
                approved_at = ?, version = ?
            WHERE lesson_key = ?
            """,
            (
                values["scope"],
                values["statement"],
                values["evidence"],
                values["control"],
                values["source"],
                values["applied_in"],
                status,
                actor_id,
                updated_at,
                version,
                lesson_key,
            ),
        )
        snapshot = {
            "lesson_key": lesson_key,
            **values,
            "status": status,
            "approved_by": actor_id,
            "approved_at": updated_at,
            "version": version,
        }
        connection.execute(
            """
            INSERT INTO memory_revisions (
                revision_id, memory_type, memory_key, version, action,
                snapshot_json, actor_id, reason, created_at
            ) VALUES (?, 'operational_lesson', ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                lesson_key,
                version,
                "retired" if status == "retired" else "updated",
                json.dumps(snapshot, ensure_ascii=False, sort_keys=True),
                actor_id,
                reason,
                updated_at,
            ),
        )
    return snapshot


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
