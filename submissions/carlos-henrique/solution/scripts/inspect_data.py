"""Run the deterministic, privacy-preserving RavenStack source audit."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

import pandas as pd


SOLUTION_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = SOLUTION_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from data_audit import (  # noqa: E402
    audit_relationship,
    build_raw_manifest,
    build_schema_map,
    classify_leakage,
    ensure_no_raw_text,
    measure_join_inflation,
    profile_dataframe,
    run_consistency_audit,
    run_temporal_audit,
)
from data_loader import (  # noqa: E402
    OFFICIAL_FILES,
    DataLoadError,
    load_all,
    resolve_raw_data_dir,
    validate_all_present,
)


ARTIFACT_DIR = SOLUTION_ROOT / "artifacts"
REPORT_DIR = SOLUTION_ROOT / "reports"
REPOSITORY_ROOT = SOLUTION_ROOT.parents[2]

ARTIFACT_PATHS = {
    "manifest": ARTIFACT_DIR / "raw_file_manifest.json",
    "profile": ARTIFACT_DIR / "data_profile.json",
    "schema": ARTIFACT_DIR / "schema_map.json",
    "relationships": ARTIFACT_DIR / "relationship_matrix.csv",
}
REPORT_PATHS = {
    "data": REPORT_DIR / "data-audit.md",
    "relationships": REPORT_DIR / "relationship-audit.md",
    "temporal": REPORT_DIR / "temporal-audit.md",
}


def write_json(path: Path, payload: object) -> None:
    """Write deterministic UTF-8 JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    path.write_text(rendered + "\n", encoding="utf-8", newline="\n")


def markdown_cell(value: object) -> str:
    """Render a compact Markdown cell without multiline content."""

    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.6f}".rstrip("0").rstrip(".")
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).replace("|", "\\|").replace("\n", " ")


def markdown_table(headers: list[str], rows: Iterable[Iterable[object]]) -> str:
    """Render a deterministic Markdown table."""

    output = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    output.extend(
        "| " + " | ".join(markdown_cell(value) for value in row) + " |"
        for row in rows
    )
    return "\n".join(output)


def write_markdown(path: Path, sections: Iterable[str]) -> None:
    """Write a stable Markdown report."""

    path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n\n".join(section.rstrip() for section in sections if section.strip()) + "\n"
    path.write_text(content, encoding="utf-8", newline="\n")


def infer_granularity(table: str, profile: Mapping[str, Any]) -> tuple[str, str]:
    """Describe observed snapshot grain and its validation status."""

    preferred = {
        "accounts": "account_id",
        "subscriptions": "subscription_id",
        "feature_usage": "usage_id",
        "support_tickets": "ticket_id",
        "churn_events": "churn_event_id",
    }[table]
    result = profile["candidate_keys"].get(preferred, {})
    if result.get("complete_and_unique_in_snapshot"):
        return f"one row per {preferred} in this snapshot", "CANDIDATE"
    if table == "feature_usage":
        composite = profile["candidate_composite_keys"].get(
            "subscription_id+usage_date+feature_name", {}
        )
        if composite.get("complete_and_unique_in_snapshot"):
            return "one row per subscription_id + usage_date + feature_name", "CANDIDATE"
        return "usage event row; supplied IDs and tested business composite are not unique", "INCONCLUSIVE"
    return f"row-level grain is not proven by {preferred}", "INCONCLUSIVE"


def relationship_rows(frames: Mapping[str, pd.DataFrame]) -> list[dict[str, object]]:
    """Audit the four required parent-child relations."""

    specifications = [
        ("accounts", "account_id", "subscriptions", "account_id"),
        ("subscriptions", "subscription_id", "feature_usage", "subscription_id"),
        ("accounts", "account_id", "support_tickets", "account_id"),
        ("accounts", "account_id", "churn_events", "account_id"),
    ]
    return [
        audit_relationship(
            parent_table,
            frames[parent_table],
            parent_column,
            child_table,
            frames[child_table],
            child_column,
        )
        for parent_table, parent_column, child_table, child_column in specifications
    ]


