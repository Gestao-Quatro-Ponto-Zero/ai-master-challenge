"""
Router: /managers
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
def list_managers(
    region: Optional[str] = Query(None),
    viability: Optional[str] = Query(None, description="Alta | Média | Baixa"),
    sort_by: Optional[str] = Query("avg_viability", description="avg_viability | avg_win_rate | total_active_deals | total_prospecting"),
) -> List[dict]:
    """Lista managers com métricas agregadas dos vendedores sob gestão."""
    benchmarks = get_benchmarks()
    _, _, _, teams_df = get_raw_data()

    # Calcular métricas por seller
    seller_data = {}
    for _, row in teams_df.iterrows():
        seller = row["sales_agent"]
        seller_data[seller] = {
            "manager": row["manager"],
            "regional_office": row["regional_office"],
            "win_rate": benchmarks["seller_wr"].get(seller, 0),
            "active_deals": benchmarks["seller_active_deals"].get(seller, 0),
            "prospecting": benchmarks["seller_prospecting"].get(seller, 0),
            "avg_ticket": benchmarks["seller_avg_ticket"].get(seller, 0),
            "viability": _calc_viability(seller, benchmarks),
        }

    # Agrupar por manager
    from collections import defaultdict
    groups: dict = defaultdict(list)
    for seller, data in seller_data.items():
        groups[data["manager"]].append({**data, "seller": seller})

    results = []
    for manager, sellers in groups.items():
        avg_vb = sum(s["viability"] for s in sellers) / len(sellers)
        results.append({
            "manager": manager,
            "regional_office": sellers[0]["regional_office"],
            "n_sellers": len(sellers),
            "avg_win_rate": round(sum(s["win_rate"] for s in sellers) / len(sellers), 1),
            "total_active_deals": sum(s["active_deals"] for s in sellers),
            "total_prospecting": sum(s["prospecting"] for s in sellers),
            "avg_ticket": round(sum(s["avg_ticket"] for s in sellers) / len(sellers), 2),
            "avg_viability": round(avg_vb, 1),
            "viability_label": _viability_label(avg_vb),
        })

    if region:
        results = [r for r in results if r["regional_office"] == region]
    if viability:
        results = [r for r in results if r["viability_label"] == viability]

    sort_key = {
        "avg_viability": "avg_viability",
        "avg_win_rate": "avg_win_rate",
        "total_active_deals": "total_active_deals",
        "total_prospecting": "total_prospecting",
    }.get(sort_by, "avg_viability")

    results.sort(key=lambda x: x[sort_key], reverse=True)
    return results
