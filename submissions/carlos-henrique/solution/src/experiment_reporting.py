"""Registry, specifications, aggregate artifacts, reports, figures, and findings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

COLORS={"READY_FOR_REVIEW":"#2f6f8f","PILOT_ONLY":"#d6a85f","UNDERPOWERED":"#a55f4f","NOT_FEASIBLE":"#777777","BLOCKED":"#3f3f3f"}


def _clean(value: Any) -> Any:
    if isinstance(value,(np.integer,)): return int(value)
    if isinstance(value,(np.floating,)): return None if np.isnan(value) else float(value)
    if isinstance(value,(pd.Timestamp,)): return value.isoformat()
    if isinstance(value,dict): return {str(k):_clean(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)): return [_clean(v) for v in value]
    return value


def stable_json(value: Any) -> str:
    return json.dumps(_clean(value),ensure_ascii=False,separators=(",",":"),sort_keys=True)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(_clean(payload),ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")


def build_registry(hypotheses: list[dict[str,Any]], feasibility: list[dict[str,Any]], baselines: list[dict[str,Any]], eligibility_summary: dict[str,dict[str,Any]], catalog: dict[str,dict[str,Any]]) -> pd.DataFrame:
    f={row["experiment_id"]:row for row in feasibility}; b={row["experiment_id"]:row for row in baselines}
    rows=[]
    for h in hypotheses:
        eid=h["experiment_id"]; status=f[eid]; base=b[eid]; eligible=eligibility_summary[eid]; intervention=catalog[h["intervention_id"]]
        rows.append({
            "experiment_id":eid,"experiment_name":h["experiment_name"],"queue":h["queue"],"hypothesis_id":h["hypothesis_id"],"intervention_id":h["intervention_id"],
            "design_type":h["design_type"],"status":status["status"],"target_population":h["target_population"],"unit_of_analysis":h["unit_of_analysis"],"unit_of_randomization":h["unit_of_randomization"],
            "reference_date":pd.Timestamp("2024-12-31T19:00:00"),"eligibility_rule_ids":stable_json(h["watchlist_rule_ids"]),"eligible_accounts":status["available_eligible_sample"],
            "required_sample":status["required_sample"],"adjusted_required_sample":status["adjusted_required_sample"],"feasibility_status":status["feasibility_status"],
            "primary_metric":h["primary_metric"],"baseline_value":status["baseline_value"],"minimum_detectable_effect":status["minimum_detectable_effect"],
            "alpha":status["alpha"],"power":status["power"],"allocation_ratio":status["allocation_ratio"],"duration_days":h["expected_duration"],"follow_up_days":h["follow_up_window"],
            "evidence_strength":"HISTORICAL_DESCRIPTIVE_ONLY","data_confidence":eligible["dominant_confidence"],"contamination_risk":h["contamination_risk"],"ethical_risk":h["ethical_risk"],
            "operational_complexity":h["operational_complexity"],"estimated_cost_category":intervention["cost_category"],"requires_approval":True,"causal_status":"UNTESTED",
            "limitations":stable_json(["NO_EXPERIMENT_EXECUTED","NO_RESULT_AVAILABLE","HISTORICAL_BASELINE_NOT_CONTROL"]),"version":"1.0.0",
        })
    return pd.DataFrame(rows).sort_values("experiment_id").reset_index(drop=True)


def build_specifications(hypotheses: list[dict[str,Any]], eligibility_specs: list[dict[str,Any]], plans: list[dict[str,Any]], guardrails: list[dict[str,Any]], stops: list[dict[str,Any]], ethics: list[dict[str,Any]], feasibility: list[dict[str,Any]], seed: int) -> pd.DataFrame:
    by_eid=lambda rows:{eid:[row for row in rows if row["experiment_id"]==eid] for eid in sorted({row["experiment_id"] for row in rows})}
    elig=by_eid(eligibility_specs); sap=by_eid(plans); guards=by_eid(guardrails); stopping=by_eid(stops); ethical=by_eid(ethics); feas=by_eid(feasibility)
    rows=[]
    for h in hypotheses:
        eid=h["experiment_id"]
        sections={"HYPOTHESIS":h,"ELIGIBILITY":elig[eid][0],"DESIGN":{"design_type":h["design_type"],"unit_of_randomization":h["unit_of_randomization"],"contamination_risk":h["contamination_risk"]},"METRICS":{"primary":h["primary_metric"],"secondary":h["secondary_metrics"],"mde":h["minimum_detectable_effect"]},"RANDOMIZATION":{"randomization_seed":seed,"stratification_variables":["mrr_band","data_confidence"],"allocation_ratio":1.0,"assignment_method":"DETERMINISTIC_SEEDED_BLOCK_SIMULATION_ONLY"},"SAP":sap[eid][0],"GUARDRAILS":guards[eid],"STOPPING_RULES":stopping[eid],"ETHICS":ethical[eid][0],"FEASIBILITY":feas[eid][0],"SUCCESS_CRITERIA":{"decision_threshold":"Pre-specified MDE with confidence interval excluding null and no guardrail violation","confidence_interval_policy":"95% interval reported regardless of direction","practical_significance":"Must meet pre-specified MDE","statistical_significance":"Not p-value alone","minimum_exposure_rate":.80,"minimum_data_completeness":.80}}
        for section,payload in sections.items():
            values=sorted(payload.items()) if isinstance(payload,dict) else [("items",payload)]
            for key,value in values:
                rows.append({"experiment_id":eid,"section":section,"specification_key":key,
                    "specification_value":stable_json(value) if isinstance(value,(dict,list,tuple)) else str(value),
                    "source":"PHASE_8_GOVERNED_DESIGN","version":"1.0.0"})
    return pd.DataFrame(rows).sort_values(["experiment_id","section","specification_key"]).reset_index(drop=True)


def build_findings(registry: pd.DataFrame) -> list[dict[str,Any]]:
    groups=[("EF01",["EXP006"],"A data-quality study has sufficient historical design population for methodological review."),("EF02",["EXP001"],"The high-MRR adoption RCT is underpowered for its pre-specified MDE with the current eligible population."),("EF03",["EXP002","EXP007"],"Adoption designs require either more eligible accounts or the missing operational rollout cohort."),("EF04",["EXP003"],"Support follow-up cannot support cluster randomization until support-agent identifiers are collected."),("EF05",["EXP004"],"Recurring-churn review is constrained by subscription-overlap exclusions and sample size."),("EF06",["EXP005"],"Reactivation supports a feasibility pilot only because the historical population is small."),("EF07",["EXP008"],"Recent-churn quasi-experimental work requires additional comparable observations and confounding controls.")]
    findings=[]
    for fid,eids,statement in groups:
        rows=registry.loc[registry["experiment_id"].isin(eids)]
        findings.append({"finding_id":fid,"title":statement.split(".")[0],"statement":statement,"experiment_ids":eids,"queue":"MULTIPLE" if rows["queue"].nunique()>1 else rows["queue"].iloc[0],"eligible_accounts":int(rows["eligible_accounts"].sum()),"required_sample":int(rows["adjusted_required_sample"].sum()),"feasibility_status":sorted(rows["feasibility_status"].unique().tolist()),"primary_metric":sorted(rows["primary_metric"].unique().tolist()),"baseline":rows[["experiment_id","baseline_value"]].to_dict("records"),"minimum_detectable_effect":rows[["experiment_id","minimum_detectable_effect"]].to_dict("records"),"quality_constraints":["HISTORICAL_BASELINE_ONLY","FUTURE_FOLLOW_UP_REQUIRED"],"ethical_constraints":["APPROVAL_REQUIRED","NO_MRR_SERVICE_DENIAL"],"operational_constraints":["NO_INTERVENTION_IMPLEMENTED","EXPOSURE_LOGGING_REQUIRED"],"confidence_level":"MEDIUM" if "READY_FOR_REVIEW" in set(rows["status"]) else "LOW","limitations":["NO_CAUSAL_RESULT","NO_UPLIFT_AVAILABLE"],"recommended_next_step":"Human methodological review and required data collection before any execution."})
    return findings


def build_artifacts(registry: pd.DataFrame, hypotheses: list[dict[str,Any]], feasibility: list[dict[str,Any]], sample_sizes: list[dict[str,Any]], baselines: list[dict[str,Any]], balance: list[dict[str,Any]], guardrails: list[dict[str,Any]], ethics: list[dict[str,Any]], gates: list[dict[str,Any]], findings: list[dict[str,Any]], validation: dict[str,Any]) -> dict[str,Any]:
    metadata={"cutoff":"2024-12-31T19:00:00","population_denominator":500,"parameters":{"alpha":.05,"power":.80,"allocation_ratio":1.0,"assignment_seed":20260721},"limitations":["DESIGN_ONLY","NO_RESULT_AVAILABLE","HISTORICAL_BASELINE_NOT_CONTROL"],"version":"8.0.0"}
    status_counts=registry["status"].value_counts().sort_index().to_dict()
    payloads={
        "experiment_lab_summary.json":{"experiment_count":len(registry),"queues":registry["queue"].nunique(),"status_counts":status_counts,"interventions_executed":0,"results_available":False},
        "experiment_hypotheses.json":{"hypothesis_count":len(hypotheses),"hypotheses":hypotheses},
        "experiment_feasibility.json":{"experiments":feasibility,"gates":gates},
        "experiment_sample_size.json":{"scenarios":sample_sizes},
        "experiment_baselines.json":{"baselines":baselines,"historical_control_valid":False},
        "experiment_balance.json":{"checks":balance,"assignment_is_simulation_only":True},
        "experiment_metrics.json":{"primary_metrics":registry[["experiment_id","primary_metric","baseline_value","minimum_detectable_effect"]].to_dict("records"),"one_primary_metric_per_experiment":True},
        "experiment_guardrails.json":{"guardrails":guardrails,"monitoring_implemented":False},
        "experiment_ethics.json":{"assessments":ethics,"approval_bypassed":0},
        "experiment_findings.json":{"finding_count":len(findings),"findings":findings},
        "experiment_validation.json":validation,
    }
    for payload in payloads.values(): payload["metadata"]=metadata
    return payloads


def _finish(path: Path, subtitle: str) -> None:
    plt.figtext(.5,.01,subtitle,ha="center",fontsize=8,color="#555555"); plt.tight_layout(rect=(0,.04,1,1)); plt.savefig(path,dpi=180,bbox_inches="tight"); plt.close()


def create_figures(registry: pd.DataFrame, balance: list[dict[str,Any]], gates: list[dict[str,Any]], output: Path) -> None:
    output.mkdir(parents=True,exist_ok=True); ids=registry["experiment_id"].tolist()
    status=registry.set_index("experiment_id")["status"]
    plt.figure(figsize=(9,5)); plt.barh(ids,[1]*len(ids),color=[COLORS.get(value,"#777777") for value in status]); plt.xlim(0,1); plt.xticks([]); plt.title("Experiment design feasibility status");
    for y,eid in enumerate(ids): plt.text(.03,y,status[eid],va="center",color="white" if status[eid]!="PILOT_ONLY" else "#222222",fontsize=9)
    _finish(output/"experiment-feasibility.png","Eight design candidates | status is feasibility, not an experimental result")
    y=np.arange(len(ids)); available=registry["eligible_accounts"].to_numpy(); required=registry["adjusted_required_sample"].to_numpy()
    plt.figure(figsize=(10,6)); plt.barh(y-.18,available,height=.36,label="Available eligible",color="#2f6f8f"); plt.barh(y+.18,required,height=.36,label="Required after 10% attrition",color="#d6a85f"); plt.yticks(y,ids); plt.xlabel("Accounts"); plt.title("Available versus required sample"); plt.legend()
    _finish(output/"experiment-sample-size-gap.png","Pre-specified MDE, alpha=0.05, power=0.80; zero means not estimable")
    plt.figure(figsize=(9,5)); plt.barh(ids,available,color="#3f728f"); plt.xlabel("Eligible anonymous accounts"); plt.title("Eligible historical design population")
    _finish(output/"experiment-eligible-population.png","Eligibility is deterministic at cutoff 31 Dec 2024; future follow-up is still required")
    graph=nx.DiGraph(); designs=sorted(registry["design_type"].unique());
    for row in registry.to_dict("records"): graph.add_edge(row["design_type"],row["experiment_id"])
    pos={**{d:(0,i) for i,d in enumerate(designs)},**{eid:(2,i*(max(len(designs)-1,1))/(max(len(ids)-1,1))) for i,eid in enumerate(ids)}}
    plt.figure(figsize=(11,6)); nx.draw_networkx(graph,pos,node_color=["#2f6f8f" if n in designs else "#a7c4c9" for n in graph],node_size=1700,font_size=7,arrows=False,width=.7,edge_color="#999999"); plt.axis("off"); plt.title("Candidate experiments by design type")
    _finish(output/"experiment-design-map.png","Edges map future design specifications; no intervention has been executed")
    balance_df=pd.DataFrame(balance); covars=sorted(balance_df["covariate"].unique()) if len(balance_df) else []
    matrix=np.full((len(ids),len(covars)),np.nan)
    for i,eid in enumerate(ids):
        for j,cov in enumerate(covars):
            values=balance_df.loc[balance_df["experiment_id"].eq(eid)&balance_df["covariate"].eq(cov),"value"]
            if len(values) and pd.notna(values.iloc[0]): matrix[i,j]=abs(float(values.iloc[0]))
    plt.figure(figsize=(11,6)); plt.imshow(matrix,aspect="auto",cmap="Blues",vmin=0,vmax=max(.3,np.nanmax(matrix) if np.isfinite(matrix).any() else .3)); plt.colorbar(label="Absolute balance diagnostic"); plt.xticks(range(len(covars)),covars,rotation=45,ha="right"); plt.yticks(range(len(ids)),ids); plt.title("Simulated assignment balance checks")
    _finish(output/"experiment-balance-check.png","SMD or maximum proportion difference; preferred threshold < 0.10; missing = not estimable")
    gate_df=pd.DataFrame(gates); gate_names=sorted(gate_df["gate"].unique()); score={"PASS":1,"PASS_WITH_APPROVAL":.8,"PASS_WITH_CONSTRAINTS":.8,"PASS_WITH_DESIGN_CONTROL":.8,"PILOT":.5,"FAIL":0}; gm=np.zeros((len(ids),len(gate_names)))
    for i,eid in enumerate(ids):
        for j,gate in enumerate(gate_names): gm[i,j]=score.get(gate_df.loc[gate_df["experiment_id"].eq(eid)&gate_df["gate"].eq(gate),"status"].iloc[0],.5)
    plt.figure(figsize=(10,5)); plt.imshow(gm,aspect="auto",cmap="Blues",vmin=0,vmax=1); plt.colorbar(label="Gate state: 0 fail, 1 pass"); plt.xticks(range(len(gate_names)),gate_names,rotation=40,ha="right"); plt.yticks(range(len(ids)),ids); plt.title("Experiment governance gates")
    _finish(output/"experiment-governance-gates.png","Seven pre-execution gates; intermediate values require approval, constraints, or pilot review")


def render_reports(report_dir: Path, registry: pd.DataFrame, artifacts: dict[str,Any], plans: list[dict[str,Any]], guardrails: list[dict[str,Any]], stops: list[dict[str,Any]]) -> None:
    report_dir.mkdir(parents=True,exist_ok=True); counts=registry["status"].value_counts().to_dict(); ready=counts.get("READY_FOR_REVIEW",0); pilot=counts.get("PILOT_ONLY",0); under=counts.get("UNDERPOWERED",0); infeasible=counts.get("NOT_FEASIBLE",0)
    main=f"""# Governed Experiment Lab

