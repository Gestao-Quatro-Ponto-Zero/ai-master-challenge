from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd


REFERENCE_DATE = pd.Timestamp("2017-12-31")
PRODUCT_NORMALIZATION = {"GTXPro": "GTX Pro"}
FORECAST_BANDS = (
    ("Strong", 0.50),
    ("Workable", 0.35),
    ("Rescue", 0.20),
)


@dataclass(frozen=True)
class ContextWeights:
    account: float
    product: float
    sector: float
    revenue_band: float


FIT_WEIGHTS_WITH_ACCOUNT = ContextWeights(account=0.45, product=0.30, sector=0.15, revenue_band=0.10)
FIT_WEIGHTS_NO_ACCOUNT = ContextWeights(account=0.00, product=0.45, sector=0.35, revenue_band=0.20)


def load_dashboard_data(data_dir: str | Path) -> Dict[str, object]:
    data_path = Path(data_dir)

    accounts = pd.read_csv(data_path / "accounts.csv")
    products = pd.read_csv(data_path / "products.csv")
    sales_teams = pd.read_csv(data_path / "sales_teams.csv")
    pipeline = pd.read_csv(data_path / "sales_pipeline.csv")

    products["product"] = products["product"].replace(PRODUCT_NORMALIZATION)
    pipeline["product"] = pipeline["product"].replace(PRODUCT_NORMALIZATION)
    products["family"] = products["product"].str.extract(r"^(GTK|GTX|MG)")

    pipeline["engage_date"] = pd.to_datetime(pipeline["engage_date"], errors="coerce")
    pipeline["close_date"] = pd.to_datetime(pipeline["close_date"], errors="coerce")
    pipeline["is_closed"] = pipeline["deal_stage"].isin(["Won", "Lost"])
    pipeline["is_won"] = (pipeline["deal_stage"] == "Won").astype(int)
    pipeline["cycle_days"] = (pipeline["close_date"] - pipeline["engage_date"]).dt.days
    pipeline["age_open_days"] = (REFERENCE_DATE - pipeline["engage_date"]).dt.days

    merged = (
        pipeline.merge(accounts, on="account", how="left")
        .merge(products[["product", "series", "sales_price", "family"]], on="product", how="left")
        .merge(sales_teams, on="sales_agent", how="left")
    )

    merged["family"] = merged["family"].fillna(merged["product"].str.extract(r"^(GTK|GTX|MG)")[0])
    merged["revenue_band"] = pd.cut(
        merged["revenue"],
        bins=[-np.inf, 250, 500, 1000, 2000, np.inf],
        labels=["<=250", "251-500", "501-1000", "1001-2000", "2000+"],
    )

    closed = merged[merged["is_closed"]].copy()
    won = closed[closed["is_won"] == 1].copy()
    open_deals = merged[~merged["is_closed"]].copy()
    overall_win_rate = float(closed["is_won"].mean())

    product_stats = closed.groupby("product")["is_won"].agg(["sum", "count"])
    sector_stats = closed.dropna(subset=["sector"]).groupby("sector")["is_won"].agg(["sum", "count"])
    revenue_band_stats = (
        closed.dropna(subset=["revenue_band"])
        .groupby("revenue_band", observed=False)["is_won"]
        .agg(["sum", "count"])
    )
    account_stats = closed.dropna(subset=["account"]).groupby("account").agg(
        wins=("is_won", "sum"),
        count=("opportunity_id", "count"),
        win_rate=("is_won", "mean"),
    )

    product_ticket = won.groupby("product")["close_value"].median()
    account_ticket = won.dropna(subset=["account"]).groupby("account").agg(
        won_count=("opportunity_id", "count"),
        median_ticket=("close_value", "median"),
    )
    product_cycle = won.groupby("product")["cycle_days"].quantile([0.5, 0.75, 0.9]).unstack()
    product_cycle.columns = ["p50", "p75", "p90"]

    context_lifts = {
        "account": build_context_lifts(closed, "account", prior=8, min_n=8),
        "product": build_context_lifts(closed, "product", prior=15, min_n=18),
        "sector": build_context_lifts(closed, "sector", prior=15, min_n=18),
        "revenue_band": build_context_lifts(closed, "revenue_band", prior=12, min_n=18),
    }
    seller_base = build_seller_base_lifts(closed, overall_win_rate)
    seller_performance = build_seller_performance(closed, overall_win_rate, sales_teams["sales_agent"].dropna().unique())

    open_scored = score_open_deals(
        open_deals=open_deals,
        overall_win_rate=overall_win_rate,
        product_stats=product_stats,
        sector_stats=sector_stats,
        revenue_band_stats=revenue_band_stats,
        account_stats=account_stats,
        product_ticket=product_ticket,
        account_ticket=account_ticket,
        product_cycle=product_cycle,
        context_lifts=context_lifts,
        seller_base=seller_base,
        seller_performance=seller_performance,
        sellers=sales_teams["sales_agent"].dropna().unique(),
    )

    seller_summary = build_seller_summary(open_scored, context_lifts, seller_performance)
    head_summary = build_head_summary(open_scored, seller_summary)

    return {
        "open_deals": open_scored,
        "closed_deals": closed,
        "seller_summary": seller_summary,
        "head_summary": head_summary,
        "context_lifts": context_lifts,
        "overall_win_rate": overall_win_rate,
    }


