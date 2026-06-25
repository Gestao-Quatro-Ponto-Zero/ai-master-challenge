"""
main.py
-------
Rotas FastAPI — responsabilidade única: receber requisição, chamar
os módulos corretos, retornar resposta serializada.
"""

from contextlib import asynccontextmanager
from typing import Optional
import logging

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware

from data.loader import CRMDataLoader
from scoring.engine import score_pipeline, score_deal
from models.schemas import (
    DealScore, FactorBreakdown, FiltersResponse, HealthResponse, PipelineResponse,
)
from auth.router import router as auth_router
from auth.dependencies import get_current_user, require_role, get_pipeline_filters_for_user
from alerts.router import router as alerts_router
from alerts.scheduler import scheduler
from notes.router import router as notes_router
from analytics.Router import router as analytics_router
from notifications.router import router as notifications_router
from notifications.digest import digest_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

loader = CRMDataLoader()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Migra senhas em texto plano para bcrypt automaticamente
    from auth.service import migrate_plain_passwords
    migrated = migrate_plain_passwords()
    if migrated > 0:
        logger.info(f"Senhas migradas para bcrypt: {migrated} usuario(s).")

    loader.load()

    # Inicia schedulers
    scheduler.setup(loader)
    await scheduler.start()

    digest_scheduler.setup(loader)
    await digest_scheduler.start()

    yield

    await scheduler.stop()
    await digest_scheduler.stop()


