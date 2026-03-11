"""
Lead Scorer — FastAPI application.
Serves the API endpoints and the frontend SPA.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from backend.data_loader import load_data, store
from backend.scoring_engine import score_all_deals
from backend.alerts import enrich_deals_with_alerts


# --- Global scored deals cache ---
scored_deals: list[dict] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load data and score all deals on startup."""
    global scored_deals
    print("\n=== Lead Scorer Starting ===\n")
    load_data()
    raw_scored = score_all_deals()
    scored_deals = enrich_deals_with_alerts(raw_scored)
    print(f"\n=== Ready! {len(scored_deals)} deals scored and enriched ===\n")
    yield


app = FastAPI(title="Lead Scorer", lifespan=lifespan)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ─── HTML Route ───────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ─── API Routes ───────────────────────────────────────────────

@app.get("/api/filters")
async def get_filters():
    """Return available filter options for the UI."""
    # Collect distinct alert types from active deals
    alert_types = set()
    for d in scored_deals:
        if d["deal_stage"] in ("Prospecting", "Engaging") and d.get("alert"):
            alert_types.add(d["alert"]["type"])

    return {
        "agents": store.filter_agents,
        "managers": store.filter_managers,
        "regions": store.filter_regions,
        "stages": ["Prospecting", "Engaging"],
        "alert_types": sorted(alert_types),
    }


@app.get("/api/pipeline")
async def get_pipeline(
    stage: str = Query(default="", description="Filter by deal stage"),
    agent: str = Query(default="", description="Filter by sales agent"),
    manager: str = Query(default="", description="Filter by manager"),
    region: str = Query(default="", description="Filter by region"),
    search: str = Query(default="", description="Search by account name"),
    sort: str = Query(default="score", description="Sort field"),
    order: str = Query(default="desc", description="Sort order: asc or desc"),
    alert_type: str = Query(default="", description="Filter by alert type"),
):
    """Return scored pipeline deals with optional filters."""
    # Only active deals by default, derive display_stage without mutating global cache
    deals = []
    for d in scored_deals:
        if d["deal_stage"] not in ("Prospecting", "Engaging"):
            continue
        # Create shallow copy to avoid mutating global cache
        deal_copy = {**d}
        if d["deal_stage"] == "Engaging" and d.get("alert") and d["alert"]["type"] in ("cooling", "stale"):
            deal_copy["display_stage"] = "Nutrir"
        elif d["deal_stage"] == "Engaging":
            deal_copy["display_stage"] = "Engaging"
        else:
            deal_copy["display_stage"] = "Prospecting"
        deals.append(deal_copy)

    # Apply filters
    if stage:
        deals = [d for d in deals if d["display_stage"] == stage]
    if agent:
        deals = [d for d in deals if d["sales_agent"] == agent]
    if manager:
        deals = [d for d in deals if d.get("manager") == manager]
    if region:
        deals = [d for d in deals if d.get("regional_office") == region]
    if search:
        search_lower = search.lower()
        deals = [
            d for d in deals
            if (d.get("account") and search_lower in d["account"].lower())
            or search_lower in d["opportunity_id"].lower()
        ]
    if alert_type:
        deals = [d for d in deals if d.get("alert") and d["alert"]["type"] == alert_type]

    # Sort
    reverse = order == "desc"
    sort_key = sort if sort in ("score", "days_in_pipeline", "estimated_value") else "score"
    deals.sort(key=lambda d: d.get(sort_key, 0) or 0, reverse=reverse)

    # Strip components for list view (keep it lightweight)
    deals_summary = []
    for d in deals:
        summary = {k: v for k, v in d.items() if k != "components"}
        # Flatten alert for table display
        if d.get("alert"):
            summary["alert_label"] = d["alert"]["label"]
            summary["alert_icon"] = d["alert"]["icon"]
            summary["alert_color"] = d["alert"]["color"]
            summary["alert_reason"] = d["alert"].get("reason", "")
        else:
            summary["alert_label"] = None
            summary["alert_icon"] = None
            summary["alert_color"] = None
            summary["alert_reason"] = None
        # Suggested action (always present)
        sa = d.get("suggested_action", {})
        summary["action_text"] = sa.get("action")
        summary["action_detail"] = sa.get("detail")
        summary["action_icon"] = sa.get("icon")
        summary["action_color"] = sa.get("color")
        summary["action_urgency"] = sa.get("urgency")
        deals_summary.append(summary)

    return {
        "deals": deals_summary,
        "total": len(deals_summary),
        "sort": sort_key,
        "order": order,
    }


