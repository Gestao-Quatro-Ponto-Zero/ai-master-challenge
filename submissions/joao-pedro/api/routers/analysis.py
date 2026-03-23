"""
Router: /analysis
"""

from collections import defaultdict
from typing import List, Literal, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from api.dependencies import get_benchmarks, get_pipeline_df
from core.data_loader import calculate_time_benchmarks
from core.pipeline_win_rate_buckets import compute_win_rate_by_pipeline_time_bucket
from core.scoring_engine import score_all_deals

router = APIRouter()


def _pipeline_for_scope(
    scope: Literal["geral", "squad"],
    manager: Optional[str],
):
    """Mesmo critério de filtro de GET /analysis/pipeline."""
    pipeline_df = get_pipeline_df()
    if scope == "squad":
        if not manager or not str(manager).strip():
            raise HTTPException(
                status_code=422,
                detail="Parâmetro 'manager' é obrigatório quando scope=squad",
            )
        pipeline_df = pipeline_df[pipeline_df["manager"] == manager]
    return pipeline_df


def _median_scalar_json(value) -> Optional[float]:
    """Converte mediana pandas para JSON (None se vazio/NaN)."""
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(v):
        return None
    return round(v, 2)


def _get_scored() -> List[dict]:
    benchmarks = get_benchmarks()
    pipeline_df = get_pipeline_df()
    deals = pipeline_df[pipeline_df["deal_stage"] == "Engaging"].to_dict("records")
    return score_all_deals(deals, benchmarks)


def _get_scored_for_scope(scope: Literal["geral", "squad"], manager: Optional[str]) -> List[dict]:
    benchmarks = get_benchmarks()
    pipeline_df = _pipeline_for_scope(scope, manager)
    deals = pipeline_df[pipeline_df["deal_stage"] == "Engaging"].to_dict("records")
    return score_all_deals(deals, benchmarks)


@router.get("/actions")
def action_distribution() -> dict:
    """Distribuição de ações recomendadas com breakdown por seller, produto e região."""
    scored = _get_scored()

    by_action: dict = defaultdict(int)
    by_seller: dict = defaultdict(lambda: defaultdict(int))
    by_product: dict = defaultdict(lambda: defaultdict(int))
    by_region: dict = defaultdict(lambda: defaultdict(int))

    for d in scored:
        action = d["action"]["type"]
        seller = d["deal_info"]["sales_agent"]
        product = d["deal_info"]["product"]
        region = d["deal_info"].get("regional_office", "N/A")

        by_action[action] += 1
        by_seller[seller][action] += 1
        by_product[product][action] += 1
        by_region[region][action] += 1

    total = len(scored)
    return {
        "total_deals": total,
        "distribution": {
            action: {"count": count, "pct": round(count / total * 100, 1)}
            for action, count in sorted(by_action.items(), key=lambda x: x[1], reverse=True)
        },
        "by_seller": {s: dict(actions) for s, actions in by_seller.items()},
        "by_product": {p: dict(actions) for p, actions in by_product.items()},
        "by_region": {r: dict(actions) for r, actions in by_region.items()},
    }


@router.get("/pipeline/time-medians")
def pipeline_time_medians(
    scope: Literal["geral", "squad"] = Query("geral"),
    manager: Optional[str] = Query(None, description="Obrigatório quando scope=squad"),
) -> dict:
    """
    Medianas de dias no pipeline (Won / Lost / Engaging) e ratio Engaging/Won,
    calculadas sobre o mesmo subconjunto que GET /analysis/pipeline (Geral ou Squad).
    """
    pipeline_df = _pipeline_for_scope(scope, manager)
    tb = calculate_time_benchmarks(pipeline_df, verbose=False)

    won_m = _median_scalar_json(tb["won_median"])
    lost_m = _median_scalar_json(tb["lost_median"])
    eng_m = _median_scalar_json(tb["engaging_median"])

    ratio = None
    if won_m is not None and won_m > 0 and eng_m is not None:
        ratio = round(eng_m / won_m, 2)

    return {
        "scope": scope,
        "manager": manager if scope == "squad" else None,
        "won_median_days": won_m,
        "lost_median_days": lost_m,
        "engaging_median_days": eng_m,
        "engaging_to_won_ratio": ratio,
        "cohort_counts": {
            "total": len(pipeline_df),
            "won": int((pipeline_df["deal_stage"] == "Won").sum()),
            "lost": int((pipeline_df["deal_stage"] == "Lost").sum()),
            "engaging": int((pipeline_df["deal_stage"] == "Engaging").sum()),
        },
    }


@router.get("/pipeline")
def pipeline_summary(
    scope: Literal["geral", "squad"] = Query("geral"),
    manager: Optional[str] = Query(None, description="Obrigatório quando scope=squad"),
) -> dict:
    """Distribuição de deals por estágio do funil (todos os estágios)."""
    pipeline_df = _pipeline_for_scope(scope, manager)
    total = len(pipeline_df)
    counts = pipeline_df["deal_stage"].value_counts().to_dict()
    stages = {}
    for stage in ["Prospecting", "Engaging", "Won", "Lost"]:
        count = int(counts.get(stage, 0))
        stages[stage] = {"count": count, "pct": round(count / total * 100, 1) if total else 0}
    return {"total_deals": total, "stages": stages}


