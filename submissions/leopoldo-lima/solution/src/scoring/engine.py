from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import Any

from src.domain.models import OpportunityFeatureSet
from src.features.engineering import feature_set_from_payload

ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_RULES_PATH = ROOT / "config" / "scoring-rules.json"


@dataclass(frozen=True)
class ScoreResult:
    score: int
    positives: list[str]
    negatives: list[str]
    risks: list[str]
    next_best_action: str


def load_rules(path: pathlib.Path | None = None) -> dict[str, Any]:
    file_path = path or DEFAULT_RULES_PATH
    return json.loads(file_path.read_text(encoding="utf-8"))


def _clamp(value: int, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, value))


def _apply_stage_weights(
    feature_set: OpportunityFeatureSet,
    cfg: dict[str, Any],
    score: int,
    positives: list[str],
    negatives: list[str],
    risks: list[str],
) -> int:
    deal_stage = feature_set.deal_stage
    stage_weights = cfg["deal_stage_weights"]
    if deal_stage in stage_weights:
        delta = int(stage_weights[deal_stage])
        score += delta
        if delta >= 0:
            positives.append(f"deal_stage {deal_stage} contribuiu +{delta}.")
        else:
            negatives.append(f"deal_stage {deal_stage} contribuiu {delta}.")
    else:
        negatives.append("deal_stage fora do mapeamento; sem bonus de maturidade.")
        risks.append("Possivel taxonomia de estagio divergente no dataset.")
    return score


def _apply_close_value(
    feature_set: OpportunityFeatureSet,
    cfg: dict[str, Any],
    score: int,
    positives: list[str],
    negatives: list[str],
) -> int:
    close_value = feature_set.close_value
    cv_cfg = cfg["close_value"]
    if close_value >= float(cv_cfg["high_threshold"]):
        w = int(cv_cfg["high_weight"])
        score += w
        positives.append("close_value alto elevou prioridade.")
    elif close_value >= float(cv_cfg["mid_threshold"]):
        w = int(cv_cfg["mid_weight"])
        score += w
        positives.append("close_value medio trouxe bonus moderado.")
    else:
        negatives.append("close_value baixo sem bonus de valor.")
    return score


def _apply_pipeline_age(
    feature_set: OpportunityFeatureSet,
    cfg: dict[str, Any],
    score: int,
    positives: list[str],
    negatives: list[str],
) -> int:
    if feature_set.is_won or feature_set.is_lost:
        return score
    pa_cfg = cfg.get("pipeline_age") or {}
    weights = pa_cfg.get("weights") or {}
    bucket = feature_set.pipeline_age_bucket
    if bucket in weights:
        delta = int(weights[bucket])
        score += delta
        if delta > 0:
            positives.append(
                f"idade no pipeline ({bucket}, {feature_set.days_since_engage}d desde engage)"
                f" +{delta}."
            )
        elif delta < 0:
            negatives.append(
                f"idade no pipeline ({bucket}, {feature_set.days_since_engage}d desde engage)"
                f" {delta}."
            )
    return score


def _apply_stage_rank(
    feature_set: OpportunityFeatureSet,
    cfg: dict[str, Any],
    score: int,
    positives: list[str],
    negatives: list[str],
) -> int:
    adj = cfg.get("stage_rank_adjustment") or {}
    key = str(feature_set.stage_rank)
    if key in adj:
        delta = int(adj[key])
        if delta != 0:
            score += delta
            if delta > 0:
                positives.append(f"stage_rank {feature_set.stage_rank} afinou +{delta}.")
            else:
                negatives.append(f"stage_rank {feature_set.stage_rank} afinou {delta}.")
    return score


