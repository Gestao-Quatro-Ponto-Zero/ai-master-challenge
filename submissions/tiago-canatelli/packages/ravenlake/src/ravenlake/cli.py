"""CLI `ravenlake`: ingest, dq e catálogo."""

from pathlib import Path
from typing import Annotated
from uuid import UUID

import typer
from rich.console import Console
from rich.table import Table

from ravenlake import pipeline, runner, sources
from ravenlake.settings import Settings

app = typer.Typer(
    help="Pipeline do RavenStack Churn Lake (Kaggle -> Supabase).", no_args_is_help=True
)
console = Console()


def _settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # valores vêm do ambiente


@app.command()
def ingest(
    source: Annotated[str, typer.Option(help="kaggle (MCP) ou local")] = "kaggle",
    path: Annotated[Path, typer.Option(help="Pasta dos CSVs quando --source local")] = Path(
        "../../datasets/kaggle-rivalytics"
    ),
    trigger: Annotated[str, typer.Option(help="manual, cron ou test")] = "manual",
    force: Annotated[
        bool, typer.Option(help="Reprocessa silver/qualidade/gold mesmo sem arquivo novo")
    ] = False,
) -> None:
    """Baixa os CSVs, grava no bucket raw, carrega bronze, silver, qualidade, gold e catálogo."""
    status = runner.run_ingest(source, path, trigger, force, console.print)
    raise typer.Exit(code=0 if status in ("success", "skipped") else 1)


@app.command()
def dq(
    run_id: Annotated[str | None, typer.Argument(help="Run; padrão = o mais recente")] = None,
) -> None:
    """Mostra o resultado das checagens de qualidade de um run."""
    s = _settings()
    with pipeline.connect(s.database_url.get_secret_value()) as conn:
        if run_id is None:
            row = conn.execute(
                "select run_id from ops.ingestion_runs order by started_at desc limit 1"
            ).fetchone()
            if row is None:
                console.print("nenhum run encontrado")
                raise typer.Exit(code=1)
            run = row[0]
        else:
            run = UUID(run_id)
        results = conn.execute(
            """select severity, status, check_name, failing_rows, total_rows, details
                 from ops.dq_results where run_id = %s
                order by case severity when 'error' then 1 when 'warning' then 2 else 3 end,
                         check_name""",
            (run,),
        ).fetchall()
    table = Table(title=f"Qualidade · run {run}")
    for col in ("severidade", "status", "checagem", "falhas", "total", "detalhe"):
        table.add_column(col)
    for severity, status, name, failing, total, details in results:
        color = "green" if status == "pass" else "red" if severity == "error" else "yellow"
        table.add_row(severity, f"[{color}]{status}[/]", name, str(failing), str(total), details)
    console.print(table)


@app.command()
def gold() -> None:
    """Atualiza o gold (fatos, dimensões, personas e score de risco) e o catálogo."""
    s = _settings()
    with pipeline.connect(s.database_url.get_secret_value()) as conn:
        row = conn.execute("select gold.refresh()").fetchone()
        conn.execute("select ops.refresh_catalog()")
    console.print(f"gold atualizado: {row[0] if row else 0} contas com score de risco")


@app.command("catalog")
def catalog_refresh() -> None:
    """Reconstrói o catálogo (ops.catalog_tables / ops.catalog_columns)."""
    s = _settings()
    with pipeline.connect(s.database_url.get_secret_value()) as conn:
        row = conn.execute("select ops.refresh_catalog()").fetchone()
    console.print(f"catálogo atualizado: {row[0] if row else 0} tabelas")


@app.command()
def version() -> None:
    """Mostra a versão atual do dataset no Kaggle (via MCP)."""
    s = _settings()
    token = s.kaggle_mcp_token.get_secret_value() if s.kaggle_mcp_token else None
    console.print(sources.kaggle_version(s.kaggle_mcp_url, s.kaggle_dataset, token))