## 1. Technical summary

Eight future design candidates were specified at the 31 December 2024 cutoff: {ready} ready for methodological review, {pilot} pilot-only, {under} underpowered, and {infeasible} not feasible with current design inputs. No intervention, outcome, uplift, or causal result exists.

## 2. Objective

The lab converts governed watchlist evidence into reproducible experiment specifications, not execution instructions or conclusions.

## 3. Observation is not causality

Historical observations motivate hypotheses. Only a future approved design with valid assignment, exposure, follow-up, analysis, and guardrails could support a causal conclusion.

## 4. Source watchlists

Six behavioral queues and one data-quality queue supply anonymous candidate populations. Data-quality review never creates a commercial intervention.

## 5. Hypotheses remain untested

All eight hypotheses have `causal_status=UNTESTED`; nulls, alternatives, mechanisms, and limitations are pre-specified without expected effects.

## 6. Candidate interventions

Ten versioned catalog entries describe possible future capabilities, approvals, risks, and prohibited uses. None is implemented.

## 7. Designs reflect interference and measurement constraints

![Design map](figures/experiment-design-map.png)

RCT is preferred when account isolation is plausible; support requires agent clusters, onboarding requires rollout cohorts, reactivation is a pilot, and data reconciliation is a quality study.

## 8. Eligibility is deterministic

