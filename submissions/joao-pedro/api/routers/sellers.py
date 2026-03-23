"""
Router: /sellers
"""

from typing import Optional, List
from fastapi import APIRouter, Query

from api.dependencies import get_benchmarks, get_raw_data

router = APIRouter()


def _viability_label(v: float) -> str:
    if v >= 60:
        return "Alta"
    elif v >= 40:
        return "Média"
    return "Baixa"


def _calc_viability(seller: str, benchmarks: dict) -> float:
    prosp = benchmarks["seller_prospecting"].get(seller, 0)
    active = benchmarks["seller_active_deals"].get(seller, 0)

    prosp_factor = 0.5 if prosp == 0 else 0.8 if prosp < 10 else 1.0 if prosp <= 30 else 1.3
    load_factor = 0.6 if active > 150 else 0.8 if active > 100 else 1.0 if active >= 40 else 1.3

    return round(min(50 * prosp_factor * load_factor, 100), 1)


@router.get("")
def list_sellers(
    region: Optional[str] = Query(None),
    viability: Optional[str] = Query(None, description="Alta | Média | Baixa"),
    sort_by: Optional[str] = Query("viability", description="viability | win_rate | active_deals | prospecting"),
) -> List[dict]:
    """Lista vendedores com métricas e viabilidade calculada."""
    benchmarks = get_benchmarks()
    pipeline_df_raw, _, _, teams_df = get_raw_data()

    closed = pipeline_df_raw[pipeline_df_raw["deal_stage"].isin(["Won", "Lost"])]
    won = pipeline_df_raw[pipeline_df_raw["deal_stage"] == "Won"]
    closed_counts = closed["sales_agent"].value_counts().to_dict()
    won_counts = won["sales_agent"].value_counts().to_dict()

    results = []
    for _, row in teams_df.iterrows():
        seller = row["sales_agent"]
        vb = _calc_viability(seller, benchmarks)
        results.append({
            "sales_agent": seller,
            "manager": row["manager"],
            "regional_office": row["regional_office"],
            "win_rate": round(benchmarks["seller_wr"].get(seller, 0), 1),
            "active_deals": benchmarks["seller_active_deals"].get(seller, 0),
            "prospecting": benchmarks["seller_prospecting"].get(seller, 0),
            "avg_ticket": round(benchmarks["seller_avg_ticket"].get(seller, 0), 2),
            "closed_deals": closed_counts.get(seller, 0),
            "won_deals": won_counts.get(seller, 0),
            "viability": vb,
            "viability_label": _viability_label(vb),
        })

    if region:
        results = [r for r in results if r["regional_office"] == region]
    if viability:
        results = [r for r in results if r["viability_label"] == viability]

    sort_key = {
        "viability": "viability",
        "win_rate": "win_rate",
        "active_deals": "active_deals",
        "prospecting": "prospecting",
    }.get(sort_by, "viability")

    results.sort(key=lambda x: x[sort_key], reverse=True)
    return results


@router.get("/{sales_agent}")
def get_seller(sales_agent: str) -> dict:
    """Retorna detalhes de um vendedor específico."""
    benchmarks = get_benchmarks()
    _, _, _, teams_df = get_raw_data()

    row = teams_df[teams_df["sales_agent"] == sales_agent]
    if row.empty:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Vendedor '{sales_agent}' não encontrado.")

    r = row.iloc[0]
    vb = _calc_viability(sales_agent, benchmarks)
    return {
        "sales_agent": sales_agent,
        "manager": r["manager"],
        "regional_office": r["regional_office"],
        "win_rate": round(benchmarks["seller_wr"].get(sales_agent, 0), 1),
        "active_deals": benchmarks["seller_active_deals"].get(sales_agent, 0),
        "prospecting": benchmarks["seller_prospecting"].get(sales_agent, 0),
        "avg_ticket": round(benchmarks["seller_avg_ticket"].get(sales_agent, 0), 2),
        "viability": vb,
        "viability_label": _viability_label(vb),
    }
