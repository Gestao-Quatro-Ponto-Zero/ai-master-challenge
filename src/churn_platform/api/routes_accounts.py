"""SPEC-10.3 + SPEC-12: Accounts risk listing and LLM explain endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from churn_platform.api import get_state

router = APIRouter()


@router.get("/accounts/risk")
async def list_accounts_risk(
    tier: Optional[str] = Query(None, description="Filtrar por health_tier"),
    industry: Optional[str] = Query(None, description="Filtrar por indústria"),
    min_score: Optional[float] = Query(None, ge=0, le=100, description="Score mínimo"),
    limit: int = Query(50, ge=1, le=500, description="Máximo de contas"),
    llm_explain: bool = Query(True, description="Incluir narrativa LLM"),
):
    state = get_state()
    scored = state.get("scored_df")
    if scored is None:
        raise HTTPException(status_code=503, detail="Pipeline ainda não foi executado. POST /api/v1/run primeiro.")

    df = scored[scored["churn_flag"] == False].copy()

    if tier:
        df = df[df["health_tier"] == tier]
    if industry:
        df = df[df["industry"] == industry]
    if min_score is not None:
        df = df[df["health_score"] >= min_score]

    df = df.sort_values("health_score").head(limit)

    accounts = []
    explainer = state.get("explainer")

    for _, row in df.iterrows():
        account_data = row.to_dict()
        entry = {
            "account_id": account_data.get("account_id"),
            "health_score": round(account_data.get("health_score", 0), 1),
            "health_tier": account_data.get("health_tier", "Unknown"),
            "mrr_amount": int(account_data.get("mrr_amount", 0)),
            "industry": account_data.get("industry", ""),
            "plan_tier": account_data.get("plan_tier_account", account_data.get("plan_tier", "")),
            "top_risk_factors": _extract_risk_signals(account_data),
            "recommended_action": _top_action(account_data),
            "estimated_save_roi": _estimate_roi(account_data),
        }

        if llm_explain and explainer:
            import asyncio
            try:
                explanation = asyncio.run(explainer.explain(account_data, depth="short"))
                entry["llm_narrative"] = explanation["narrative"]
            except Exception:
                entry["llm_narrative"] = None

        accounts.append(entry)

    at_risk = sum(1 for a in accounts if a["health_tier"] in ("Critical", "At Risk"))
    total_mrr_at_risk = sum(a["mrr_amount"] for a in accounts if a["health_tier"] in ("Critical", "At Risk"))

    return {
        "accounts": accounts,
        "total_at_risk": at_risk,
        "total_mrr_at_risk": total_mrr_at_risk,
        "generated_at": _now_iso(),
    }


@router.get("/accounts/{account_id}/explain")
async def explain_account(
    account_id: str,
    depth: str = Query("detailed", pattern="^(short|detailed)$"),
):
    state = get_state()
    scored = state.get("scored_df")
    if scored is None:
        raise HTTPException(status_code=503, detail="Pipeline ainda não foi executado. POST /api/v1/run primeiro.")

    match = scored[scored["account_id"] == account_id]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Conta {account_id} não encontrada")

    explainer = state.get("explainer")
    if not explainer:
        raise HTTPException(status_code=503, detail="LLM Explainer não inicializado")

    account_data = match.iloc[0].to_dict()
    import asyncio
    try:
        result = asyncio.run(explainer.explain(account_data, depth=depth))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _extract_risk_signals(account: dict) -> list[str]:
    signals = []
    if account.get("pillar_usage", 50) < 40:
        signals.append("usage_drop_40pct")
    if account.get("escalation_count", 0) > 2:
        signals.append(f"{int(account['escalation_count'])}_escalations")
    if account.get("downgrade_flag", False):
        signals.append("recent_downgrade")
    if account.get("avg_satisfaction", 5) < 3:
        signals.append("low_satisfaction")
    if account.get("beta_feature_used", False) == False:
        signals.append("champion_inactive")
    return signals[:5] or ["stable"]


def _top_action(account: dict) -> str:
    if account.get("pillar_usage", 50) < 40:
        return "INT-001"
    if account.get("escalation_count", 0) > 2:
        return "INT-002"
    if account.get("pillar_financial", 50) < 40:
        return "INT-004"
    return "INT-000"


def _estimate_roi(account: dict) -> str:
    mrr = account.get("mrr_amount", 0)
    months_saved = 6
    roi = mrr * months_saved
    return f"${roi:,}"


def _now_iso() -> str:
    from datetime import datetime
    return datetime.utcnow().isoformat() + "Z"