@router.get("/pipeline/win-rate-by-time-bucket")
def pipeline_win_rate_by_time_bucket(
    scope: Literal["geral", "squad"] = Query("geral"),
    manager: Optional[str] = Query(None, description="Obrigatório quando scope=squad"),
) -> dict:
    """
    Win rate (%) por faixa de dias no pipeline para deals fechados (Won/Lost),
    no mesmo recorte que GET /analysis/pipeline.

    `benchmark_global_wr` é o win rate global da base (referência tipo Streamlit);
    `scoped_closed_win_rate` é o win rate entre todos os fechados do recorte atual.
    """
    pipeline_df = _pipeline_for_scope(scope, manager)
    out = compute_win_rate_by_pipeline_time_bucket(pipeline_df)
    b = get_benchmarks()
    benchmark_wr = b.get("global_wr")
    benchmark_global_wr = None
    if benchmark_wr is not None:
        try:
            bf = float(benchmark_wr)
        except (TypeError, ValueError):
            benchmark_global_wr = None
        else:
            benchmark_global_wr = None if pd.isna(bf) else round(bf, 2)

    return {
        "scope": scope,
        "manager": manager if scope == "squad" else None,
        "benchmark_global_wr": benchmark_global_wr,
        **out,
    }


@router.get("/transfers")
def transfer_recommendations() -> dict:
    """Deals que requerem transferência com destino recomendado."""
    scored = _get_scored()
    transfer_actions = {"TRANSFER", "CONSIDER_TRANSFER"}

    transfers = [
        {
            "opportunity_id": d["opportunity_id"],
            "sales_agent": d["deal_info"]["sales_agent"],
            "product": d["deal_info"]["product"],
            "account": d["deal_info"]["account"],
            "score": d["score"],
            "viability": d["viability"],
            "action": d["action"]["type"],
            "message": d["action"].get("message", ""),
            "details": d["action"].get("details", {}),
        }
        for d in scored
        if d["action"]["type"] in transfer_actions
    ]

    transfers.sort(key=lambda x: x["score"], reverse=True)

    return {
        "total_transfers": len(transfers),
        "deals": transfers,
    }


# =============================================================================
# REGIONAL ANALYSIS
# =============================================================================

def _build_regional_stats(scored: List[dict], benchmarks: dict) -> dict:
    """Agrupa deals scored por região e calcula métricas agregadas."""
    region_stats: dict = {}

    for d in scored:
        region = d["deal_info"].get("regional_office") or "Unknown"
        if region not in region_stats:
            region_stats[region] = {
                "scores": [],
                "viabilities": [],
                "sellers": set(),
                "actions": defaultdict(int),
            }
        region_stats[region]["scores"].append(d["score"])
        region_stats[region]["viabilities"].append(d["viability"])
        region_stats[region]["sellers"].add(d["deal_info"]["sales_agent"])
        region_stats[region]["actions"][d["action"]["type"]] += 1

    result = {}
    for region, stats in region_stats.items():
        if region == "Unknown":
            continue
        sellers = stats["sellers"]
        n_sellers = len(sellers)
        total_load = sum(benchmarks["seller_active_deals"].get(s, 0) for s in sellers)
        total_prosp = sum(benchmarks["seller_prospecting"].get(s, 0) for s in sellers)
        n_deals = len(stats["scores"])
        actions = dict(stats["actions"])

        result[region] = {
            "region": region,
            "deals_engaging": n_deals,
            "sellers_count": n_sellers,
            "avg_score": round(sum(stats["scores"]) / n_deals, 1),
            "avg_viability": round(sum(stats["viabilities"]) / n_deals, 1),
            "win_rate": round(benchmarks["region_wr"].get(region, 0), 1),
            "total_load": total_load,
            "avg_load_per_seller": round(total_load / n_sellers, 1) if n_sellers else 0,
            "total_prospecting": total_prosp,
            "avg_prospecting_per_seller": round(total_prosp / n_sellers, 1) if n_sellers else 0,
            "discard_pct": round(actions.get("DISCARD", 0) / n_deals * 100, 1) if n_deals else 0,
            "transfer_pct": round(
                (actions.get("TRANSFER", 0) + actions.get("CONSIDER_TRANSFER", 0)) / n_deals * 100, 1
            ) if n_deals else 0,
            "actions": actions,
        }

    return result


