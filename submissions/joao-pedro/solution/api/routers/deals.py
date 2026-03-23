"""
Router: /deals
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query

from api.dependencies import get_benchmarks, get_pipeline_df
from core.scoring_engine import calculate_score, score_all_deals

router = APIRouter()


def _scored_deals_list(
    stage: Optional[str] = None,
    all_stages: bool = False,
    sales_agent: Optional[str] = None,
    product: Optional[str] = None,
    account: Optional[str] = None,
    action: Optional[str] = None,
    min_score: Optional[float] = None,
    min_days: Optional[int] = None,
) -> List[dict]:
    benchmarks = get_benchmarks()
    pipeline_df = get_pipeline_df()

    df = pipeline_df.copy()
    if all_stages:
        pass  # sem filtro de stage — retorna todos
    elif stage:
        df = df[df["deal_stage"] == stage]
    else:
        df = df[df["deal_stage"] == "Engaging"]

    deals = df.to_dict("records")
    scored = score_all_deals(deals, benchmarks)

    if sales_agent:
        scored = [d for d in scored if d["deal_info"]["sales_agent"] == sales_agent]
    if product:
        scored = [d for d in scored if d["deal_info"]["product"] == product]
    if account:
        scored = [d for d in scored if d["deal_info"]["account"] == account]
    if action:
        scored = [d for d in scored if d["action"]["type"] == action.upper()]
    if min_score is not None:
        scored = [d for d in scored if d["score"] >= min_score]
    if min_days is not None:
        scored = [d for d in scored if d["deal_info"]["days_in_pipeline"] >= min_days]

    return scored


@router.get("")
def list_deals(
    sales_agent: Optional[str] = Query(None),
    product: Optional[str] = Query(None),
    account: Optional[str] = Query(None),
    action: Optional[str] = Query(None, description="PUSH_HARD | ACCELERATE | MONITOR | INVESTIGATE | TRANSFER | CONSIDER_TRANSFER | DISCARD | RE_QUALIFY"),
    min_score: Optional[float] = Query(None),
    min_days: Optional[int] = Query(None),
    all_stages: bool = Query(False),
) -> List[dict]:
    """Lista deals com score calculado e ação recomendada. Por padrão retorna apenas Engaging; use all_stages=true para todos os stages."""
    scored = _scored_deals_list(
        all_stages=all_stages,
        sales_agent=sales_agent,
        product=product,
        account=account,
        action=action,
        min_score=min_score,
        min_days=min_days,
    )

    result = [
        {
            "opportunity_id": d["opportunity_id"],
            "sales_agent": d["deal_info"]["sales_agent"],
            "product": d["deal_info"]["product"],
            "account": d["deal_info"]["account"],
            "deal_stage": d["deal_info"]["deal_stage"],
            "close_value": d["deal_info"]["close_value"],
            "days_in_pipeline": d["deal_info"]["days_in_pipeline"],
            "regional_office": d["deal_info"]["regional_office"],
            "score": d["score"],
            "urgency": d["urgency"],
            "probability": d["probability"],
            "value": d["value"],
            "viability": d["viability"],
            "action": d["action"]["type"],
            "message": d["action"].get("message") or "",
        }
        for d in sorted(scored, key=lambda x: x["score"], reverse=True)
    ]

    # Incluir deals Won/Lost sem score (apenas para exibição no kanban)
    if all_stages:
        pipeline_df = get_pipeline_df()
        df_closed = pipeline_df[pipeline_df["deal_stage"].isin(["Won", "Lost"])].copy()
        if sales_agent:
            df_closed = df_closed[df_closed["sales_agent"] == sales_agent]
        if product:
            df_closed = df_closed[df_closed["product"] == product]
        if account:
            df_closed = df_closed[df_closed["account"] == account]
        if min_days is not None:
            df_closed = df_closed[df_closed["days_in_pipeline"] >= min_days]

        df_closed["close_value"] = df_closed["close_value"].fillna(0)
        df_closed["days_in_pipeline"] = df_closed["days_in_pipeline"].fillna(0)
        df_closed["regional_office"] = df_closed["regional_office"].fillna("")

        for row in df_closed.to_dict("records"):
            result.append({
                "opportunity_id": row["opportunity_id"],
                "sales_agent": row["sales_agent"],
                "product": row["product"],
                "account": row["account"],
                "deal_stage": row["deal_stage"],
                "close_value": float(row["close_value"]),
                "days_in_pipeline": int(row["days_in_pipeline"]),
                "regional_office": row["regional_office"],
                "score": 0,
                "urgency": 0,
                "probability": 0,
                "value": 0,
                "viability": 0,
                "action": None,
                "message": "",
            })

    return result


@router.get("/{opportunity_id}")
def get_deal(opportunity_id: str) -> dict:
    """Retorna deal completo com breakdown detalhado do score e ação recomendada."""
    benchmarks = get_benchmarks()
    pipeline_df = get_pipeline_df()

    row = pipeline_df[pipeline_df["opportunity_id"] == opportunity_id]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"Deal '{opportunity_id}' não encontrado.")

    deal = row.iloc[0].to_dict()
    result = calculate_score(deal, benchmarks)
    return result
