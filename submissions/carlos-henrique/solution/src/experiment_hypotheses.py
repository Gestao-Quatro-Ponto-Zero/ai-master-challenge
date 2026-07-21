"""Governed hypothesis registry separating observation, mechanism, and future test."""

from __future__ import annotations

from typing import Any

ALLOWED_METRICS = {
    "ADOPTION_RATE_30D", "ACTIVE_USAGE_DAYS_30D", "FEATURE_DIVERSITY_30D",
    "FEATURE_DIVERSITY_90D", "TIME_TO_FIRST_FEATURE", "SUPPORT_REOPEN_RATE",
    "SUPPORT_RECURRENCE_30D", "SATISFACTION_RATE", "REACTIVATION_USAGE_RETURN",
    "SUBSCRIPTION_CONTINUATION", "OBSERVED_CHURN_RATE", "TIME_TO_OBSERVED_CHURN",
    "DATA_COMPLETENESS", "TIMESTAMP_VALIDITY_RATE", "SUBSCRIPTION_RECONCILIATION_RATE",
}

EXPERIMENT_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {"experiment_id":"EXP001","experiment_name":"HIGH_MRR_LOW_ENGAGEMENT_ADOPTION","queue":"HIGH_MRR_LOW_ENGAGEMENT_REVIEW","hypothesis_id":"H001","watchlist_rule_ids":["W001","W002"],"intervention_id":"I001","observation":"Higher associated-MRR accounts showed low recent usage at the historical cutoff.","mechanism_hypothesis":"Structured product education may change observed 30-day adoption; the mechanism is untested.","design_type":"RANDOMIZED_CONTROLLED_TRIAL","unit_of_analysis":"ACCOUNT","unit_of_randomization":"ACCOUNT","primary_metric":"ADOPTION_RATE_30D","secondary_metrics":["ACTIVE_USAGE_DAYS_30D","FEATURE_DIVERSITY_30D","OBSERVED_CHURN_RATE"],"guardrail_metrics":["SUPPORT_RECURRENCE_30D","SATISFACTION_RATE"],"minimum_detectable_effect":0.10,"directionality":"INCREASE","expected_duration":30,"follow_up_window":30,"contamination_risk":"LOW","ethical_risk":"MEDIUM","operational_complexity":"MEDIUM"},
    {"experiment_id":"EXP002","experiment_name":"LOW_ENGAGEMENT_FEATURE_DISCOVERY","queue":"ADOPTION_REVIEW","hypothesis_id":"H002","watchlist_rule_ids":["W003","W016"],"intervention_id":"I002","observation":"Some accounts showed low or narrow feature adoption at the cutoff.","mechanism_hypothesis":"Non-coercive in-app discovery may change feature diversity; the mechanism is untested.","design_type":"RANDOMIZED_CONTROLLED_TRIAL","unit_of_analysis":"ACCOUNT","unit_of_randomization":"ACCOUNT","primary_metric":"FEATURE_DIVERSITY_30D","secondary_metrics":["ADOPTION_RATE_30D","ACTIVE_USAGE_DAYS_30D"],"guardrail_metrics":["SUPPORT_RECURRENCE_30D","SATISFACTION_RATE"],"minimum_detectable_effect":0.50,"directionality":"INCREASE","expected_duration":30,"follow_up_window":30,"contamination_risk":"MEDIUM","ethical_risk":"LOW","operational_complexity":"HIGH"},
    {"experiment_id":"EXP003","experiment_name":"SUPPORT_FOLLOW_UP","queue":"SUPPORT_JOURNEY_REVIEW","hypothesis_id":"H003","watchlist_rule_ids":["W009","W010"],"intervention_id":"I004","observation":"Support events occurred near churn or repeatedly in some historical journeys.","mechanism_hypothesis":"A consistent post-resolution process may change support recurrence or measured satisfaction; the mechanism is untested.","design_type":"CLUSTER_RANDOMIZED_TRIAL","unit_of_analysis":"ACCOUNT","unit_of_randomization":"SUPPORT_AGENT","primary_metric":"SUPPORT_RECURRENCE_30D","secondary_metrics":["SATISFACTION_RATE","ADOPTION_RATE_30D"],"guardrail_metrics":["OBSERVED_CHURN_RATE","DATA_COMPLETENESS"],"minimum_detectable_effect":0.10,"directionality":"DECREASE","expected_duration":60,"follow_up_window":30,"contamination_risk":"HIGH","ethical_risk":"MEDIUM","operational_complexity":"HIGH"},
    {"experiment_id":"EXP004","experiment_name":"RECURRING_CHURN_REVIEW_PROCESS","queue":"RECURRING_CHURN_REVIEW","hypothesis_id":"H004","watchlist_rule_ids":["W005","W006"],"intervention_id":"I003","observation":"Multiple observed churn events occurred for a subset of accounts.","mechanism_hypothesis":"A structured human review process may change subscription continuation; the mechanism is untested.","design_type":"RANDOMIZED_CONTROLLED_TRIAL","unit_of_analysis":"ACCOUNT","unit_of_randomization":"ACCOUNT","primary_metric":"SUBSCRIPTION_CONTINUATION","secondary_metrics":["TIME_TO_OBSERVED_CHURN","ADOPTION_RATE_30D"],"guardrail_metrics":["SATISFACTION_RATE","SUPPORT_RECURRENCE_30D"],"minimum_detectable_effect":0.10,"directionality":"INCREASE","expected_duration":90,"follow_up_window":90,"contamination_risk":"MEDIUM","ethical_risk":"HIGH","operational_complexity":"HIGH"},
    {"experiment_id":"EXP005","experiment_name":"REACTIVATION_EXPERIENCE_PILOT","queue":"REACTIVATION_REVIEW","hypothesis_id":"H005","watchlist_rule_ids":["W007","W008"],"intervention_id":"I007","observation":"Explicit reactivation was observed for a small historical population.","mechanism_hypothesis":"A structured post-reactivation experience may change observed usage return; the small population supports a pilot only.","design_type":"PILOT_FEASIBILITY_STUDY","unit_of_analysis":"ACCOUNT","unit_of_randomization":"ACCOUNT","primary_metric":"REACTIVATION_USAGE_RETURN","secondary_metrics":["ACTIVE_USAGE_DAYS_30D","SUBSCRIPTION_CONTINUATION"],"guardrail_metrics":["SUPPORT_RECURRENCE_30D","OBSERVED_CHURN_RATE"],"minimum_detectable_effect":0.15,"directionality":"INCREASE","expected_duration":30,"follow_up_window":30,"contamination_risk":"MEDIUM","ethical_risk":"MEDIUM","operational_complexity":"MEDIUM"},
    {"experiment_id":"EXP006","experiment_name":"SUBSCRIPTION_DATA_RECONCILIATION","queue":"DATA_QUALITY_REVIEW","hypothesis_id":"H006","watchlist_rule_ids":["W011","W012","W013","W014"],"intervention_id":"I009","observation":"Subscription overlap and quality constraints limit historical interpretation for many accounts.","mechanism_hypothesis":"A governed instrumentation and reconciliation change may improve measurable subscription consistency; this is a data-quality study.","design_type":"DATA_QUALITY_STUDY","unit_of_analysis":"ACCOUNT","unit_of_randomization":"COHORT","primary_metric":"SUBSCRIPTION_RECONCILIATION_RATE","secondary_metrics":["DATA_COMPLETENESS","TIMESTAMP_VALIDITY_RATE"],"guardrail_metrics":["DATA_COMPLETENESS"],"minimum_detectable_effect":0.10,"directionality":"INCREASE","expected_duration":60,"follow_up_window":30,"contamination_risk":"HIGH","ethical_risk":"LOW","operational_complexity":"HIGH"},
    {"experiment_id":"EXP007","experiment_name":"ONBOARDING_ADOPTION_CHECKLIST","queue":"ADOPTION_REVIEW","hypothesis_id":"H007","watchlist_rule_ids":["W003","W016"],"intervention_id":"I006","observation":"Low feature diversity was observed in the adoption-review population.","mechanism_hypothesis":"A versioned checklist may change 90-day feature diversity; the mechanism is untested.","design_type":"STEPPED_WEDGE","unit_of_analysis":"ACCOUNT","unit_of_randomization":"COHORT","primary_metric":"FEATURE_DIVERSITY_90D","secondary_metrics":["TIME_TO_FIRST_FEATURE","ADOPTION_RATE_30D"],"guardrail_metrics":["SUPPORT_RECURRENCE_30D","SATISFACTION_RATE"],"minimum_detectable_effect":0.50,"directionality":"INCREASE","expected_duration":90,"follow_up_window":90,"contamination_risk":"HIGH","ethical_risk":"LOW","operational_complexity":"HIGH"},
    {"experiment_id":"EXP008","experiment_name":"RECENT_CHURN_CONTEXT_STUDY","queue":"RECENT_CHURN_REVIEW","hypothesis_id":"H008","watchlist_rule_ids":["W004","W015"],"intervention_id":"I010","observation":"Recent churn and promoted churn-path context were observed historically.","mechanism_hypothesis":"No treatment mechanism is asserted; a matched observational design could validate measurement and confounding assumptions.","design_type":"QUASI_EXPERIMENT","unit_of_analysis":"ACCOUNT","unit_of_randomization":"ACCOUNT","primary_metric":"TIME_TO_OBSERVED_CHURN","secondary_metrics":["OBSERVED_CHURN_RATE","SUBSCRIPTION_CONTINUATION"],"guardrail_metrics":["DATA_COMPLETENESS"],"minimum_detectable_effect":0.80,"directionality":"TWO_SIDED","expected_duration":90,"follow_up_window":90,"contamination_risk":"MEDIUM","ethical_risk":"LOW","operational_complexity":"MEDIUM"},
)