@router.get("/regional")
def regional_overview(
    scope: Literal["geral", "squad"] = Query("geral"),
    manager: Optional[str] = Query(None),
) -> dict:
    """
    Overview completo de todas as regiões: métricas, insights de performance,
    análise de carga e transferências inter-regionais.
    """
    scored = _get_scored_for_scope(scope, manager)
    benchmarks = get_benchmarks()
    global_wr = round(benchmarks["global_wr"], 1)

    region_stats = _build_regional_stats(scored, benchmarks)

    if not region_stats:
        return {"global_wr": global_wr, "regions": [], "insights": {}, "inter_regional_transfers": {}}

    regions_list = sorted(region_stats.values(), key=lambda r: r["deals_engaging"], reverse=True)

    # Insights: melhor e pior região por win rate
    sorted_by_wr = sorted(regions_list, key=lambda r: r["win_rate"])
    best = sorted_by_wr[-1]
    worst = sorted_by_wr[0]

    # Desbalanceamento de carga
    loads = [r["avg_load_per_seller"] for r in regions_list if r["avg_load_per_seller"] > 0]
    load_imbalance: dict = {"detected": False}
    if len(loads) >= 2:
        max_load = max(loads)
        min_load = min(loads)
        ratio = round(max_load / min_load, 1) if min_load > 0 else 0
        if ratio > 1.5:
            most_loaded = max(regions_list, key=lambda r: r["avg_load_per_seller"])
            least_loaded = min(regions_list, key=lambda r: r["avg_load_per_seller"])
            load_imbalance = {
                "detected": True,
                "ratio": ratio,
                "most_loaded": {"region": most_loaded["region"], "avg_load_per_seller": most_loaded["avg_load_per_seller"]},
                "least_loaded": {"region": least_loaded["region"], "avg_load_per_seller": least_loaded["avg_load_per_seller"]},
            }

    # Transferências inter-regionais
    transfer_actions = {"TRANSFER", "CONSIDER_TRANSFER"}
    transfer_deals = [d for d in scored if d["action"]["type"] in transfer_actions]
    inter_regional = [
        d for d in transfer_deals
        if d["action"].get("details", {}).get("transfer_level") == "other_region"
    ]
    total_transfers = len(transfer_deals)
    inter_count = len(inter_regional)

    return {
        "global_wr": global_wr,
        "regions": regions_list,
        "insights": {
            "best_region": {
                "region": best["region"],
                "win_rate": best["win_rate"],
                "avg_score": best["avg_score"],
                "avg_viability": best["avg_viability"],
                "sellers_count": best["sellers_count"],
            },
            "worst_region": {
                "region": worst["region"],
                "win_rate": worst["win_rate"],
                "avg_score": worst["avg_score"],
                "avg_viability": worst["avg_viability"],
                "sellers_count": worst["sellers_count"],
            },
            "load_imbalance": load_imbalance,
        },
        "inter_regional_transfers": {
            "total_transfers": total_transfers,
            "inter_regional_count": inter_count,
            "inter_regional_pct": round(inter_count / total_transfers * 100, 1) if total_transfers else 0,
        },
    }


@router.get("/regional/{region}")
def regional_detail(region: str) -> dict:
    """
    Drill-down de uma região específica: métricas resumidas + tabela de vendedores.
    """
    scored = _get_scored()
    benchmarks = get_benchmarks()

    region_deals = [d for d in scored if d["deal_info"].get("regional_office") == region]

    if not region_deals:
        raise HTTPException(status_code=404, detail=f"Região '{region}' não encontrada ou sem deals em Engaging.")

    sellers_set = set(d["deal_info"]["sales_agent"] for d in region_deals)
    n_deals = len(region_deals)

    # Métricas por vendedor dentro da região
    sellers_map: dict = {}
    for d in region_deals:
        seller = d["deal_info"]["sales_agent"]
        if seller not in sellers_map:
            sellers_map[seller] = {"scores": [], "viabilities": []}
        sellers_map[seller]["scores"].append(d["score"])
        sellers_map[seller]["viabilities"].append(d["viability"])

    sellers_list = []
    for seller, data in sellers_map.items():
        n = len(data["scores"])
        sellers_list.append({
            "sales_agent": seller,
            "deals_engaging": n,
            "avg_score": round(sum(data["scores"]) / n, 1),
            "avg_viability": round(sum(data["viabilities"]) / n, 1),
            "total_load": benchmarks["seller_active_deals"].get(seller, 0),
            "prospecting": benchmarks["seller_prospecting"].get(seller, 0),
            "win_rate": round(benchmarks["seller_wr"].get(seller, 0), 1),
        })

    sellers_list.sort(key=lambda s: s["deals_engaging"], reverse=True)

    return {
        "region": region,
        "deals_engaging": n_deals,
        "sellers_count": len(sellers_set),
        "avg_score": round(sum(d["score"] for d in region_deals) / n_deals, 1),
        "avg_viability": round(sum(d["viability"] for d in region_deals) / n_deals, 1),
        "sellers": sellers_list,
    }


# =============================================================================
# PRODUCTS ANALYSIS
# =============================================================================

