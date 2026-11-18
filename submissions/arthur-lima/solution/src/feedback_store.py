"""Local JSON feedback history with serialized writes and atomic replacement.

This is a local prototype store, not a tamper-proof audit service. A reset is an
event in the history, so restoring the queue does not delete earlier decisions.
"""
from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import tempfile
import time


# H5 — Persistência implementada pelo Codex após Arthur solicitar os ajustes da
# revalidação. Preservar decisões anteriores ao restaurar a fila foi incorporado
# nessa rodada; não é uma alegação de autoria humana exclusiva ou log inviolável.
# Contexto: PROCESS_LOG.md, mapa H1–H5 e seção 6.
class FeedbackStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    @contextmanager
    def _locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock = self.path.with_suffix(self.path.suffix + ".lock")
        deadline = time.monotonic() + 10
        while True:
            try:
                fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                break
            # Windows can report access denied while a competing lock is pending
            # deletion, rather than FileExistsError. Both require a bounded retry.
            except (FileExistsError, PermissionError):
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"Histórico ocupado. Verifique o processo responsável por {lock}.")
                time.sleep(0.02)
        try:
            yield
        finally:
            os.close(fd)
            lock.unlink()

    def _read(self) -> list[dict]:
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
            raise ValueError("Histórico de feedback inválido; restaure uma cópia antes de gravar.")
        return data

    def read(self) -> list[dict]:
        with self._locked():
            return self._read()

    def append(self, record: dict) -> None:
        with self._locked():
            records = self._read()
            records.append(record)
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent,
                                                 prefix=self.path.name + ".", suffix=".tmp", delete=False) as f:
                    temporary = Path(f.name)
                    json.dump(records, f, ensure_ascii=False, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(temporary, self.path)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)


def active_overrides(records: list[dict]) -> dict[str, dict]:
    active = {}
    for record in records:
        if record.get("event") == "reset_all":
            active.clear()
            continue
        opp = str(record.get("opportunity_id", "")).strip()
        disposition = str(record.get("disposition", "none")).strip().lower()
        if not opp:
            continue
        if disposition == "none":
            active.pop(opp, None)
        elif disposition in {"promote", "pause", "archive"}:
            active[opp] = {
                "disposition": disposition,
                "reason": str(record.get("feedback_reason", "")),
                "notes": str(record.get("proposed_action", "")),
            }
    return active
