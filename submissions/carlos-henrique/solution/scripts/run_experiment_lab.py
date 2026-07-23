"""Run the deterministic, design-only Phase 8 Experiment Lab."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

SOLUTION_ROOT=Path(__file__).resolve().parents[1]; SRC_ROOT=SOLUTION_ROOT/"src"
if str(SRC_ROOT) not in sys.path: sys.path.insert(0,str(SRC_ROOT))

from experiment_analysis_plan import build_analysis_plans,build_guardrails,build_stopping_rules,validate_analysis_plans  # noqa:E402
from experiment_catalog import catalog_index,load_catalog  # noqa:E402
from experiment_eligibility import EXPERIMENT_CONFLICT_POLICY,build_eligibility,validate_eligibility  # noqa:E402
from experiment_governance import evaluate_feasibility,validate_governance  # noqa:E402
from experiment_hypotheses import build_hypotheses  # noqa:E402
from experiment_power import build_account_metrics,calculate_power  # noqa:E402
from experiment_randomization import DEFAULT_SEED,balance_checks,simulate_assignments,validate_randomization  # noqa:E402
from experiment_reporting import build_artifacts,build_findings,build_registry,build_specifications,create_figures,render_reports,stable_json,write_json  # noqa:E402

PROCESSED=SOLUTION_ROOT/"data"/"processed"; ARTIFACTS=SOLUTION_ROOT/"artifacts"; REPORTS=SOLUTION_ROOT/"reports"; FIGURES=REPORTS/"figures"; EXPERIMENTS=SOLUTION_ROOT/"experiments"
EXPECTED_BASE="1ed6655cf86f9068f56a10af25537ea8747a25b1"
EXPECTED_HASHES={
 "data/processed/intervention_watchlist.parquet":"17636089c4ff4ff6a62280a04fb39575cdb27d7b35496ab5c337149cac806361",
 "data/processed/account_watchlist_summary.parquet":"89f927b65c73db78febcd890be7aec3e65e9f2d288af25e280bcb8cdcc503c2d",
 "data/processed/watchlist_evidence.parquet":"c841ce99d7f29a0113ee07f12f9fd127f6ba7ffebaaecf6c8589774e4b502f10",
 "artifacts/watchlist_rules.json":"fe29b1939ff670510d5cb3ef92e3da67abb55b5bc28aec2cc56459a241dc6e4d",
 "artifacts/watchlist_findings.json":"fbe4aa080104f81847efbd4ad5e015026b3857f656d53f308d4ccbdbc3807e21",
 "artifacts/graph_findings.json":"ecb52c72df6b5a498feb0b5269c67c3d0bdfd945c0b83c3eac15c36556a7d360",
 "artifacts/journey_findings.json":"58f31818ec28049c334190c10c9405a82b7062d34b4cf0185de90b1ed2c02008",
 "artifacts/survival_findings.json":"0357cb4692d8cb94ef594450d2e2557322c62c8be70c4725dda9fcbf85cc04cc",
 "data/processed/account_survival_dataset.parquet":"f0e82247f3ca4d4db32886c818881011f9dbd1f18adaab8f1d36291cd6c92c4e",
 "data/processed/event_log.parquet":"0e9e60d06ce6fbd62103924aab7beda6d0eab9ed5a87ea32cee786abcdb0373f",
}
ARTIFACT_NAMES=("experiment_lab_summary.json","experiment_hypotheses.json","experiment_feasibility.json","experiment_sample_size.json","experiment_baselines.json","experiment_balance.json","experiment_metrics.json","experiment_guardrails.json","experiment_ethics.json","experiment_findings.json","experiment_validation.json")


def sha256(path: Path) -> str:
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""): digest.update(chunk)
    return digest.hexdigest()


def validate_inputs() -> dict[str,Any]:
    failures=[]
    for relative,expected in EXPECTED_HASHES.items():
        path=SOLUTION_ROOT/relative
        if not path.is_file() or sha256(path)!=expected: failures.append(relative)
    if failures: raise RuntimeError(f"Phase 8 input gate failed: {failures}")
    return {"expected_base_commit":EXPECTED_BASE,"verified_inputs":len(EXPECTED_HASHES),"all_hashes_match":True,"input_hashes":EXPECTED_HASHES}


def _eligibility_summary(eligibility: pd.DataFrame, hypotheses: list[dict[str,Any]]) -> dict[str,dict[str,Any]]:
    output={}
    for h in hypotheses:
        group=eligibility.loc[eligibility["experiment_id"].eq(h["experiment_id"])]
        eligible=group.loc[group["eligibility_status"].eq("ELIGIBLE")]
        dominant=eligible["data_confidence"].mode().iloc[0] if len(eligible) else "NOT_ESTIMABLE"
        output[h["experiment_id"]]={"candidate_accounts":group["account_key"].nunique(),"eligible_accounts":eligible["account_key"].nunique(),"excluded_accounts":group.loc[group["eligibility_status"].eq("EXCLUDED"),"account_key"].nunique(),"low_confidence_eligible":int(eligible["data_confidence"].eq("LOW").sum()),"dominant_confidence":dominant,"potential_conflicts":int(eligible["potential_behavioral_conflict_count"].gt(1).sum())}
    return output


def _validate_outputs(registry: pd.DataFrame,specifications: pd.DataFrame,assignments: pd.DataFrame,eligibility: pd.DataFrame,hypotheses: list[dict[str,Any]],feasibility: list[dict[str,Any]],balance: list[dict[str,Any]],governance: dict[str,Any],input_gate: dict[str,Any]) -> dict[str,Any]:
    if registry["experiment_id"].duplicated().any() or len(registry)<6: raise AssertionError("Registry grain failed.")
    if specifications.duplicated(["experiment_id","section","specification_key"]).any(): raise AssertionError("Specification grain failed.")
    if "account_id" in assignments or not assignments["simulation_only"].all(): raise AssertionError("Assignment privacy or simulation gate failed.")
    if pd.to_datetime(registry["reference_date"]).gt(pd.Timestamp("2024-12-31T19:00:00")).any(): raise AssertionError("Future reference date.")
    available={row["experiment_id"]:row["available_eligible_sample"] for row in feasibility}
    reconciled={eid:int(group.loc[group["eligibility_status"].eq("ELIGIBLE"),"account_key"].nunique()) for eid,group in eligibility.groupby("experiment_id")}
    if available!=reconciled: raise AssertionError("Available sample does not reconcile.")
    if any(h["causal_status"]!="UNTESTED" for h in hypotheses): raise AssertionError("Causal status advanced.")
    return {"gate_result":"PASS_WITH_WARNINGS","input_gate":input_gate,"registry":{"experiments":len(registry),"duplicate_experiments":0},"specifications":{"rows":len(specifications),"duplicate_logical_rows":0},"eligibility":{"candidate_rows":len(eligibility),"eligible_rows":int(eligibility["eligibility_status"].eq("ELIGIBLE").sum()),"sample_reconciled":True},"randomization":validate_randomization(assignments),"balance":{"checks":len(balance),"review_required":sum(row["balance_status"]=="REVIEW_REQUIRED" for row in balance),"documented":True},"governance":governance,"privacy":{"raw_account_ids":0,"pii_fields":0},"temporal":{"future_events_used":0,"cutoff":"2024-12-31T19:00:00"},"results":{"interventions_executed":0,"contacts":0,"synthetic_outcomes":0,"uplift_values":0,"experimental_results":0},"reconciliation":{"difference_unexplained":0},"deterministic":True}


def _write_experiment_jsons(registry: pd.DataFrame,hypotheses: list[dict[str,Any]],specifications: pd.DataFrame,feasibility: list[dict[str,Any]]) -> list[str]:
    EXPERIMENTS.mkdir(parents=True,exist_ok=True); f={row["experiment_id"]:row for row in feasibility}; h={row["experiment_id"]:row for row in hypotheses}; names=[]
    for row in registry.to_dict("records"):
        eid=row["experiment_id"]; name=f"{eid}_{row['experiment_name'].lower()}.json"; names.append(name)
        payload={"experiment":row,"hypothesis":h[eid],"feasibility":f[eid],"specifications":specifications.loc[specifications["experiment_id"].eq(eid)].to_dict("records"),"experiment_conflict_policy":EXPERIMENT_CONFLICT_POLICY,"result":None,"causal_status":"UNTESTED","execution_authorized":False}
        write_json(EXPERIMENTS/name,payload)
    return names


def run() -> dict[str,Any]:
    input_gate=validate_inputs(); catalog_payload=load_catalog(SOLUTION_ROOT/"config"/"intervention_catalog.json"); catalog=catalog_index(catalog_payload); hypotheses=build_hypotheses()
    watchlist=pd.read_parquet(PROCESSED/"intervention_watchlist.parquet"); events=pd.read_parquet(PROCESSED/"event_log.parquet")
    eligibility,eligibility_specs=build_eligibility(watchlist,hypotheses); eligibility_validation=validate_eligibility(eligibility); eligibility_summary=_eligibility_summary(eligibility,hypotheses)
    metrics=build_account_metrics(watchlist,events); baselines,sample_sizes,power_summaries=calculate_power(hypotheses,eligibility,metrics)
    baseline_map={row["experiment_id"]:row for row in baselines}; gates,ethics,feasibility=evaluate_feasibility(hypotheses,power_summaries,eligibility_summary,catalog,baseline_map)
    assignments=simulate_assignments(eligibility,DEFAULT_SEED); balance=balance_checks(assignments,eligibility)
    plans=build_analysis_plans(hypotheses); guardrails=build_guardrails(hypotheses); stops=build_stopping_rules(hypotheses); plan_validation=validate_analysis_plans(plans,guardrails,stops)
    registry=build_registry(hypotheses,feasibility,baselines,eligibility_summary,catalog); findings=build_findings(registry); governance=validate_governance(registry.to_dict("records"),findings)
    governance.update({"eligibility":eligibility_validation,"analysis_plan":plan_validation})
    specifications=build_specifications(hypotheses,eligibility_specs,plans,guardrails,stops,ethics,feasibility,DEFAULT_SEED)
    validation=_validate_outputs(registry,specifications,assignments,eligibility,hypotheses,feasibility,balance,governance,input_gate)
    artifacts=build_artifacts(registry,hypotheses,feasibility,sample_sizes,baselines,balance,guardrails,ethics,gates,findings,validation)
    aggregate_text=json.dumps(artifacts,ensure_ascii=False,default=str)
    if '"account_key"' in aggregate_text: raise AssertionError("Aggregate JSON exposes account_key.")
    PROCESSED.mkdir(parents=True,exist_ok=True); registry.to_parquet(PROCESSED/"experiment_registry.parquet",index=False); specifications.to_parquet(PROCESSED/"experiment_specifications.parquet",index=False); assignments.to_parquet(PROCESSED/"experiment_assignment_simulation.parquet",index=False)
    for name in ARTIFACT_NAMES: write_json(ARTIFACTS/name,artifacts[name])
    experiment_files=_write_experiment_jsons(registry,hypotheses,specifications,feasibility)
    create_figures(registry,balance,gates,FIGURES); render_reports(REPORTS,registry,artifacts,plans,guardrails,stops)
    return {"gate_result":validation["gate_result"],"experiments":len(registry),"statuses":registry["status"].value_counts().sort_index().to_dict(),"eligible_assignments":int(assignments["eligibility_status"].eq("ELIGIBLE").sum()),"individual_specs":len(experiment_files),"cutoff":"2024-12-31T19:00:00"}


if __name__=="__main__": print(json.dumps(run(),ensure_ascii=False,indent=2,sort_keys=True))