def join_simulations(frames: Mapping[str, pd.DataFrame]) -> list[dict[str, object]]:
    """Run controlled key-only simulations without persisting joined records."""

    simulations = [
        measure_join_inflation(
            frames["accounts"],
            "account_id",
            frames["subscriptions"],
            "account_id",
            label="accounts LEFT JOIN subscriptions",
        ),
        measure_join_inflation(
            frames["subscriptions"],
            "subscription_id",
            frames["feature_usage"],
            "subscription_id",
            label="subscriptions LEFT JOIN feature_usage",
        ),
        measure_join_inflation(
            frames["accounts"],
            "account_id",
            frames["support_tickets"],
            "account_id",
            label="accounts LEFT JOIN support_tickets",
        ),
        measure_join_inflation(
            frames["accounts"],
            "account_id",
            frames["churn_events"],
            "account_id",
            label="accounts LEFT JOIN churn_events",
        ),
    ]

    chain = frames["accounts"][["account_id"]].copy()
    chain_start = len(chain)
    steps: list[dict[str, object]] = []

    chain = chain.merge(
        frames["subscriptions"][["account_id", "subscription_id"]],
        how="left",
        on="account_id",
    )
    steps.append({"step": "subscriptions", "rows": int(len(chain))})
    chain = chain.merge(
        frames["feature_usage"][["subscription_id"]],
        how="left",
        on="subscription_id",
    )
    steps.append({"step": "feature_usage", "rows": int(len(chain))})
    chain = chain.merge(
        frames["support_tickets"][["account_id"]].rename(
            columns={"account_id": "ticket_account_id"}
        ),
        how="left",
        left_on="account_id",
        right_on="ticket_account_id",
    )
    steps.append({"step": "support_tickets", "rows": int(len(chain))})
    chain = chain.merge(
        frames["churn_events"][["account_id"]].rename(
            columns={"account_id": "churn_account_id"}
        ),
        how="left",
        left_on="account_id",
        right_on="churn_account_id",
    )
    steps.append({"step": "churn_events", "rows": int(len(chain))})

    simulations.append(
        {
            "join": "accounts -> subscriptions -> feature_usage -> support_tickets -> churn_events",
            "grain_before": "one row per account_id",
            "rows_before": int(chain_start),
            "rows_after": int(len(chain)),
            "multiplier": round(len(chain) / chain_start, 6) if chain_start else 0.0,
            "unique_source_entities_before": int(
                frames["accounts"]["account_id"].nunique(dropna=True)
            ),
            "unique_source_entities_after": int(chain["account_id"].nunique(dropna=True)),
            "unique_source_entities_preserved": True,
            "many_to_many_risk": True,
            "one_to_many_expansion": True,
            "recommended_strategy": (
                "Do not materialize a mega-table. Build source-specific temporal events and "
                "aggregate as-of features at an explicitly selected grain."
            ),
            "steps": steps,
        }
    )
    return simulations


def leakage_rows(frames: Mapping[str, pd.DataFrame]) -> list[dict[str, str]]:
    """Return only columns with an identified leakage control requirement."""

    rows: list[dict[str, str]] = []
    for table, frame in frames.items():
        for column in frame.columns:
            result = classify_leakage(table, str(column))
            if result["risk"] != "NONE_IDENTIFIED":
                rows.append({"table": table, "column": str(column), **result})
    return rows


