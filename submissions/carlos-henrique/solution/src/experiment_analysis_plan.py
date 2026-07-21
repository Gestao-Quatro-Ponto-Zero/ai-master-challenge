"""Pre-specified estimands, statistical analysis plans, guardrails, and stops."""

from __future__ import annotations

from typing import Any


def _estimand(metric: str) -> str:
    if metric in {"ADOPTION_RATE_30D","SUPPORT_RECURRENCE_30D","REACTIVATION_USAGE_RETURN","SUBSCRIPTION_CONTINUATION","SUBSCRIPTION_RECONCILIATION_RATE"}:
        return f"Absolute difference in {metric} between future assigned groups at the pre-specified follow-up."
    if metric == "TIME_TO_OBSERVED_CHURN": return "Difference in the future time-to-observed-churn distribution under the defined quasi-experimental comparison."
    return f"Mean difference in {metric} between future assigned groups at the pre-specified follow-up."


def build_analysis_plans(hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows=[]
    for hypothesis in hypotheses:
        design=hypothesis["design_type"]; metric=hypothesis["primary_metric"]
        primary=("Two-sided difference in proportions with confidence interval" if metric.endswith("RATE_30D") or metric in {"ADOPTION_RATE_30D","REACTIVATION_USAGE_RETURN","SUBSCRIPTION_CONTINUATION","SUBSCRIPTION_RECONCILIATION_RATE"} else "Cluster-aware generalized linear model" if design=="CLUSTER_RANDOMIZED_TRIAL" else "Survival model with pre-specified matching and robust uncertainty" if metric=="TIME_TO_OBSERVED_CHURN" else "Difference in means with robust confidence interval")
        rows.append({
            "experiment_id":hypothesis["experiment_id"],"analysis_population":"ALL_FUTURE_RANDOMIZED_OR_ASSIGNED_ELIGIBLE_UNITS",
            "intention_to_treat":True,"per_protocol_policy":"SECONDARY_ONLY_IF_EXPOSURE_IS_MEASURABLE",
            "primary_estimand":_estimand(metric),"primary_analysis":primary,
            "secondary_analyses":["pre-specified secondary metrics","exposure diagnostic without causal replacement of ITT"],
            "covariate_adjustment":["baseline metric","MRR band","data confidence"],
            "missing_data_policy":"Report missingness by arm; use conservative sensitivity analyses; never impute favorable outcomes.",
            "multiple_testing_policy":"One primary metric per experiment; Holm correction across confirmatory secondary metrics.",
            "outlier_policy":"Pre-specify winsorization sensitivity only; primary analysis retains valid observations.",
            "interim_analysis":"No efficacy interim analysis; operational, safety, and data-quality reviews only.",
            "stopping_rule":"Stop only under a pre-specified safety, futility, data-quality, operational, exhaustion, or completion condition.",
            "heterogeneity_analysis":"Exploratory only for pre-specified MRR band and taxonomy; no individual treatment-effect estimate.",
            "sensitivity_analysis":["complete-case versus conservative missing-data scenario","covariate-adjusted versus unadjusted","contamination sensitivity"],
            "reporting_policy":"Report effect estimate and confidence interval regardless of direction; distinguish practical from statistical significance.",
            "version":"1.0.0",
        })
    return rows


def build_guardrails(hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows=[]
    for hypothesis in hypotheses:
        common=[
            {"guardrail_metric":"DATA_COMPLETENESS","threshold":.80,"direction":"BELOW","evaluation_frequency":"WEEKLY","stop_action":"PAUSE_FOR_DATA_REVIEW","owner":"Data Governance"},
            {"guardrail_metric":"DELIVERY_FAILURE_RATE","threshold":.10,"direction":"ABOVE","evaluation_frequency":"WEEKLY","stop_action":"PAUSE_FOR_OPERATIONAL_REVIEW","owner":"Operational Owner"},
            {"guardrail_metric":"CONSENT_VIOLATION_COUNT","threshold":0,"direction":"ABOVE","evaluation_frequency":"CONTINUOUS_IF_FUTURE_EXECUTION","stop_action":"SAFETY_STOP","owner":"Privacy + Legal"},
        ]
        for index,item in enumerate(common,1): rows.append({"experiment_id":hypothesis["experiment_id"],"guardrail_id":f"{hypothesis['experiment_id']}_G{index:02d}",**item,"specification_only":True})
    return rows


def build_stopping_rules(hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    templates=[
        ("SAFETY_STOP","CONSENT_OR_HARM_EVENT","> 0 confirmed event","Ethics Owner","Pause future delivery and convene review"),
        ("FUTILITY_STOP","CONDITIONAL_POWER","< 20% at pre-specified information fraction","Statistician","Recommend methodological review"),
        ("DATA_QUALITY_STOP","DATA_COMPLETENESS","< 80%","Data Governance","Pause measurement and repair data"),
        ("OPERATIONAL_STOP","DELIVERY_FAILURE_RATE","> 10%","Operational Owner","Pause future delivery"),
        ("SAMPLE_EXHAUSTION","RECRUITMENT","Eligible pool exhausted before required sample","Experiment Owner","Classify underpowered"),
        ("PLANNED_COMPLETION","FOLLOW_UP","Required sample and follow-up complete","Experiment Owner","Lock future analysis dataset"),
    ]
    return [{"experiment_id":h["experiment_id"],"stop_type":kind,"metric":metric,"condition":threshold,"owner":owner,"authorized_decision":decision,"monitoring_implemented":False} for h in hypotheses for kind,metric,threshold,owner,decision in templates]


def validate_analysis_plans(plans: list[dict[str, Any]], guardrails: list[dict[str, Any]], stops: list[dict[str, Any]]) -> dict[str, Any]:
    if not all(row["intention_to_treat"] for row in plans): raise AssertionError("ITT must be primary.")
    if len({row["experiment_id"] for row in plans}) != len(plans): raise AssertionError("One SAP required per experiment.")
    return {"analysis_plans":len(plans),"itt_false":0,"guardrails":len(guardrails),"stopping_rules":len(stops),"monitoring_implemented":0}