app = FastAPI(
    title="Lead Scorer API",
    description="Priorização inteligente de deals para o time de vendas.",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(alerts_router)
app.include_router(notes_router)
app.include_router(analytics_router)
app.include_router(notifications_router)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialize_deal(row: dict) -> DealScore:
    factors = [
        FactorBreakdown(
            label=f["label"], points=f["points"],
            max_points=f["max_points"], reason=f["reason"], signal=f["signal"],
        )
        for f in row.get("factors", [])
    ]

    def safe(val, default=None):
        if val != val: return default
        return val

    return DealScore(
        opportunity_id=str(row.get("opportunity_id", "")),
        account=safe(row.get("account")),
        product=safe(row.get("product")),
        sales_agent=safe(row.get("sales_agent")),
        manager=safe(row.get("manager")),
        regional_office=safe(row.get("regional_office")),
        deal_stage=safe(row.get("deal_stage")),
        close_value=safe(row.get("close_value"), 0.0),
        days_in_pipeline=int(safe(row.get("days_in_pipeline"), 0)),
        sector=safe(row.get("sector")),
        revenue=safe(row.get("revenue"), 0.0),
        employees=safe(row.get("employees"), 0.0),
        score=int(row.get("score", 0)),
        tier=row.get("tier", "cold"),
        action=row.get("action", ""),
        action_urgency=row.get("action_urgency", "low"),
        factors=factors,
    )


# ---------------------------------------------------------------------------
# Rotas públicas
# ---------------------------------------------------------------------------

@app.get("/api/health", response_model=HealthResponse, tags=["Sistema"])
def health():
    active = loader.get_active_pipeline()
    return HealthResponse(
        status="ok",
        total_deals=len(loader.pipeline),
        active_deals=len(active),
        global_win_rate=round(loader.metrics.get("global_win_rate", 0), 4),
    )


# ---------------------------------------------------------------------------
# Rotas protegidas
# ---------------------------------------------------------------------------

@app.get("/api/filters", response_model=FiltersResponse, tags=["Filtros"])
def get_filters(current_user: dict = Depends(get_current_user)):
    df   = loader.pipeline
    role = current_user["role"]

    if role == "agent":
        agents = [current_user["sales_agent"]] if current_user.get("sales_agent") else []
    else:
        agents = sorted(df["sales_agent"].dropna().astype(str).unique().tolist()) if "sales_agent" in df.columns else []

    def sorted_unique(col):
        if col not in df.columns: return []
        return sorted(df[col].dropna().astype(str).unique().tolist())

    return FiltersResponse(
        agents=agents,
        managers=sorted_unique("manager"),
        regions=sorted_unique("regional_office"),
        stages=["Prospecting", "Engaging"],
        products=sorted_unique("product"),
    )


@app.get("/api/pipeline", response_model=PipelineResponse, tags=["Pipeline"])
def get_pipeline(
    agent:   Optional[str] = Query(None),
    manager: Optional[str] = Query(None),
    region:  Optional[str] = Query(None),
    stage:   Optional[str] = Query(None),
    product: Optional[str] = Query(None),
    limit:   int           = Query(200, ge=1, le=1000),
    current_user: dict     = Depends(get_current_user),
):
    df = loader.get_active_pipeline()
    role_filters      = get_pipeline_filters_for_user(current_user)
    effective_agent   = role_filters.get("agent")   or agent
    effective_manager = role_filters.get("manager") or manager

    if effective_agent:
        df = df[df["sales_agent"].astype(str).str.lower() == effective_agent.lower()]
    if effective_manager and "manager" in df.columns:
        df = df[df["manager"].astype(str).str.lower() == effective_manager.lower()]
    if region and "regional_office" in df.columns:
        df = df[df["regional_office"].astype(str).str.lower() == region.lower()]
    if stage:
        df = df[df["deal_stage"].astype(str).str.lower() == stage.lower()]
    if product:
        df = df[df["product"].astype(str).str.lower() == product.lower()]

    if len(df) == 0:
        return PipelineResponse(total=0, deals=[])

    scored_df = score_pipeline(df, loader.metrics)
    scored_df = scored_df.head(limit)
    deals = [_serialize_deal(row) for row in scored_df.to_dict(orient="records")]
    return PipelineResponse(total=len(deals), deals=deals)


@app.get("/api/deal/{opportunity_id}", response_model=DealScore, tags=["Pipeline"])
def get_deal(opportunity_id: str, current_user: dict = Depends(get_current_user)):
    deal = loader.get_deal_by_id(opportunity_id)
    if deal is None:
        raise HTTPException(status_code=404, detail=f"Deal '{opportunity_id}' não encontrado.")
    if current_user["role"] == "agent":
        if deal.get("sales_agent") != current_user.get("sales_agent"):
            raise HTTPException(status_code=403, detail="Acesso negado a este deal.")
    scored = score_deal(deal, loader.metrics)
    row = {**deal.to_dict(), **scored}
    return _serialize_deal(row)


@app.get("/api/summary", tags=["Analytics"])
def get_summary(
    agent:   Optional[str] = Query(None),
    manager: Optional[str] = Query(None),
    region:  Optional[str] = Query(None),
    current_user: dict     = Depends(get_current_user),
):
    df = loader.get_active_pipeline()
    role_filters      = get_pipeline_filters_for_user(current_user)
    effective_agent   = role_filters.get("agent")   or agent
    effective_manager = role_filters.get("manager") or manager

    if effective_agent:
        df = df[df["sales_agent"].astype(str).str.lower() == effective_agent.lower()]
    if effective_manager and "manager" in df.columns:
        df = df[df["manager"].astype(str).str.lower() == effective_manager.lower()]
    if region and "regional_office" in df.columns:
        df = df[df["regional_office"].astype(str).str.lower() == region.lower()]

    if len(df) == 0:
        return {"total": 0, "hot": 0, "warm": 0, "cold": 0, "pipeline_value": 0}

    scored_df = score_pipeline(df, loader.metrics)
    return {
        "total":          len(scored_df),
        "hot":            int((scored_df["tier"] == "hot").sum()),
        "warm":           int((scored_df["tier"] == "warm").sum()),
        "cold":           int((scored_df["tier"] == "cold").sum()),
        "pipeline_value": round(float(scored_df["close_value"].fillna(0).sum()), 2),
        "top_deal": {
            "opportunity_id": str(scored_df.iloc[0].get("opportunity_id", "")),
            "account":        str(scored_df.iloc[0].get("account", "")),
            "score":          int(scored_df.iloc[0].get("score", 0)),
            "action":         str(scored_df.iloc[0].get("action", "")),
        },
    }


@app.get("/api/admin/users", tags=["Admin"])
def list_users(current_user: dict = Depends(require_role("admin"))):
    import json
    from pathlib import Path
    users = json.loads((Path(__file__).parent / "users.json").read_text())["users"]
    return [{k: v for k, v in u.items() if k != "password"} for u in users]