def determine_event_log_gate(
    profiles: Mapping[str, Mapping[str, Any]],
    relationships: Iterable[Mapping[str, Any]],
    temporal: Mapping[str, Any],
    consistency: Mapping[str, Any],
) -> tuple[str, list[str]]:
    """Classify feasibility without advancing to event-log construction."""

    reasons: list[str] = []
    invalid_relationships = [
        row for row in relationships if row.get("status") in {"INVALID", "INCONCLUSIVE"}
    ]
    date_columns = temporal.get("temporal_columns", {})
    if invalid_relationships or not date_columns:
        reasons.append("Required relationship or temporal evidence is unavailable.")
        return "BLOCKED", reasons

    preferred_keys = {
        "accounts": "account_id",
        "subscriptions": "subscription_id",
        "feature_usage": "usage_id",
        "support_tickets": "ticket_id",
        "churn_events": "churn_event_id",
    }
    invalid_keys = [
        f"{table}.{column}"
        for table, column in preferred_keys.items()
        if profiles[table]["candidate_keys"].get(column, {}).get("status") != "CANDIDATE"
    ]
    confirmed_temporal = [
        check
        for check in temporal["cross_table_checks"]
        if check["classification"] == "CONFIRMED_ERROR" and check["occurrence_count"] > 0
    ]
    unsafe_relationships = [
        row for row in relationships if row.get("status") == "UNSAFE_WITHOUT_AGGREGATION"
    ]
    high_consistency_warnings = [
        check
        for check in consistency["checks"]
        if check["severity"] == "HIGH" and check["occurrence_count"] > 0
    ]
    if invalid_keys:
        reasons.append("Non-unique preferred identifiers: " + ", ".join(invalid_keys) + ".")
    if confirmed_temporal:
        reasons.append("Confirmed temporal exceptions require explicit Phase 2 treatment.")
    if unsafe_relationships:
        reasons.append("One-to-many relations require event-source separation or aggregation.")
    if high_consistency_warnings:
        reasons.append("High-severity cross-source consistency conflicts require explicit precedence rules.")
    if invalid_keys or confirmed_temporal or unsafe_relationships or high_consistency_warnings:
        return "PASS_WITH_WARNINGS", reasons
    reasons.append("Required keys, dates, and relationships are sufficient at the audited snapshot.")
    return "PASS", reasons


