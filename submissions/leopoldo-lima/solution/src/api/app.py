from __future__ import annotations

import json
import logging
import pathlib
import time
import uuid
from collections.abc import AsyncIterator, Iterable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.contracts import (
    ApiError,
    DashboardFilterOptionsResponse,
    DashboardKpisResponse,
    OpportunitiesListResponse,
    OpportunityDetailResponse,
    OpportunityListItemResponse,
)
from src.api.dataset_loader import get_data_source_mode, load_opportunity_rows_for_serving
from src.api.view_models import (
    build_detail_view,
    build_list_item_view,
    to_dict,
)
from src.domain.deal_stage import (
    OFFICIAL_DEAL_STAGES,
    is_official_deal_stage,
    is_pipeline_open_stage,
    normalize_deal_stage,
)
from src.infrastructure.http.mappers import (
    map_wire_detail_to_contract,
    map_wire_list_item_to_contract,
)
from src.scoring.engine import ScoreResult, load_rules, score_opportunity

ROOT = pathlib.Path(__file__).resolve().parents[2]
PUBLIC_DIR = ROOT / "public"


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
    _safe_log("api_startup", lead_scorer_data_source_mode=get_data_source_mode())
    yield


app = FastAPI(title="Lead Scorer API", version="0.1.0", lifespan=_lifespan)
app.mount("/ui", StaticFiles(directory=str(PUBLIC_DIR)), name="ui")

logger = logging.getLogger("lead_scorer.api")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

METRICS: dict[str, int] = {
    "requests_total": 0,
    "ranking_requests": 0,
    "detail_requests": 0,
    "errors_total": 0,
    "status_404_total": 0,
    "status_422_total": 0,
    "status_500_total": 0,
}


def _safe_log(event: str, **fields: Any) -> None:
    payload = {"event": event, **fields}
    logger.info(json.dumps(payload, ensure_ascii=True))