def build_context_lifts(
    closed: pd.DataFrame,
    context_col: str,
    prior: int,
    min_n: int,
) -> pd.DataFrame:
    df = closed.dropna(subset=[context_col]).copy()
    context_base = df.groupby(context_col, observed=False)["is_won"].agg(["sum", "count"])
    context_base["baseline"] = context_base["sum"] / context_base["count"]

    pair = df.groupby(["sales_agent", context_col], observed=False)["is_won"].agg(["sum", "count"])
    out = pair.join(context_base[["baseline"]], on=context_col)
    out["support"] = out["count"].astype(int)
    out["smoothed_rate"] = (out["sum"] + prior * out["baseline"]) / (out["count"] + prior)
    out["lift"] = out["smoothed_rate"] - out["baseline"]
    out = out[out["support"] >= min_n].copy()
    return out.reset_index().sort_values(["lift", "support"], ascending=[False, False])


def build_seller_base_lifts(closed: pd.DataFrame, overall_win_rate: float) -> pd.DataFrame:
    seller = closed.groupby("sales_agent")["is_won"].agg(["sum", "count"]).reset_index()
    seller["smoothed_rate"] = (seller["sum"] + 25 * overall_win_rate) / (seller["count"] + 25)
    seller["lift"] = seller["smoothed_rate"] - overall_win_rate
    return seller[["sales_agent", "lift", "count"]].rename(columns={"count": "support"})


def build_seller_performance(
    closed: pd.DataFrame,
    overall_win_rate: float,
    sellers: Iterable[str],
) -> pd.DataFrame:
    performance = closed.groupby("sales_agent").agg(
        closed_deals=("opportunity_id", "count"),
        wins=("is_won", "sum"),
        seller_win_rate=("is_won", "mean"),
    )
    performance = performance.reindex(pd.Index(sorted(set(sellers)), name="sales_agent")).fillna(0).reset_index()
    performance["performance_gap_pp"] = (performance["seller_win_rate"] - overall_win_rate) * 100
    performance["performance_vs_avg_pct"] = np.where(
        overall_win_rate > 0,
        ((performance["seller_win_rate"] - overall_win_rate) / overall_win_rate) * 100,
        0,
    )
    performance["yellow_flag"] = (
        (performance["closed_deals"] >= 100)
        & (performance["performance_gap_pp"] <= -4.0)
    )
    return performance


def smooth_rate(
    stats_df: pd.DataFrame,
    key: object,
    overall_win_rate: float,
    win_col: str = "sum",
    count_col: str = "count",
    prior: int = 15,
) -> Tuple[float, int]:
    if key is None or (isinstance(key, float) and pd.isna(key)) or key not in stats_df.index:
        return overall_win_rate, 0

    row = stats_df.loc[key]
    wins = float(row[win_col])
    count = float(row[count_col])
    rate = (wins + prior * overall_win_rate) / (count + prior)
    return rate, int(count)