@app.get("/api/deal/{opportunity_id}")
async def get_deal(opportunity_id: str):
    """Return full deal details with score breakdown."""
    for deal in scored_deals:
        if deal["opportunity_id"] == opportunity_id:
            return deal
    raise HTTPException(status_code=404, detail="Deal not found")


@app.get("/api/dashboard")
async def get_dashboard(
    region: str = Query(default="", description="Filter by region"),
    manager: str = Query(default="", description="Filter by manager"),
):
    """Return dashboard KPIs and aggregate stats."""
    deals = scored_deals
    if region:
        deals = [d for d in deals if d.get("regional_office") == region]
    if manager:
        deals = [d for d in deals if d.get("manager") == manager]

    active = [d for d in deals if d["deal_stage"] in ("Prospecting", "Engaging")]
    won = [d for d in deals if d["deal_stage"] == "Won"]
    lost = [d for d in deals if d["deal_stage"] == "Lost"]

    # Score distribution for active deals
    score_dist = {"0-20": 0, "20-40": 0, "40-60": 0, "60-80": 0, "80-100": 0}
    for d in active:
        s = d["score"]
        if s < 20: score_dist["0-20"] += 1
        elif s < 40: score_dist["20-40"] += 1
        elif s < 60: score_dist["40-60"] += 1
        elif s < 80: score_dist["60-80"] += 1
        else: score_dist["80-100"] += 1

    # Win rate by product (uses filtered deals)
    product_stats = {}
    for d in deals:
        if d["deal_stage"] in ("Won", "Lost"):
            p = d["product"]
            if p not in product_stats:
                product_stats[p] = {"won": 0, "lost": 0}
            if d["deal_stage"] == "Won":
                product_stats[p]["won"] += 1
            else:
                product_stats[p]["lost"] += 1

    products_wr = []
    for p, stats in sorted(product_stats.items()):
        total = stats["won"] + stats["lost"]
        products_wr.append({
            "product": p,
            "win_rate": round(stats["won"] / total * 100, 1) if total > 0 else 0,
            "total_deals": total,
        })

    # Alert counts
    alert_counts = {}
    for d in active:
        if d.get("alert"):
            atype = d["alert"]["type"]
            alert_counts[atype] = alert_counts.get(atype, 0) + 1

    # Deals by region
    region_stats = {}
    for d in active:
        r = d.get("regional_office", "Desconhecido")
        if r not in region_stats:
            region_stats[r] = {"count": 0, "total_value": 0}
        region_stats[r]["count"] += 1
        region_stats[r]["total_value"] += d.get("estimated_value", 0)

    return {
        "total_active": len(active),
        "total_pipeline_value": round(sum(d.get("estimated_value", 0) for d in active)),
        "avg_score": round(sum(d["score"] for d in active) / len(active), 1) if active else 0,
        "overall_winrate": round(len(won) / (len(won) + len(lost)) * 100, 1) if (won or lost) else 0,
        "deals_by_stage": {
            "Prospecting": sum(1 for d in deals if d["deal_stage"] == "Prospecting"),
            "Engaging": sum(1 for d in deals if d["deal_stage"] == "Engaging"),
            "Won": len(won),
            "Lost": len(lost),
        },
        "score_distribution": score_dist,
        "products_winrate": products_wr,
        "alert_counts": alert_counts,
        "region_stats": region_stats,
    }


@app.get("/api/agents")
async def get_agents(
    manager: str = Query(default=""),
    region: str = Query(default=""),
):
    """Return agent comparison stats."""
    agents_data = []
    active_deals = [d for d in scored_deals if d["deal_stage"] in ("Prospecting", "Engaging")]

    for _, row in store.df_teams.iterrows():
        agent_name = row["sales_agent"]
        agent_manager = row["manager"]
        agent_region = row["regional_office"]

        if manager and agent_manager != manager:
            continue
        if region and agent_region != region:
            continue

        stats = store.agent_stats.get(agent_name, {})
        agent_active = [d for d in active_deals if d["sales_agent"] == agent_name]

        hot = sum(1 for d in agent_active if d.get("alert") and d["alert"]["type"] == "hot")
        at_risk = sum(1 for d in agent_active if d.get("alert") and d["alert"]["type"] in ("at_risk", "stale"))

        agents_data.append({
            "name": agent_name,
            "manager": agent_manager,
            "region": agent_region,
            "win_rate": round(float(stats.get("win_rate", 0)) * 100, 1),
            "total_deals": int(stats.get("total_deals", 0)),
            "won_deals": int(stats.get("won_deals", 0)),
            "total_won_value": int(round(float(stats.get("total_won_value", 0)))),
            "avg_deal_value": int(round(float(stats.get("avg_deal_value", 0)))),
            "active_deals": len(agent_active),
            "avg_score": round(sum(d["score"] for d in agent_active) / len(agent_active), 1) if agent_active else 0,
            "hot_deals": hot,
            "at_risk_deals": at_risk,
        })

    agents_data.sort(key=lambda a: a["win_rate"], reverse=True)
    return {"agents": agents_data}