def _build_product_stats(scored: List[dict], pipeline_df: pd.DataFrame, benchmarks: dict) -> dict:
    """Agrupa deals scored por produto e calcula métricas agregadas."""
    # Ciclo médio histórico dos deals Won por produto
    won_df = pipeline_df[pipeline_df["deal_stage"] == "Won"]
    won_cycle = won_df.groupby("product")["days_in_pipeline"].mean().to_dict()

    product_stats: dict = {}
    for d in scored:
        product = d["deal_info"]["product"]
        if product not in product_stats:
            product_stats[product] = {
                "scores": [],
                "days": [],
                "values": [],
                "actions": defaultdict(int),
            }
        product_stats[product]["scores"].append(d["score"])
        product_stats[product]["days"].append(d["deal_info"]["days_in_pipeline"])
        product_stats[product]["values"].append(d["deal_info"]["close_value"])
        product_stats[product]["actions"][d["action"]["type"]] += 1

    result = {}
    for product, stats in product_stats.items():
        n = len(stats["scores"])
        actions = dict(stats["actions"])
        avg_days_won = round(won_cycle.get(product, 0), 1)
        avg_days_eng = round(sum(stats["days"]) / n, 1) if n else 0
        cycle_ratio = round(avg_days_eng / avg_days_won, 2) if avg_days_won > 0 else None

        result[product] = {
            "product": product,
            "deals_engaging": n,
            "avg_score": round(sum(stats["scores"]) / n, 1),
            "win_rate": round(benchmarks["product_wr"].get(product, 0), 1),
            "avg_ticket": round(sum(stats["values"]) / n, 2) if n else 0,
            "avg_days_engaging": avg_days_eng,
            "avg_cycle_days_won": avg_days_won,
            "cycle_ratio": cycle_ratio,
            "discard_pct": round(actions.get("DISCARD", 0) / n * 100, 1) if n else 0,
            "transfer_pct": round(
                (actions.get("TRANSFER", 0) + actions.get("CONSIDER_TRANSFER", 0)) / n * 100, 1
            ) if n else 0,
            "actions": actions,
        }

    return result


@router.get("/products")
def products_overview(
    scope: Literal["geral", "squad"] = Query("geral"),
    manager: Optional[str] = Query(None),
) -> dict:
    """
    Overview completo de todos os produtos: métricas, insights de performance,
    ciclo de tempo, produto mais travado e especialistas por produto.
    """
    scored = _get_scored_for_scope(scope, manager)
    benchmarks = get_benchmarks()
    pipeline_df = _pipeline_for_scope(scope, manager)
    global_wr = round(benchmarks["global_wr"], 1)

    product_stats = _build_product_stats(scored, pipeline_df, benchmarks)

    if not product_stats:
        return {"global_wr": global_wr, "products": [], "insights": {}, "specialists": []}

    products_list = sorted(product_stats.values(), key=lambda p: p["deals_engaging"], reverse=True)

    # Insights: melhor e pior por win rate
    sorted_by_wr = sorted(products_list, key=lambda p: p["win_rate"])
    best = sorted_by_wr[-1]
    worst = sorted_by_wr[0]

    # Produto mais travado (maior cycle_ratio)
    stuck_candidates = [p for p in products_list if p["cycle_ratio"] is not None]
    most_stuck = max(stuck_candidates, key=lambda p: p["cycle_ratio"]) if stuck_candidates else None

    # Produto com maior DISCARD %
    most_discard = max(products_list, key=lambda p: p["discard_pct"])
    high_discard_warning = (
        {"product": most_discard["product"], "discard_pct": most_discard["discard_pct"]}
        if most_discard["discard_pct"] > 30 else None
    )

    # Especialistas: vendedor com WR no produto >= seller_avg + 5 pts
    specialists = []
    for combo_key, combo_wr in benchmarks["product_seller_wr"].items():
        product, seller = combo_key.split("|")
        seller_avg = benchmarks["seller_wr"].get(seller, benchmarks["global_wr"])
        delta = combo_wr - seller_avg
        if delta > 5:
            specialists.append({
                "product": product,
                "sales_agent": seller,
                "combo_wr": round(combo_wr, 1),
                "seller_avg_wr": round(seller_avg, 1),
                "delta": round(delta, 1),
            })

    specialists.sort(key=lambda s: s["delta"], reverse=True)

    return {
        "global_wr": global_wr,
        "products": products_list,
        "insights": {
            "best_product": {
                "product": best["product"],
                "win_rate": best["win_rate"],
                "avg_ticket": best["avg_ticket"],
                "deals_engaging": best["deals_engaging"],
            },
            "worst_product": {
                "product": worst["product"],
                "win_rate": worst["win_rate"],
                "avg_ticket": worst["avg_ticket"],
                "deals_engaging": worst["deals_engaging"],
            },
            "most_stuck": {
                "product": most_stuck["product"],
                "avg_days_engaging": most_stuck["avg_days_engaging"],
                "avg_cycle_days_won": most_stuck["avg_cycle_days_won"],
                "ratio": most_stuck["cycle_ratio"],
            } if most_stuck else None,
            "high_discard_warning": high_discard_warning,
        },
        "specialists": specialists,
    }