![Eligible population](figures/experiment-eligible-population.png)

Eligibility excludes low confidence, insufficient coverage, missing design units, and metric-specific blockers. Historical eligibility does not guarantee future enrollment.

## 9. One primary metric per experiment

Primary metrics are selected for the intervention mechanism and decision cadence; churn is long-term or observational where the population cannot support it as a sole near-term endpoint.

## 10. Baselines are descriptive only

Historical baseline values size the design. They are not randomized controls and cannot establish an effect.

## 11. Sample size precedes promotion

![Sample gap](figures/experiment-sample-size-gap.png)

Required sample uses alpha 0.05, power 0.80, equal allocation, the pre-specified MDE, and 10% attrition. Underpowered designs retain their label.

## 12. Randomization is simulated only

Seeded blocked assignment validates mechanics with anonymous keys and `simulation_only=true`; it creates no operational treatment list.

## 13. Balance is diagnostic, not a result

![Balance checks](figures/experiment-balance-check.png)

Absolute SMD and proportion differences are compared with the preferred 0.10 threshold. Failures require design review, never manual account manipulation.

## 14. Statistical analysis is pre-specified

ITT is primary, per-protocol is secondary, estimands are explicit, missing data cannot be imputed favorably, and multiple testing uses one primary metric plus Holm-controlled confirmatory secondaries.