def render_data_report(
    manifest: Mapping[str, Any],
    profiles: Mapping[str, Mapping[str, Any]],
    schema_map: Mapping[str, Any],
    leakage: list[Mapping[str, Any]],
    consistency: Mapping[str, Any],
    gate: str,
    gate_reasons: list[str],
) -> list[str]:
    """Render the structural audit report without business findings."""

    overview_rows = []
    manifest_by_table = {item["table"]: item for item in manifest["files"]}
    for table in OFFICIAL_FILES:
        profile = profiles[table]
        grain, grain_status = infer_granularity(table, profile)
        overview_rows.append(
            [
                table,
                profile["records"],
                profile["column_count"],
                manifest_by_table[table]["physical_lines"],
                profile["exact_duplicate_rows"],
                grain,
                grain_status,
            ]
        )

    schema_rows = []
    for table in OFFICIAL_FILES:
        for column in schema_map["tables"][table]:
            schema_rows.append(
                [
                    table,
                    column["column"],
                    column["dtype_inferred"],
                    column["candidate_role"],
                    column["candidate_key"] or "—",
                    column["leakage_risk"],
                ]
            )

    missing_rows = []
    for table in OFFICIAL_FILES:
        for column, detail in profiles[table]["column_profiles"].items():
            if detail["missing_count"]:
                missing_rows.append(
                    [table, column, detail["missing_count"], detail["missing_rate"]]
                )
    if not missing_rows:
        missing_rows.append(["all", "none", 0, 0.0])

    key_rows = []
    for table in OFFICIAL_FILES:
        for key, detail in profiles[table]["candidate_keys"].items():
            key_rows.append(
                [
                    table,
                    key,
                    detail.get("null_rows", "—"),
                    detail.get("duplicate_excess_rows", "—"),
                    detail["status"],
                ]
            )
        for key, detail in profiles[table]["candidate_composite_keys"].items():
            key_rows.append(
                [
                    table,
                    key,
                    detail.get("null_rows", "—"),
                    detail.get("duplicate_excess_rows", "—"),
                    detail["status"],
                ]
            )

    privacy_rows = []
    for table in OFFICIAL_FILES:
        for column, detail in profiles[table]["text_privacy"].items():
            privacy_rows.append(
                [
                    table,
                    column,
                    detail["missing_rate"],
                    detail["average_length"],
                    detail["maximum_length"],
                    detail["possible_email_count"],
                    detail["possible_phone_count"],
                    detail["possible_url_count"],
                ]
            )

    leakage_table = [
        [
            row["table"],
            row["column"],
            row["risk"],
            row["reason"],
            row["allowed_use"],
            row["prohibited_use"],
            row["decision"],
        ]
        for row in leakage
    ]
    consistency_rows = [
        [
            row["check"],
            row["occurrence_count"],
            row["evaluated_records"],
            row["occurrence_rate"],
            row["severity"],
            row["status"],
            row["interpretation"],
        ]
        for row in consistency["checks"]
    ]

    limitation_items = [
        "A single snapshot validates observed completeness and uniqueness, not cross-snapshot key stability.",
        "Pandas dtypes are inferred load metadata, not an imposed canonical schema.",
        "No causal, churn-driver, risk-segmentation, revenue, or predictive analysis was performed.",
        "Text was assessed only through aggregate regex and length statistics; raw text is excluded.",
    ]
    pending_items = [
        "Define the canonical event identity for feature usage because the preferred usage ID must be evaluated against duplicates.",
        "Define as-of cutoffs and lifecycle rules for multiple subscriptions, churn recurrence, and reactivation.",
        "Keep outcome and post-outcome fields outside pre-churn feature sets.",
    ]

    return [
        "# RavenStack data audit",
        "## 1. Objective\n\nValidate the five raw source tables for structural use in a future temporal event log. This report contains no churn diagnosis or business conclusion.",
        "## 2. Audited files\n\n" + markdown_table(
            ["table", "file", "bytes", "SHA-256", "encoding", "delimiter"],
            [
                [
                    item["table"],
                    item["file"],
                    item["bytes"],
                    item["sha256"],
                    item["encoding"],
                    item["delimiter"],
                ]
                for item in manifest["files"]
            ],
        ),
        "## 3. Methodology\n\nRead-only loading, deterministic hashing, schema profiling, null and uniqueness checks, key tests, regex-only privacy checks, referential audits, key-only join simulations, temporal consistency checks, and explicit leakage classification.",
        "## 4. Table overview and observed grain\n\n" + markdown_table(
            ["table", "records", "columns", "physical lines", "exact duplicates", "observed grain", "status"],
            overview_rows,
        ),
        "## 5. Real schema by table\n\n" + markdown_table(
            ["table", "column", "dtype", "candidate role", "key status", "leakage"],
            schema_rows,
        ),
        "## 6. Granularity\n\nGranularity is inferred from tested uniqueness and completeness in this snapshot. Technical identifiers marked `CANDIDATE` still require source-governance evidence for long-term stability.",
        "## 7. Missingness\n\n" + markdown_table(
            ["table", "column", "missing", "missing rate"], missing_rows
        ),
        "## 8. Duplicates\n\nExact full-row duplicate counts are shown in the overview. Identifier and composite-key duplication is shown with affected key evidence below.",
        "## 9. Candidate keys\n\n" + markdown_table(
            ["table", "candidate", "null rows", "duplicate excess rows", "status"],
            key_rows,
        ),
        "## 10. Structural consistency\n\n" + markdown_table(
            ["check", "count", "evaluated", "rate", "severity", "status", "interpretation"],
            consistency_rows,
        ),
        "## 11. Text fields and privacy\n\nNo raw text is reproduced. Counts below are aggregate regex and length statistics only.\n\n"
        + markdown_table(
            ["table", "column", "missing rate", "avg length", "max length", "email", "phone", "URL"],
            privacy_rows,
        ),
        "## 12. Leakage risks\n\n" + markdown_table(
            ["table", "column", "risk", "reason", "allowed", "prohibited", "decision"],
            leakage_table,
        ),
        "## 13. Limitations\n\n" + "\n".join(f"- {item}" for item in limitation_items),
        "## 14. Pending decisions\n\n" + "\n".join(f"- {item}" for item in pending_items),
        f"## 15. Gate for Phase 2\n\n**{gate}**\n\n"
        + "\n".join(f"- {reason}" for reason in gate_reasons)
        + "\n\nThe audit does not start or materialize the event log.",
    ]