def _apply_revenue_and_employees(
    feature_set: OpportunityFeatureSet,
    cfg: dict[str, Any],
    score: int,
    positives: list[str],
    negatives: list[str],
) -> int:
    rev_map = cfg.get("account_revenue_band") or {}
    band_r = feature_set.account_revenue_band
    if band_r in rev_map:
        delta = int(rev_map[band_r])
        score += delta
        if delta > 0:
            positives.append(f"conta {band_r} por receita (+{delta}).")
        elif delta < 0:
            negatives.append(f"receita da conta desconhecida ou baixa ({band_r}) {delta}.")

    emp_map = cfg.get("employee_band") or {}
    band_e = feature_set.employee_band
    if band_e in emp_map:
        delta = int(emp_map[band_e])
        score += delta
        if delta > 0:
            positives.append(f"porte por headcount {band_e} (+{delta}).")
        elif delta < 0:
            negatives.append(f"headcount desconhecido ({band_e}) {delta}.")
    return score


def _apply_product_series_and_price(
    feature_set: OpportunityFeatureSet,
    cfg: dict[str, Any],
    score: int,
    positives: list[str],
    negatives: list[str],
) -> int:
    ps_cfg = cfg.get("product_series") or {}
    default_s = int(ps_cfg.get("default", 0))
    by_series = ps_cfg.get("by_series") or {}
    series = feature_set.product_series
    delta = int(by_series.get(series, default_s))
    if delta != 0:
        score += delta
        if delta > 0:
            positives.append(f"serie de produto {series} (+{delta}).")
        else:
            negatives.append(f"serie de produto {series} {delta}.")

    pp_cfg = cfg.get("product_price") or {}
    price = feature_set.product_price
    if price >= float(pp_cfg.get("high_threshold", 9e12)):
        w = int(pp_cfg.get("high_weight", 0))
        score += w
        if w:
            positives.append("preco de lista do produto elevado reforcou prioridade.")
    elif price >= float(pp_cfg.get("mid_threshold", 0)):
        w = int(pp_cfg.get("mid_weight", 0))
        score += w
        if w:
            positives.append("preco de lista do produto moderado trouxe bonus leve.")
    return score


def _apply_regional_and_manager(
    feature_set: OpportunityFeatureSet,
    cfg: dict[str, Any],
    score: int,
    positives: list[str],
) -> int:
    ro_cfg = cfg.get("regional_office") or {}
    office = feature_set.regional_office
    delta = int((ro_cfg.get("by_office") or {}).get(office, ro_cfg.get("default", 0)))
    if delta != 0:
        score += delta
        positives.append(f"regiao comercial {office} (+{delta}).")
    known_bonus = int(ro_cfg.get("known_office_bonus", 0))
    if known_bonus and office not in ("unknown", "", "Unknown"):
        score += known_bonus
        positives.append(
            f"escritorio regional identificado ({office}); sinal de completude +{known_bonus}."
        )

    ms_cfg = cfg.get("manager_signal") or {}
    bonus = int(ms_cfg.get("known_manager_bonus", 0))
    if bonus and feature_set.manager_name and feature_set.manager_name.strip().lower() != "unknown":
        score += bonus
        positives.append("manager atribuido (completude de equipe).")
    return score


def _apply_data_quality(
    feature_set: OpportunityFeatureSet,
    cfg: dict[str, Any],
    score: int,
    positives: list[str],
    negatives: list[str],
    risks: list[str],
) -> int:
    dq = cfg.get("data_quality") or {}
    if feature_set.pipeline_age_bucket == "unknown" and feature_set.is_open:
        pen = int(dq.get("missing_engage_date_penalty", 0))
        if pen:
            score += pen
            negatives.append(f"data de engage ausente ou invalida ({pen}).")
            risks.append("Sem engage_date confiavel, idade de pipeline e aproximada.")

    if (feature_set.is_won or feature_set.is_lost) and not feature_set.has_close_date:
        pen = int(dq.get("closed_deal_missing_close_date_penalty", 0))
        if pen:
            score += pen
            negatives.append(f"oportunidade terminal sem close_date ({pen}).")

    if (feature_set.is_won or feature_set.is_lost) and feature_set.has_close_date:
        bonus = int(dq.get("has_close_date_when_terminal_bonus", 0))
        if bonus:
            score += bonus
            positives.append(
                "close_date presente para oportunidade fechada (qualidade de registro)."
            )

    return score


