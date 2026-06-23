#!/usr/bin/env python3
"""Build explainable opportunity scores and routing signals for the web app."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FRONTEND_DATA_DIR = PROJECT_ROOT / "frontend" / "data"

HIGH_VALUE_CUTOFF = 4_821
FIT_DELTA_CONSULT = 8
FIT_DELTA_TRANSFER = 12
MATCH_CONFIDENCE_TRANSFER = 0.65

SCORE_WEIGHTS = {
    "value_score": 0.20,
    "fit_score": 0.25,
    "timing_score": 0.20,
    "stage_score": 0.10,
    "account_score": 0.10,
    "portfolio_score": 0.10,
    "confidence_score": 0.05,
}


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    if pd.isna(value):
        return low
    return float(max(low, min(high, value)))


def bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def age_class(stage: object, days_open: object) -> str:
    stage_value = str(stage).lower()
    if stage_value == "prospecting":
        return "prospecting"
    if pd.isna(days_open):
        return "unknown_age"
    days = float(days_open)
    if days <= 90:
        return "normal"
    if days <= 180:
        return "recovery"
    if days <= 270:
        return "intervention"
    return "quarantine"


def timing_score(stage: object, days_open: object) -> float:
    return {
        "prospecting": 50,
        "unknown_age": 35,
        "normal": 82,
        "recovery": 72,
        "intervention": 35,
        "quarantine": 12,
    }[age_class(stage, days_open)]


def stage_score(stage: object) -> float:
    return 78 if str(stage).lower() == "engaging" else 48


def account_score(row: pd.Series) -> float:
    if not bool_value(row.get("account_known")):
        return 22

    score = 62.0
    revenue_band = str(row.get("revenue_band", ""))
    employee_band = str(row.get("employee_band", ""))
    age = row.get("account_age_years_as_of_snapshot")

    if revenue_band == "over_3b":
        score += 16
    elif revenue_band == "1_5b_to_3b":
        score += 12
    elif revenue_band == "500m_to_1_5b":
        score += 7

    if employee_band == "over_10k":
        score += 12
    elif employee_band == "2k_to_10k":
        score += 8
    elif employee_band == "500_to_2k":
        score += 4

    if not pd.isna(age):
        if float(age) >= 25:
            score += 6
        elif float(age) >= 10:
            score += 3

    return clamp(score)


def history_points(history_maturity: object) -> float:
    return {
        "consolidated": 15,
        "limited_history": 10,
        "thin_history": 5,
        "no_history": 0,
    }.get(str(history_maturity), 5)


def red_flag_tier(row: pd.Series) -> str:
    open_deals = int(row.get("open_deals", 0) or 0)
    win_rate = row.get("win_rate")
    history = str(row.get("history_maturity", ""))
    risk = str(row.get("portfolio_risk", ""))

    if open_deals <= 0 or pd.isna(win_rate):
        return "none"
    win_rate = float(win_rate)
    if history == "consolidated" and win_rate < 0.60:
        return "tier_1_low_performance"
    if history == "consolidated" and win_rate < 0.62:
        return "tier_2_last_chance"
    if risk == "large_stale_backlog" and open_deals >= 80:
        return "tier_3_capacity_watch"
    if risk == "high_value_low_conversion":
        return "tier_2_last_chance"
    return "none"


def portfolio_score(row: pd.Series) -> float:
    score = 66.0
    performance = str(row.get("performance_band", ""))
    risk = str(row.get("portfolio_risk", ""))
    tier = red_flag_tier(row)

    score += {
        "top_performer": 18,
        "above_average": 10,
        "around_average": 0,
        "underperformer": -18,
        "insufficient_sample": -4,
        "no_history": -8,
    }.get(performance, 0)

    score += {
        "high_value_low_conversion": -16,
        "large_stale_backlog": -12,
        "low_data_confidence": -6,
        "normal": 0,
        "no_open_pipeline": 0,
    }.get(risk, 0)

    if tier == "tier_1_low_performance":
        score -= 8
    elif tier == "tier_2_last_chance":
        score -= 5
    elif tier == "tier_3_capacity_watch":
        score -= 8

    return clamp(score)


def confidence_score(row: pd.Series, seller_row: pd.Series) -> float:
    score = 20.0
    account_known = bool_value(row.get("account_known"))
    if account_known:
        score += 25
    if bool_value(row.get("product_known")):
        score += 10
    if bool_value(row.get("sales_agent_known")):
        score += 10
    if str(row.get("deal_stage")) == "prospecting" or not pd.isna(row.get("days_open_as_of_snapshot")):
        score += 10

    current_confidence = row.get("current_match_confidence")
    if not pd.isna(current_confidence):
        score += 15 * float(current_confidence)

    score += history_points(seller_row.get("history_maturity"))
    if not account_known:
        score = min(score, 45)
    return clamp(score)


def value_scores(values: pd.Series) -> pd.Series:
    logged = np.log1p(values.fillna(0).astype(float))
    low = float(logged.min())
    high = float(logged.max())
    if high == low:
        return pd.Series(50.0, index=values.index)
    return ((logged - low) / (high - low) * 100).clip(0, 100)


def priority_band(score: float, routing_signal: str) -> str:
    if routing_signal in {"manager_review", "corrigir_dados", "last_chance"}:
        return "revisao"
    if routing_signal == "nurture":
        return "baixa"
    if score >= 72:
        return "alta"
    if score >= 56:
        return "media"
    return "baixa"


def confidence_band(score: float) -> str:
    if score >= 72:
        return "alta"
    if score >= 48:
        return "media"
    return "baixa"


def recommended_action(signal: str) -> str:
    return {
        "manter": "Agir agora na carteira atual",
        "consultar_especialista": "Consultar especialista ou aplicar playbook recomendado",
        "remanejar": "Remanejar ownership com gerente",
        "manager_review": "Revisar com gerente antes de agir",
        "corrigir_dados": "Corrigir dados antes de decidir roteamento",
        "last_chance": "Executar última tentativa com SLA curto",
        "nurture": "Mover para nutrição ou close-lost operacional",
    }[signal]


def approval_type(signal: object) -> str:
    return {
        "remanejar": "remanejamento",
        "manager_review": "revisao_gerente",
    }.get(str(signal), "sem_aprovacao")


def approval_label(signal: object) -> str:
    return {
        "remanejar": "Aprovar remanejamento",
        "manager_review": "Aprovar revisão gerente",
    }.get(str(signal), "Sem aprovação")


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    open_pipeline = pd.read_csv(PROCESSED_DIR / "open_pipeline_for_scoring.csv")
    recommendations = pd.read_csv(PROCESSED_DIR / "open_deal_specialist_recommendations.csv")
    sellers = pd.read_csv(PROCESSED_DIR / "seller_xray.csv")
    return open_pipeline, recommendations, sellers


def build_base_scores(open_pipeline: pd.DataFrame, recommendations: pd.DataFrame, sellers: pd.DataFrame) -> pd.DataFrame:
    sellers = sellers.copy()
    sellers["seller_red_flag_tier"] = sellers.apply(red_flag_tier, axis=1)
    sellers["seller_portfolio_score"] = sellers.apply(portfolio_score, axis=1)
    seller_cols = [
        "sales_agent_id",
        "win_rate",
        "closed_opportunities",
        "open_deals",
        "open_value",
        "old_engaging_deals",
        "old_engaging_value",
        "history_maturity",
        "performance_band",
        "portfolio_risk",
        "open_account_known_pct",
        "seller_red_flag_tier",
        "seller_portfolio_score",
    ]

    scored = recommendations.merge(
        open_pipeline[
            [
                "opportunity_id",
                "product_id",
                "series",
                "sales_price",
                "has_engage_date",
                "product_known",
                "sales_agent_known",
                "account_age_years_as_of_snapshot",
            ]
        ],
        on="opportunity_id",
        how="left",
    ).merge(
        sellers[seller_cols],
        left_on="current_sales_agent_id",
        right_on="sales_agent_id",
        how="left",
    )
    scored = scored.drop(columns=["sales_agent_id"])
    scored["account_known"] = scored["account_known"].map(bool_value)
    scored["value_score"] = value_scores(scored["estimated_deal_value"])
    scored["fit_delta"] = scored["match_score"].fillna(0) - scored["current_match_score"].fillna(0)
    scored["age_class"] = scored.apply(
        lambda row: age_class(row["deal_stage"], row["days_open_as_of_snapshot"]),
        axis=1,
    )
    scored["timing_score"] = scored.apply(
        lambda row: timing_score(row["deal_stage"], row["days_open_as_of_snapshot"]),
        axis=1,
    )
    scored["stage_score"] = scored["deal_stage"].map(stage_score)
    scored["account_score"] = scored.apply(account_score, axis=1)
    scored["fit_score"] = scored["current_match_score"].fillna(scored["match_score"]).fillna(50).clip(0, 100)
    scored["portfolio_score"] = scored["seller_portfolio_score"].fillna(50)
    scored["confidence_score"] = scored.apply(
        lambda row: confidence_score(row, row),
        axis=1,
    )

    scored["priority_score"] = sum(
        scored[col] * weight for col, weight in SCORE_WEIGHTS.items()
    ).round(1)
    return scored


def transfer_candidate(row: pd.Series) -> bool:
    if not bool_value(row.get("account_known")):
        return False
    if not bool_value(row.get("recommended_differs_from_current")):
        return False
    if float(row.get("fit_delta", 0) or 0) < FIT_DELTA_TRANSFER:
        return False
    if float(row.get("match_confidence", 0) or 0) < MATCH_CONFIDENCE_TRANSFER:
        return False
    if row["age_class"] == "recovery":
        return True
    if row["age_class"] == "normal" and float(row["estimated_deal_value"]) >= HIGH_VALUE_CUTOFF:
        return True
    return False


def apply_routing(scored: pd.DataFrame, sellers: pd.DataFrame) -> pd.DataFrame:
    scored = scored.copy()
    seller_capacity = sellers.set_index("sales_agent")[["open_deals"]].to_dict("index")
    soft_caps = {
        seller: int(max(5, round(float(values["open_deals"]) * 0.15)))
        for seller, values in seller_capacity.items()
    }
    hard_caps = {
        seller: int(max(8, round(float(values["open_deals"]) * 0.25)))
        for seller, values in seller_capacity.items()
    }
    allocated = {seller: 0 for seller in soft_caps}

    scored["is_transfer_candidate"] = scored.apply(transfer_candidate, axis=1)
    scored["routing_signal"] = "manter"
    scored["capacity_status"] = "available"

    candidate_idx = scored[scored["is_transfer_candidate"]].sort_values(
        ["priority_score", "fit_delta", "estimated_deal_value"],
        ascending=[False, False, False],
    ).index

    for idx in candidate_idx:
        recommended = scored.at[idx, "recommended_sales_agent"]
        soft_cap = soft_caps.get(recommended, 5)
        hard_cap = hard_caps.get(recommended, 8)
        if allocated.get(recommended, 0) < soft_cap:
            scored.at[idx, "routing_signal"] = "remanejar"
            allocated[recommended] = allocated.get(recommended, 0) + 1
            scored.at[idx, "capacity_status"] = f"allocated_{allocated[recommended]}_of_{soft_cap}_soft"
        elif allocated.get(recommended, 0) < hard_cap:
            scored.at[idx, "routing_signal"] = "consultar_especialista"
            allocated[recommended] = allocated.get(recommended, 0) + 1
            scored.at[idx, "capacity_status"] = f"consult_only_{allocated[recommended]}_of_{hard_cap}_hard"
        else:
            scored.at[idx, "routing_signal"] = "consultar_especialista"
            scored.at[idx, "capacity_status"] = "specialist_at_capacity"

    for idx, row in scored.iterrows():
        value = float(row["estimated_deal_value"])
        age = str(row["age_class"])
        signal = str(scored.at[idx, "routing_signal"])
        fit_delta = float(row.get("fit_delta", 0) or 0)
        is_red_flag = str(row.get("seller_red_flag_tier")) in {
            "tier_1_low_performance",
            "tier_2_last_chance",
        }

        account_known = bool_value(row["account_known"])
        if not account_known and value >= HIGH_VALUE_CUTOFF:
            signal = "corrigir_dados"
        elif not account_known and signal in {"remanejar", "consultar_especialista"}:
            signal = "manter"
        elif age == "quarantine":
            signal = "last_chance" if value >= HIGH_VALUE_CUTOFF else "nurture"
        elif age == "intervention" and (value >= HIGH_VALUE_CUTOFF or fit_delta >= FIT_DELTA_TRANSFER):
            signal = "manager_review"
        elif (
            account_known
            and signal == "manter"
            and fit_delta >= FIT_DELTA_CONSULT
            and bool_value(row["recommended_differs_from_current"])
        ):
            signal = "consultar_especialista"
        elif signal == "manter" and is_red_flag and float(row["priority_score"]) >= 50:
            signal = "last_chance"

        scored.at[idx, "routing_signal"] = signal

    scored["priority_band"] = scored.apply(
        lambda row: priority_band(float(row["priority_score"]), str(row["routing_signal"])),
        axis=1,
    )
    scored["confidence_band"] = scored["confidence_score"].map(confidence_band)
    scored["recommended_action"] = scored["routing_signal"].map(recommended_action)
    scored["approval_required"] = scored["routing_signal"].isin({"remanejar", "manager_review"})
    scored["approval_type"] = scored["routing_signal"].map(approval_type)
    scored["approval_label"] = scored["routing_signal"].map(approval_label)
    return scored


def reason_codes(row: pd.Series) -> list[str]:
    reasons: list[str] = []
    value = float(row["estimated_deal_value"])
    fit_delta = float(row.get("fit_delta", 0) or 0)

    if value >= HIGH_VALUE_CUTOFF:
        reasons.append("Alto valor economico")
    if row.get("current_match_band") in {"specialist_match", "possible_specialist"}:
        reasons.append("Bom fit do vendedor atual")
    if fit_delta >= FIT_DELTA_TRANSFER and bool_value(row.get("recommended_differs_from_current")):
        reasons.append("Especialista sugerido tem fit superior")
    if row["age_class"] == "recovery":
        reasons.append("Deal em janela de recovery")
    elif row["age_class"] == "intervention":
        reasons.append("Deal envelhecido exige revisao")
    elif row["age_class"] == "quarantine":
        reasons.append("Deal muito antigo")
    if not bool_value(row.get("account_known")):
        reasons.append("Conta ausente reduz confianca")
    if row.get("seller_red_flag_tier") == "tier_1_low_performance":
        reasons.append("Vendedor em red-flag de performance")
    elif row.get("seller_red_flag_tier") == "tier_2_last_chance":
        reasons.append("Vendedor em última tentativa assistida")
    elif row.get("seller_red_flag_tier") == "tier_3_capacity_watch":
        reasons.append("Carteira atual ja esta sobrecarregada")
    if row.get("routing_signal") == "consultar_especialista":
        reasons.append("Capacidade ou governanca pede apoio, nao transferencia")
    if not reasons:
        reasons.append("Prioridade calculada por score balanceado")
    return reasons[:5]


def summarize_sellers(scored: pd.DataFrame, sellers: pd.DataFrame) -> pd.DataFrame:
    signal_counts = pd.crosstab(scored["current_sales_agent_id"], scored["routing_signal"])
    grouped = scored.groupby(
        [
            "current_sales_agent_id",
            "current_sales_agent",
            "current_manager",
            "current_region",
        ]
    ).agg(
        open_deals=("opportunity_id", "count"),
        open_value=("estimated_deal_value", "sum"),
        avg_priority_score=("priority_score", "mean"),
        high_priority_deals=("priority_band", lambda s: int((s == "alta").sum())),
        review_deals=("priority_band", lambda s: int((s == "revisao").sum())),
        approval_queue_deals=("approval_required", lambda s: int(s.map(bool_value).sum())),
        low_confidence_deals=("confidence_band", lambda s: int((s == "baixa").sum())),
        high_value_missing_account=(
            "opportunity_id",
            lambda ids: int(
                (
                    (~scored.loc[ids.index, "account_known"].map(bool_value))
                    & (scored.loc[ids.index, "estimated_deal_value"] >= HIGH_VALUE_CUTOFF)
                ).sum()
            ),
        ),
        top_deal_value=("estimated_deal_value", "max"),
    ).reset_index()

    grouped = grouped.merge(
        sellers[
            [
                "sales_agent_id",
                "win_rate",
                "closed_opportunities",
                "history_maturity",
                "performance_band",
                "portfolio_risk",
                "old_engaging_deals",
                "seller_red_flag_tier",
            ]
        ],
        left_on="current_sales_agent_id",
        right_on="sales_agent_id",
        how="left",
    ).drop(columns=["sales_agent_id"])

    for signal in ["manter", "consultar_especialista", "remanejar", "manager_review", "corrigir_dados", "last_chance", "nurture"]:
        grouped[f"{signal}_deals"] = grouped["current_sales_agent_id"].map(signal_counts.get(signal, pd.Series(dtype=int))).fillna(0).astype(int)

    grouped["avg_priority_score"] = grouped["avg_priority_score"].round(1)
    grouped["seller_action"] = np.select(
        [
            grouped["seller_red_flag_tier"] == "tier_1_low_performance",
            grouped["seller_red_flag_tier"] == "tier_2_last_chance",
            grouped["seller_red_flag_tier"] == "tier_3_capacity_watch",
            grouped["high_priority_deals"] > 0,
        ],
        [
            "Limitar carga e usar última tentativa controlada",
            "Última tentativa assistida com SLA",
            "Nao adicionar carga; limpar backlog",
            "Focar top prioridades",
        ],
        default="Manter rotina de priorizacao",
    )
    return grouped.sort_values(["review_deals", "open_value"], ascending=[False, False])


def summarize_managers(scored: pd.DataFrame, seller_summary: pd.DataFrame) -> pd.DataFrame:
    manager = scored.groupby("current_manager").agg(
        open_deals=("opportunity_id", "count"),
        open_value=("estimated_deal_value", "sum"),
        avg_priority_score=("priority_score", "mean"),
        high_priority_deals=("priority_band", lambda s: int((s == "alta").sum())),
        review_deals=("priority_band", lambda s: int((s == "revisao").sum())),
        approval_queue_deals=("approval_required", lambda s: int(s.map(bool_value).sum())),
        remanejar_deals=("routing_signal", lambda s: int((s == "remanejar").sum())),
        consult_deals=("routing_signal", lambda s: int((s == "consultar_especialista").sum())),
        data_fix_deals=("routing_signal", lambda s: int((s == "corrigir_dados").sum())),
        last_chance_deals=("routing_signal", lambda s: int((s == "last_chance").sum())),
        nurture_deals=("routing_signal", lambda s: int((s == "nurture").sum())),
        low_confidence_deals=("confidence_band", lambda s: int((s == "baixa").sum())),
    ).reset_index()

    red_flags = seller_summary.groupby("current_manager").agg(
        red_flag_sellers=("seller_red_flag_tier", lambda s: int((s != "none").sum())),
        sellers=("current_sales_agent", "count"),
    ).reset_index()
    manager = manager.merge(red_flags, on="current_manager", how="left")
    manager["avg_priority_score"] = manager["avg_priority_score"].round(1)
    manager["manager_focus"] = np.select(
        [
            manager["approval_queue_deals"] >= 10,
            manager["data_fix_deals"] >= 20,
            manager["last_chance_deals"] >= 20,
            manager["remanejar_deals"] >= 5,
        ],
        [
            "Aprovar fila de decisões",
            "Saneamento de dados de alto valor",
            "Limpar pipeline envelhecido",
            "Aprovar remanejamentos com cap",
        ],
        default="Gerir prioridades da carteira",
    )
    return manager.sort_values("open_value", ascending=False)


def json_ready(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    clean_records: list[dict[str, Any]] = []
    for record in records:
        clean: dict[str, Any] = {}
        for key, value in record.items():
            if isinstance(value, float) and np.isnan(value):
                clean[key] = None
            elif isinstance(value, (np.integer, np.floating)):
                clean[key] = value.item()
            elif isinstance(value, (np.bool_)):
                clean[key] = bool(value)
            else:
                clean[key] = value
        clean_records.append(clean)
    return clean_records


def write_outputs(scored: pd.DataFrame, seller_summary: pd.DataFrame, manager_summary: pd.DataFrame) -> None:
    scored = scored.copy()
    scored["reason_codes"] = scored.apply(lambda row: " | ".join(reason_codes(row)), axis=1)
    scored["reason_codes_list"] = scored.apply(reason_codes, axis=1)

    output_cols = [
        "opportunity_id",
        "deal_stage",
        "current_sales_agent_id",
        "current_sales_agent",
        "current_manager",
        "current_region",
        "product",
        "ticket_band",
        "estimated_deal_value",
        "account",
        "sector",
        "revenue_band",
        "employee_band",
        "days_open_as_of_snapshot",
        "account_known",
        "age_class",
        "priority_score",
        "priority_band",
        "confidence_score",
        "confidence_band",
        "routing_signal",
        "recommended_action",
        "approval_required",
        "approval_type",
        "approval_label",
        "recommended_sales_agent",
        "recommended_manager",
        "match_score",
        "current_match_score",
        "fit_delta",
        "match_confidence",
        "current_match_confidence",
        "current_match_band",
        "capacity_status",
        "seller_red_flag_tier",
        "performance_band",
        "portfolio_risk",
        "value_score",
        "fit_score",
        "timing_score",
        "stage_score",
        "account_score",
        "portfolio_score",
        "reason_codes",
    ]
    scored[output_cols].to_csv(PROCESSED_DIR / "scored_open_opportunities.csv", index=False)
    seller_summary.to_csv(PROCESSED_DIR / "seller_portal_summary.csv", index=False)
    manager_summary.to_csv(PROCESSED_DIR / "manager_portal_summary.csv", index=False)

    FRONTEND_DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": "2026-06-23",
        "score_weights": SCORE_WEIGHTS,
        "cutoffs": {
            "high_value": HIGH_VALUE_CUTOFF,
            "fit_delta_consult": FIT_DELTA_CONSULT,
            "fit_delta_transfer": FIT_DELTA_TRANSFER,
            "match_confidence_transfer": MATCH_CONFIDENCE_TRANSFER,
            "age_bands": {
                "normal": "0-90 dias",
                "recovery": "91-180 dias",
                "intervention": "181-270 dias",
                "quarantine": ">270 dias",
            },
        },
        "deals": json_ready(scored[output_cols + ["reason_codes_list"]].to_dict("records")),
        "sellers": json_ready(seller_summary.to_dict("records")),
        "managers": json_ready(manager_summary.to_dict("records")),
    }
    (FRONTEND_DATA_DIR / "dashboard_data.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    open_pipeline, recommendations, sellers = load_data()
    scored = build_base_scores(open_pipeline, recommendations, sellers)
    sellers = sellers.copy()
    sellers["seller_red_flag_tier"] = sellers.apply(red_flag_tier, axis=1)
    scored = apply_routing(scored, sellers)
    seller_summary = summarize_sellers(scored, sellers)
    manager_summary = summarize_managers(scored, seller_summary)
    write_outputs(scored, seller_summary, manager_summary)

    print(f"Wrote {PROCESSED_DIR / 'scored_open_opportunities.csv'} rows={len(scored)}")
    print(f"Wrote {PROCESSED_DIR / 'seller_portal_summary.csv'} rows={len(seller_summary)}")
    print(f"Wrote {PROCESSED_DIR / 'manager_portal_summary.csv'} rows={len(manager_summary)}")
    print(f"Wrote {FRONTEND_DATA_DIR / 'dashboard_data.json'}")


if __name__ == "__main__":
    main()
