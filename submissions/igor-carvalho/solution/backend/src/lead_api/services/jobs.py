"""Jobs administrativos. O retreino roda em PROCESSO SEPARADO (lead_trainer); a API só dispara e acompanha."""
from __future__ import annotations

import json
import subprocess
import sys
import threading
from typing import Callable, Protocol

from lead_core.persistence import JobAlreadyRunning, JobRepository

from ..errors import ApiError
from ..settings import Settings
from ..store import ScoreStore
from .auth import AuthService


class JobRunner(Protocol):
    def start(self, job_id: str) -> None: ...


class JobService:
    """Regras dos jobs (um retreino por vez); persistência no JobRepository."""

    def __init__(self, jobs: JobRepository):
        self.jobs = jobs

    def create_retrain(self, requested_by: str) -> str:
        try:
            return self.jobs.create("retrain", requested_by)
        except JobAlreadyRunning:
            raise ApiError(409, "JOB_ALREADY_RUNNING", "Já existe um retreino em andamento.") from None

    def get(self, job_id: str) -> dict:
        job = self.jobs.get(job_id)
        if job is None:
            raise ApiError(404, "JOB_NOT_FOUND", "Job não encontrado.")
        return job


class SubprocessJobRunner:
    """Executa `python -m lead_trainer train ...` numa thread; ao terminar bem, recarrega o modelo na API."""

    def __init__(self, settings: Settings, store: ScoreStore, jobs: JobRepository, auth: AuthService | None = None,
                 runner: Callable[..., subprocess.CompletedProcess] = subprocess.run):
        self.settings, self.store, self.jobs, self.auth, self._run = settings, store, jobs, auth, runner

    def command(self) -> list[str]:
        s = self.settings
        return [sys.executable, "-m", "lead_trainer", "--data-dir", str(s.data_dir), "--artifact-dir",
                str(s.artifact_dir), "--db", str(s.db_path), "train"]

    def start(self, job_id: str) -> None:
        threading.Thread(target=self._execute, args=(job_id,), daemon=True).start()

    def _execute(self, job_id: str) -> None:
        self.jobs.mark(job_id, "running")
        try:
            proc = self._run(self.command(), capture_output=True, text=True)
            if proc.returncode != 0:
                self.jobs.mark(job_id, "failed", error=(proc.stderr or proc.stdout)[-1000:])
                return
            result = json.loads(proc.stdout.strip().splitlines()[-1])
            self.store.reload()
            if self.auth is not None:
                self.auth.sync_users(self.store.require().bundle.tables)
            self.jobs.mark(job_id, "succeeded", result=result)
        except Exception as exc:   # o job nunca pode derrubar o servidor
            self.jobs.mark(job_id, "failed", error=str(exc)[-1000:])
