"""Converte linhas do parquet em objetos do contrato (único lugar que conhece o formato das colunas)."""
from __future__ import annotations

import json

import pandas as pd

from lead_core.bands import priority_level
from lead_core.constants import LOW_CONFIDENCE_AGENT_N, SUGGESTED_ACTIONS, VIEW_OF_BAND
from lead_core.reasons import DISCLAIMER


def _none(v):
    return None if v is None or (isinstance(v, float) and pd.isna(v)) or v is pd.NA else v


def confidence_reason(confidence: str, stage: str) -> str:
    """Por que a confiança é baixa, média ou alta (regra do back-end; o front só exibe)."""
    if stage == "Prospecting":
        return "o deal ainda não tem histórico"
    if confidence == "low":
        return f"o vendedor tem menos de {LOW_CONFIDENCE_AGENT_N} deals fechados"
    return f"o vendedor tem {LOW_CONFIDENCE_AGENT_N} ou mais deals fechados"


def data_quality(account_missing: bool) -> dict:
    """Completude dos dados do deal, separada da confiança da previsão. A conta não entra no modelo."""
    if not account_missing:
        return {"status": "complete", "summary": "Todos os campos do deal estão preenchidos.", "missing": []}
    return {"status": "incomplete", "summary": "Falta informar a conta. Ela não entra no cálculo da prioridade.",
            "missing": [{"field": "account", "label": "Conta", "affects_prediction": False}]}


def _split_label(label: str) -> tuple[str, str]:
    name, _, observed = label.partition(": ")
    return (name, observed) if observed else (label, "")


def _reference(code: str, value, bundle) -> str | None:
    """Com o que comparar o valor observado de cada fator (a partir das tabelas e limiares do modelo)."""
    thr, base = bundle.thresholds, bundle.tables.get("base_wr")
    if code == "age_band":
        return f"Prazo típico: {thr['typical_p50']} dias. A maioria fecha em até {thr['stale_days']} dias."
    if code in ("agent_wr", "product_wr", "agent_product_wr", "agent_recent_wr") and base is not None:
        return f"Média geral de vitória: {float(base) * 100:.0f}%"
    if code == "agent_n":
        return f"Confiança baixa abaixo de {LOW_CONFIDENCE_AGENT_N} deals fechados"
    return None


def explain_reason(reason: dict, bundle) -> dict:
    """Fator, valor observado e referência de um motivo (para a tabela de explicação do detalhe)."""
    factor, observed = _split_label(reason["label"])
    return {**reason, "factor": factor, "observed": observed or reason.get("value"),
            "reference": _reference(reason["code"], reason.get("value"), bundle)}


def summary_dict(row: pd.Series, show_probability: bool) -> dict:
    score = _none(row["score"])
    age = _none(row["age_days"])
    reasons = json.loads(row["reasons"])
    return {
        "opportunity_id": row["opportunity_id"], "seller": row["seller"], "manager": row["manager"],
        "office": row["office"], "stage": row["stage"], "product": row["product"], "series": row["series"],
        "account": _none(row["account"]), "account_missing": bool(row["account_missing"]),
        "list_price": float(row["list_price"]), "engage_date": _none(row["engage_date"]),
        "age_days": None if age is None else int(age),
        "score": None if score is None else int(score), "priority_level": priority_level(None if score is None else int(score)),
        "band": row["band"], "view": VIEW_OF_BAND[row["band"]], "expected_value": round(float(row["expected_value"]), 2),
        "p_win": round(float(row["p_win"]), 4) if show_probability else None,
        "confidence": row["confidence"], "confidence_reason": confidence_reason(row["confidence"], row["stage"]),
        "data_quality": data_quality(bool(row["account_missing"])),
        "suggested_action": SUGGESTED_ACTIONS[row["band"]], "flags": json.loads(row["flags"]), "reasons": reasons[:3],
    }


def detail_dict(row: pd.Series, bundle, show_probability: bool) -> dict:
    base = summary_dict(row, show_probability)
    all_reasons = json.loads(row["reasons"])
    won, n = bundle.tables["agent_product"].get(f"{row['seller']}||{row['product']}", [0.0, 0.0])
    thr = bundle.thresholds
    return {
        **base,
        "explanation": {"base_label": "Média histórica de vitória",
                        "contributions": [explain_reason(r, bundle) for r in all_reasons],
                        "disclaimer": DISCLAIMER},
        "context": {
            "seller_product": {"won": int(won), "lost": int(n - won), "n": int(n)},
            "typical_duration_days": {"p50": thr["typical_p50"], "p90": thr["stale_days"], "max": thr["review_days"]},
        },
    }
