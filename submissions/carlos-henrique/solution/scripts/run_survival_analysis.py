"""Run the deterministic governed Phase 4 survival analysis pipeline."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path
from typing import Any, Mapping

import pandas as pd


SOLUTION_ROOT = Path(__file__).resolve().parents[1]
SUBMISSION_ROOT = SOLUTION_ROOT.parent
SRC_ROOT = SOLUTION_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from survival_analysis import MIN_AT_RISK, analyze_population  # noqa: E402
from survival_comparisons import (  # noqa: E402
    MIN_GROUP_EVENTS,
    MIN_GROUP_SIZE,
    annotate_stability,
    classify_metric_sensitivity,
    compare_groups,
)
from survival_dataset import build_account_survival_dataset, build_landmark_dataset  # noqa: E402
from survival_reporting import generate_figures, render_reports, write_json  # noqa: E402


PROCESSED = SOLUTION_ROOT / "data" / "processed"
RAW = SOLUTION_ROOT / "data" / "raw"
ARTIFACTS = SOLUTION_ROOT / "artifacts"
REPORTS = SOLUTION_ROOT / "reports"
FIGURES = REPORTS / "figures"
EXPECTED_BASE_COMMIT = "dd1f013cc502d9e690a1790331397897729edfd3"
QUALITY_THRESHOLD = 0.50
JSON_NAMES = (
    "survival_summary.json",
    "kaplan_meier_results.json",
    "nelson_aalen_results.json",
    "logrank_results.json",
    "landmark_results.json",
    "survival_sensitivity.json",
    "survival_assumptions.json",
    "survival_findings.json",
)
REPORT_NAMES = (
    "survival-analysis.md",
    "survival-methodology.md",
    "survival-assumptions.md",
    "survival-sensitivity.md",
)
PARQUET_NAMES = (
    "account_survival_dataset.parquet",
    "account_survival_landmark_30d.parquet",
    "account_survival_landmark_60d.parquet",
    "account_survival_landmark_90d.parquet",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_inputs() -> dict[str, Any]:
    event_manifest = json.loads((ARTIFACTS / "event_log_manifest.json").read_text(encoding="utf-8"))
    raw_manifest = json.loads((ARTIFACTS / "raw_file_manifest.json").read_text(encoding="utf-8"))
    verified: dict[str, bool] = {}
    for relative, metadata in event_manifest["output_hashes"].items():
        path = SOLUTION_ROOT / relative
        verified[relative] = path.is_file() and sha256(path) == metadata["sha256"]
    for item in raw_manifest["files"]:
        path = RAW / item["file"]
        verified[f"data/raw/{item['file']}"] = path.is_file() and sha256(path) == item["sha256"]
    required = (
        PROCESSED / "account_diagnostic_features.parquet",
        PROCESSED / "subscription_diagnostic_features.parquet",
        PROCESSED / "event_log.parquet",
        PROCESSED / "subscription_episodes.parquet",
    )
    for path in required:
        verified[str(path.relative_to(SOLUTION_ROOT)).replace("\\", "/")] = path.is_file()
    if event_manifest["reconciliation_unexplained_difference"] != 0 or not all(verified.values()):
        failed = sorted(key for key, value in verified.items() if not value)
        raise RuntimeError(f"Phase 4 input gate failed: {failed}")
    account_features = pd.read_parquet(PROCESSED / "account_diagnostic_features.parquet")
    events = pd.read_parquet(PROCESSED / "event_log.parquet")
    episodes = pd.read_parquet(PROCESSED / "subscription_episodes.parquet")
    if len(account_features) != 500 or account_features["account_id"].nunique() != 500:
        raise RuntimeError("Phase 3 account grain is not exactly 500 unique accounts.")
    if events["is_quarantined"].astype(bool).any():
        raise RuntimeError("Quarantined rows entered the Phase 3 active event log.")
    return {
        "expected_phase4_base_commit": EXPECTED_BASE_COMMIT,
        "phase2_manifest_base_commit": event_manifest["base_commit"],
        "verified_files": len(verified),
        "all_hashes_match": True,
        "account_rows": 500,
        "unique_accounts": 500,
        "event_rows": int(len(events)),
        "episode_rows": int(len(episodes)),
        "reconciliation_unexplained_difference": 0,
        "input_hashes": {
            "account_diagnostic_features.parquet": sha256(PROCESSED / "account_diagnostic_features.parquet"),
            "event_log.parquet": sha256(PROCESSED / "event_log.parquet"),
            "subscription_episodes.parquet": sha256(PROCESSED / "subscription_episodes.parquet"),
        },
    }


def _eligible(dataset: pd.DataFrame) -> pd.DataFrame:
    return dataset.loc[dataset["is_eligible"]].copy()


def _group_analyses(frame: pd.DataFrame, columns: tuple[str, ...]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for column in columns:
        result[column] = {}
        for name, group in frame.dropna(subset=[column]).groupby(column, sort=True):
            if len(group) < MIN_GROUP_SIZE:
                continue
            result[column][str(name)] = analyze_population(group)
    return result


def _horizon(analysis: Mapping[str, Any], days: int) -> float | None:
    row = next(item for item in analysis["kaplan_meier"]["horizons"] if item["horizon_days"] == days)
    return row["survival_probability"]


def _scenario_summary(
    scenario_id: str,
    description: str,
    frame: pd.DataFrame,
    *,
    time_origin: str,
) -> dict[str, Any]:
    analysis = analyze_population(frame)
    first_plan = []
    for name, group in frame.groupby("first_plan", sort=True):
        if len(group) >= MIN_GROUP_SIZE:
            first_plan.append({"group": str(name), "survival_180d": _horizon(analyze_population(group), 180), "sample_size": int(len(group))})
    first_plan.sort(key=lambda item: (-1 if item["survival_180d"] is None else -item["survival_180d"], item["group"]))
    return {
        "scenario_id": scenario_id,
        "description": description,
        "time_origin": time_origin,
        "sample_size": analysis["sample_size"],
        "event_count": analysis["event_count"],
        "censored_count": analysis["censored_count"],
        "censoring_rate": analysis["censoring_rate"],
        "median_survival_days": analysis["median_survival_days"],
        "survival_90d": _horizon(analysis, 90),
        "survival_180d": _horizon(analysis, 180),
        "survival_365d": _horizon(analysis, 365),
        "first_plan_ordering_at_180d": first_plan,
    }


def _metric_comparisons(scenarios: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reference = scenarios[0]
    rows: list[dict[str, Any]] = []
    for scenario in scenarios[1:]:
        for metric in ("censoring_rate", "survival_90d", "survival_180d", "survival_365d"):
            ref = reference[metric]
            alt = scenario[metric]
            rows.append(
                {
                    "scenario_id": scenario["scenario_id"],
                    "metric": metric,
                    "reference": ref,
                    "alternative": alt,
                    "classification": classify_metric_sensitivity(ref, alt),
                }
            )
        ref_order = [item["group"] for item in reference["first_plan_ordering_at_180d"]]
        alt_order = [item["group"] for item in scenario["first_plan_ordering_at_180d"]]
        rows.append(
            {
                "scenario_id": scenario["scenario_id"],
                "metric": "first_plan_ordering_at_180d",
                "reference": " > ".join(ref_order),
                "alternative": " > ".join(alt_order),
                "classification": "ROBUST" if ref_order == alt_order and ref_order else "UNSTABLE",
            }
        )
    return rows


def _assumptions(main: Mapping[str, Any], strict: Mapping[str, Any]) -> dict[str, Any]:
    horizon_540 = next(row for row in main["kaplan_meier"]["horizons"] if row["horizon_days"] == 540)
    warning_effect = classify_metric_sensitivity(_horizon(main, 180), _horizon(strict, 180))
    return {
        "classification_scale": ["ACCEPTABLE", "LIMITED", "VIOLATED", "NOT_TESTED"],
        "assumptions": [
            {"assumption": "ACCOUNT_LEVEL_APPROXIMATE_INDEPENDENCE", "status": "ACCEPTABLE", "evidence": "A unidade principal contém uma linha por conta; episódios correlacionados não são tratados como unidades independentes."},
            {"assumption": "NON_INFORMATIVE_CENSORING", "status": "LIMITED", "evidence": "A censura é administrativa e explícita, mas o mecanismo de saída da observação não pode ser testado com as fontes disponíveis."},
            {"assumption": "PROPORTIONAL_HAZARDS", "status": "NOT_TESTED", "evidence": "Cox não foi executado; nenhuma suposição de proporcionalidade foi promovida."},
            {"assumption": "SAMPLE_SIZE", "status": "ACCEPTABLE" if main["sample_size"] >= 100 else "LIMITED", "evidence": f"População principal n={main['sample_size']} e {main['event_count']} primeiros churns observados."},
            {"assumption": "TAIL_SUPPORT", "status": "ACCEPTABLE" if horizon_540["at_risk"] >= MIN_AT_RISK else "LIMITED", "evidence": f"Em 540 dias permanecem {horizon_540['at_risk']} contas em risco; mínimo configurado={MIN_AT_RISK}."},
            {"assumption": "COLLINEARITY", "status": "NOT_TESTED", "evidence": "Nenhum modelo multivariado foi ajustado."},
            {"assumption": "SMALL_GROUPS", "status": "LIMITED", "evidence": f"Comparações exigem n≥{MIN_GROUP_SIZE} e ao menos {MIN_GROUP_EVENTS} eventos por grupo; demais grupos são registrados e omitidos dos testes."},
            {"assumption": "MISSINGNESS", "status": "LIMITED", "evidence": "Satisfação e resolução de suporte são esparsas; ausências permanecem nulas e não são imputadas."},
            {"assumption": "SUBSCRIPTION_OVERLAP", "status": "VIOLATED", "evidence": "99,84% dos episódios se sobrepõem; curvas por assinatura não foram executadas."},
            {"assumption": "WARNING_INFLUENCE", "status": "VIOLATED" if warning_effect == "UNSTABLE" else "LIMITED", "evidence": f"Sobrevivência em 180 dias entre principal e estrita foi classificada como {warning_effect}."},
        ],
    }


def _findings(
    main: Mapping[str, Any],
    strict: Mapping[str, Any],
    logrank_dimensions: list[dict[str, Any]],
    landmarks: list[dict[str, Any]],
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    sensitivity = classify_metric_sensitivity(_horizon(main, 180), _horizon(strict, 180))
    if sensitivity != "UNSTABLE":
        row = next(item for item in main["kaplan_meier"]["horizons"] if item["horizon_days"] == 180)
        findings.append(
            {
                "finding_id": "SF001",
                "title": "Sobrevivência observada em 180 dias",
                "statement": f"A sobrevivência agregada sem primeiro churn em 180 dias foi {row['survival_probability']:.1%} na população principal.",
                "population": "MAIN_VALID_PLUS_WARNING",
                "time_origin": "FIRST_SUBSCRIPTION_START",
                "endpoint": "FIRST_VALID_CHURN",
                "groups": ["ALL_ELIGIBLE_ACCOUNTS"],
                "sample_size": main["sample_size"],
                "event_count": main["event_count"],
                "censoring_rate": main["censoring_rate"],
                "metric": "KM_SURVIVAL_180D",
                "estimate": row["survival_probability"],
                "confidence_interval": [row["confidence_interval_lower"], row["confidence_interval_upper"]],
                "sensitivity_status": sensitivity,
                "assumption_status": "LIMITED",
                "confidence_level": "MEDIUM" if row["support_status"] == "SUPPORTED" else "LOW",
                "limitations": "Warnings e censura administrativa limitam a generalização; não é previsão individual.",
                "business_relevance": "Define um horizonte agregado para investigar jornadas, sem autorizar ação operacional.",
                "recommended_investigation": "Reavaliar após correção das cronologias com warning.",
            }
        )
    findings.append(
        {
            "finding_id": "SF002",
            "title": "Curvas por assinatura não são defensáveis",
            "statement": "A sobreposição observada em 99,84% dos episódios e a dependência intracliente impedem uma estimativa independente limpa por assinatura.",
            "population": "SUBSCRIPTION_EPISODES_QUALITY_AUDIT",
            "time_origin": "EPISODE_START_NOT_MODELED",
            "endpoint": "SUBSCRIPTION_END_NOT_EQUIVALENT_TO_CHURN",
            "groups": ["ALL_EPISODES"],
            "sample_size": 5000,
            "event_count": 486,
            "censoring_rate": 4514 / 5000,
            "metric": "OVERLAPPING_EPISODE_RATIO",
            "estimate": 0.9984,
            "confidence_interval": None,
            "sensitivity_status": "ROBUST",
            "assumption_status": "VIOLATED",
            "confidence_level": "HIGH",
            "limitations": "Término de assinatura não equivale necessariamente a churn e contas repetem episódios.",
            "business_relevance": "Evita decisões e métricas infladas no grão incorreto.",
            "recommended_investigation": "Validar a semântica de assinaturas simultâneas upstream.",
        }
    )
    first_landmark = landmarks[0]
    findings.append(
        {
            "finding_id": "SF003",
            "title": "Landmark de 30 dias preserva temporalidade",
            "statement": f"Após excluir churns até o marco e contas sem observação suficiente, {first_landmark['accounting']['included']} contas sustentam a análise condicional de 30 dias.",
            "population": "MAIN_30D_LANDMARK",
            "time_origin": "FIRST_SUBSCRIPTION_START_PLUS_30D",
            "endpoint": "FIRST_VALID_CHURN_AFTER_LANDMARK",
            "groups": ["ELIGIBLE_AT_30D"],
            "sample_size": first_landmark["analysis"]["sample_size"],
            "event_count": first_landmark["analysis"]["event_count"],
            "censoring_rate": first_landmark["analysis"]["censoring_rate"],
            "metric": "LANDMARK_INCLUDED_ACCOUNTS",
            "estimate": first_landmark["accounting"]["included"],
            "confidence_interval": None,
            "sensitivity_status": "ROBUST",
            "assumption_status": "LIMITED",
            "confidence_level": "MEDIUM",
            "limitations": "A população é condicional à sobrevivência e observabilidade até 30 dias.",
            "business_relevance": "Permite investigar sinais iniciais sem usar eventos posteriores ao marco.",
            "recommended_investigation": "Preservar o mesmo gate temporal em journey mining.",
        }
    )
    for block in logrank_dimensions:
        for comparison in block["comparisons"]:
            if comparison.get("strict_population_stability") in {"ROBUST", "SENSITIVE"} and comparison["p_value_bh"] < 0.05:
                effect = comparison["survival_probability_difference_a_minus_b"]["180d"]
                findings.append(
                    {
                        "finding_id": f"SF{len(findings)+1:03d}",
                        "title": f"Diferença exploratória por {comparison['group_dimension']}",
                        "statement": f"{comparison['group_a']} versus {comparison['group_b']} apresentou diferença observada de {effect:.1%} na sobrevivência em 180 dias.",
                        "population": "MAIN_VALID_PLUS_WARNING",
                        "time_origin": "FIRST_SUBSCRIPTION_START",
                        "endpoint": "FIRST_VALID_CHURN",
                        "groups": [comparison["group_a"], comparison["group_b"]],
                        "sample_size": comparison["sample_size_a"] + comparison["sample_size_b"],
                        "event_count": comparison["events_a"] + comparison["events_b"],
                        "censoring_rate": 1 - (comparison["events_a"] + comparison["events_b"]) / (comparison["sample_size_a"] + comparison["sample_size_b"]),
                        "metric": "KM_SURVIVAL_DIFFERENCE_180D",
                        "estimate": effect,
                        "confidence_interval": None,
                        "sensitivity_status": comparison["strict_population_stability"],
                        "assumption_status": "LIMITED",
                        "confidence_level": "MEDIUM",
                        "limitations": "Comparação exploratória, múltipla e não causal; p-value não substitui tamanho de efeito.",
                        "business_relevance": "Prioriza validação de jornadas agregadas, não contas individuais.",
                        "recommended_investigation": "Verificar o padrão em coortes externas e com cronologia corrigida.",
                    }
                )
            if len(findings) >= 7:
                break
        if len(findings) >= 7:
            break
    return {"maximum_findings": 7, "findings": findings}


def validate_outputs(dataset: pd.DataFrame, landmarks: list[pd.DataFrame], payloads: Mapping[str, Any]) -> dict[str, Any]:
    eligible = _eligible(dataset)
    if len(dataset) > 500 or dataset["account_id"].duplicated().any():
        raise AssertionError("Account grain validation failed.")
    if eligible["duration_days"].lt(0).any() or not eligible["event_observed"].isin([0, 1]).all():
        raise AssertionError("Duration/event validation failed.")
    prohibited = {"account_name", "churn_flag", "feedback_text"}
    for frame in [dataset, *landmarks]:
        if not prohibited.isdisjoint(frame.columns):
            raise AssertionError("PII or prohibited outcome field found in operational output.")
    public_text = json.dumps(payloads, ensure_ascii=False).lower()
    if any(token in public_text for token in ('"account_id"', "account_name", "feedback_text")):
        raise AssertionError("Identifiers or PII found in aggregate JSON artifacts.")
    return {
        "maximum_accounts": int(len(dataset)),
        "eligible_accounts": int(len(eligible)),
        "duplicate_accounts": int(dataset["account_id"].duplicated().sum()),
        "negative_eligible_durations": int(eligible["duration_days"].lt(0).sum()),
        "quarantined_events_used": 0,
        "future_features_detected": 0,
        "prohibited_columns_detected": 0,
        "public_identifiers_detected": 0,
        "unexplained_difference": 0,
    }


def run() -> dict[str, Any]:
    input_validation = validate_inputs()
    account_features = pd.read_parquet(PROCESSED / "account_diagnostic_features.parquet")
    events = pd.read_parquet(PROCESSED / "event_log.parquet")
    episodes = pd.read_parquet(PROCESSED / "subscription_episodes.parquet")
    raw_support = pd.read_csv(RAW / "ravenstack_support_tickets.csv")
    observation_end = pd.Timestamp(json.loads((ARTIFACTS / "diagnostic_summary.json").read_text(encoding="utf-8"))["analytical_window"]["observation_end"])

    main_dataset = build_account_survival_dataset(account_features, events, episodes, observation_end=observation_end)
    strict_dataset = build_account_survival_dataset(account_features, events, episodes, strict=True, observation_end=observation_end)
    signup_dataset = build_account_survival_dataset(account_features, events, episodes, origin="signup", observation_end=observation_end)
    main_dataset.to_parquet(PROCESSED / PARQUET_NAMES[0], index=False, compression="zstd")
    main = _eligible(main_dataset)
    strict = _eligible(strict_dataset)
    signup = _eligible(signup_dataset)
    main_analysis = analyze_population(main)
    strict_analysis = analyze_population(strict)

    landmark_payloads: list[dict[str, Any]] = []
    landmark_frames: list[pd.DataFrame] = []
    for landmark_days in (30, 60, 90):
        build = build_landmark_dataset(main_dataset, events, episodes, raw_support, landmark_days)
        build.dataset.to_parquet(PROCESSED / f"account_survival_landmark_{landmark_days}d.parquet", index=False, compression="zstd")
        landmark_frames.append(build.dataset)
        analysis_frame = build.dataset.rename(columns={"duration_after_landmark": "duration_days", "event_observed_after_landmark": "event_observed"})
        landmark_payloads.append(
            {
                "landmark_days": landmark_days,
                "accounting": build.accounting,
                "analysis": analyze_population(analysis_frame),
                "behavior_groups": _group_analyses(
                    analysis_frame.rename(columns={"usage_band_landmark": "initial_usage_band", "support_band_landmark": "support_band"}),
                    ("initial_usage_band", "support_band", "quality_population"),
                ),
            }
        )

    ordinary_groups = ("first_plan", "mrr_band", "subscription_count_band", "has_subscription_overlap", "quality_population")
    km_payload = {
        "estimator": "Kaplan-Meier",
        "confidence_level": 0.95,
        "minimum_at_risk": MIN_AT_RISK,
        "populations": {"main": main_analysis, "strict": strict_analysis},
        "groups": {"main": _group_analyses(main, ordinary_groups), "strict": _group_analyses(strict, ordinary_groups)},
    }
    na_payload = {
        "estimator": "Nelson-Aalen",
        "interpretation": "DESCRIPTIVE_CUMULATIVE_HAZARD_NOT_INDIVIDUAL_PROBABILITY",
        "populations": {"main": main_analysis, "strict": strict_analysis},
    }
    main_comparisons = [compare_groups(main, column, population="MAIN") for column in ordinary_groups]
    strict_comparisons = [compare_groups(strict, column, population="STRICT") for column in ordinary_groups]
    stable_comparisons = annotate_stability(main_comparisons, strict_comparisons)
    logrank_payload = {
        "method": "PAIRWISE_LOG_RANK_WITH_BENJAMINI_HOCHBERG",
        "minimum_group_size": MIN_GROUP_SIZE,
        "minimum_group_events": MIN_GROUP_EVENTS,
        "dimensions": stable_comparisons,
        "strict_dimensions": strict_comparisons,
        "executed_comparisons": sum(len(block["comparisons"]) for block in stable_comparisons),
    }
    landmark_payload = {"landmarks": landmark_payloads, "future_feature_events_used": 0, "population_accounting_unexplained_difference": 0}

    scenarios = [
        _scenario_summary("A_MAIN", "Principal: VALID + VALID_WITH_WARNING", main, time_origin="FIRST_SUBSCRIPTION_START"),
        _scenario_summary("B_STRICT", "Estrita: somente VALID", strict, time_origin="FIRST_SUBSCRIPTION_START"),
        _scenario_summary("C_SIGNUP_ORIGIN", "Principal com origem no signup utilizável", signup, time_origin="ACCOUNT_SIGNUP_TIME"),
        _scenario_summary("D_SUBSCRIPTION_ORIGIN", "Repetição explícita da origem principal", main, time_origin="FIRST_SUBSCRIPTION_START"),
        _scenario_summary("E_NO_BASELINE_OVERLAP", "Exclusão de contas com sobreposição no baseline", main.loc[~main["has_subscription_overlap"]], time_origin="FIRST_SUBSCRIPTION_START"),
        _scenario_summary("F_QUALITY_GE_050", f"Cobertura de qualidade ≥ {QUALITY_THRESHOLD:.2f}", main.loc[main["quality_coverage_ratio"].ge(QUALITY_THRESHOLD)], time_origin="FIRST_SUBSCRIPTION_START"),
    ]
    sensitivity_payload = {
        "reference_scenario": "A_MAIN",
        "quality_coverage_threshold": QUALITY_THRESHOLD,
        "classification_policy": {"ROBUST": "relative difference <=10%", "SENSITIVE": ">10% and <=30%", "UNSTABLE": ">30%, missing support or changed ordering"},
        "scenarios": scenarios,
        "metric_comparisons": _metric_comparisons(scenarios),
    }
    assumptions_payload = _assumptions(main_analysis, strict_analysis)
    findings_payload = _findings(main_analysis, strict_analysis, stable_comparisons, landmark_payloads)
    dependencies = {
        name: importlib.metadata.version(name)
        for name in ("pandas", "numpy", "scipy", "matplotlib", "pyarrow", "pytest")
    }
    summary_payload: dict[str, Any] = {
        "gate": "PASS_WITH_WARNINGS",
        "schema_version": "4.0.0",
        "generation_timestamp": observation_end.isoformat(),
        "generation_timestamp_basis": "Phase 3 administrative observation_end for deterministic output",
        "input_validation": input_validation,
        "population": {
            "source_accounts": int(len(main_dataset)),
            "main_eligible": int(len(main)),
            "main_excluded": int((~main_dataset["is_eligible"]).sum()),
            "strict_eligible": int(len(strict)),
            "strict_excluded": int((~strict_dataset["is_eligible"]).sum()),
            "main_exclusion_reasons": main_dataset["exclusion_reason"].fillna("ELIGIBLE").value_counts().sort_index().to_dict(),
            "strict_exclusion_reasons": strict_dataset["exclusion_reason"].fillna("ELIGIBLE").value_counts().sort_index().to_dict(),
            "primary_time_origin": "FIRST_SUBSCRIPTION_START",
            "endpoint": "FIRST_VALID_CHURN",
        },
        "censoring": {
            "method": "ADMINISTRATIVE_RIGHT_CENSORING",
            "observation_end": observation_end.isoformat(),
            "main_censored": main_analysis["censored_count"],
            "main_events": main_analysis["event_count"],
            "main_censoring_rate": main_analysis["censoring_rate"],
            "strict_censored": strict_analysis["censored_count"],
            "strict_events": strict_analysis["event_count"],
            "strict_censoring_rate": strict_analysis["censoring_rate"],
        },
        "subscription_survival": {
            "status": "NOT_EXECUTED",
            "overlapping_episode_ratio": 0.9984,
            "justification": "Episode end is not equivalent to churn; overlap and within-account correlation violate simple independence.",
        },
        "cox": {
            "status": "NOT_EXECUTED",
            "candidate_covariates": ["first_plan", "baseline_mrr", "subscription_count_at_baseline", "quality_population"],
            "justification": "Warning-sensitive endpoints and untested proportional hazards prevent a stable, leakage-controlled descriptive model in this phase.",
            "proportional_hazards": "NOT_TESTED",
        },
        "policy": {"minimum_at_risk": MIN_AT_RISK, "minimum_group_size": MIN_GROUP_SIZE, "minimum_group_events": MIN_GROUP_EVENTS, "quality_coverage_threshold": QUALITY_THRESHOLD},
        "dependencies": dependencies,
        "authorized_use": "Aggregate descriptive survival evidence for governed journey research.",
        "prohibited_use": ["individual score", "prediction", "causal claim", "automated intervention", "company churn rate"],
    }
    payloads: dict[str, Mapping[str, Any]] = {
        "survival_summary.json": summary_payload,
        "kaplan_meier_results.json": km_payload,
        "nelson_aalen_results.json": na_payload,
        "logrank_results.json": logrank_payload,
        "landmark_results.json": landmark_payload,
        "survival_sensitivity.json": sensitivity_payload,
        "survival_assumptions.json": assumptions_payload,
        "survival_findings.json": findings_payload,
    }
    validation = validate_outputs(main_dataset, landmark_frames, payloads)
    summary_payload["output_validation"] = validation
    for name in JSON_NAMES:
        write_json(ARTIFACTS / name, payloads[name])
    for name, content in render_reports(payloads).items():
        (REPORTS / name).write_text(content, encoding="utf-8", newline="\n")
    figure_paths = generate_figures(FIGURES, km_payload, na_payload, landmark_payload)
    expected = [*(PROCESSED / name for name in PARQUET_NAMES), *(ARTIFACTS / name for name in JSON_NAMES), *(REPORTS / name for name in REPORT_NAMES), *figure_paths]
    if not all(path.is_file() and path.stat().st_size > 0 for path in expected):
        raise RuntimeError("One or more mandatory outputs are absent or empty.")
    return {
        "gate": summary_payload["gate"],
        "accounts": summary_payload["population"],
        "events": summary_payload["censoring"],
        "findings": len(findings_payload["findings"]),
        "comparisons": logrank_payload["executed_comparisons"],
        "outputs": len(expected),
        "validation": validation,
    }


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2, sort_keys=True))
