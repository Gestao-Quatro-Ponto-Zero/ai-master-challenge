"""API HTTP: login por papel, dados do painel, prompts/perfis, assistente e MCP em /mcp.

Rodar: uv run uvicorn api.main:app --reload
"""

import hmac
import os
import threading
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from api import assistant, auth, db
from api.mcp_server import mcp

api = FastAPI(title="RavenStack Churn API", version="0.2.0")
api.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in db.settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Quais abas liberam quais views. A visão geral é de todos; "ia" só lê prompts/perfis.
TAB_VIEWS = {
    "geral": {
        "kpi_overview",
        "tenure_hazard",
        "cohort",
        "churn_type",
        "persona_summary",
        "persona_catalog",
        "revenue_monthly",
        "loss_concentration",
        "support_health",
        "silent_churn",
        "usage_quarterly",
        "churn_by_segment",
        "reactivation",
        "feature_health",
    },
    "risco": {"risk_queue", "account_360", "churn_reason_vs_behavior"},
    "dados": {
        "ingestion_runs",
        "ingestion_steps",
        "dq_results",
        "catalog_tables",
        "catalog_columns",
    },
    "ia": {"prompts", "profiles"},
}

User = dict[str, Any]


def allowed_views(user: User) -> set[str]:
    return set().union(*(TAB_VIEWS.get(t, set()) for t in user["tabs"]))


def require_edit(user: User = Depends(auth.current_user)) -> User:
    if not user["can_edit"]:
        raise HTTPException(status_code=403, detail="seu papel não pode editar prompts e perfis")
    return user


class Login(BaseModel):
    email: str
    code: str


@api.post("/auth/login")
def login(body: Login) -> dict[str, Any]:
    return auth.login(body.email, body.code)


@api.get("/me")
def me(user: User = Depends(auth.current_user)) -> User:
    return user


@api.get("/health")
def health() -> dict[str, Any]:
    row = db.rows("select gold.as_of_date() as as_of_date")
    return {
        "status": "ok",
        "as_of_date": str(row[0]["as_of_date"]) if row else None,
        "assistant": db.settings.anthropic_api_key is not None,
        "commit": os.environ.get("RENDER_GIT_COMMIT", "local")[:7],
        "model": db.settings.claude_model,
    }


@api.get("/data/{view}")
def data(
    view: str,
    account_id: str | None = None,
    run_id: str | None = None,
    limit: int = 2000,
    user: User = Depends(auth.current_user),
) -> list[dict[str, Any]]:
    if view not in allowed_views(user):
        raise HTTPException(status_code=403, detail=f"seu papel não acessa {view}")
    where = {k: v for k, v in {"account_id": account_id, "run_id": run_id}.items() if v}
    rows = db.read_view(view, where, min(limit, 5000))
    if view == "prompts" and user["role"] not in ("admin", "executivo"):
        rows = [r for r in rows if r["profile_slug"] == user["profile_slug"]]
    if view == "profiles" and user["role"] not in ("admin", "executivo"):
        rows = [r for r in rows if r["slug"] == user["profile_slug"]]
    return rows


class TextUpdate(BaseModel):
    text: str


@api.put("/prompts/{slug}")
def update_prompt(
    slug: str, body: TextUpdate, user: User = Depends(require_edit)
) -> dict[str, str]:
    db.execute(
        "update app.prompt_templates set body = %s, version = version + 1, updated_at = now() where slug = %s",
        (body.text, slug),
    )
    return {"status": "salvo"}


@api.post("/prompts/{slug}/restore")
def restore_prompt(slug: str, user: User = Depends(require_edit)) -> dict[str, str]:
    db.execute(
        "update app.prompt_templates set body = default_body, version = version + 1, updated_at = now() "
        "where slug = %s",
        (slug,),
    )
    return {"status": "restaurado"}


@api.put("/profiles/{slug}")
def update_profile(
    slug: str, body: TextUpdate, user: User = Depends(require_edit)
) -> dict[str, str]:
    db.execute(
        "update app.analysis_profiles set instructions = %s, version = version + 1, updated_at = now() "
        "where slug = %s",
        (body.text, slug),
    )
    return {"status": "salvo"}


