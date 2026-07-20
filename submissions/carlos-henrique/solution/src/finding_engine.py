"""Evidence gates and sensitivity controls for executive findings."""

from __future__ import annotations

from typing import Any, Mapping

import pandas as pd


REQUIRED_FINDING_FIELDS = {
    "finding_id", "title", "statement", "evidence", "population", "metric",
    "comparison", "sample_size", "effect_size", "confidence_level", "limitations",
    "business_relevance", "recommended_investigation", "sensitivity_status",
}


def sensitivity_status(main: float | None, strict: float | None) -> str:
    """Classify magnitude stability between expanded and strict populations."""

    if main is None or strict is None:
        return "UNSTABLE"
    scale = max(abs(main), abs(strict), 1e-12)
    relative_difference = abs(main - strict) / scale
    if relative_difference <= 0.10:
        return "ROBUST"
    if relative_difference <= 0.30:
        return "SENSITIVE"
    return "UNSTABLE"


def build_sensitivity_analysis(
    main_accounts: pd.DataFrame,
    strict_accounts: pd.DataFrame,
    main_journeys: Mapping[str, Any],
    strict_journeys: Mapping[str, Any],
) -> dict[str, Any]:
    def metrics(frame: pd.DataFrame) -> dict[str, float]:
        denominator = len(frame)
        return {
            "account_population": float(denominator),
            "observed_churn_proportion": float(frame["churn_count"].gt(0).mean()),
            "observed_recurring_churn_proportion": float(frame["churn_count"].ge(2).mean()),
            "observed_reactivated_proportion": float(frame["is_reactivated"].mean()),
            "observed_no_usage_30d_proportion": float(frame["feature_event_count_30d"].eq(0).mean()),
            "median_feature_events_90d": float(frame["feature_event_count_90d"].median()),
            "median_support_tickets_90d": float(frame["support_ticket_count_90d"].median()),
            "mrr_at_account_cutoffs_total": float(frame["total_mrr_current"].sum()),
        }

    main = metrics(main_accounts)
    strict = metrics(strict_accounts)
    comparisons = []
    for name in main:
        status = sensitivity_status(main[name], strict[name])
        comparisons.append(
            {
                "metric": name,
                "expanded_value": main[name],
                "strict_value": strict[name],
                "absolute_difference": main[name] - strict[name],
                "relative_difference_to_larger_magnitude": abs(main[name] - strict[name]) / max(abs(main[name]), abs(strict[name]), 1e-12),
                "classification": status,
            }
        )
    main_top = main_journeys["top_complete_journeys"][0]["sequence"] if main_journeys["top_complete_journeys"] else []
    strict_top = strict_journeys["top_complete_journeys"][0]["sequence"] if strict_journeys["top_complete_journeys"] else []
    return {
        "methodology": "All principal metrics are recomputed for VALID only and VALID + VALID_WITH_WARNING.",
        "expanded_population": "VALID + VALID_WITH_WARNING; quarantine excluded",
        "strict_population": "VALID only; quarantine excluded",
        "comparisons": comparisons,
        "journey_top_rank": {
            "expanded_sequence": main_top,
            "strict_sequence": strict_top,
            "classification": "ROBUST" if main_top == strict_top and main_top else "UNSTABLE",
        },
        "classification_rules": {
            "ROBUST": "relative magnitude difference at most 10%",
            "SENSITIVE": "same numeric definition with relative difference above 10% and at most 30%",
            "UNSTABLE": "relative difference above 30%, unavailable result, or changed top journey",
        },
        "limitations": [
            "Thresholds are governance rules, not statistical significance tests.",
            "Strict filtering can change both cutoff dates and available events for an account.",
        ],
    }


def validate_finding(finding: Mapping[str, Any]) -> None:
    missing = REQUIRED_FINDING_FIELDS - set(finding)
    if missing:
        raise ValueError(f"Finding is missing required fields: {sorted(missing)}")
    evidence = finding["evidence"]
    if evidence is None or evidence == {} or evidence == [] or evidence == "":
        raise ValueError("Finding without quantitative evidence is prohibited.")
    if finding["sensitivity_status"] == "UNSTABLE":
        raise ValueError("UNSTABLE findings cannot be promoted as principal findings.")
    if finding["confidence_level"] not in {"HIGH", "MEDIUM", "LOW"}:
        raise ValueError("Invalid confidence level.")


def _metric_status(sensitivity: Mapping[str, Any], metric: str, default: str = "ROBUST") -> str:
    for item in sensitivity["comparisons"]:
        if item["metric"] == metric:
            return str(item["classification"])
    return default