def score_open_deals(
    open_deals: pd.DataFrame,
    overall_win_rate: float,
    product_stats: pd.DataFrame,
    sector_stats: pd.DataFrame,
    revenue_band_stats: pd.DataFrame,
    account_stats: pd.DataFrame,
    product_ticket: pd.Series,
    account_ticket: pd.DataFrame,
    product_cycle: pd.DataFrame,
    context_lifts: Dict[str, pd.DataFrame],
    seller_base: pd.DataFrame,
    seller_performance: pd.DataFrame,
    sellers: Iterable[str],
) -> pd.DataFrame:
    account_lookup = to_context_lookup(context_lifts["account"], "account")
    product_lookup = to_context_lookup(context_lifts["product"], "product")
    sector_lookup = to_context_lookup(context_lifts["sector"], "sector")
    revenue_band_lookup = to_context_lookup(context_lifts["revenue_band"], "revenue_band")
    seller_base_lookup = {row["sales_agent"]: float(row["lift"]) for _, row in seller_base.iterrows()}
    performance_lookup = seller_performance.set_index("sales_agent").to_dict("index")

    open_rows: List[Dict[str, object]] = []
    for _, deal in open_deals.iterrows():
        account_rate, account_n = smooth_rate(account_stats, deal["account"], overall_win_rate, "wins", "count", prior=20)
        product_rate, _ = smooth_rate(product_stats, deal["product"], overall_win_rate, prior=15)
        sector_rate, _ = smooth_rate(sector_stats, deal["sector"], overall_win_rate, prior=15)
        revenue_band_rate, _ = smooth_rate(revenue_band_stats, deal["revenue_band"], overall_win_rate, prior=15)

        components: List[float] = []
        weights: List[float] = []
        if pd.notna(deal["account"]) and account_n >= 20:
            components.append(account_rate)
            weights.append(0.35)
        components.append(product_rate)
        weights.append(0.30)
        if pd.notna(deal["sector"]):
            components.append(sector_rate)
            weights.append(0.20)
        if pd.notna(deal["revenue_band"]):
            components.append(revenue_band_rate)
            weights.append(0.15)

        base_probability = float(np.average(components, weights=weights))
        age_factor, age_ratio = compute_age_factor(deal, product_cycle)
        data_factor = 1.0
        missing_fields = []
        if pd.isna(deal["account"]):
            data_factor *= 0.75
            missing_fields.append("conta")
        if pd.isna(deal["engage_date"]):
            data_factor *= 0.85
            missing_fields.append("data de engajamento")
        if deal["deal_stage"] == "Prospecting":
            data_factor *= 0.80

        deal_probability = float(np.clip(base_probability * age_factor * data_factor, 0.05, 0.90))
        ticket_proxy = compute_ticket_proxy(deal, product_ticket, account_ticket)
        expected_value_proxy = deal_probability * ticket_proxy

        scored_sellers = []
        for seller in sellers:
            fit_components: List[Tuple[str, float]] = []
            if pd.notna(deal["account"]):
                account_lift = account_lookup.get((seller, deal["account"]))
                if account_lift is not None:
                    fit_components.append(("account", account_lift))

            product_lift = product_lookup.get((seller, deal["product"]))
            if product_lift is not None:
                fit_components.append(("product", product_lift))

            if pd.notna(deal["sector"]):
                sector_lift = sector_lookup.get((seller, deal["sector"]))
                if sector_lift is not None:
                    fit_components.append(("sector", sector_lift))

            if pd.notna(deal["revenue_band"]):
                band_lift = revenue_band_lookup.get((seller, deal["revenue_band"]))
                if band_lift is not None:
                    fit_components.append(("revenue", band_lift))

            if not fit_components:
                fallback_lift = seller_base_lookup.get(seller)
                if fallback_lift is None:
                    continue
                fit_components.append(("fallback", fallback_lift))

            weights_to_use = FIT_WEIGHTS_WITH_ACCOUNT if any(name == "account" for name, _ in fit_components) else FIT_WEIGHTS_NO_ACCOUNT
            weighted_fit = weighted_fit_score(fit_components, weights_to_use)
            basis = ", ".join(name for name, _ in fit_components)
            performance = performance_lookup.get(seller, {})
            scored_sellers.append(
                {
                    "seller": seller,
                    "fit": float(weighted_fit),
                    "fit_pp": float(weighted_fit * 100),
                    "basis": basis,
                    "yellow_flag": bool(performance.get("yellow_flag", False)),
                    "performance_vs_avg_pct": float(performance.get("performance_vs_avg_pct", 0)),
                    "closed_deals": int(performance.get("closed_deals", 0)),
                }
            )

        if not scored_sellers:
            continue

        scored_sellers = sorted(scored_sellers, key=lambda item: item["fit"], reverse=True)
        specialist = scored_sellers[0]
        current_owner = deal["sales_agent"]
        current_candidate = next((cand for cand in scored_sellers if cand["seller"] == current_owner), None)
        if current_candidate is None:
            current_candidate = {
                "seller": current_owner,
                "fit": 0.0,
                "fit_pp": 0.0,
                "basis": "",
                "yellow_flag": False,
                "performance_vs_avg_pct": 0.0,
                "closed_deals": 0,
            }

        reroute_delta = specialist["fit"] - current_candidate["fit"]
        needs_data_completion = len(missing_fields) > 0
        data_quality_status = "Dados completos" if not needs_data_completion else f"Faltando: {', '.join(missing_fields)}"

        open_rows.append(
            {
                **deal.to_dict(),
                "deal_probability": round(deal_probability, 4),
                "forecast_pct": round(deal_probability * 100, 1),
                "ticket_proxy": round(ticket_proxy, 2),
                "expected_value_proxy": round(expected_value_proxy, 2),
                "age_ratio": round(age_ratio, 2) if not pd.isna(age_ratio) else np.nan,
                "forecast_band": classify_forecast_band(deal_probability),
                "current_owner": current_owner,
                "current_fit_pp": round(current_candidate["fit_pp"], 2),
                "current_basis": current_candidate["basis"],
                "specialist_owner": specialist["seller"],
                "specialist_fit_pp": round(specialist["fit_pp"], 2),
                "specialist_basis": specialist["basis"],
                "specialist_delta_pp": round(reroute_delta * 100, 2),
                "missing_fields": missing_fields,
                "needs_data_completion": needs_data_completion,
                "data_quality_status": data_quality_status,
                "data_completion_pct": 100 - (len(missing_fields) * 50),
                "candidate_pool": scored_sellers[:5],
                "current_owner_yellow_flag": bool(current_candidate["yellow_flag"]),
                "current_owner_vs_avg_pct": round(current_candidate["performance_vs_avg_pct"], 2),
            }
        )

    scored = pd.DataFrame(open_rows)
    scored = scored.sort_values(
        ["expected_value_proxy", "deal_probability", "specialist_fit_pp"],
        ascending=[False, False, False],
    ).reset_index(drop=True)

    scored = apply_conservative_rebalance(scored, seller_performance)
    scored["alignment_status"] = np.where(
        (scored["current_owner"] == scored["suggested_owner"]) | (scored["suggested_delta_pp"] < 5),
        "Aligned",
        "Reassign",
    )
    scored["recommended_action"] = scored.apply(classify_action, axis=1)
    scored["action_detail"] = scored.apply(build_action_detail, axis=1)
    scored["why_now"] = scored.apply(build_why_now, axis=1)
    return scored