def build_hypotheses() -> list[dict[str, Any]]:
    output=[]
    for row in EXPERIMENT_DEFINITIONS:
        if row["primary_metric"] not in ALLOWED_METRICS: raise ValueError(row["primary_metric"])
        hypothesis={**row,
            "target_population":"WATCHLIST_QUEUE_WITH_GOVERNED_ELIGIBILITY",
            "null_hypothesis":"No difference in the pre-specified primary estimand between future comparison groups.",
            "alternative_hypothesis":"A difference exists in the pre-specified direction for the primary estimand.",
            "evidence_strength":"HISTORICAL_DESCRIPTIVE_ONLY","data_confidence":"TO_BE_DERIVED",
            "feasibility_status":"TO_BE_EVALUATED","limitations":["NO_EXPERIMENT_EXECUTED","NO_RESULT_AVAILABLE","HISTORICAL_BASELINE_NOT_A_CONTROL"],
            "causal_status":"UNTESTED",
        }
        output.append(hypothesis)
    validate_hypotheses(output)
    return output


def validate_hypotheses(rows: list[dict[str, Any]]) -> None:
    if len(rows) < 6 or len({row["hypothesis_id"] for row in rows}) != len(rows): raise ValueError("Hypothesis registry is incomplete.")
    for row in rows:
        if row["causal_status"] != "UNTESTED": raise ValueError("Causal status must remain UNTESTED.")
        if row["primary_metric"] not in ALLOWED_METRICS or not row["secondary_metrics"] or not row["guardrail_metrics"]: raise ValueError("Metric contract failed.")