## 15. Guardrails can stop a future study

Guardrails cover completeness, delivery failure, consent, operational capacity, and adverse conditions; this phase implements no monitoring.

## 16. Ethics constrains every candidate

MRR cannot deny service or silently exclude beneficial treatment. Consent, equity, reversibility, minimization, and human approval are mandatory.

## 17. Feasibility is mixed by design

![Feasibility status](figures/experiment-feasibility.png)

The portfolio deliberately preserves underpowered, pilot-only, and not-feasible candidates instead of weakening MDE or inventing operational identifiers.

## 18. Findings identify preparation work

Seven findings prioritize methodological review, additional recruitment, support-agent instrumentation, rollout cohorts, and controlled quality-study execution.

## 19. Limitations

The dataset is historical, follow-up is not future-observed, exposure logs do not exist, cluster/cohort keys are incomplete, and no result can be interpreted causally.

## 20. Preparation for application integration

The application may display designs, gates, sample gaps, and specifications. It must not provide launch controls, treatment lists, causal results, or outbound actions.
"""
    methodology=f"""# Experiment Methodology

## Decision frame

Design future tests without executing interventions. Eight candidates use a hierarchy from RCT through quality study and pilot.

## Eligibility and conflict policy

Anonymous queue populations are filtered deterministically. Future operations allow one active behavioral experiment per account; data-quality studies may coexist. Technical simulations remain independent and non-operational.