def apply_conservative_rebalance(scored: pd.DataFrame, seller_performance: pd.DataFrame) -> pd.DataFrame:
    current_open = scored.groupby("current_owner").size().to_dict()
    performance_lookup = seller_performance.set_index("sales_agent").to_dict("index")

    capacity_map: Dict[str, int] = {}
    for seller in seller_performance["sales_agent"].tolist():
        perf = performance_lookup.get(seller, {})
        closed_deals = int(perf.get("closed_deals", 0))
        current_load = int(current_open.get(seller, 0))
        capacity = max(current_load, int(round(closed_deals * 0.60)), 20)
        if perf.get("yellow_flag", False):
            capacity = max(current_load, int(round(capacity * 0.85)))
        capacity_map[seller] = capacity

    assigned_count: Dict[str, int] = defaultdict(int)
    suggested_rows = []

    priority_df = scored.sort_values(["expected_value_proxy", "deal_probability"], ascending=[False, False])
    value_p75 = float(priority_df["expected_value_proxy"].quantile(0.75))
    value_p50 = float(priority_df["expected_value_proxy"].quantile(0.50))
    for _, row in priority_df.iterrows():
        if bool(row["needs_data_completion"]):
            suggested_rows.append(
                {
                    "opportunity_id": row["opportunity_id"],
                    "suggested_owner": row["current_owner"],
                    "suggested_fit_pp": round(float(row["current_fit_pp"]), 2),
                    "suggested_basis": str(row["current_basis"]),
                    "suggested_fit_loss_pp": 0.0,
                    "suggested_assignment_source": "Manter owner atual ate completar CRM",
                    "suggested_delta_pp": 0.0,
                }
            )
            assigned_count[row["current_owner"]] += 1
            continue

        candidates = row["candidate_pool"]
        best_fit_pp = float(candidates[0]["fit_pp"])
        if row["expected_value_proxy"] >= value_p75:
            max_fit_loss = 3.0
        elif row["expected_value_proxy"] >= value_p50:
            max_fit_loss = 5.0
        else:
            max_fit_loss = 8.0

        eligible = []
        for candidate in candidates:
            fit_gap = best_fit_pp - float(candidate["fit_pp"])
            if fit_gap <= max_fit_loss:
                eligible.append(candidate)
                continue
            if candidate["seller"] == row["current_owner"] and fit_gap <= max_fit_loss + 2.0:
                eligible.append(candidate)

        if not eligible:
            eligible = [candidates[0]]

        available = [cand for cand in eligible if assigned_count[cand["seller"]] < capacity_map.get(cand["seller"], 20)]
        if not available:
            relaxed_pool = []
            for candidate in candidates:
                fit_gap = best_fit_pp - float(candidate["fit_pp"])
                if fit_gap <= max_fit_loss + 3.0:
                    relaxed_pool.append(candidate)
            available = [cand for cand in relaxed_pool if assigned_count[cand["seller"]] < capacity_map.get(cand["seller"], 20)]

        pool = available if available else eligible

        def score_candidate(candidate: Dict[str, object]) -> Tuple[float, float, float]:
            bonus = 0.0
            if candidate["seller"] == row["current_owner"]:
                bonus += 0.30
            if candidate["yellow_flag"]:
                bonus -= 0.75
            return (
                float(candidate["fit_pp"]) + bonus,
                -assigned_count[candidate["seller"]] / max(capacity_map.get(candidate["seller"], 20), 1),
                -candidate["performance_vs_avg_pct"],
            )

        chosen = sorted(pool, key=score_candidate, reverse=True)[0]
        assigned_count[chosen["seller"]] += 1
        fit_loss_pp = best_fit_pp - float(chosen["fit_pp"])
        suggested_rows.append(
            {
                "opportunity_id": row["opportunity_id"],
                "suggested_owner": chosen["seller"],
                "suggested_fit_pp": round(float(chosen["fit_pp"]), 2),
                "suggested_basis": str(chosen["basis"]),
                "suggested_fit_loss_pp": round(fit_loss_pp, 2),
                "suggested_assignment_source": "Especialista puro"
                if chosen["seller"] == row["specialist_owner"]
                else "Rebalanceado com perda controlada",
                "suggested_delta_pp": round(float(chosen["fit_pp"]) - float(row["current_fit_pp"]), 2),
            }
        )

    suggested_df = pd.DataFrame(suggested_rows)
    return scored.merge(suggested_df, on="opportunity_id", how="left")