@router.get("/products/{product}")
def product_detail(product: str) -> dict:
    """
    Drill-down de um produto específico: métricas resumidas + lista de deals em Engaging.
    """
    scored = _get_scored()
    benchmarks = get_benchmarks()

    product_deals = [d for d in scored if d["deal_info"]["product"] == product]

    if not product_deals:
        raise HTTPException(status_code=404, detail=f"Produto '{product}' não encontrado ou sem deals em Engaging.")

    n = len(product_deals)
    product_wr = round(benchmarks["product_wr"].get(product, 0), 1)
    global_wr = round(benchmarks["global_wr"], 1)

    deals_list = [
        {
            "opportunity_id": d["opportunity_id"],
            "label": f"{d['deal_info']['product']} @ {d['deal_info']['account']} ({int(d['deal_info']['days_in_pipeline'])}d)",
            "score": round(d["score"], 1),
            "sales_agent": d["deal_info"]["sales_agent"],
            "days_in_pipeline": int(d["deal_info"]["days_in_pipeline"]),
            "close_value": round(d["deal_info"]["close_value"], 2),
            "action": d["action"]["type"],
        }
        for d in product_deals
    ]
    deals_list.sort(key=lambda d: d["score"], reverse=True)

    return {
        "product": product,
        "deals_engaging": n,
        "avg_score": round(sum(d["score"] for d in product_deals) / n, 1),
        "win_rate": product_wr,
        "delta_vs_global": round(product_wr - global_wr, 1),
        "avg_ticket": round(sum(d["deal_info"]["close_value"] for d in product_deals) / n, 2),
        "deals": deals_list,
    }


# =============================================================================
# SELLER WON VALUE OVER TIME
# =============================================================================

@router.get("/sellers/won-value-over-time")
def won_value_over_time(
    sales_agent: str = Query(..., description="Nome do vendedor"),
) -> dict:
    """
    Retorna série temporal de valor convertido (Won) por dia para um vendedor.
    Cada ponto: { date: 'YYYY-MM-DD', value: float, count: int }
    """
    pipeline_df = get_pipeline_df()

    won = pipeline_df[
        (pipeline_df["deal_stage"] == "Won") &
        (pipeline_df["sales_agent"] == sales_agent) &
        pipeline_df["close_date"].notna() &
        pipeline_df["close_value"].notna()
    ].copy()

    if won.empty:
        return {"sales_agent": sales_agent, "date_range": None, "points": []}

    won["close_date"] = pd.to_datetime(won["close_date"])

    grouped = (
        won.groupby(won["close_date"].dt.date)
        .agg(value=("close_value", "sum"), count=("close_value", "count"))
        .reset_index()
        .rename(columns={"close_date": "date"})
        .sort_values("date")
    )

    points = [
        {
            "date": str(row["date"]),
            "value": round(float(row["value"]), 2),
            "count": int(row["count"]),
        }
        for _, row in grouped.iterrows()
    ]

    return {
        "sales_agent": sales_agent,
        "date_range": {
            "min": str(grouped["date"].min()),
            "max": str(grouped["date"].max()),
        },
        "points": points,
    }


# =============================================================================
# ALERTS
# =============================================================================

def _build_alert(key: str, severity: str, triggered: bool, title: str, message: str, data: dict) -> dict:
    return {
        "key": key,
        "severity": severity,
        "triggered": triggered,
        "title": title,
        "message": message,
        "data": data,
    }