def build_findings(
    health: Mapping[str, Any],
    product: Mapping[str, Any],
    support: Mapping[str, Any],
    revenue: Mapping[str, Any],
    sensitivity: Mapping[str, Any],
) -> dict[str, Any]:
    """Create a short governed list; unstable candidate findings are omitted."""

    accounts = int(product["denominator_accounts"])
    usable = int(health["valid_events"] + health["warning_events"])
    generated = int(health["eligible_generated_events"])
    open_mrr = float(revenue["mrr_associated_with_open_episodes"])
    episode_mrr = float(revenue["episode_mrr_total"])
    candidates: list[dict[str, Any]] = [
        {
            "finding_id": "F001",
            "title": "A cobertura analítica limita a leitura comportamental",
            "statement": "Menos da metade dos eventos gerados compõe a população analítica utilizável.",
            "evidence": {"usable_events": usable, "generated_events": generated, "analytical_coverage_ratio": health["analytical_coverage_ratio"]},
            "population": "Todos os eventos gerados na Fase 2",
            "metric": "analytical_coverage_ratio",
            "comparison": "Eventos utilizáveis / eventos gerados",
            "sample_size": generated,
            "effect_size": float(health["analytical_coverage_ratio"]),
            "confidence_level": "HIGH",
            "limitations": "O indicador mede qualidade analítica, não qualidade do negócio.",
            "business_relevance": "Decisões de retenção exigem ressalva explícita de cobertura.",
            "recommended_investigation": "Priorizar correção upstream das regras temporais com maior quarentena.",
            "sensitivity_status": "ROBUST",
        },
        {
            "finding_id": "F002",
            "title": "Sobreposição de assinaturas é quase universal no snapshot",
            "statement": "A maioria dos episódios possui ao menos uma sobreposição temporal observada.",
            "evidence": {"episodes": int(health["episodes"]), "overlapping_episode_ratio": health["overlapping_episode_ratio"]},
            "population": "Episódios de assinatura governados",
            "metric": "overlapping_episode_ratio",
            "comparison": "Episódios sobrepostos / episódios",
            "sample_size": int(health["episodes"]),
            "effect_size": float(health["overlapping_episode_ratio"]),
            "confidence_level": "HIGH",
            "limitations": "Sobreposição pode ser legítima; não prova duplicidade de cobrança ou churn.",
            "business_relevance": "MRR e churn não devem ser atribuídos a uma assinatura sem regra adicional.",
            "recommended_investigation": "Validar semântica de múltiplas assinaturas com produto e billing.",
            "sensitivity_status": "ROBUST",
        },
        {
            "finding_id": "F003",
            "title": "Ausência de uso recente aparece em parte relevante das contas",
            "statement": "Há contas sem eventos de uso nos 30 dias anteriores ao cutoff governado.",
            "evidence": {"accounts_without_usage_30d": product["accounts_without_usage_30d"], "denominator_accounts": accounts, "observed_share": product["observed_share_without_usage_30d"]},
            "population": "Contas na população ampliada",
            "metric": "observed_no_usage_30d_proportion",
            "comparison": "Contas sem uso 30d / contas",
            "sample_size": accounts,
            "effect_size": float(product["observed_share_without_usage_30d"]),
            "confidence_level": "MEDIUM",
            "limitations": "Uso em quarentena é excluído e ausência medida não equivale a ausência real.",
            "business_relevance": "O grupo merece validação de adoção antes de intervenção.",
            "recommended_investigation": "Cruzar qualitativamente cobertura e contexto de produto, sem inferir causalidade.",
            "sensitivity_status": _metric_status(sensitivity, "observed_no_usage_30d_proportion"),
        },
        {
            "finding_id": "F004",
            "title": "A satisfação tem cobertura parcial entre fechamentos utilizáveis",
            "statement": "Uma parcela dos fechamentos de suporte utilizáveis não possui satisfação observada.",
            "evidence": {"available": support["satisfaction_available"], "missing": support["satisfaction_missing"], "usable_closures": support["usable_ticket_close_events"]},
            "population": "Eventos utilizáveis de fechamento de ticket",
            "metric": "satisfaction_missing_share",
            "comparison": "Satisfação ausente / fechamentos utilizáveis",
            "sample_size": int(support["usable_ticket_close_events"]),
            "effect_size": float(support["satisfaction_missing"] / support["usable_ticket_close_events"]) if support["usable_ticket_close_events"] else 0.0,
            "confidence_level": "MEDIUM",
            "limitations": "Missingness pode não ser aleatório e reduz comparabilidade.",
            "business_relevance": "Satisfação não deve sustentar decisão isoladamente.",
            "recommended_investigation": "Auditar o processo de coleta de satisfação por período e prioridade.",
            "sensitivity_status": "ROBUST",
        },
        {
            "finding_id": "F005",
            "title": "O MRR de episódios abertos domina o snapshot",
            "statement": "A maior parcela do MRR de episódios está associada a episódios administrativamente censurados.",
            "evidence": {"open_episode_mrr": open_mrr, "episode_mrr_total": episode_mrr, "observed_share": open_mrr / episode_mrr if episode_mrr else None},
            "population": "Episódios de assinatura governados",
            "metric": "open_episode_mrr_share",
            "comparison": "MRR de episódios abertos / MRR de episódios",
            "sample_size": int(revenue["denominator_episodes"]),
            "effect_size": float(open_mrr / episode_mrr) if episode_mrr else 0.0,
            "confidence_level": "HIGH",
            "limitations": "MRR associado não é receita salva, perdida ou reconhecida.",
            "business_relevance": "A censura precisa ser preservada na próxima análise temporal.",
            "recommended_investigation": "Usar exposição temporal explícita na Fase 4, sem fechar episódios abertos.",
            "sensitivity_status": "ROBUST",
        },
    ]
    findings: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    for candidate in candidates:
        try:
            validate_finding(candidate)
        except ValueError as exc:
            rejected.append({"finding_id": str(candidate["finding_id"]), "reason": str(exc)})
            continue
        findings.append(candidate)
    return {
        "methodology": "Rule-based evidence gate; no LLM, model, causal ranking or automated recommendation.",
        "population": "Only governed aggregate evidence; quarantine used solely for data health.",
        "finding_count": len(findings),
        "findings": findings[:10],
        "rejected_candidates": rejected,
        "limitations": [
            "Findings are descriptive associations or governance observations.",
            "UNSTABLE candidates are excluded from the principal list.",
        ],
    }