def to_context_lookup(context_df: pd.DataFrame, context_col: str) -> Dict[Tuple[str, object], float]:
    return {
        (row["sales_agent"], row[context_col]): float(row["lift"])
        for _, row in context_df.iterrows()
    }


def weighted_fit_score(
    fit_components: List[Tuple[str, float]],
    configured_weights: ContextWeights,
) -> float:
    declared = {
        "account": configured_weights.account,
        "product": configured_weights.product,
        "sector": configured_weights.sector,
        "revenue": configured_weights.revenue_band,
        "fallback": 1.0,
    }
    values: List[float] = []
    weights: List[float] = []
    for name, lift in fit_components:
        values.append(lift)
        weights.append(declared[name])
    return float(np.average(values, weights=weights))


def compute_age_factor(deal: pd.Series, product_cycle: pd.DataFrame) -> Tuple[float, float]:
    if pd.isna(deal["engage_date"]):
        return 0.55, np.nan

    p75 = product_cycle.loc[deal["product"], "p75"] if deal["product"] in product_cycle.index else np.nan
    if pd.isna(p75) or not p75:
        return 0.75, np.nan

    ratio = float(deal["age_open_days"] / p75)
    if ratio <= 1.0:
        return 1.00, ratio
    if ratio <= 1.5:
        return 0.85, ratio
    if ratio <= 2.0:
        return 0.70, ratio
    if ratio <= 2.5:
        return 0.55, ratio
    return 0.40, ratio


