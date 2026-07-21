"""Run the deterministic, governed Phase 5 journey-mining pipeline."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd


SOLUTION_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = SOLUTION_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from journey_patterns import ngram_rows, pre_churn_analysis, prefix_suffix_patterns, transition_rows  # noqa: E402
from journey_reporting import generate_figures, render_reports, write_json  # noqa: E402
from journey_sequences import assign_length_bands, build_account_journeys  # noqa: E402
from journey_taxonomy import TAXONOMY, classify_journeys  # noqa: E402
from sequential_mining import annotate_population_stability, mine_frequent_sequences  # noqa: E402


PROCESSED = SOLUTION_ROOT / "data" / "processed"
ARTIFACTS = SOLUTION_ROOT / "artifacts"
REPORTS = SOLUTION_ROOT / "reports"
FIGURES = REPORTS / "figures"
EXPECTED_BASE_COMMIT = "83d9b16a270e2227bd67c52e4ebf3ce4aae3eb61"
JSON_NAMES = (
    "journey_mining_summary.json", "transition_matrix.json", "ngram_patterns.json",
    "sequential_patterns.json", "pre_churn_patterns.json", "reactivation_patterns.json",
    "recurring_churn_patterns.json", "journey_taxonomy.json", "journey_stability.json",
    "journey_findings.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_inputs() -> dict[str, Any]:
    manifest = json.loads((ARTIFACTS / "event_log_manifest.json").read_text(encoding="utf-8"))
    verified: dict[str, bool] = {}
    for relative, metadata in manifest["output_hashes"].items():
        path = SOLUTION_ROOT / relative
        verified[relative] = path.is_file() and sha256(path) == metadata["sha256"]
    required = (
        PROCESSED / "account_diagnostic_features.parquet", PROCESSED / "account_survival_dataset.parquet",
        PROCESSED / "account_survival_landmark_30d.parquet", PROCESSED / "account_survival_landmark_60d.parquet",
        PROCESSED / "account_survival_landmark_90d.parquet", ARTIFACTS / "sensitivity_analysis.json",
        ARTIFACTS / "survival_sensitivity.json", ARTIFACTS / "event_type_dictionary.json",
        ARTIFACTS / "temporal_quality_summary.json",
    )
    for path in required:
        verified[str(path.relative_to(SOLUTION_ROOT)).replace("\\", "/")] = path.is_file()
    if manifest.get("reconciliation_unexplained_difference") != 0 or not all(verified.values()):
        raise RuntimeError(f"Phase 5 input gate failed: {[k for k, v in verified.items() if not v]}")
    events = pd.read_parquet(PROCESSED / "event_log.parquet")
    features = pd.read_parquet(PROCESSED / "account_diagnostic_features.parquet")
    if len(features) != 500 or features["account_id"].nunique() != 500:
        raise RuntimeError("Expected exactly 500 account features.")
    if events["is_quarantined"].astype(bool).any():
        raise RuntimeError("Quarantined rows entered the active event log.")
    return {
        "expected_base_commit": EXPECTED_BASE_COMMIT, "verified_files": len(verified),
        "all_hashes_match": True, "event_rows": len(events), "account_rows": len(features),
        "event_log_sha256": sha256(PROCESSED / "event_log.parquet"),
        "account_features_sha256": sha256(PROCESSED / "account_diagnostic_features.parquet"),
        "reconciliation_unexplained_difference": 0,
    }


def _sequences(records: list[dict[str, Any]], population: str, scope: str) -> dict[str, tuple[list[str], list[pd.Timestamp]]]:
    return {
        row["account_id"]: (row["_tokens"], row["_dates"])
        for row in records if row["quality_population"] == population and row["journey_scope"] == scope
    }


def _outcome_comparisons(patterns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs = (
        ("NO_CHURN_OBSERVED", "SINGLE_CHURN"),
        ("NO_CHURN_OBSERVED", "RECURRING_CHURN"),
        ("SINGLE_CHURN", "RECURRING_CHURN"),
        ("CHURNED_NOT_REACTIVATED", "REACTIVATED"),
        ("REACTIVATED", "REACTIVATED_THEN_CHURNED_AGAIN"),
    )
    base = [row for row in patterns if row["journey_scope"] == "FULL_OBSERVED_JOURNEY" and row["representation"] == "COLLAPSED"]
    support: dict[tuple[str, str, str], tuple[int, int]] = {}
    for population in ("MAIN", "STRICT"):
        rows = base
        keys = {(row["pattern_label"], row["outcome"]) for row in rows}
        for pattern, outcome in keys:
            selected = [row for row in rows if row["pattern_label"] == pattern and row["outcome"] == outcome]
            support_column = "account_support" if population == "MAIN" else "strict_support"
            denominator_column = "denominator_accounts" if population == "MAIN" else "strict_denominator_accounts"
            support[(population, pattern, outcome)] = (sum(int(row[support_column]) for row in selected), max([int(row[denominator_column]) for row in selected] or [0]))
        for pattern in {row["pattern_label"] for row in rows}:
            left = support.get((population, pattern, "SINGLE_CHURN"), (0, 0))
            right = support.get((population, pattern, "RECURRING_CHURN"), (0, 0))
            support[(population, pattern, "CHURNED_NOT_REACTIVATED")] = (left[0] + right[0], left[1] + right[1])
    output = []
    for left, right in pairs:
        pattern_names = sorted({row["pattern_label"] for row in base})
        for pattern in pattern_names:
            values: dict[str, dict[str, float | int | None]] = {}
            for population in ("MAIN", "STRICT"):
                left_support, left_n = support.get((population, pattern, left), (0, 0))
                right_support, right_n = support.get((population, pattern, right), (0, 0))
                left_rate = left_support / left_n if left_n else None
                right_rate = right_support / right_n if right_n else None
                values[population] = {
                    "left_support": left_support, "left_denominator": left_n, "left_rate": left_rate,
                    "right_support": right_support, "right_denominator": right_n, "right_rate": right_rate,
                    "absolute_difference_right_minus_left": None if left_rate is None or right_rate is None else right_rate - left_rate,
                    "ratio_right_over_left": None if not left_rate or right_rate is None else right_rate / left_rate,
                }
            main_diff = values["MAIN"]["absolute_difference_right_minus_left"]
            strict_diff = values["STRICT"]["absolute_difference_right_minus_left"]
            stable_direction = main_diff is not None and strict_diff is not None and float(main_diff) * float(strict_diff) >= 0
            if stable_direction and abs(float(strict_diff) - float(main_diff)) <= .05:
                status = "ROBUST"
            elif stable_direction:
                status = "SENSITIVE"
            else:
                status = "UNSTABLE"
            output.append({
                "pattern_label": pattern, "outcomes_compared": [left, right],
                "principal": values["MAIN"], "strict": values["STRICT"], "stability_status": status,
                "small_sample": min(int(values["MAIN"]["left_denominator"]), int(values["MAIN"]["right_denominator"])) < 20,
                "lift_right_vs_left": values["MAIN"]["ratio_right_over_left"],
                "limitations": ["DESCRIPTIVE_NOT_CAUSAL", "FULL_JOURNEY_EXPOSURE_REQUIRES_LENGTH_STRATIFICATION"],
            })
    return output


def _reactivation(records: list[dict[str, Any]]) -> dict[str, Any]:
    scoped = [r for r in records if r["quality_population"] == "MAIN" and r["journey_scope"] == "BETWEEN_CHURN_AND_REACTIVATION"]
    full = [r for r in records if r["quality_population"] == "MAIN" and r["journey_scope"] == "FULL_OBSERVED_JOURNEY" and "REACTIVATION" in r["_tokens"]]
    counts = Counter(tuple(r["_tokens"]) for r in scoped)
    durations = [(pd.Timestamp(r["journey_end"]) - pd.Timestamp(r["journey_start"])).days for r in scoped]
    before_feature, after_feature, before_support, after_support, new_churn = [], [], [], [], 0
    for row in full:
        tokens = row["_raw_tokens"]
        index = tokens.index("REACTIVATION")
        before, after = tokens[:index], tokens[index + 1:]
        before_feature.append(before.count("FEATURE")); after_feature.append(after.count("FEATURE"))
        before_support.append(before.count("SUPPORT_OPEN")); after_support.append(after.count("SUPPORT_OPEN"))
        new_churn += "CHURN" in after
    return {
        "population": "MAIN", "journey_scope": "BETWEEN_CHURN_AND_REACTIVATION",
        "denominator_accounts": len(scoped), "median_days_to_reactivation": float(pd.Series(durations).median()) if durations else None,
        "subscription_start_present": sum("SUBSCRIPTION_START" in r["_tokens"] for r in scoped),
        "feature_use_present": sum("FEATURE" in r["_tokens"] for r in scoped),
        "support_present": sum("SUPPORT_OPEN" in r["_tokens"] for r in scoped),
        "median_feature_events_before_reactivation": float(pd.Series(before_feature).median()) if before_feature else None,
        "median_feature_events_after_reactivation": float(pd.Series(after_feature).median()) if after_feature else None,
        "median_support_opens_before_reactivation": float(pd.Series(before_support).median()) if before_support else None,
        "median_support_opens_after_reactivation": float(pd.Series(after_support).median()) if after_support else None,
        "new_churn_after_reactivation": new_churn,
        "top_sequences": [{"pattern": list(pattern), "pattern_label": " -> ".join(pattern), "account_support": support, "relative_support": support / len(scoped)} for pattern, support in counts.most_common(20)] if scoped else [],
        "limitations": ["DESCRIPTIVE_NOT_CAUSAL", "CUSTOMER_SUCCESS_ACTION_NOT_INFERRED"],
    }


def _recurring(records: list[dict[str, Any]]) -> dict[str, Any]:
    scoped = [r for r in records if r["quality_population"] == "MAIN" and r["journey_scope"] == "FULL_OBSERVED_JOURNEY" and r["_raw_tokens"].count("CHURN") >= 2]
    categories = Counter()
    durations = []
    examples = Counter()
    for row in scoped:
        tokens = row["_raw_tokens"]
        dates = row["_raw_dates"]
        churn_indices = [index for index, token in enumerate(tokens) if token == "CHURN"]
        for start, end in zip(churn_indices, churn_indices[1:]):
            interval = tokens[start:end + 1]
            interval_dates = dates[start:end + 1]
            durations.append((pd.Timestamp(interval_dates[-1]) - pd.Timestamp(interval_dates[0])).days)
            if "REACTIVATION" in interval: categories["REACTIVATION_PATH"] += 1
            if interval.count("SUPPORT_OPEN") >= 3: categories["SUPPORT_HEAVY_INTERVAL"] += 1
            if "FEATURE" in interval: categories["USAGE_RECOVERY_INTERVAL"] += 1
            if len(interval) <= 2 or max([(pd.Timestamp(b) - pd.Timestamp(a)).days for a, b in zip(interval_dates, interval_dates[1:])] or [0]) >= 90: categories["DORMANT_INTERVAL"] += 1
            categories["REPEATED_CHURN_PATH"] += 1
            examples.update([tuple(interval[-min(5, len(interval)):])])
    return {
        "population": "MAIN", "journey_scope": "BETWEEN_RECURRING_CHURNS", "denominator_accounts": len(scoped),
        "intervals_represented": len(durations),
        "median_interval_days": float(pd.Series(durations).median()) if durations else None,
        "classification_counts": dict(sorted(categories.items())),
        "top_patterns": [{"pattern": list(p), "pattern_label": " -> ".join(p), "account_support": n} for p, n in examples.most_common(20)],
        "limitations": ["PARQUET_RETAINS_ONE_SCOPE_ROW_PER_ACCOUNT", "INTERNAL_ANALYSIS_USES_CONSECUTIVE_CHURN_INTERVALS", "DESCRIPTIVE_NOT_CAUSAL"],
    }


def _findings(pre: list[dict[str, Any]], transitions: list[dict[str, Any]], seq: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    eligible_pre = [r for r in pre if r["stability_status"] in {"ROBUST", "SENSITIVE"} and r["churn_denominator"] >= 20 and r["non_churn_denominator"] >= 20 and r["churn_support"] >= 10]
    eligible_pre.sort(key=lambda r: (-abs(r["absolute_difference"] or 0), r["pattern_label"], r["window_days"]))
    for index, row in enumerate(eligible_pre[:4], 1):
        candidates.append({
            "finding_id": f"JF{index:02d}", "title": f"Sufixo pré-churn em janela de {row['window_days']} dias",
            "statement": f"{row['pattern_label']} ocorreu em {row['churn_support']}/{row['churn_denominator']} contas com churn e {row['non_churn_support']}/{row['non_churn_denominator']} sem churn no pseudo-cutoff comparável.",
            "journey_scope": "PRE_FIRST_CHURN", "population": "MAIN_WITH_STRICT_SENSITIVITY",
            "outcomes_compared": ["CHURN_OBSERVED", "NO_CHURN_OBSERVED"], "pattern": row["pattern"], "pattern_type": "FIXED_WINDOW_SUFFIX",
            "sample_size": row["churn_denominator"] + row["non_churn_denominator"], "account_support": row["churn_support"],
            "relative_support": row["churn_rate"], "comparison_metric": "ABSOLUTE_SUPPORT_DIFFERENCE", "estimate": row["absolute_difference"],
            "stability_status": row["stability_status"], "same_day_dependency": "NONE", "exposure_control": row["exposure_control"],
            "confidence_level": "MEDIUM" if row["stability_status"] == "ROBUST" else "LOW",
            "limitations": row["limitations"], "business_relevance": "Prioriza investigação agregada da jornada, sem inferir causa.",
            "recommended_investigation": "Validar o padrão em coorte futura e por banda de comprimento antes de qualquer ação.",
        })
    for row in [r for r in transitions if r["stability_status"] == "ROBUST" and not r["small_sample"] and r["same_day_dependency"] != "HIGH"][:max(0, 6 - len(candidates))]:
        index = len(candidates) + 1
        candidates.append({
            "finding_id": f"JF{index:02d}", "title": "Transição recorrente e estável",
            "statement": f"{row['source_event']} → {row['target_event']} ocorreu em {row['account_support']}/{row['denominator_accounts']} contas no escopo {row['journey_scope']} ({row['outcome']}).",
            "journey_scope": row["journey_scope"], "population": "MAIN_WITH_STRICT_SENSITIVITY", "outcomes_compared": [row["outcome"], "POPULATION_REFERENCE"],
            "pattern": [row["source_event"], row["target_event"]], "pattern_type": "TRANSITION", "sample_size": row["denominator_accounts"],
            "account_support": row["account_support"], "relative_support": row["relative_support"], "comparison_metric": "LIFT_VS_POPULATION",
            "estimate": row["lift_vs_population"], "stability_status": row["stability_status"], "same_day_dependency": row["same_day_dependency"],
            "exposure_control": "ACCOUNT_SUPPORT_AND_SCOPE_STRATIFICATION", "confidence_level": "MEDIUM", "limitations": row["limitations"],
            "business_relevance": "Mapeia uma passagem frequente para investigação operacional agregada.", "recommended_investigation": "Reavaliar por landmark e desfecho na próxima coleta.",
        })
    return candidates[:8]


def validate_outputs(journeys: pd.DataFrame, taxonomy: pd.DataFrame, artifacts: dict[str, Any]) -> None:
    if journeys["account_id"].nunique() > 500: raise AssertionError("More than 500 accounts entered journeys.")
    if journeys.duplicated(["account_id", "journey_scope", "quality_population"]).any(): raise AssertionError("Journey grain violation.")
    if taxonomy.duplicated(["account_id", "journey_scope", "quality_population"]).any(): raise AssertionError("Taxonomy grain violation.")
    serialized = json.dumps(artifacts, ensure_ascii=False).lower()
    for forbidden in ("account_name", "feedback_text", "churn_flag", "caused by", "causa "):
        if forbidden in serialized: raise AssertionError(f"Forbidden content in aggregates: {forbidden}")


def main() -> None:
    gate = validate_inputs()
    events = pd.read_parquet(PROCESSED / "event_log.parquet")
    features = pd.read_parquet(PROCESSED / "account_diagnostic_features.parquet")
    observation_end = pd.Timestamp(events["event_time"].max())
    main_build = build_account_journeys(events, features, strict=False, observation_end=observation_end)
    strict_build = build_account_journeys(events, features, strict=True, observation_end=observation_end)
    all_records = main_build.records + strict_build.records
    journeys, bands = assign_length_bands(pd.concat([main_build.dataset, strict_build.dataset], ignore_index=True))
    journeys.to_parquet(PROCESSED / "account_journeys.parquet", index=False)

    transitions = transition_rows(all_records)
    ngrams = ngram_rows(all_records)
    outcome_comparisons = _outcome_comparisons(ngrams)
    prefixes_suffixes = prefix_suffix_patterns(all_records)
    pre_churn = pre_churn_analysis(all_records, observation_end)
    main_mining = mine_frequent_sequences(_sequences(all_records, "MAIN", "FULL_OBSERVED_JOURNEY"))
    strict_mining = mine_frequent_sequences(_sequences(all_records, "STRICT", "FULL_OBSERVED_JOURNEY"))
    sequence_patterns = annotate_population_stability(main_mining, strict_mining)
    reactivation = _reactivation(all_records)
    recurring = _recurring(all_records)
    taxonomy = classify_journeys(all_records, features)
    taxonomy.to_parquet(PROCESSED / "account_journey_taxonomy.parquet", index=False)
    findings = _findings(pre_churn, transitions, sequence_patterns)
    stability_counts = Counter(row["stability_status"] for row in sequence_patterns)
    taxonomy_counts = taxonomy.loc[taxonomy["quality_population"].eq("MAIN"), "primary_journey_class"].value_counts().sort_index().to_dict()
    dependency_counts = journeys["same_day_order_dependency"].value_counts().sort_index().to_dict()
    summary = {
        "schema_version": "5.0.0", "generation_timestamp": observation_end.isoformat(), "generation_timestamp_basis": "event_log_observation_end",
        "gate_result": "PASS_WITH_WARNINGS", "accounts": int(journeys.loc[journeys["quality_population"].eq("MAIN"), "account_id"].nunique()),
        "event_rows": int(len(events)), "journey_rows": int(len(journeys)), "scope_count": int(journeys["journey_scope"].nunique()),
        "main_accounting": main_build.accounting, "strict_accounting": strict_build.accounting,
        "length_bands": {"short_upper": bands[0], "medium_upper": bands[1], "basis": "MAIN_FULL_OBSERVED_JOURNEY_Q33_Q67"},
        "same_day_dependency_counts": dependency_counts, "transition_rows": len(transitions), "ngram_rows": len(ngrams),
        "patterns_before_pruning": main_mining["patterns_before_pruning"], "patterns_after_pruning": main_mining["patterns_after_pruning"],
        "redundancy_removed": main_mining["redundancy_removed"], "sequential_pattern_count": len(sequence_patterns),
        "finding_count": len(findings), "quarantined_events_used": 0, "input_validation": gate,
        "dependencies": {name: importlib.metadata.version(name) for name in ("pandas", "numpy", "scipy", "matplotlib", "pyarrow", "pytest")},
        "limitations": ["DESCRIPTIVE_NOT_CAUSAL", "VALID_WITH_WARNING_IN_MAIN", "TECHNICAL_SAME_DAY_ORDER", "UNEQUAL_JOURNEY_EXPOSURE_CONTROLLED_NOT_ELIMINATED"],
    }
    artifacts: dict[str, Any] = {
        "journey_mining_summary.json": summary,
        "transition_matrix.json": {"parameters": {"support_unit": "ACCOUNT", "reference": "SCOPE_POPULATION"}, "denominators_explicit": True, "transitions": transitions},
        "ngram_patterns.json": {"parameters": {"n": [2, 3, 4, 5], "min_account_support": 10, "min_relative_support": .02, "min_group_size": 20}, "patterns": ngrams, "prefix_suffix_patterns": prefixes_suffixes, "outcome_comparisons": outcome_comparisons},
        "sequential_patterns.json": {"method": "TESTED_GOVERNED_SUBSEQUENCE_ENUMERATION", "parameters": main_mining["parameters"], "patterns_before_pruning": main_mining["patterns_before_pruning"], "patterns_after_pruning": main_mining["patterns_after_pruning"], "redundancy_removed": main_mining["redundancy_removed"], "patterns": sequence_patterns},
        "pre_churn_patterns.json": {"parameters": {"windows_days": [7, 30, 60, 90], "suffix_lengths": [2, 3, 5], "non_churn_cutoff": "OBSERVATION_END"}, "patterns": pre_churn},
        "reactivation_patterns.json": reactivation,
        "recurring_churn_patterns.json": recurring,
        "journey_taxonomy.json": {"definitions": list(TAXONOMY), "main_distribution": taxonomy_counts, "classification_is_descriptive": True},
        "journey_stability.json": {"population_comparison": "MAIN_VS_STRICT", "status_counts": dict(sorted(stability_counts.items())), "rules": {"ROBUST": "present with materially preserved support and no HIGH ordering", "SENSITIVE": "present with material magnitude variation", "UNSTABLE": "absent, reversed, small, or HIGH-dependent"}},
        "journey_findings.json": {"maximum_findings": 8, "finding_count": len(findings), "promotion_rules": ["ROBUST_OR_EXCEPTIONAL_SENSITIVE", "EXPLICIT_DENOMINATOR", "EXPOSURE_CONTROL", "NO_HIGH_ORDER_DEPENDENCY", "NO_CAUSAL_LANGUAGE"], "findings": findings},
    }
    validate_outputs(journeys, taxonomy, artifacts)
    for name in JSON_NAMES: write_json(ARTIFACTS / name, artifacts[name])
    context = {
        "summary": summary, "findings": findings, "transitions": transitions, "sequential_patterns": sequence_patterns,
        "pre_churn": pre_churn, "reactivation_summary": reactivation, "taxonomy_counts": taxonomy_counts,
        "taxonomy_definitions": TAXONOMY, "stability_counts": dict(stability_counts),
        "journey_lengths": journeys.loc[(journeys["quality_population"] == "MAIN") & (journeys["journey_scope"] == "FULL_OBSERVED_JOURNEY"), "raw_length"].tolist(),
    }
    render_reports(REPORTS, context)
    generate_figures(FIGURES, context)
    print(json.dumps({"gate": summary["gate_result"], "journeys": len(journeys), "patterns": len(sequence_patterns), "findings": len(findings)}, sort_keys=True))


if __name__ == "__main__":
    main()