def render_relationship_report(
    relationships: list[Mapping[str, Any]], simulations: list[Mapping[str, Any]]
) -> list[str]:
    """Render referential and join-shape evidence."""

    relation_table = markdown_table(
        [
            "source",
            "target",
            "match rate",
            "orphan rows",
            "cardinality",
            "children/source min-med-max",
            "sources without children",
            "inflation risk",
            "status",
        ],
        [
            [
                f"{row['source_table']}.{row['source_column']}",
                f"{row['target_table']}.{row['target_column']}",
                row["match_rate"],
                row["orphan_rows"],
                row["observed_cardinality"],
                (
                    f"{row['children_per_source_minimum']}-"
                    f"{row['children_per_source_median']}-"
                    f"{row['children_per_source_maximum']}"
                ),
                row["source_values_without_children"],
                row["inflation_risk"],
                row["status"],
            ]
            for row in relationships
        ],
    )
    inflation_table = markdown_table(
        ["join", "before", "after", "multiplier", "entities preserved", "many-to-many risk", "strategy"],
        [
            [
                row["join"],
                row["rows_before"],
                row["rows_after"],
                row["multiplier"],
                row["unique_source_entities_preserved"],
                row["many_to_many_risk"],
                row["recommended_strategy"],
            ]
            for row in simulations
        ],
    )
    rejected = [row for row in relationships if row["status"] == "INVALID"]
    rejected_text = (
        "- None at the tested foreign-key level."
        if not rejected
        else "\n".join(
            f"- {row['source_table']} to {row['target_table']}: {row['observation']}"
            for row in rejected
        )
    )
    return [
        "# RavenStack relationship audit",
        "## 1–5. Tested relations, match rates, cardinalities, and orphans\n\n" + relation_table,
        "## 6. Controlled join inflation\n\nOnly keys were joined in memory; no consolidated table was saved.\n\n" + inflation_table,
        "## 7. Future integration strategy\n\nMaintain source-specific event grains. Aggregate or select as-of child records before entity-level joins, and reconcile row counts and unique entities after every step.",
        "## 8. Rejected relations\n\n" + rejected_text,
        "## 9. Gate for event-log construction\n\nA naïve mega-join is explicitly prohibited whenever the measured multiplier exceeds 1. Event-log construction must union normalized source events rather than multiply child tables against each other.",
    ]


def render_temporal_report(temporal: Mapping[str, Any]) -> list[str]:
    """Render temporal ranges, exceptions, recurrence, and pending rules."""

    column_rows = [
        [
            qualified,
            detail["predominant_format"],
            detail["timezone"],
            detail["granularity"],
            detail["minimum"],
            detail["maximum"],
            detail["missing_count"],
            detail["invalid_count"],
            detail["future_suspect_count"],
        ]
        for qualified, detail in temporal["temporal_columns"].items()
    ]
    check_rows = [
        [
            row["check"],
            row["occurrence_count"],
            row["evaluated_records"],
            row["occurrence_rate"],
            row["classification"],
            row["interpretation"],
        ]
        for row in temporal["cross_table_checks"]
    ]
    recurrence = temporal["churn_recurrence_and_reactivation"]
    recurrence_rows = [[key, value] for key, value in recurrence.items()]
    simultaneous_rows = [
        [key, value] for key, value in temporal["simultaneous_event_rows"].items()
    ]
    return [
        "# RavenStack temporal audit",
        "## 1–4. Temporal columns, ranges, formats, and invalid dates\n\n"
        + markdown_table(
            ["field", "format", "timezone", "grain", "minimum", "maximum", "missing", "invalid", "future"],
            column_rows,
        ),
        "## 5. Temporal inconsistencies and occurrences\n\n"
        + markdown_table(
            ["check", "count", "evaluated", "rate", "classification", "interpretation"], check_rows
        ),
        "## 6–7. Multiple churns and reactivation\n\n"
        + markdown_table(["measure", "value"], recurrence_rows),
        "## 8. Simultaneous events\n\n"
        + markdown_table(["check", "affected rows"], simultaneous_rows),
        "## 9. Temporal leakage risks\n\nOutcome dates and all events after an as-of cutoff are prohibited as pre-churn features. Tickets after churn are occurrences to investigate, not automatically data errors.",
        "## 10. Decisions required for Phase 2\n\n- Define event-time and source-time semantics.\n- Define treatment for repeated usage identifiers and same-time events.\n- Define subscription lifecycle precedence for overlapping or sequential subscriptions.\n- Define the provisional reactivation rule using explicit flags plus subscription chronology.\n- Enforce per-event as-of cutoffs and exclude outcome/post-outcome fields.",
    ]


