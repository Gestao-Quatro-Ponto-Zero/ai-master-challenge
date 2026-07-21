"""Deterministic eligibility, exclusions, and future conflict policy."""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

REFERENCE_DATE = pd.Timestamp("2024-12-31T19:00:00")
CONFIDENCE_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
BEHAVIORAL_EXPERIMENTS = {"EXP001","EXP002","EXP003","EXP004","EXP005","EXP007"}

EXPERIMENT_CONFLICT_POLICY = {
    "behavioral_active_limit_per_account": 1,
    "data_quality_studies_may_coexist": True,
    "queue_precedence": ["REACTIVATION_REVIEW","SUPPORT_JOURNEY_REVIEW","RECURRING_CHURN_REVIEW","HIGH_MRR_LOW_ENGAGEMENT_REVIEW","ADOPTION_REVIEW","RECENT_CHURN_REVIEW"],
    "cooldown_days": 90,
    "recent_exposure_exclusion": True,
    "simulation_policy": "INDEPENDENT_DESIGN_VALIDATION_NOT_CONCURRENT_OPERATION",
}


def _queue_accounts(watchlist: pd.DataFrame, queue: str) -> pd.DataFrame:
    scoped=watchlist.loc[watchlist["queue"].eq(queue)].copy()
    level={"LOW":1,"MEDIUM":2,"HIGH":3}; priority={"P1":1,"P2":2,"P3":3,"P4":4}
    scoped["_confidence_rank"]=scoped["data_confidence"].map(level); scoped["_priority_rank"]=scoped["priority"].map(priority)
    rows=[]
    for account_key, group in scoped.groupby("account_key",sort=True):
        best=group.sort_values(["_priority_rank","watchlist_rule_id"]).iloc[0]
        rows.append({
            "account_key":account_key,"reference_date":best["reference_date"],"queue":queue,
            "priority":best["priority"],"data_confidence":min(group["data_confidence"],key=level.get),
            "stability_status":best["stability_status"],"quality_coverage_ratio":float(best["quality_coverage_ratio"]),
            "associated_mrr":float(best["associated_mrr"]),"mrr_band":best["mrr_band"],"taxonomy_class":best["taxonomy_class"],
            "primary_outcome":best["primary_outcome"],"usage_count_30d":float(best["usage_count_30d"]),
            "usage_count_90d":float(best["usage_count_90d"]),"distinct_features_90d":int(best["distinct_features_90d"]),
            "support_count_30d":int(best["support_count_30d"]),"support_count_90d":int(best["support_count_90d"]),
            "churn_count":int(best["churn_count"]),"reactivation_count":int(best["reactivation_count"]),
            "has_subscription_overlap":bool(best["has_subscription_overlap"]),
            "requires_data_review":bool(group["requires_data_review"].any()),
            "rule_ids":json.dumps(sorted(group["watchlist_rule_id"].unique()),separators=(",",":")),
        })
    return pd.DataFrame(rows)


def eligibility_spec(hypothesis: dict[str, Any]) -> dict[str, Any]:
    is_quality=hypothesis["design_type"]=="DATA_QUALITY_STUDY"
    return {
        "reference_date":REFERENCE_DATE.isoformat(),"queue":hypothesis["queue"],
        "minimum_data_confidence":"LOW" if is_quality else "MEDIUM",
        "allowed_priorities":["P1","P2","P3","P4"],"allowed_stability":["ROBUST","SENSITIVE"],
        "minimum_quality_coverage":0.0 if is_quality else 0.4,"required_observation_window":hypothesis["follow_up_window"],
        "required_activity_history":hypothesis["primary_metric"],"required_subscription_state":"METRIC_DEPENDENT",
        "required_mrr_band":"ANY","allowed_outcomes":"QUEUE_DEFINED",
        "exclusions":["LOW_DATA_CONFIDENCE","LOW_QUALITY_COVERAGE","MISSING_DESIGN_UNIT","METRIC_SPECIFIC_DATA_BLOCKER","ACTIVE_CONFLICTING_EXPERIMENT","UNAVAILABLE_FOLLOW_UP"],
    }


def build_eligibility(watchlist: pd.DataFrame, hypotheses: list[dict[str, Any]]) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    if pd.to_datetime(watchlist["reference_date"]).gt(REFERENCE_DATE).any(): raise AssertionError("Future watchlist row.")
    frames=[]; specs=[]
    for hypothesis in hypotheses:
        spec=eligibility_spec(hypothesis); specs.append({"experiment_id":hypothesis["experiment_id"],**spec})
        accounts=_queue_accounts(watchlist,hypothesis["queue"])
        for row in accounts.to_dict("records"):
            reasons=[]; is_quality=hypothesis["design_type"]=="DATA_QUALITY_STUDY"
            if not is_quality and CONFIDENCE_ORDER.get(row["data_confidence"],0)<CONFIDENCE_ORDER[spec["minimum_data_confidence"]]: reasons.append("LOW_DATA_CONFIDENCE")
            if not is_quality and row["quality_coverage_ratio"]<spec["minimum_quality_coverage"]: reasons.append("LOW_QUALITY_COVERAGE")
            if row["stability_status"] not in spec["allowed_stability"]: reasons.append("UNSTABLE_EVIDENCE")
            if hypothesis["experiment_id"]=="EXP003": reasons.append("MISSING_SUPPORT_AGENT_CLUSTER_KEY")
            if hypothesis["experiment_id"]=="EXP007": reasons.append("MISSING_OPERATIONAL_ROLLOUT_COHORT")
            if hypothesis["experiment_id"] in {"EXP004","EXP008"} and row["has_subscription_overlap"]: reasons.append("SUBSCRIPTION_OVERLAP_BLOCKS_OUTCOME")
            if hypothesis["experiment_id"]=="EXP005" and row["reactivation_count"]<1: reasons.append("NO_EXPLICIT_REACTIVATION")
            if hypothesis["experiment_id"]=="EXP006" and not row["requires_data_review"]: reasons.append("NO_DOCUMENTED_QUALITY_GAP")
            status="ELIGIBLE" if not reasons else "EXCLUDED"
            frames.append({"experiment_id":hypothesis["experiment_id"],**row,"eligibility_status":status,"exclusion_reason":";".join(sorted(set(reasons))),"required_follow_up_days":hypothesis["follow_up_window"],"future_follow_up_required":True})
    result=pd.DataFrame(frames).sort_values(["experiment_id","account_key"]).reset_index(drop=True)
    eligible=result.loc[result["eligibility_status"].eq("ELIGIBLE")]
    conflicts=eligible.loc[eligible["experiment_id"].isin(BEHAVIORAL_EXPERIMENTS)].groupby("account_key")["experiment_id"].nunique()
    result["potential_behavioral_conflict_count"]=result["account_key"].map(conflicts).fillna(0).astype(int)
    result["conflict_policy_applied_operationally"]=False
    return result,specs


def validate_eligibility(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.duplicated(["experiment_id","account_key"]).any(): raise AssertionError("Duplicate experiment-account eligibility.")
    if frame["account_key"].astype(str).str.contains("@| ").any(): raise AssertionError("Unexpected identifier shape.")
    return {"rows":len(frame),"eligible_rows":int(frame["eligibility_status"].eq("ELIGIBLE").sum()),"excluded_rows":int(frame["eligibility_status"].eq("EXCLUDED").sum()),"operational_assignments":0}
