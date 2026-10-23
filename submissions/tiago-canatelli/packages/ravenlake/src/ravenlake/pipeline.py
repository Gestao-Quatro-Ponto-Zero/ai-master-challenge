"""Orquestra uma ingestão: raw (Storage) -> bronze (COPY) -> silver -> qualidade -> catálogo.

As transformações e checagens vivem no Postgres (silver.refresh, ops.run_dq, ops.refresh_catalog);
aqui só movemos arquivos, carregamos o bronze e registramos o progresso em ops.*.
"""

import csv
import hashlib
import io
import subprocess
import time
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

import psycopg
from psycopg import sql
from supabase import Client

from ravenlake.sources import DATASETS, Snapshot, file_name

Log = Callable[[str], None]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_sha() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True
        )
        return out.stdout.strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


def connect(database_url: str) -> psycopg.Connection:
    # prepare_threshold=None: compatível com o pooler do Supabase em modo transaction.
    return psycopg.connect(database_url, autocommit=True, prepare_threshold=None)


def start_run(conn: psycopg.Connection, snapshot: Snapshot, trigger: str) -> UUID:
    row = conn.execute(
        """insert into ops.ingestion_runs (trigger, source, source_ref, source_version, git_sha)
           values (%s, %s, %s, %s, %s) returning run_id""",
        (trigger, snapshot.source, snapshot.source_ref, snapshot.version, git_sha()),
    ).fetchone()
    assert row is not None
    run_id: UUID = row[0]
    return run_id


def finish_run(
    conn: psycopg.Connection, run_id: UUID, status: str, error: str | None = None
) -> None:
    conn.execute(
        """update ops.ingestion_runs set status = %s, error = %s, finished_at = now()
            where run_id = %s""",
        (status, error, run_id),
    )


def _start_step(
    conn: psycopg.Connection, run_id: UUID, dataset: str, layer: str, **fields: object
) -> int:
    cols = ["run_id", "dataset", "layer", *fields]
    query = sql.SQL("insert into ops.ingestion_steps ({}) values ({}) returning step_id").format(
        sql.SQL(", ").join(map(sql.Identifier, cols)),
        sql.SQL(", ").join(sql.Placeholder() * len(cols)),
    )
    row = conn.execute(query, (run_id, dataset, layer, *fields.values())).fetchone()
    assert row is not None
    step_id: int = row[0]
    return step_id


def _end_step(
    conn: psycopg.Connection, step_id: int, status: str, error: str | None = None
) -> None:
    conn.execute(
        """update ops.ingestion_steps
              set status = %s, error = %s, finished_at = now(),
                  duration_ms = (extract(epoch from now() - started_at) * 1000)::integer
            where step_id = %s""",
        (status, error, step_id),
    )


def upload_raw(
    conn: psycopg.Connection, storage: Client, bucket: str, run_id: UUID, dataset: str, data: bytes
) -> str:
    """Guarda o CSV original no bucket raw (imutável, nomeado pelo hash)."""
    digest = sha256(data)
    path = f"{dataset}/{datetime.now(UTC):%Y-%m-%d}/{digest}.csv"
    step = _start_step(
        conn, run_id, dataset, "raw", file_sha256=digest, bytes=len(data), storage_path=path
    )
    try:
        existing = storage.storage.from_(bucket).list(
            path.rsplit("/", 1)[0], {"search": f"{digest}.csv"}
        )
        if existing:
            _end_step(conn, step, "skipped")
        else:
            storage.storage.from_(bucket).upload(path, data, {"content-type": "text/csv"})
            _end_step(conn, step, "success")
    except Exception as exc:
        _end_step(conn, step, "failed", str(exc))
        raise
    return digest


def _already_loaded(conn: psycopg.Connection, dataset: str, digest: str) -> bool:
    row = conn.execute(
        """select exists (select 1 from ops.ingestion_steps
                           where layer = 'bronze' and dataset = %s and file_sha256 = %s
                             and status = 'success')""",
        (dataset, digest),
    ).fetchone()
    return bool(row and row[0])