## Baseline and power

Baselines are historical descriptions. Proportion, mean, and survival calculations use alpha 0.05 and power 0.80; sample requirements are never reduced to force feasibility. Attrition scenarios are 5%, 10%, and 20%.

## Assignment and balance

Seed 20260721 performs blocked technical assignment by MRR band and data confidence. Balance uses SMD and maximum proportion difference, with 0.10 as preferred review threshold.

## Causal boundary

No result, uplift, synthetic outcome, effect estimate, or causal conclusion is produced.
"""
    registry_lines=["# Experiment Registry","","| Experiment | Design | Eligible | Adjusted required | Status | Primary metric |","|---|---:|---:|---:|---|---|"]
    for row in registry.to_dict("records"): registry_lines.append(f"| {row['experiment_id']} | {row['design_type']} | {row['eligible_accounts']} | {row['adjusted_required_sample']} | {row['status']} | {row['primary_metric']} |")
    sap_lines=["# Statistical Analysis Plans",""]
    for plan in plans: sap_lines += [f"## {plan['experiment_id']}","",f"- ITT: `{str(plan['intention_to_treat']).lower()}`",f"- Estimand: {plan['primary_estimand']}",f"- Primary analysis: {plan['primary_analysis']}",f"- Missing data: {plan['missing_data_policy']}",f"- Multiple testing: {plan['multiple_testing_policy']}",f"- Stopping: {plan['stopping_rule']}",""]
    governance=f"""# Experiment Governance