@api.post("/profiles/{slug}/restore")
def restore_profile(slug: str, user: User = Depends(require_edit)) -> dict[str, str]:
    db.execute(
        "update app.analysis_profiles set instructions = default_instructions, version = version + 1, "
        "updated_at = now() where slug = %s",
        (slug,),
    )
    return {"status": "restaurado"}


class Question(BaseModel):
    question: str
    profile_slug: str | None = None
    prompt_slug: str | None = None


@api.post("/assistant")
def ask(q: Question, user: User = Depends(auth.current_user)) -> dict[str, Any]:
    if "ia" not in user["tabs"]:
        raise HTTPException(status_code=403, detail="seu papel não usa o assistente")
    if len(q.question) > 4000:
        raise HTTPException(status_code=400, detail="pergunta longa demais")
    # Cada área analisa com a própria lente; admin e CEO podem escolher qualquer perfil.
    profile = q.profile_slug if user["role"] in ("admin", "executivo") else user["profile_slug"]
    try:
        return assistant.ask(q.question, profile, q.prompt_slug, user["email"])
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


class IngestRequest(BaseModel):
    force: bool = False


_ingest_lock = threading.Lock()


def _run_ingest_background(force: bool, email: str, trigger: str = "manual") -> None:
    from ravenlake.runner import run_ingest

    try:
        run_ingest(
            source="kaggle",
            trigger=trigger,
            force=force,
            log=lambda m: print(f"[ingest {email}] {m}"),
        )
    except Exception as exc:  # o erro fica registrado em ops.ingestion_runs pelo pipeline
        print(f"[ingest {email}] falhou: {exc}")
    finally:
        _ingest_lock.release()


@api.post("/ingest")
def start_ingest(body: IngestRequest, user: User = Depends(require_edit)) -> dict[str, str]:
    """Dispara uma ingestão (Kaggle MCP -> raw -> bronze -> silver -> DQ -> gold) em segundo plano."""
    running = db.rows(
        "select run_id from ops.ingestion_runs where status = 'running' and started_at > now() - interval '15 minutes'"
    )
    if running or not _ingest_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="já existe uma ingestão em andamento")
    threading.Thread(
        target=_run_ingest_background, args=(body.force, user["email"]), daemon=True
    ).start()
    return {"status": "iniciada", "mode": "reprocessar" if body.force else "verificar fonte"}


@api.post("/ingest/cron")
def cron_ingest(x_cron_token: str | None = Header(None)) -> dict[str, str]:
    """Agendador: o pg_cron do Supabase chama a cada 15 min (verifica a versão no Kaggle)."""
    token = db.settings.cron_token
    if (
        token is None
        or x_cron_token is None
        or not hmac.compare_digest(x_cron_token, token.get_secret_value())
    ):
        raise HTTPException(status_code=401, detail="token do agendador inválido")
    running = db.rows(
        "select 1 from ops.ingestion_runs where status = 'running' and started_at > now() - interval '15 minutes'"
    )
    if running or not _ingest_lock.acquire(blocking=False):
        return {"status": "ignorada", "detail": "já existe uma ingestão em andamento"}
    threading.Thread(
        target=_run_ingest_background, args=(False, "pg_cron", "cron"), daemon=True
    ).start()
    return {"status": "iniciada", "mode": "verificar fonte"}


# MCP (streamable HTTP) como app externo; a API FastAPI fica montada na raiz.
app = mcp.streamable_http_app(
    streamable_http_path="/mcp",
    stateless_http=True,
    json_response=True,
    host="0.0.0.0",
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


class MCPAuth(BaseHTTPMiddleware):
    """Exige `Authorization: Bearer <MCP_TOKEN>` nas rotas /mcp (quando o token está configurado)."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        token = db.settings.mcp_token
        if request.url.path.startswith("/mcp") and token is not None:
            header = request.headers.get("authorization", "")
            if not hmac.compare_digest(header, f"Bearer {token.get_secret_value()}"):
                return JSONResponse({"detail": "token MCP inválido"}, status_code=401)
        response: Response = await call_next(request)
        return response


app.add_middleware(MCPAuth)
app.mount("/", api)