def load_bronze(
    conn: psycopg.Connection, run_id: UUID, dataset: str, data: bytes, batch_size: int, log: Log
) -> bool:
    """COPY do CSV para bronze.<dataset>; devolve False se o arquivo já estava carregado."""
    digest = sha256(data)
    rows = list(csv.reader(io.StringIO(data.decode("utf-8"))))
    header, body = rows[0], rows[1:]
    step = _start_step(conn, run_id, dataset, "bronze", file_sha256=digest, rows_read=len(body))

    if _already_loaded(conn, dataset, digest):
        _end_step(conn, step, "skipped")
        log(f"  bronze.{dataset}: arquivo já carregado ({digest[:8]}), pulando")
        return False

    table = sql.Identifier("bronze", dataset)
    columns = [*header, "_run_id", "_file_sha256", "_row_number", "_row_hash"]
    copy_sql = sql.SQL("copy {} ({}) from stdin").format(
        table, sql.SQL(", ").join(map(sql.Identifier, columns))
    )
    try:
        # Carga anterior do mesmo arquivo que falhou no meio: limpa antes de recarregar.
        conn.execute(sql.SQL("delete from {} where _file_sha256 = %s").format(table), (digest,))
        loaded = 0
        for start in range(0, len(body), batch_size):
            batch = body[start : start + batch_size]
            with conn.transaction(), conn.cursor() as cur, cur.copy(copy_sql) as copy:
                for offset, values in enumerate(batch, start=start + 1):
                    row_hash = sha256(",".join(values).encode())
                    copy.write_row([*values, run_id, digest, offset, row_hash])
            loaded += len(batch)
            conn.execute(
                "update ops.ingestion_steps set rows_loaded = %s where step_id = %s",
                (loaded, step),
            )
            log(f"  bronze.{dataset}: {loaded}/{len(body)}")
        _end_step(conn, step, "success")
        return True
    except Exception as exc:
        _end_step(conn, step, "failed", str(exc))
        raise


def last_successful_version(conn: psycopg.Connection, source_ref: str) -> int | None:
    row = conn.execute(
        """select source_version from ops.ingestion_runs
            where source_ref = %s and status in ('success', 'skipped')
            order by started_at desc limit 1""",
        (source_ref,),
    ).fetchone()
    return row[0] if row else None


def ingest(
    conn: psycopg.Connection,
    storage: Client,
    bucket: str,
    snapshot: Snapshot,
    trigger: str,
    batch_size: int,
    log: Log,
    force: bool = False,
) -> tuple[UUID, str]:
    """Executa uma ingestão completa; devolve (run_id, status)."""
    t0 = time.monotonic()
    run_id = start_run(conn, snapshot, trigger)
    log(f"run {run_id} · fonte {snapshot.source} · versão {snapshot.version}")
    try:
        changed = False
        for dataset in DATASETS:
            data = snapshot.files[dataset]
            log(f"{file_name(dataset)} ({len(data):,} bytes)")
            upload_raw(conn, storage, bucket, run_id, dataset, data)
            changed |= load_bronze(conn, run_id, dataset, data, batch_size, log)

        silver_empty = conn.execute("select not exists (select 1 from silver.accounts)").fetchone()
        if not changed and not force and silver_empty and not silver_empty[0]:
            finish_run(conn, run_id, "skipped")
            log("nenhum arquivo novo: run marcado como skipped (use --force para reprocessar)")
            return run_id, "skipped"

        log("silver.refresh …")
        for dataset, read, loaded, rejected in conn.execute(
            "select * from silver.refresh(%s)", (run_id,)
        ).fetchall():
            log(f"  silver.{dataset}: {loaded}/{read} carregadas, {rejected} rejeitadas")

        log("checagens de qualidade …")
        dq_row = conn.execute("select ops.run_dq(%s)", (run_id,)).fetchone()
        errors = dq_row[0] if dq_row else 0

        if errors:
            conn.execute("select ops.refresh_catalog(%s)", (run_id,))
            finish_run(conn, run_id, "failed", f"{errors} checagem(ns) de qualidade com erro")
            log(f"FALHOU: {errors} checagem(ns) de erro — gold não atualizado; ver ops.dq_results")
            return run_id, "failed"

        log("gold (fatos, dimensões, score de risco) …")
        scores = conn.execute("select gold.refresh(%s)", (run_id,)).fetchone()
        log(f"  gold.risk_scores: {scores[0] if scores else 0} contas")

        log("catálogo …")
        conn.execute("select ops.refresh_catalog(%s)", (run_id,))
        finish_run(conn, run_id, "success")
        log(f"concluído em {time.monotonic() - t0:.1f}s")
        return run_id, "success"
    except Exception as exc:
        finish_run(conn, run_id, "failed", str(exc))
        raise
