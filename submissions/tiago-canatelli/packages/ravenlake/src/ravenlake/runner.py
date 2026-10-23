"""Execução de uma ingestão a partir das configurações (usada pela CLI, pela API e pelo cron)."""

from pathlib import Path

from supabase import create_client

from ravenlake import pipeline, sources
from ravenlake.pipeline import Log
from ravenlake.settings import Settings


def run_ingest(
    source: str = "kaggle",
    path: Path | None = None,
    trigger: str = "manual",
    force: bool = False,
    log: Log = print,
) -> str:
    """Kaggle MCP (ou pasta local) -> raw -> bronze -> silver -> qualidade -> gold -> catálogo."""
    s = Settings()  # type: ignore[call-arg]
    if source == "kaggle":
        token = s.kaggle_mcp_token.get_secret_value() if s.kaggle_mcp_token else None
        log(f"Kaggle MCP: {s.kaggle_dataset}")
        snapshot = sources.from_kaggle(s.kaggle_mcp_url, s.kaggle_dataset, token)
    elif source == "local" and path is not None:
        snapshot = sources.from_local(path)
    else:
        raise ValueError("use source='kaggle' ou source='local' com path")
    storage = create_client(s.supabase_url, s.supabase_secret_key.get_secret_value())
    with pipeline.connect(s.database_url.get_secret_value()) as conn:
        _, status = pipeline.ingest(
            conn, storage, s.raw_bucket, snapshot, trigger, s.batch_size, log, force
        )
    return status