def compute_ticket_proxy(
    deal: pd.Series,
    product_ticket: pd.Series,
    account_ticket: pd.DataFrame,
) -> float:
    product_median = product_ticket.get(deal["product"], np.nan)
    if (
        pd.notna(deal["account"])
        and deal["account"] in account_ticket.index
        and int(account_ticket.loc[deal["account"], "won_count"]) >= 10
    ):
        account_median = float(account_ticket.loc[deal["account"], "median_ticket"])
        if pd.notna(product_median):
            return float(0.60 * account_median + 0.40 * float(product_median))
        return account_median

    if pd.notna(product_median):
        return float(product_median)
    return float(deal.get("sales_price", 0) or 0)


def classify_forecast_band(probability: float) -> str:
    for label, threshold in FORECAST_BANDS:
        if probability >= threshold:
            return label
    return "Low confidence"


def classify_action(row: pd.Series) -> str:
    if row["needs_data_completion"]:
        return "Completar CRM"
    if pd.notna(row["age_ratio"]) and row["age_ratio"] >= 2.0:
        return "Retomar ou encerrar"
    if row["deal_probability"] >= 0.25:
        return "Prioridade comercial"
    return "Acompanhar"


def build_action_detail(row: pd.Series) -> str:
    if row["needs_data_completion"]:
        return f"Preencher {', '.join(row['missing_fields'])} para recuperar contexto e retomar a negociacao."
    if pd.notna(row["age_ratio"]) and row["age_ratio"] >= 2.0:
        return "Deal envelhecido acima do ritmo historico. Tentar reengajar ou encerrar."
    if row["deal_probability"] >= 0.25:
        return "Deal com bom sinal de captura. Prioridade de contato comercial agora."
    return "Manter acompanhamento leve e revisar se ganhar novos sinais."


def build_why_now(row: pd.Series) -> str:
    reasons = []
    if row["deal_probability"] >= 0.50:
        reasons.append("forecast forte")
    elif row["deal_probability"] >= 0.35:
        reasons.append("forecast acionavel")
    else:
        reasons.append("forecast fragil")

    if row["ticket_proxy"] >= 4500:
        reasons.append("ticket premium")
    elif row["ticket_proxy"] >= 2500:
        reasons.append("ticket alto")

    if row["needs_data_completion"]:
        reasons.append(row["data_quality_status"].lower())
    elif pd.notna(row["age_ratio"]) and row["age_ratio"] >= 2.0:
        reasons.append("deal envelhecido")

    if row["current_owner"] == row["suggested_owner"]:
        reasons.append("owner atual aderente")
    elif row["suggested_assignment_source"] == "Rebalanceado com perda controlada":
        reasons.append("rebalanceado sem perda material")
    else:
        reasons.append(f"fit melhor com {row['suggested_owner']}")

    return " | ".join(reasons[:4])


def build_seller_summary(
    open_deals: pd.DataFrame,
    context_lifts: Dict[str, pd.DataFrame],
    seller_performance: pd.DataFrame,
) -> pd.DataFrame:
    current = (
        open_deals.groupby("current_owner")
        .agg(
            current_open_deals=("opportunity_id", "count"),
            current_expected_value=("expected_value_proxy", "sum"),
            data_gaps=("needs_data_completion", "sum"),
            stale_deals=("recommended_action", lambda s: int((s == "Retomar ou encerrar").sum())),
        )
        .reset_index()
        .rename(columns={"current_owner": "seller"})
    )

    suggested = (
        open_deals.groupby("suggested_owner")
        .agg(
            suggested_open_deals=("opportunity_id", "count"),
            suggested_expected_value=("expected_value_proxy", "sum"),
            transfer_in=("alignment_status", lambda s: int((s == "Reassign").sum())),
        )
        .reset_index()
        .rename(columns={"suggested_owner": "seller"})
    )

    summary = seller_performance.rename(columns={"sales_agent": "seller"}).merge(current, on="seller", how="left").merge(
        suggested,
        on="seller",
        how="left",
    )
    numeric_columns = [
        "closed_deals",
        "wins",
        "seller_win_rate",
        "performance_gap_pp",
        "performance_vs_avg_pct",
        "current_open_deals",
        "current_expected_value",
        "data_gaps",
        "stale_deals",
        "suggested_open_deals",
        "suggested_expected_value",
        "transfer_in",
    ]
    summary[numeric_columns] = summary[numeric_columns].fillna(0)
    summary["portfolio_alignment_pct"] = np.where(
        summary["current_open_deals"] > 0,
        ((summary["current_open_deals"] - summary["data_gaps"]) / summary["current_open_deals"]) * 100,
        0,
    )
    summary["net_opportunity_shift"] = summary["suggested_open_deals"] - summary["current_open_deals"]

    top_product_edges = top_context_for_seller(context_lifts["product"], "product")
    top_sector_edges = top_context_for_seller(context_lifts["sector"], "sector")
    summary = summary.merge(top_product_edges, on="seller", how="left")
    summary = summary.merge(top_sector_edges, on="seller", how="left")
    summary["top_product"] = summary["top_product"].fillna("n/d")
    summary["top_sector"] = summary["top_sector"].fillna("n/d")
    summary["top_product_lift"] = summary["top_product_lift"].fillna(0)
    summary["top_sector_lift"] = summary["top_sector_lift"].fillna(0)
    return summary.sort_values("suggested_expected_value", ascending=False)