def _manager_view_alerts_payload(
    scored: List[dict],
    pipeline_df: pd.DataFrame,
    benchmarks: dict,
    *,
    scope: Literal["geral", "squad"],
    manager: Optional[str],
) -> dict:
    """
    Mesmas regras de alertas da Manager view, sobre scored + pipeline já filtrados ao escopo.
    scope=squad + manager restringe métricas de prospecção aos vendedores do manager.
    """
    total = len(scored)
    alerts = []

    # ------------------------------------------------------------------
    # ACTION ANALYSIS
    # ------------------------------------------------------------------
    action_counts: dict = defaultdict(int)
    for d in scored:
        action_counts[d["action"]["type"]] += 1

    discard_count = action_counts.get("DISCARD", 0)
    discard_pct = round(discard_count / total * 100, 1) if total else 0

    transfer_count = action_counts.get("TRANSFER", 0) + action_counts.get("CONSIDER_TRANSFER", 0)
    transfer_pct = round(transfer_count / total * 100, 1) if total else 0

    push_count = action_counts.get("PUSH_HARD", 0) + action_counts.get("ACCELERATE", 0)
    push_pct = round(push_count / total * 100, 1) if total else 0

    alerts.append(_build_alert(
        key="action_high_discard",
        severity="error",
        triggered=discard_pct > 25,
        title="Alta taxa de DISCARD",
        message=f"{discard_pct}% dos deals devem ser descartados (threshold: >25%).",
        data={"discard_count": discard_count, "discard_pct": discard_pct, "threshold": 25},
    ))

    alerts.append(_build_alert(
        key="action_high_transfer",
        severity="warning",
        triggered=transfer_pct > 20,
        title="Alta taxa de TRANSFERÊNCIA",
        message=f"{transfer_pct}% dos deals precisam de transferência (threshold: >20%).",
        data={"transfer_count": transfer_count, "transfer_pct": transfer_pct, "threshold": 20},
    ))

    alerts.append(_build_alert(
        key="action_low_push",
        severity="info",
        triggered=push_pct < 10,
        title="Baixa taxa de ação imediata",
        message=f"Apenas {push_pct}% dos deals têm ação imediata PUSH_HARD/ACCELERATE (threshold: <10%).",
        data={"push_count": push_count, "push_pct": push_pct, "threshold": 10},
    ))

    # ------------------------------------------------------------------
    # DEALS / PIPELINE ANALYSIS
    # ------------------------------------------------------------------
    tb = calculate_time_benchmarks(pipeline_df, verbose=False)
    won_median = _median_scalar_json(tb["won_median"]) or 0
    engaging_median = _median_scalar_json(tb["engaging_median"]) or 0
    engaging_ratio = round(engaging_median / won_median, 1) if won_median > 0 else None

    scope_label = "do squad" if scope == "squad" else "da empresa"
    alerts.append(_build_alert(
        key="pipeline_ratio",
        severity="error",
        triggered=True,
        title="Pipeline Engaging acima da mediana Won",
        message=(
            f"Pipeline Engaging ({scope_label}) está {engaging_ratio}× acima da mediana dos deals ganhos."
            if engaging_ratio is not None
            else f"Mediana Engaging/Won indisponível {scope_label} (sem dados suficientes)."
        ),
        data={
            "engaging_median_days": engaging_median,
            "won_median_days": won_median,
            "ratio": engaging_ratio,
        },
    ))

    seller_prosp = benchmarks.get("seller_prospecting", {})
    seller_active = benchmarks.get("seller_active_deals", {})
    if scope == "squad" and manager and str(manager).strip():
        full_df = get_pipeline_df()
        squad_sellers = full_df[full_df["manager"] == manager]["sales_agent"].dropna().unique().tolist()
        sellers_total = len(squad_sellers)
        sellers_no_prosp = sum(1 for s in squad_sellers if seller_prosp.get(s, 0) == 0)
    else:
        sellers_total = len(seller_prosp)
        sellers_no_prosp = sum(1 for v in seller_prosp.values() if v == 0)
    pct_no_prosp = round(sellers_no_prosp / sellers_total * 100, 1) if sellers_total else 0

    prosp_title = (
        "Maioria dos vendedores do squad sem prospecção ativa"
        if scope == "squad"
        else "Maioria dos vendedores sem prospecção ativa"
    )
    alerts.append(_build_alert(
        key="pipeline_no_prospecting",
        severity="warning",
        triggered=pct_no_prosp > 50 and sellers_total > 0,
        title=prosp_title,
        message=f"{pct_no_prosp}% dos vendedores no escopo estão sem prospecting (threshold: >50%).",
        data={
            "sellers_no_prospecting": sellers_no_prosp,
            "sellers_total": sellers_total,
            "pct_no_prospecting": pct_no_prosp,
            "threshold": 50,
        },
    ))

    # ------------------------------------------------------------------
    # REGIONAL ANALYSIS
    # ------------------------------------------------------------------
    region_stats: dict = {}
    for d in scored:
        region = d["deal_info"].get("regional_office") or "Unknown"
        if region == "Unknown":
            continue
        if region not in region_stats:
            region_stats[region] = {"sellers": set(), "active_total": 0}
        region_stats[region]["sellers"].add(d["deal_info"]["sales_agent"])

    for region, stats in region_stats.items():
        for seller in stats["sellers"]:
            stats["active_total"] += seller_active.get(seller, 0)

    region_avg_loads = {
        r: round(s["active_total"] / len(s["sellers"]), 1)
        for r, s in region_stats.items() if s["sellers"]
    }

    if len(region_avg_loads) >= 2:
        max_load_region = max(region_avg_loads, key=region_avg_loads.get)
        min_load_region = min(region_avg_loads, key=region_avg_loads.get)
        max_load = region_avg_loads[max_load_region]
        min_load = region_avg_loads[min_load_region]
        load_ratio = round(max_load / min_load, 1) if min_load > 0 else 0
    else:
        max_load_region = min_load_region = None
        max_load = min_load = load_ratio = 0

    if len(region_avg_loads) >= 2:
        reg_msg = (
            f"Região mais carregada ({max_load_region}: {max_load:.0f} deals/vendedor) está "
            f"{load_ratio}× acima da menos carregada ({min_load_region}: {min_load:.0f}) (threshold: >1.5×)."
        )
    else:
        reg_msg = (
            "São necessárias pelo menos 2 regiões com deals Engaging no escopo para comparar carga."
            if scope == "squad"
            else "São necessárias pelo menos 2 regiões com deals Engaging para comparar carga."
        )

    alerts.append(_build_alert(
        key="regional_load_imbalance",
        severity="warning",
        triggered=len(region_avg_loads) >= 2 and load_ratio > 1.5,
        title="Desbalanceamento de carga entre regiões",
        message=reg_msg,
        data={
            "load_ratio": load_ratio,
            "most_loaded_region": max_load_region,
            "most_loaded_avg": max_load,
            "least_loaded_region": min_load_region,
            "least_loaded_avg": min_load,
            "threshold": 1.5,
        },
    ))

    transfer_deals = [d for d in scored if d["action"]["type"] in {"TRANSFER", "CONSIDER_TRANSFER"}]
    inter_regional = [
        d for d in transfer_deals
        if d["action"].get("details", {}).get("transfer_level") == "other_region"
    ]
    total_transfers = len(transfer_deals)
    inter_count = len(inter_regional)
    inter_pct = round(inter_count / total_transfers * 100, 1) if total_transfers else 0

    alerts.append(_build_alert(
        key="regional_inter_transfers",
        severity="info",
        triggered=inter_count > 0,
        title="Transferências inter-regionais detectadas",
        message=f"{inter_pct}% das transferências ({inter_count}/{total_transfers}) são inter-regionais.",
        data={
            "inter_regional_count": inter_count,
            "total_transfers": total_transfers,
            "inter_regional_pct": inter_pct,
        },
    ))

    # ------------------------------------------------------------------
    # PRODUCTS ANALYSIS
    # ------------------------------------------------------------------
    product_stats: dict = {}
    for d in scored:
        product = d["deal_info"]["product"]
        if product not in product_stats:
            product_stats[product] = {"scores": [], "days": [], "actions": defaultdict(int)}
        product_stats[product]["scores"].append(d["score"])
        product_stats[product]["days"].append(d["deal_info"]["days_in_pipeline"])
        product_stats[product]["actions"][d["action"]["type"]] += 1

    won_df = pipeline_df[pipeline_df["deal_stage"] == "Won"]
    won_cycle = won_df.groupby("product")["days_in_pipeline"].mean().to_dict()

    product_ratios = {}
    product_discard_pcts = {}
    for product, stats in product_stats.items():
        n = len(stats["scores"])
        avg_days_eng = sum(stats["days"]) / n if n else 0
        avg_days_won = won_cycle.get(product, 0)
        if avg_days_won > 0:
            product_ratios[product] = round(avg_days_eng / avg_days_won, 2)
        discard_n = stats["actions"].get("DISCARD", 0)
        product_discard_pcts[product] = round(discard_n / n * 100, 1) if n else 0

    most_stuck_product = max(product_ratios, key=product_ratios.get) if product_ratios else None
    most_stuck_ratio = product_ratios[most_stuck_product] if most_stuck_product else None

    alerts.append(_build_alert(
        key="product_most_stuck",
        severity="warning",
        triggered=True,
        title="Produto mais travado no pipeline",
        message=(
            f"{most_stuck_product} está {most_stuck_ratio}× acima do ciclo histórico de deals Won."
            if most_stuck_product else "Nenhum produto com ciclo Won disponível para comparação."
        ),
        data={
            "product": most_stuck_product,
            "engaging_vs_won_ratio": most_stuck_ratio,
            "avg_days_engaging": round(sum(product_stats[most_stuck_product]["days"]) / len(product_stats[most_stuck_product]["days"]), 1) if most_stuck_product else None,
            "avg_days_won": round(won_cycle.get(most_stuck_product, 0), 1) if most_stuck_product else None,
        },
    ))

    high_discard_product = max(product_discard_pcts, key=product_discard_pcts.get) if product_discard_pcts else None
    high_discard_pct = product_discard_pcts[high_discard_product] if high_discard_product else 0

    alerts.append(_build_alert(
        key="product_high_discard",
        severity="error",
        triggered=high_discard_pct > 30,
        title="Produto com alta taxa de DISCARD",
        message=f"{high_discard_product} tem {high_discard_pct}% de DISCARD (threshold: >30%).",
        data={
            "product": high_discard_product,
            "discard_pct": high_discard_pct,
            "threshold": 30,
        },
    ))

    # ------------------------------------------------------------------
    # TRANSFER ANALYSIS
    # ------------------------------------------------------------------
    hierarchy_counts: dict = defaultdict(int)
    for d in transfer_deals:
        level = d["action"].get("details", {}).get("transfer_level", "unknown")
        hierarchy_counts[level] += 1

    same_team = hierarchy_counts.get("same_team", 0)
    other_region = hierarchy_counts.get("other_region", 0)
    well_allocated = same_team > other_region if total_transfers else False

    if total_transfers == 0:
        xfer_msg = "Nenhum deal Engaging com recomendação de transferência neste escopo."
        xfer_severity = "info"
        xfer_triggered = False
    elif well_allocated:
        xfer_msg = (
            f"{same_team} transfers ({round(same_team / total_transfers * 100, 1)}%) "
            f"podem ser resolvidos no mesmo time."
        )
        xfer_severity = "success"
        xfer_triggered = True
    else:
        xfer_msg = (
            f"Maioria dos transfers ({other_region}) precisa ir para outras regiões — possível desbalanceamento de carga."
        )
        xfer_severity = "warning"
        xfer_triggered = True

    alerts.append(_build_alert(
        key="transfer_hierarchy_balance",
        severity=xfer_severity,
        triggered=xfer_triggered,
        title="Distribuição hierárquica de transferências",
        message=xfer_msg,
        data={
            "same_team": same_team,
            "same_region": hierarchy_counts.get("same_region", 0),
            "other_region": other_region,
            "escalate": hierarchy_counts.get("escalate", 0),
            "well_allocated": well_allocated if total_transfers else None,
        },
    ))

    triggered_count = sum(1 for a in alerts if a["triggered"])

    return {
        "scope": scope,
        "total_alerts": len(alerts),
        "triggered_count": triggered_count,
        "alerts": alerts,
    }