def execute_audit() -> dict[str, object]:
    """Execute the complete Phase 1 audit and return a safe summary."""

    raw_dir = resolve_raw_data_dir()
    source_paths = validate_all_present(raw_dir)
    frames, load_metadata_objects = load_all(raw_data_dir=raw_dir)
    load_metadata = {
        table: metadata.to_dict() for table, metadata in load_metadata_objects.items()
    }
    records = {table: len(frame) for table, frame in frames.items()}
    manifest = build_raw_manifest(
        source_paths,
        load_metadata,
        records,
        relative_to=REPOSITORY_ROOT,
    )

    profiles = {
        table: profile_dataframe(
            table,
            frame,
            file_name=OFFICIAL_FILES[table],
            file_metadata={
                "sha256": next(
                    item["sha256"] for item in manifest["files"] if item["table"] == table
                ),
                "bytes": next(
                    item["bytes"] for item in manifest["files"] if item["table"] == table
                ),
                "encoding": load_metadata[table]["encoding"],
                "delimiter": load_metadata[table]["delimiter"],
                "physical_lines": next(
                    item["physical_lines"]
                    for item in manifest["files"]
                    if item["table"] == table
                ),
            },
        )
        for table, frame in frames.items()
    }
    schema_map = build_schema_map(frames, profiles)
    relationships = relationship_rows(frames)
    simulations = join_simulations(frames)
    temporal = run_temporal_audit(frames)
    consistency = run_consistency_audit(frames)
    leakage = leakage_rows(frames)
    gate, gate_reasons = determine_event_log_gate(
        profiles, relationships, temporal, consistency
    )

    free_text_values: list[str] = []
    for table, columns in {
        "accounts": ["account_name"],
        "churn_events": ["feedback_text"],
    }.items():
        for column in columns:
            if column in frames[table]:
                free_text_values.extend(frames[table][column].dropna().astype(str).tolist())
    privacy_payload = {
        "manifest": manifest,
        "profiles": profiles,
        "schema_map": schema_map,
        "relationships": relationships,
        "consistency": consistency,
    }
    if not ensure_no_raw_text(privacy_payload, free_text_values):
        raise RuntimeError("Privacy gate failed: raw free text reached an artifact payload.")

    write_json(ARTIFACT_PATHS["manifest"], manifest)
    write_json(ARTIFACT_PATHS["profile"], {"tables": profiles, "structural_consistency": consistency})
    write_json(ARTIFACT_PATHS["schema"], schema_map)

    relationship_fields = [
        "source_table",
        "source_column",
        "target_table",
        "target_column",
        "records_in_source",
        "unique_values_in_source",
        "records_in_target",
        "unique_values_in_target",
        "matching_values",
        "orphan_values",
        "orphan_rows",
        "null_target_keys",
        "match_rate",
        "observed_cardinality",
        "children_per_source_minimum",
        "children_per_source_median",
        "children_per_source_mean",
        "children_per_source_maximum",
        "source_values_without_children",
        "inflation_risk",
        "status",
        "observation",
    ]
    ARTIFACT_PATHS["relationships"].parent.mkdir(parents=True, exist_ok=True)
    with ARTIFACT_PATHS["relationships"].open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=relationship_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(relationships)

    write_markdown(
        REPORT_PATHS["data"],
        render_data_report(
            manifest,
            profiles,
            schema_map,
            leakage,
            consistency,
            gate,
            gate_reasons,
        ),
    )
    write_markdown(
        REPORT_PATHS["relationships"],
        render_relationship_report(relationships, simulations),
    )
    write_markdown(REPORT_PATHS["temporal"], render_temporal_report(temporal))

    return {
        "tables": len(frames),
        "records": records,
        "relationship_count": len(relationships),
        "temporal_check_count": len(temporal["cross_table_checks"]),
        "event_log_gate": gate,
        "gate_reasons": gate_reasons,
        "artifact_paths": [path.relative_to(REPOSITORY_ROOT).as_posix() for path in ARTIFACT_PATHS.values()],
        "report_paths": [path.relative_to(REPOSITORY_ROOT).as_posix() for path in REPORT_PATHS.values()],
    }


def main() -> int:
    """CLI entry point with safe, aggregate-only console output."""

    try:
        summary = execute_audit()
    except (DataLoadError, OSError, RuntimeError, ValueError) as exc:
        print(f"audit-status=FAILED error={type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print("audit-status=OK")
    print(f"tables={summary['tables']}")
    print("records=" + ",".join(f"{key}:{value}" for key, value in summary["records"].items()))
    print(f"relationships={summary['relationship_count']}")
    print(f"temporal-checks={summary['temporal_check_count']}")
    print(f"event-log-gate={summary['event_log_gate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