## Approval and ethics

Every candidate requires approval, consent review, fairness review, reversibility, and data minimization. MRR may support stratification but cannot determine service denial.

## Contamination and operational boundaries

![Governance gates](figures/experiment-governance-gates.png)

High contamination requires cluster, stepped-wedge, switchback, or quality-study controls. Missing operational keys fail the relevant gate.

## Guardrails and stopping

There are {len(guardrails)} guardrail specifications and {len(stops)} stopping-rule specifications. Monitoring and intervention delivery remain unimplemented.

## Prohibited operations

No contact, discount, plan change, cancellation, product modification, treatment assignment, or automated recommendation is authorized.
"""
    validation=f"""# Experiment Lab Validation

## Result

`{artifacts['experiment_validation.json']['gate_result']}` with zero unexplained reconciliation difference.

## Passed controls

- no raw IDs or PII;
- no future events;
- no intervention execution or customer contact;
- no synthetic outcome, uplift, result, or EFFECTIVE/RUNNING status;
- simulation-only assignment with anonymous keys;
- available sample reconciled to deterministic eligibility;
- historical baselines explicitly not causal controls;
- ethics, contamination, measurement, sample, data, quality, and operational gates recorded.

## Required caveats

Underpowered, pilot-only, and missing-design-unit candidates require more data or operational preparation before review can advance.
"""
    outputs={"experiment-lab.md":main,"experiment-methodology.md":methodology,"experiment-registry.md":"\n".join(registry_lines)+"\n","experiment-statistical-analysis-plan.md":"\n".join(sap_lines).rstrip()+"\n","experiment-governance.md":governance,"experiment-validation.md":validation}
    for name,text in outputs.items(): (report_dir/name).write_text(text,encoding="utf-8")