@app.get("/api/monday")
async def get_monday(
    manager: str = Query(default=""),
    region: str = Query(default=""),
    agent: str = Query(default=""),
):
    """Return Monday morning view: deals grouped by priority bucket."""
    active = [d for d in scored_deals if d["deal_stage"] in ("Prospecting", "Engaging")]

    if manager:
        active = [d for d in active if d.get("manager") == manager]
    if region:
        active = [d for d in active if d.get("regional_office") == region]
    if agent:
        active = [d for d in active if d["sales_agent"] == agent]

    buckets = {"fechar_agora": [], "nutrir": [], "repensar": []}
    for d in active:
        bucket = d.get("priority_bucket", "repensar")
        if bucket in buckets:
            summary = {k: v for k, v in d.items() if k != "components"}
            if d.get("alert"):
                summary["alert_label"] = d["alert"]["label"]
                summary["alert_icon"] = d["alert"]["icon"]
                summary["alert_color"] = d["alert"]["color"]
            else:
                summary["alert_label"] = None
            # Suggested action (always present)
            sa = d.get("suggested_action", {})
            summary["action_text"] = sa.get("action")
            summary["action_detail"] = sa.get("detail")
            summary["action_icon"] = sa.get("icon")
            summary["action_color"] = sa.get("color")
            summary["action_urgency"] = sa.get("urgency")
            buckets[bucket].append(summary)

    # Sort each bucket by score descending
    for bucket in buckets.values():
        bucket.sort(key=lambda d: d["score"], reverse=True)

    return {
        "fechar_agora": buckets["fechar_agora"],
        "nutrir": buckets["nutrir"],
        "repensar": buckets["repensar"],
        "summary": {
            "total_fechar": len(buckets["fechar_agora"]),
            "total_nutrir": len(buckets["nutrir"]),
            "total_repensar": len(buckets["repensar"]),
            "valor_fechar": round(sum(d.get("estimated_value", 0) for d in buckets["fechar_agora"])),
            "valor_nutrir": round(sum(d.get("estimated_value", 0) for d in buckets["nutrir"])),
            "valor_repensar": round(sum(d.get("estimated_value", 0) for d in buckets["repensar"])),
        },
    }

@app.get("/api/teams-grid")
async def get_teams_grid():
    """Return manager × region grid with deal counts, pipeline value, and avg score."""
    active = [d for d in scored_deals if d["deal_stage"] in ("Prospecting", "Engaging")]

    # Collect all regions and managers
    regions_set: set[str] = set()
    managers_set: set[str] = set()
    for d in active:
        regions_set.add(d.get("regional_office", "Unknown"))
        managers_set.add(d.get("manager", "Unknown"))
    regions = sorted(regions_set)
    managers = sorted(managers_set)

    def _make_cell(deals: list[dict]) -> dict:
        count = len(deals)
        pipeline = round(sum(d.get("estimated_value", 0) for d in deals))
        avg = round(sum(d["score"] for d in deals) / count, 1) if count else 0
        return {"deals_active": count, "pipeline_value": pipeline, "avg_score": avg}

    # Build rows per manager
    rows = []
    for mgr in managers:
        mgr_deals = [d for d in active if d.get("manager") == mgr]
        cells: dict[str, dict] = {}
        for reg in regions:
            reg_deals = [d for d in mgr_deals if d.get("regional_office") == reg]
            cells[reg] = _make_cell(reg_deals)
        cells["Total"] = _make_cell(mgr_deals)
        rows.append({"manager": mgr, "cells": cells})

    # Build totals row
    totals: dict[str, dict] = {}
    for reg in regions:
        reg_deals = [d for d in active if d.get("regional_office") == reg]
        totals[reg] = _make_cell(reg_deals)
    totals["Total"] = _make_cell(active)

    return {"regions": regions, "rows": rows, "totals": totals}


# ─── Run ──────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
