"""Repositório da entidade Job."""
from __future__ import annotations

import json
import uuid

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError

from ...db import utc_now
from ..database import Database
from ..models import Job


class JobAlreadyRunning(Exception):
    """Já existe um retreino na fila ou rodando (índice parcial do esquema)."""


class JobRepository:
    def __init__(self, db: Database):
        self.db = db

    def create(self, kind: str, requested_by: str | None, params: dict | None = None) -> str:
        job_id = uuid.uuid4().hex[:12]
        try:
            with self.db.session() as s:
                s.add(Job(job_id=job_id, kind=kind, status="queued", requested_by=requested_by,
                          params_json=json.dumps(params or {}), created_at=utc_now()))
        except IntegrityError as exc:           # ux_job_one_retrain
            raise JobAlreadyRunning(str(exc.orig)) from exc
        return job_id

    def get(self, job_id: str) -> dict | None:
        with self.db.session() as s:
            j = s.get(Job, job_id)
            if j is None:
                return None
            return {"job_id": j.job_id, "kind": j.kind, "status": j.status,
                    "result": json.loads(j.result_json) if j.result_json else None, "error": j.error,
                    "created_at": j.created_at, "started_at": j.started_at, "finished_at": j.finished_at}

    def mark(self, job_id: str, status: str, result: dict | None = None, error: str | None = None) -> None:
        stamp = {"started_at": utc_now()} if status == "running" else {"finished_at": utc_now()}
        with self.db.session() as s:
            s.execute(update(Job).where(Job.job_id == job_id).values(
                status=status, result_json=json.dumps(result) if result else None, error=error, **stamp))