@router.get("/alerts")
def global_alerts(
    manager: Optional[str] = Query(
        None,
        description="Quando informado, inclui o bloco 'squad' com os mesmos alertas filtrados ao manager.",
    ),
) -> dict:
    """
    Avisos consolidados da Manager view.

    Retorna sempre `geral` (toda a empresa). Se `manager` for passado, também retorna `squad`
    para os deals/vendedores desse manager (mesmo critério de escopo de GET /analysis/pipeline).
    """
    benchmarks = get_benchmarks()
    geral = _manager_view_alerts_payload(
        _get_scored(),
        get_pipeline_df(),
        benchmarks,
        scope="geral",
        manager=None,
    )

    squad_payload = None
    m = (manager or "").strip()
    if m:
        pipeline_sq = _pipeline_for_scope("squad", m)
        scored_sq = _get_scored_for_scope("squad", m)
        squad_payload = _manager_view_alerts_payload(
            scored_sq,
            pipeline_sq,
            benchmarks,
            scope="squad",
            manager=m,
        )
        squad_payload["manager"] = m

    return {"geral": geral, "squad": squad_payload}


@router.get("/alerts/seller/{sales_agent}")
def seller_alerts(sales_agent: str) -> dict:
    """
    Avisos contextuais para um vendedor específico (drill-down da Seller_Analysis).
    Inclui: prospecting, sobrecarga e taxa de DISCARD.
    """
    benchmarks = get_benchmarks()
    pipeline_df = get_pipeline_df()
    deals = pipeline_df[pipeline_df["deal_stage"] == "Engaging"].to_dict("records")
    scored = score_all_deals(deals, benchmarks)

    seller_deals = [d for d in scored if d["deal_info"]["sales_agent"] == sales_agent]

    if not seller_deals:
        raise HTTPException(
            status_code=404,
            detail=f"Vendedor '{sales_agent}' não encontrado ou sem deals em Engaging.",
        )

    prosp = benchmarks["seller_prospecting"].get(sales_agent, 0)
    active = benchmarks["seller_active_deals"].get(sales_agent, 0)
    total = len(seller_deals)

    action_counts: dict = defaultdict(int)
    for d in seller_deals:
        action_counts[d["action"]["type"]] += 1

    discard_count = action_counts.get("DISCARD", 0)
    discard_pct = round(discard_count / total * 100, 1) if total else 0

    alerts = []

    alerts.append(_build_alert(
        key="seller_no_prospecting",
        severity="warning",
        triggered=prosp == 0,
        title="Vendedor sem prospecção ativa",
        message=f"{sales_agent} não tem prospecting — indica proteção de deals e reduz viabilidade.",
        data={"sales_agent": sales_agent, "prospecting": prosp},
    ))

    alerts.append(_build_alert(
        key="seller_overloaded_critical",
        severity="error",
        triggered=active > 150,
        title="Vendedor criticamente sobrecarregado",
        message=f"{sales_agent} tem {active} deals ativos (threshold crítico: >150).",
        data={"sales_agent": sales_agent, "active_deals": active, "threshold": 150},
    ))

    alerts.append(_build_alert(
        key="seller_overloaded_warning",
        severity="warning",
        triggered=100 < active <= 150,
        title="Vendedor com alta carga",
        message=f"{sales_agent} tem {active} deals ativos (threshold: >100).",
        data={"sales_agent": sales_agent, "active_deals": active, "threshold": 100},
    ))

    alerts.append(_build_alert(
        key="seller_high_discard",
        severity="info",
        triggered=discard_pct > 30,
        title="Alto percentual de DISCARD",
        message=f"{discard_count} deals ({discard_pct}%) de {sales_agent} devem ser descartados (threshold: >30%).",
        data={
            "sales_agent": sales_agent,
            "discard_count": discard_count,
            "discard_pct": discard_pct,
            "total_deals": total,
            "threshold": 30,
        },
    ))

    triggered_count = sum(1 for a in alerts if a["triggered"])

    return {
        "sales_agent": sales_agent,
        "total_alerts": len(alerts),
        "triggered_count": triggered_count,
        "alerts": alerts,
    }
