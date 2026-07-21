"""Deterministic design simulation and covariate balance diagnostics."""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np
import pandas as pd

DEFAULT_SEED=20260721
ARMS=("SIMULATED_CONTROL","SIMULATED_TREATMENT")


def _hash_order(experiment_id: str, account_key: str, seed: int) -> str:
    return hashlib.sha256(f"{seed}|{experiment_id}|{account_key}".encode()).hexdigest()


def simulate_assignments(eligibility: pd.DataFrame, seed: int=DEFAULT_SEED) -> pd.DataFrame:
    """Validate assignment mechanics only; no operational treatment list is created."""
    rows=[]
    for experiment_id, group in eligibility.groupby("experiment_id",sort=True):
        work=group.copy(); work["stratum"]=work["mrr_band"].astype(str)+"|"+work["data_confidence"].astype(str)
        eligible=work.loc[work["eligibility_status"].eq("ELIGIBLE")].copy()
        assignments={}
        for stratum, members in eligible.groupby("stratum",sort=True):
            members=members.assign(_order=members["account_key"].map(lambda key:_hash_order(experiment_id,key,seed))).sort_values("_order")
            for index,key in enumerate(members["account_key"]): assignments[key]=ARMS[index%2]
        for item in work.to_dict("records"):
            rows.append({"experiment_id":experiment_id,"account_key":item["account_key"],"simulated_arm":assignments.get(item["account_key"],"SIMULATED_NOT_ASSIGNED"),"stratum":item["stratum"],"assignment_seed":seed,"eligibility_status":item["eligibility_status"],"exclusion_reason":item["exclusion_reason"],"simulation_only":True})
    result=pd.DataFrame(rows).sort_values(["experiment_id","account_key"]).reset_index(drop=True)
    assigned=result["eligibility_status"].eq("ELIGIBLE")
    if not result["simulation_only"].all() or not set(result.loc[assigned,"simulated_arm"]).issubset(set(ARMS)): raise AssertionError("Simulation-only assignment contract failed.")
    return result


def standardized_mean_difference(control: pd.Series, treatment: pd.Series) -> float | None:
    left=pd.to_numeric(control,errors="coerce").dropna(); right=pd.to_numeric(treatment,errors="coerce").dropna()
    if not len(left) or not len(right): return None
    pooled=np.sqrt((left.var(ddof=1)+right.var(ddof=1))/2) if len(left)>1 and len(right)>1 else 0.0
    if pooled==0: return 0.0 if left.mean()==right.mean() else None
    return float((right.mean()-left.mean())/pooled)


def categorical_difference(control: pd.Series, treatment: pd.Series) -> float | None:
    if not len(control) or not len(treatment): return None
    levels=sorted(set(control.dropna().astype(str))|set(treatment.dropna().astype(str)))
    return float(max((abs((treatment.astype(str)==level).mean()-(control.astype(str)==level).mean()) for level in levels),default=0.0))


def balance_checks(assignments: pd.DataFrame, eligibility: pd.DataFrame) -> list[dict[str, Any]]:
    covariates=["associated_mrr","usage_count_30d","support_count_90d","quality_coverage_ratio","mrr_band","taxonomy_class","primary_outcome","data_confidence","priority"]
    joined=assignments.merge(eligibility[["experiment_id","account_key",*covariates]],on=["experiment_id","account_key"],how="left",validate="one_to_one")
    output=[]
    for experiment_id, group in joined.loc[joined["eligibility_status"].eq("ELIGIBLE")].groupby("experiment_id",sort=True):
        control=group.loc[group["simulated_arm"].eq("SIMULATED_CONTROL")]; treatment=group.loc[group["simulated_arm"].eq("SIMULATED_TREATMENT")]
        if control.empty or treatment.empty:
            output.append({"experiment_id":experiment_id,"covariate":"ALL","metric":"NOT_ESTIMABLE","value":None,"threshold":.10,"balance_status":"NOT_ESTIMABLE","control_n":len(control),"treatment_n":len(treatment)})
            continue
        for covariate in covariates:
            numeric=covariate in {"associated_mrr","usage_count_30d","support_count_90d","quality_coverage_ratio"}
            value=standardized_mean_difference(control[covariate],treatment[covariate]) if numeric else categorical_difference(control[covariate],treatment[covariate])
            output.append({"experiment_id":experiment_id,"covariate":covariate,"metric":"STANDARDIZED_MEAN_DIFFERENCE" if numeric else "MAX_PROPORTION_DIFFERENCE","value":value,"threshold":.10,"balance_status":"PASS" if value is not None and abs(value)<.10 else "REVIEW_REQUIRED","control_n":len(control),"treatment_n":len(treatment)})
    return output


def validate_randomization(assignments: pd.DataFrame) -> dict[str, Any]:
    eligible=assignments["eligibility_status"].eq("ELIGIBLE")
    if assignments.duplicated(["experiment_id","account_key"]).any(): raise AssertionError("Duplicate simulated assignment.")
    forbidden={"outcome","uplift","result","effect"}&set(assignments.columns)
    if forbidden: raise AssertionError(f"Synthetic result fields: {forbidden}")
    return {"rows":len(assignments),"simulated_assignments":int(eligible.sum()),"not_assigned":int((~eligible).sum()),"simulation_only_false":int((~assignments["simulation_only"]).sum()),"synthetic_outcomes":0,"operational_assignments":0}