@app.middleware("http")
async def request_observability_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    start = time.perf_counter()
    METRICS["requests_total"] += 1
    try:
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)
        response.headers["x-request-id"] = request_id
        if response.status_code == 404:
            METRICS["status_404_total"] += 1
            METRICS["errors_total"] += 1
        elif response.status_code == 422:
            METRICS["status_422_total"] += 1
            METRICS["errors_total"] += 1
        elif response.status_code >= 500:
            METRICS["status_500_total"] += 1
            METRICS["errors_total"] += 1
        _safe_log(
            "http_request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response
    except Exception:
        METRICS["errors_total"] += 1
        METRICS["status_500_total"] += 1
        duration_ms = int((time.perf_counter() - start) * 1000)
        _safe_log(
            "http_error",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=500,
            duration_ms=duration_ms,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
            headers={"x-request-id": request_id},
        )


def _unique_sorted_strings_ci(values: Iterable[str]) -> list[str]:
    """Remove vazios/duplicados e ordena alfabeticamente (case-insensitive, estável). CRP-CBX-01."""
    seen: set[str] = set()
    out: list[str] = []
    for raw in values:
        s = str(raw or "").strip()
        if not s:
            continue
        key = s.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    out.sort(key=lambda x: x.casefold())
    return out


def _row_deal_stage(row: dict[str, Any]) -> str:
    raw = row.get("deal_stage") if row.get("deal_stage") is not None else row.get("status")
    return normalize_deal_stage(str(raw or ""))


def _real_data_fields_from_row(row: dict[str, Any]) -> dict[str, Any]:
    """Campos explícitos do dataset para UI/API (CRP-REAL-05)."""
    try:
        amt = float(row.get("amount") or 0)
    except (TypeError, ValueError):
        amt = 0.0
    return {
        "account": str(row.get("account_name") or row.get("title") or ""),
        "product": str(row.get("product") or ""),
        "sales_agent": str(row.get("seller") or ""),
        "regional_office": str(row.get("team_regional_office") or row.get("region") or ""),
        "close_value": amt,
    }


def _to_scoring_payload(row: dict[str, Any]) -> dict[str, Any]:
    """Campos alinhados ao pipeline real (CRP-REAL-04).

    Chaves omitidas usam defaults no feature builder.
    """
    return {
        "id": row.get("id", ""),
        "deal_stage": _row_deal_stage(row),
        "close_value": row.get("amount", 0),
        "account": row.get("account_name") or row.get("title", ""),
        "engage_date": str(row.get("engage_date", "") or ""),
        "close_date": row.get("close_date"),
        "account_revenue": str(row.get("account_revenue", "") or ""),
        "account_employees": str(row.get("account_employees", "") or ""),
        "product_series": str(row.get("product_series", "") or ""),
        "product_sales_price": row.get("product_sales_price", row.get("amount", 0)),
        "product": str(row.get("product", "") or ""),
        "team_regional_office": str(row.get("team_regional_office", "") or ""),
        "region": str(row.get("region", "") or ""),
        "manager": str(row.get("manager", "") or ""),
    }


def _build_item(row: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    score_data: ScoreResult = score_opportunity(_to_scoring_payload(row), rules)
    base = {
        "id": row["id"],
        "title": row["title"],
        "seller": row["seller"],
        "manager": row["manager"],
        "region": row["region"],
        "deal_stage": _row_deal_stage(row),
        "amount": row["amount"],
    }
    list_view = build_list_item_view(base, score_data)
    wire_payload = {
        **to_dict(list_view),
        "nextBestAction": list_view.next_action,
    }
    merged = {
        **map_wire_list_item_to_contract(wire_payload).model_dump(),
        **_real_data_fields_from_row(row),
    }
    return OpportunityListItemResponse.model_validate(merged).model_dump()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
def metrics() -> dict[str, int]:
    return METRICS


@app.get("/")
def ui_index() -> FileResponse:
    return FileResponse(PUBLIC_DIR / "index.html")


def _row_matches_search_q(row: dict[str, Any], q: str) -> bool:
    """Busca em título, ID e conta (CRP-UX-07 — conta / ID)."""
    qn = q.lower()
    parts = [
        str(row.get("title", "") or ""),
        str(row.get("id", "") or ""),
        str(row.get("account_name", "") or ""),
    ]
    return any(qn in p.lower() for p in parts)


@app.get("/api/opportunities", response_model=OpportunitiesListResponse)
def list_opportunities(
    region: str | None = Query(default=None),
    manager: str | None = Query(default=None),
    deal_stage: str | None = Query(default=None),
    q: str | None = Query(default=None),
    priority_band: str | None = Query(default=None, max_length=16),
    sort_by: str = Query(default="score", pattern="^(score|amount|title|deal_stage)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    limit: int = Query(default=20, ge=1, le=200),
) -> dict[str, Any]:
    METRICS["ranking_requests"] += 1
    started = time.perf_counter()
    rows = load_opportunity_rows_for_serving()
    rules = load_rules()

    band_filter: str | None = None
    if priority_band and priority_band.strip():
        band_filter = priority_band.strip().lower()
        if band_filter not in ("high", "medium", "low"):
            raise HTTPException(
                status_code=422,
                detail="priority_band must be one of: high, medium, low",
            )

    filtered = []
    for row in rows:
        if region and row.get("region") != region:
            continue
        if manager and row.get("manager") != manager:
            continue
        if deal_stage and _row_deal_stage(row) != deal_stage.strip():
            continue
        if q and not _row_matches_search_q(row, q.strip()):
            continue
        item = _build_item(row, rules)
        if band_filter and str(item.get("priority_band", "")).strip().lower() != band_filter:
            continue
        filtered.append(item)

    reverse = sort_order == "desc"
    if sort_by == "amount":
        filtered.sort(key=lambda item: float(item.get("amount", 0)), reverse=reverse)
    elif sort_by == "title":
        filtered.sort(key=lambda item: str(item.get("title", "")).lower(), reverse=reverse)
    elif sort_by == "deal_stage":
        filtered.sort(key=lambda item: str(item.get("deal_stage", "")).lower(), reverse=reverse)
    else:
        filtered.sort(key=lambda item: int(item.get("score", 0)), reverse=reverse)
    _safe_log(
        "ranking_computed",
        returned_items=min(len(filtered), limit),
        total_filtered=len(filtered),
        duration_ms=int((time.perf_counter() - started) * 1000),
    )
    return {"total": len(filtered), "items": filtered[:limit]}


@app.get("/api/ranking", response_model=OpportunitiesListResponse)
def ranking(
    region: str | None = Query(default=None),
    manager: str | None = Query(default=None),
    deal_stage: str | None = Query(default=None),
    q: str | None = Query(default=None),
    priority_band: str | None = Query(default=None, max_length=16),
    sort_by: str = Query(default="score", pattern="^(score|amount|title|deal_stage)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    limit: int = Query(default=20, ge=1, le=200),
) -> dict[str, Any]:
    # Compat endpoint for older UI while /api/opportunities is the canonical path.
    return list_opportunities(
        region=region,
        manager=manager,
        deal_stage=deal_stage,
        q=q,
        priority_band=priority_band,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
    )


@app.get(
    "/api/opportunities/{opportunity_id}",
    response_model=OpportunityDetailResponse,
    responses={404: {"model": ApiError}},
)
def opportunity_detail(opportunity_id: str) -> dict[str, Any]:
    METRICS["detail_requests"] += 1
    rules = load_rules()
    rows = load_opportunity_rows_for_serving()
    for row in rows:
        if row.get("id") == opportunity_id:
            score_data: ScoreResult = score_opportunity(_to_scoring_payload(row), rules)
            base = {
                "id": row["id"],
                "title": row["title"],
                "seller": row["seller"],
                "manager": row["manager"],
                "region": row["region"],
                "deal_stage": _row_deal_stage(row),
                "amount": row["amount"],
            }
            detail = to_dict(build_detail_view(base, score_data))
            detail["scoreExplanation"] = detail.pop("explanation")
            detail.update(_real_data_fields_from_row(row))
            detail["engage_date"] = str(row.get("engage_date") or "")
            detail["close_date"] = row.get("close_date")
            detail["product_series"] = str(row.get("product_series") or "")
            return map_wire_detail_to_contract(detail).model_dump()
    raise HTTPException(status_code=404, detail="Opportunity not found")


@app.get("/api/dashboard/kpis", response_model=DashboardKpisResponse)
def dashboard_kpis() -> dict[str, Any]:
    rows = load_opportunity_rows_for_serving()
    rules = load_rules()
    total = len(rows)
    open_count = sum(1 for row in rows if is_pipeline_open_stage(_row_deal_stage(row)))
    won_count = sum(1 for row in rows if _row_deal_stage(row) == "Won")
    lost_count = sum(1 for row in rows if _row_deal_stage(row) == "Lost")
    scored = [_build_item(row, rules)["score"] for row in rows]
    avg_score = round(sum(scored) / len(scored), 2) if scored else 0.0
    return {
        "total_opportunities": total,
        "open_opportunities": open_count,
        "won_opportunities": won_count,
        "lost_opportunities": lost_count,
        "avg_score": avg_score,
    }


@app.get("/api/dashboard/filter-options", response_model=DashboardFilterOptionsResponse)
def dashboard_filter_options() -> dict[str, list[str]]:
    rows = load_opportunity_rows_for_serving()
    regional_raw = (str(row.get("region", "") or "").strip() for row in rows if row.get("region"))
    manager_raw = (str(row.get("manager", "") or "").strip() for row in rows if row.get("manager"))
    regional_offices = _unique_sorted_strings_ci(regional_raw)
    managers = _unique_sorted_strings_ci(manager_raw)
    present_stages = {_row_deal_stage(row) for row in rows}
    deal_stages = [
        s for s in OFFICIAL_DEAL_STAGES if s in present_stages and is_official_deal_stage(s)
    ]
    return {
        "regional_offices": regional_offices,
        "managers": managers,
        "deal_stages": deal_stages,
        "regions": regional_offices,
    }