def _apply_open_operational_signals(
    feature_set: OpportunityFeatureSet,
    cfg: dict[str, Any],
    score: int,
    negatives: list[str],
) -> int:
    """Sinais extra para pipeline aberto (CRP-FIN-04)."""
    oo = cfg.get("open_operational") or {}
    if not feature_set.is_open:
        return score
    thr = float(oo.get("low_value_threshold", 0))
    pen = int(oo.get("prospecting_no_traction_penalty", 0))
    if (
        thr > 0
        and pen
        and feature_set.deal_stage == "Prospecting"
        and feature_set.close_value < thr
        and feature_set.pipeline_age_bucket in ("active", "stale")
    ):
        score += pen
        negatives.append(
            "Prospecção com ticket ainda baixo e tempo no pipeline: "
            "menos urgência face a deals mais maduros."
        )
    return score


def _band_fallback_action(score: int, actions: dict[str, str]) -> str:
    if score >= 75:
        return str(actions["high"])
    if score >= 45:
        return str(actions["medium"])
    return str(actions["low"])


def _pick_contextual_next_action(
    feature_set: OpportunityFeatureSet, cfg: dict[str, Any], score: int
) -> str:
    """Diversifica próxima ação por contexto (CRP-FIN-05)."""
    legacy = cfg["actions"]
    ac = cfg.get("actions_by_context") or {}
    if not ac:
        return _band_fallback_action(score, legacy)

    oid = feature_set.opportunity_id or ""
    h = abs(hash(oid)) if oid else 0

    def pick(seq: object) -> str | None:
        if not isinstance(seq, list) or not seq:
            return None
        return str(seq[h % len(seq)])

    if feature_set.is_won:
        return pick(ac.get("won")) or _band_fallback_action(score, legacy)
    if feature_set.is_lost:
        return pick(ac.get("lost")) or str(legacy["low"])
    if feature_set.pipeline_age_bucket == "stale":
        chosen = pick(ac.get("open_stale"))
        if chosen:
            return chosen
    band_high = score >= 75
    band_mid = score >= 45
    if band_high:
        return pick(ac.get("open_high")) or _band_fallback_action(score, legacy)
    if band_mid:
        return pick(ac.get("open_medium")) or _band_fallback_action(score, legacy)
    return pick(ac.get("open_low")) or _band_fallback_action(score, legacy)


def score_from_features(
    feature_set: OpportunityFeatureSet, rules: dict[str, Any] | None = None
) -> ScoreResult:
    cfg = rules or load_rules()
    positives: list[str] = []
    negatives: list[str] = []
    risks: list[str] = []

    score = int(cfg["base_score"])

    score = _apply_stage_weights(feature_set, cfg, score, positives, negatives, risks)
    score = _apply_close_value(feature_set, cfg, score, positives, negatives)

    if not feature_set.has_account:
        penalty = int(cfg["missing_account_penalty"])
        score += penalty
        negatives.append(f"account ausente aplicou penalidade {penalty}.")
        risks.append("Registro sem account dificulta acao comercial direcionada.")

    if int(cfg.get("version", 1)) >= 2:
        score = _apply_pipeline_age(feature_set, cfg, score, positives, negatives)
        score = _apply_stage_rank(feature_set, cfg, score, positives, negatives)
        score = _apply_revenue_and_employees(feature_set, cfg, score, positives, negatives)
        score = _apply_product_series_and_price(feature_set, cfg, score, positives, negatives)
        score = _apply_regional_and_manager(feature_set, cfg, score, positives)
        score = _apply_data_quality(feature_set, cfg, score, positives, negatives, risks)
        score = _apply_open_operational_signals(feature_set, cfg, score, negatives)

    score = _clamp(int(round(score)))

    action = _pick_contextual_next_action(feature_set, cfg, score)

    return ScoreResult(
        score=score,
        positives=positives,
        negatives=negatives,
        risks=risks,
        next_best_action=action,
    )


def score_opportunity(
    opportunity: dict[str, Any], rules: dict[str, Any] | None = None
) -> ScoreResult:
    """Score a partir de dict (payload HTTP). CRP-REAL-04: features derivadas do dataset real."""
    feature_set = feature_set_from_payload(opportunity)
    return score_from_features(feature_set, rules)