def top_context_for_seller(context_df: pd.DataFrame, context_col: str) -> pd.DataFrame:
    top = (
        context_df.sort_values(["sales_agent", "lift"], ascending=[True, False])
        .groupby("sales_agent")
        .head(1)[["sales_agent", context_col, "lift"]]
        .rename(
            columns={
                "sales_agent": "seller",
                context_col: f"top_{context_col}",
                "lift": f"top_{context_col}_lift",
            }
        )
    )
    top[f"top_{context_col}_lift"] = (top[f"top_{context_col}_lift"] * 100).round(2)
    return top


def build_head_summary(open_deals: pd.DataFrame, seller_summary: pd.DataFrame) -> Dict[str, object]:
    transfer_candidates = open_deals[
        open_deals["account"].notna()
        & (open_deals["current_owner"] != open_deals["suggested_owner"])
        & (open_deals["suggested_delta_pp"] >= 5)
    ].copy()
    transfer_candidates["movement_history"] = transfer_candidates.apply(
        lambda row: f"{row['current_owner']} -> {row['suggested_owner']}",
        axis=1,
    )
    transfer_candidates["movement_reason"] = transfer_candidates.apply(
        lambda row: (
            f"Agora com {row['suggested_owner']} por +{row['suggested_delta_pp']:.1f} pp de fit"
            + (
                f" | perda controlada de {row['suggested_fit_loss_pp']:.1f} pp"
                if row["suggested_fit_loss_pp"] > 0
                else ""
            )
        ),
        axis=1,
    )

    return {
        "expected_value_total": float(open_deals["expected_value_proxy"].sum()),
        "avg_probability": float(open_deals["deal_probability"].mean()),
        "transfer_candidates": int(len(transfer_candidates)),
        "crm_fix_candidates": int(open_deals["needs_data_completion"].sum()),
        "mean_fit_loss_pp": float(open_deals["suggested_fit_loss_pp"].mean()),
        "movement_history": transfer_candidates.sort_values(
            ["expected_value_proxy", "suggested_delta_pp"],
            ascending=[False, False],
        ).head(30),
        "expected_by_family": (
            open_deals.groupby("family")["expected_value_proxy"].sum().reset_index().sort_values(
                "expected_value_proxy", ascending=False
            )
        ),
        "expected_by_current_owner": (
            open_deals.groupby("current_owner")["expected_value_proxy"].sum().reset_index().sort_values(
                "expected_value_proxy", ascending=False
            )
        ),
        "recommended_by_owner": (
            open_deals.groupby("suggested_owner")["expected_value_proxy"].sum().reset_index().sort_values(
                "expected_value_proxy", ascending=False
            )
        ),
        "actions_breakdown": (
            open_deals.groupby("recommended_action").size().reset_index(name="deals").sort_values("deals", ascending=False)
        ),
        "seller_board": seller_summary.sort_values("suggested_expected_value", ascending=False),
    }


def format_currency(value: float) -> str:
    return f"R$ {value:,.0f}".replace(",", ".")


def format_percent(value: float) -> str:
    return f"{value:.1f}%"
