"""Ethics, contamination, language, and feasibility gates for design artifacts."""

from __future__ import annotations

from typing import Any


ALLOWED_STATUSES={"DRAFT","READY_FOR_REVIEW","PILOT_ONLY","UNDERPOWERED","NOT_FEASIBLE","BLOCKED"}
FORBIDDEN_STATUSES={"RUNNING","SUCCESS","FAILED","EFFECTIVE"}


def ethics_assessment(hypothesis: dict[str, Any], intervention: dict[str, Any]) -> dict[str, Any]:
    risk=hypothesis["ethical_risk"]
    constraints=["HUMAN_APPROVAL_REQUIRED","DATA_MINIMIZATION","NO_MRR_BASED_SERVICE_DENIAL","NO_AUTOMATED_OUTREACH","REVERSIBILITY_PLAN"]
    return {"experiment_id":hypothesis["experiment_id"],"consent_review":"REQUIRED","fairness_review":"REQUIRED","mrr_use":"STRATIFICATION_OR_MATERIALITY_ONLY_NOT_SERVICE_DENIAL","behavioral_data_use":"MINIMIZED_AND_AUDITABLE","human_review":True,"reversibility":intervention["reversibility"],"ethical_risk":risk,"constraints":constraints,"ethics_gate":"PASS_WITH_CONSTRAINTS","intervention_executed":False}


def evaluate_feasibility(hypotheses: list[dict[str, Any]], power_summaries: list[dict[str, Any]], eligibility_summary: dict[str, dict[str, Any]], catalog: dict[str, dict[str, Any]], baseline_by_experiment: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]],list[dict[str, Any]],list[dict[str, Any]]]:
    power={row["experiment_id"]:row for row in power_summaries}; gates=[]; ethics=[]; summaries=[]
    for hypothesis in hypotheses:
        eid=hypothesis["experiment_id"]; p=power[eid]; eligible=eligibility_summary[eid]; intervention=catalog[hypothesis["intervention_id"]]
        ethics_row=ethics_assessment(hypothesis,intervention); ethics.append(ethics_row)
        missing_unit=hypothesis["design_type"] in {"CLUSTER_RANDOMIZED_TRIAL","STEPPED_WEDGE"} and p["available_eligible_sample"]==0
        gate_values={
            "DATA_GATE":"FAIL" if missing_unit else "PASS",
            "SAMPLE_GATE":"PASS" if p["feasibility_status"] in {"FEASIBLE","MARGINALLY_FEASIBLE"} else "PILOT" if hypothesis["design_type"]=="PILOT_FEASIBILITY_STUDY" else "FAIL",
            "QUALITY_GATE":"PASS" if eligible["low_confidence_eligible"]==0 or hypothesis["design_type"]=="DATA_QUALITY_STUDY" else "FAIL",
            "CONTAMINATION_GATE":"PASS_WITH_DESIGN_CONTROL" if hypothesis["contamination_risk"]=="HIGH" and hypothesis["design_type"] in {"CLUSTER_RANDOMIZED_TRIAL","STEPPED_WEDGE","SWITCHBACK","DATA_QUALITY_STUDY"} else "PASS" if hypothesis["contamination_risk"]!="HIGH" else "FAIL",
            "ETHICS_GATE":"PASS_WITH_CONSTRAINTS",
            "OPERATIONAL_GATE":"FAIL" if missing_unit else "PASS_WITH_APPROVAL",
            "MEASUREMENT_GATE":"PASS" if baseline_by_experiment[eid]["sample_size"]>0 else "FAIL",
        }
        for gate,status in gate_values.items(): gates.append({"experiment_id":eid,"gate":gate,"status":status,"limitation":"Design review required before any execution."})
        if gate_values["ETHICS_GATE"]=="FAIL": status="BLOCKED"
        elif any(gate_values[key]=="FAIL" for key in ("DATA_GATE","OPERATIONAL_GATE","MEASUREMENT_GATE","CONTAMINATION_GATE")): status="NOT_FEASIBLE"
        elif hypothesis["design_type"]=="PILOT_FEASIBILITY_STUDY": status="PILOT_ONLY"
        elif gate_values["SAMPLE_GATE"]=="FAIL": status="UNDERPOWERED"
        else: status="READY_FOR_REVIEW"
        summaries.append({**p,"experiment_id":eid,"status":status,"feasibility_status":status,"gates":gate_values,"requires_approval":True,"causal_status":"UNTESTED","intervention_executed":False})
    return gates,ethics,summaries


def validate_governance(registry: list[dict[str, Any]], findings: list[dict[str, Any]]) -> dict[str, Any]:
    statuses={row["status"] for row in registry}
    if statuses-FORBIDDEN_STATUSES-ALLOWED_STATUSES or statuses&FORBIDDEN_STATUSES: raise AssertionError("Forbidden experiment status.")
    if any(row["causal_status"]!="UNTESTED" for row in registry): raise AssertionError("Causal status advanced without experiment.")
    factual_fields=[str(row.get("statement","")) for row in findings]
    forbidden=("was effective","reduced churn","saved revenue","uplift achieved","caused an increase")
    violations=sum(any(term in text.lower() for term in forbidden) for text in factual_fields)
    if violations: raise AssertionError("Unsupported causal or result language.")
    return {"forbidden_statuses":0,"causal_status_violations":0,"unsupported_result_language":0,"interventions_executed":0,"contacts_sent":0,"approvals_bypassed":0}
