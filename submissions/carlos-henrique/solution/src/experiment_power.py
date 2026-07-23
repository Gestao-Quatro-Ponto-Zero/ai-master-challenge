"""Historical baselines and transparent sample-size feasibility calculations."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import norm

from graph_schema import stable_key

REFERENCE_DATE=pd.Timestamp("2024-12-31T19:00:00")
PROPORTION_METRICS={"ADOPTION_RATE_30D","SUPPORT_REOPEN_RATE","SUPPORT_RECURRENCE_30D","SATISFACTION_RATE","REACTIVATION_USAGE_RETURN","SUBSCRIPTION_CONTINUATION","OBSERVED_CHURN_RATE","DATA_COMPLETENESS","TIMESTAMP_VALIDITY_RATE","SUBSCRIPTION_RECONCILIATION_RATE"}
MEAN_METRICS={"ACTIVE_USAGE_DAYS_30D","FEATURE_DIVERSITY_30D","FEATURE_DIVERSITY_90D","TIME_TO_FIRST_FEATURE"}
SURVIVAL_METRICS={"TIME_TO_OBSERVED_CHURN"}


def build_account_metrics(watchlist: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    base=watchlist.sort_values(["account_key","watchlist_rule_id"]).drop_duplicates("account_key").copy()
    columns=["account_key","associated_mrr","mrr_band","taxonomy_class","primary_outcome","data_confidence","quality_coverage_ratio","priority","usage_count_30d","usage_count_90d","distinct_features_90d","support_count_30d","support_count_90d","churn_count","reactivation_count","has_subscription_overlap"]
    base=base[columns].set_index("account_key")
    work=events.copy(); work["event_time"]=pd.to_datetime(work["event_time"]); work=work.loc[work["event_time"].le(REFERENCE_DATE) & work["quality_status"].isin(["VALID","VALID_WITH_WARNING"]) & ~work["is_quarantined"].astype(bool)].copy()
    work["account_key"]=work["account_id"].astype(str).map(lambda value:stable_key("acct",value))
    start30=REFERENCE_DATE-pd.Timedelta(days=30); recent=work.loc[work["event_time"].gt(start30)]
    usage=recent.loc[recent["event_type"].eq("FEATURE_USED")]
    usage_days=usage.assign(day=usage["event_time"].dt.floor("D")).groupby("account_key")["day"].nunique()
    diversity30=usage.groupby("account_key")["event_value_category"].nunique()
    created=work.loc[work["event_type"].eq("ACCOUNT_CREATED")].groupby("account_key")["event_time"].min()
    first_feature=work.loc[work["event_type"].eq("FEATURE_USED")].groupby("account_key")["event_time"].min()
    first_churn=work.loc[work["event_type"].eq("CHURN_RECORDED")].groupby("account_key")["event_time"].min()
    valid_counts=work.loc[work["quality_status"].eq("VALID")].groupby("account_key").size(); main_counts=work.groupby("account_key").size()
    satisfaction=recent.loc[recent["event_type"].eq("SUPPORT_TICKET_CLOSED"),["account_key","event_value_numeric"]].dropna()
    sat_rate=satisfaction.assign(ok=satisfaction["event_value_numeric"].ge(4)).groupby("account_key")["ok"].mean()
    last_reactivation=work.loc[work["event_type"].eq("REACTIVATION_RECORDED")].groupby("account_key")["event_time"].max()
    usage_events=work.loc[work["event_type"].eq("FEATURE_USED"),["account_key","event_time"]]
    return_usage={}
    for key, when in last_reactivation.items():
        after=usage_events.loc[usage_events["account_key"].eq(key) & usage_events["event_time"].gt(when) & usage_events["event_time"].le(when+pd.Timedelta(days=30))]
        return_usage[key]=float(len(after)>0)
    result=base.copy()
    result["ADOPTION_RATE_30D"]=result["usage_count_30d"].gt(0).astype(float)
    result["ACTIVE_USAGE_DAYS_30D"]=usage_days.reindex(result.index).fillna(0).astype(float)
    result["FEATURE_DIVERSITY_30D"]=diversity30.reindex(result.index).fillna(0).astype(float)
    result["FEATURE_DIVERSITY_90D"]=result["distinct_features_90d"].astype(float)
    result["TIME_TO_FIRST_FEATURE"]=(first_feature.reindex(result.index)-created.reindex(result.index)).dt.total_seconds().div(86400).clip(lower=0)
    result["SUPPORT_REOPEN_RATE"]=result["support_count_30d"].gt(1).astype(float)
    result["SUPPORT_RECURRENCE_30D"]=result["support_count_30d"].gt(1).astype(float)
    result["SATISFACTION_RATE"]=sat_rate.reindex(result.index)
    result["REACTIVATION_USAGE_RETURN"]=pd.Series(return_usage).reindex(result.index)
    result["SUBSCRIPTION_CONTINUATION"]=result["churn_count"].eq(0).astype(float)
    result["OBSERVED_CHURN_RATE"]=result["churn_count"].gt(0).astype(float)
    result["TIME_TO_OBSERVED_CHURN"]=(first_churn.reindex(result.index)-created.reindex(result.index)).dt.total_seconds().div(86400).clip(lower=0)
    result["DATA_COMPLETENESS"]=result["quality_coverage_ratio"].astype(float)
    result["TIMESTAMP_VALIDITY_RATE"]=(valid_counts/main_counts).reindex(result.index).fillna(0).astype(float)
    result["SUBSCRIPTION_RECONCILIATION_RATE"]=(~result["has_subscription_overlap"].astype(bool)).astype(float)
    return result.reset_index()


def baseline_for_metric(values: pd.Series, metric: str) -> dict[str, Any]:
    observed=pd.to_numeric(values,errors="coerce").dropna().astype(float)
    if observed.empty: return {"sample_size":0,"event_count":0,"baseline_rate":None,"baseline_mean":None,"baseline_median":None,"standard_deviation":None,"interquartile_range":None}
    proportion=metric in PROPORTION_METRICS
    return {"sample_size":len(observed),"event_count":int(observed.sum()) if proportion else int(observed.notna().sum()),"baseline_rate":float(observed.mean()) if proportion else None,"baseline_mean":float(observed.mean()),"baseline_median":float(observed.median()),"standard_deviation":float(observed.std(ddof=1)) if len(observed)>1 else 0.0,"interquartile_range":float(observed.quantile(.75)-observed.quantile(.25))}


def proportion_sample_size(p0: float, delta: float, alpha: float=.05, power: float=.8, ratio: float=1.0) -> int:
    p1=min(max(p0+delta,.001),.999); delta=abs(p1-p0)
    if delta<=0: return 0
    pbar=(p0+p1)/2; za=norm.ppf(1-alpha/2); zb=norm.ppf(power)
    n=((za*math.sqrt(2*pbar*(1-pbar))+zb*math.sqrt(p0*(1-p0)+p1*(1-p1)))**2)/(delta**2)
    return int(math.ceil(n*(1+ratio)))


def mean_sample_size(sd: float, delta: float, alpha: float=.05, power: float=.8, ratio: float=1.0) -> int:
    if sd<=0 or delta<=0: return 0
    per_arm=((norm.ppf(1-alpha/2)+norm.ppf(power))**2*2*sd**2)/(delta**2)
    return int(math.ceil(per_arm*(1+ratio)))


def survival_sample_size(event_rate: float, hazard_ratio: float, alpha: float=.05, power: float=.8) -> int:
    if not 0<event_rate<=1 or hazard_ratio<=0 or hazard_ratio==1: return 0
    events=4*(norm.ppf(1-alpha/2)+norm.ppf(power))**2/(math.log(hazard_ratio)**2)
    return int(math.ceil(events/event_rate))


def _required(metric: str, baseline: dict[str, Any], mde: float) -> int:
    if int(baseline.get("sample_size",0))==0: return 0
    if metric in PROPORTION_METRICS:
        p=float(baseline["baseline_rate"] if baseline["baseline_rate"] is not None else .5)
        signed=-abs(mde) if p>mde and metric in {"SUPPORT_RECURRENCE_30D","OBSERVED_CHURN_RATE"} else abs(mde)
        return proportion_sample_size(p,signed)
    if metric in MEAN_METRICS: return mean_sample_size(float(baseline["standard_deviation"] or 0),abs(mde))
    if metric in SURVIVAL_METRICS:
        event_rate=max(min(float(baseline["event_count"])/max(float(baseline["sample_size"]),1),.99),.01)
        return survival_sample_size(event_rate,mde)
    return 0


def calculate_power(hypotheses: list[dict[str, Any]], eligibility: pd.DataFrame, account_metrics: pd.DataFrame, alpha: float=.05, power: float=.8, allocation_ratio: float=1.0) -> tuple[list[dict[str, Any]],list[dict[str, Any]],list[dict[str, Any]]]:
    baseline_rows=[]; sample_rows=[]; summaries=[]
    metric_index=account_metrics.set_index("account_key")
    for hypothesis in hypotheses:
        experiment_id=hypothesis["experiment_id"]; metric=hypothesis["primary_metric"]
        eligible=eligibility.loc[eligibility["experiment_id"].eq(experiment_id)&eligibility["eligibility_status"].eq("ELIGIBLE"),"account_key"]
        values=metric_index.reindex(eligible)[metric] if metric in metric_index else pd.Series(dtype=float)
        baseline=baseline_for_metric(values,metric)
        baseline_rows.append({"experiment_id":experiment_id,"metric_name":metric,"population":"ELIGIBLE_HISTORICAL_WATCHLIST","queue":hypothesis["queue"],"rule_ids":hypothesis["watchlist_rule_ids"],**baseline,"observation_window":hypothesis["follow_up_window"],"data_quality":"HISTORICAL_DESCRIPTIVE","limitations":["NOT_A_RANDOMIZED_CONTROL","NO_FUTURE_OUTCOME"]})
        scenarios=[.05,.10,.15]
        if metric in MEAN_METRICS: scenarios=[hypothesis["minimum_detectable_effect"]]
        elif metric in SURVIVAL_METRICS: scenarios=[.80]
        else:
            base_rate=baseline["baseline_rate"]
            if base_rate is not None: scenarios.append(max(round(abs(base_rate)*.20,4),.01))
        scenario_results=[]
        for mde in sorted(set(scenarios)):
            required=_required(metric,baseline,mde)
            for attrition in (.05,.10,.20):
                adjusted=int(math.ceil(required/(1-attrition))) if required else 0
                ratio=len(eligible)/adjusted if adjusted else 0.0
                status="NOT_ESTIMABLE" if not required or not len(eligible) else ("FEASIBLE" if ratio>=1 else "MARGINALLY_FEASIBLE" if ratio>=.8 else "UNDERPOWERED")
                sample_rows.append({"experiment_id":experiment_id,"metric_name":metric,"metric_type":"SURVIVAL" if metric in SURVIVAL_METRICS else "MEAN" if metric in MEAN_METRICS else "PROPORTION","baseline_value":baseline["baseline_rate"] if metric in PROPORTION_METRICS else baseline["baseline_mean"],"minimum_detectable_effect":mde,"alpha":alpha,"power":power,"allocation_ratio":allocation_ratio,"required_total_sample":required,"attrition_rate":attrition,"adjusted_required_sample":adjusted,"available_eligible_sample":len(eligible),"feasibility_ratio":ratio,"feasibility_status":status})
                if abs(mde-hypothesis["minimum_detectable_effect"])<1e-9 and attrition==.10: scenario_results.append(sample_rows[-1])
        chosen=scenario_results[0] if scenario_results else next(row for row in sample_rows if row["experiment_id"]==experiment_id and row["attrition_rate"]==.10)
        status=chosen["feasibility_status"]
        if hypothesis["design_type"]=="PILOT_FEASIBILITY_STUDY": status="PILOT_ONLY"
        if hypothesis["design_type"] in {"CLUSTER_RANDOMIZED_TRIAL","STEPPED_WEDGE"} and len(eligible)==0: status="NOT_FEASIBLE"
        summaries.append({"experiment_id":experiment_id,"available_eligible_sample":len(eligible),"required_sample":chosen["required_total_sample"],"adjusted_required_sample":chosen["adjusted_required_sample"],"feasibility_ratio":chosen["feasibility_ratio"],"feasibility_status":status,"baseline_value":chosen["baseline_value"],"minimum_detectable_effect":chosen["minimum_detectable_effect"],"alpha":alpha,"power":power,"allocation_ratio":allocation_ratio})
    return baseline_rows,sample_rows,summaries
