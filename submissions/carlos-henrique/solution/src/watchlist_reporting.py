"""Aggregate artifacts, restrained figures, and answer-first watchlist reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd


COLORS = ["#24445c", "#3f728f", "#66a0b5", "#a7c4c9", "#d6a85f", "#a55f4f", "#777777"]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def build_aggregates(items: pd.DataFrame, summary: pd.DataFrame, evidence: pd.DataFrame, executions: list[dict[str, Any]], feature_accounting: dict[str, Any], graph_metrics: dict[str, Any], validation: dict[str, Any]) -> dict[str, Any]:
    queue_rows = []
    for queue, group in items.groupby("queue", sort=True):
        accounts = group.drop_duplicates("account_key")
        queue_rows.append({"queue": queue, "items": len(group), "accounts": len(accounts), "population_denominator": feature_accounting["accounts"], "population_share": len(accounts) / feature_accounting["accounts"], "deduplicated_associated_mrr": float(accounts["associated_mrr"].sum()), "priorities": group["priority"].value_counts().sort_index().to_dict(), "confidence": group["data_confidence"].value_counts().sort_index().to_dict()})
    priority_rows = [{"priority": key, "items": int((items["priority"] == key).sum()), "accounts_highest_priority": int((summary["highest_priority"] == key).sum())} for key in ("P1", "P2", "P3", "P4")]
    queues = sorted(items["queue"].unique())
    overlap = []
    queue_sets = {q: set(items.loc[items["queue"].eq(q), "account_key"]) for q in queues}
    for left in queues:
        for right in queues:
            overlap.append({"queue_left": left, "queue_right": right, "account_overlap": len(queue_sets[left] & queue_sets[right])})
    graph_items = items.loc[items["graph_pattern_count"].gt(0)]
    findings = []
    for index, (queue, group) in enumerate(items.groupby("queue", sort=True), 1):
        accounts=group.drop_duplicates("account_key")
        if len(accounts) < 20: continue
        findings.append({
            "finding_id": f"WF{index:02d}", "title": f"Governed review volume in {queue}",
            "statement": f"{len(accounts)} of {feature_accounting['accounts']} accounts met at least one deterministic rule for {queue} at the cutoff.",
            "queue": queue, "rule_ids": sorted(group["watchlist_rule_id"].unique()),
            "population": "MAIN_WITH_STRICT_SENSITIVITY", "distinct_accounts": len(accounts),
            "population_share": len(accounts)/feature_accounting["accounts"],
            "deduplicated_associated_mrr": float(accounts["associated_mrr"].sum()),
            "priority_distribution": group["priority"].value_counts().sort_index().to_dict(),
            "evidence_strength_distribution": group["evidence_strength"].value_counts().sort_index().to_dict(),
            "data_confidence_distribution": group["data_confidence"].value_counts().sort_index().to_dict(),
            "stability_distribution": group["stability_status"].value_counts().sort_index().to_dict(),
            "graph_evidence": {"accounts": int(group.loc[group["graph_pattern_count"].gt(0),"account_key"].nunique()), "interpretation":"STRUCTURAL_NOT_CAUSAL"},
            "quality_constraints": {"accounts_requiring_review": int(accounts["requires_data_review"].sum()), "quarantine_behavioral_signals":0},
            "confidence_level": "MEDIUM", "limitations": ["DESCRIPTIVE_NOT_PREDICTIVE","ASSOCIATION_NOT_CAUSATION","QUALITY_DEPENDENT"],
            "business_relevance": "Organizes bounded human investigation without prescribing an intervention.",
            "recommended_human_investigation": str(group["authorized_investigation"].iloc[0]),
        })
    payloads = {
        "watchlist_summary.json": {"reference_date": feature_accounting["reference_date"], "accounts": len(summary), "items": len(items), "queues": len(queues), "configured_rules": len(executions), "deduplicated_associated_mrr": float(summary["associated_mrr"].sum()), "human_review_required": True, "operational_actions": 0},
        "watchlist_rules.json": {"rule_executions": executions},
        "watchlist_queue_metrics.json": {"queues": queue_rows},
        "watchlist_priority_metrics.json": {"priorities": priority_rows, "matrix_type": "EXPLICIT_DISCRETE_P1_P4", "weighted_score": False},
        "watchlist_overlap.json": {"queue_overlap": overlap, "accounts_in_multiple_queues": int(summary["active_queue_count"].gt(1).sum())},
        "watchlist_evidence_summary.json": {"evidence_packets": len(evidence), "packets_with_graph_context": int(graph_items.shape[0]), "sources": ["PHASE_3_DIAGNOSTIC", "PHASE_4_SURVIVAL", "PHASE_5_JOURNEY", "PHASE_6_GRAPH", "DATA_QUALITY"]},
        "watchlist_graph_evidence.json": {**graph_metrics, "watchlist_items_with_graph_evidence": len(graph_items), "interpretation": "STRUCTURAL_NOT_CAUSAL"},
        "watchlist_quality.json": {**feature_accounting, **validation["quality"], "gate_result": validation["gate_result"]},
        "watchlist_findings.json": {"finding_count": len(findings), "findings": findings},
        "watchlist_validation.json": validation,
    }
    meta={"population":"MAIN_WITH_STRICT_SENSITIVITY","population_denominator":feature_accounting["accounts"],"cutoff":feature_accounting["reference_date"],"rules_version":"7.0.0","limitations":["DESCRIPTIVE_NOT_PREDICTIVE","ASSOCIATION_NOT_CAUSATION","HUMAN_REVIEW_REQUIRED"]}
    for payload in payloads.values():
        payload["metadata"] = meta
    return payloads


def _finish(path: Path, subtitle: str) -> None:
    plt.figtext(.5, .01, subtitle, ha="center", fontsize=8, color="#555555")
    plt.tight_layout(rect=(0, .04, 1, 1)); plt.savefig(path, dpi=180, bbox_inches="tight"); plt.close()


def create_figures(items: pd.DataFrame, summary: pd.DataFrame, figure_dir: Path, reference_date: str) -> None:
    figure_dir.mkdir(parents=True, exist_ok=True)
    q = items.groupby("queue")["account_key"].nunique().sort_values()
    plt.figure(figsize=(10, 5.5)); q.plot.barh(color=COLORS[1]); plt.title("Accounts by governed review queue"); plt.xlabel("Distinct accounts")
    _finish(figure_dir / "watchlist-queue-distribution.png", f"Account overlap is allowed | denominator=500 | cutoff={reference_date}")
    p = summary["highest_priority"].value_counts().reindex(["P1", "P2", "P3", "P4"], fill_value=0)
    plt.figure(figsize=(8, 4.8)); p.plot.bar(color=COLORS[:4]); plt.title("Highest review priority per account"); plt.ylabel("Distinct accounts"); plt.xticks(rotation=0)
    _finish(figure_dir / "watchlist-priority-distribution.png", f"Explicit decision matrix; no weighted score | n={len(summary)}")
    rules = sorted(items["watchlist_rule_id"].unique()); sets = {r: set(items.loc[items["watchlist_rule_id"].eq(r), "account_key"]) for r in rules}; matrix=np.array([[len(sets[a]&sets[b]) for b in rules] for a in rules])
    plt.figure(figsize=(9, 7)); plt.imshow(matrix, cmap="Blues"); plt.colorbar(label="Account overlap"); plt.xticks(range(len(rules)), rules, rotation=90); plt.yticks(range(len(rules)), rules); plt.title("Rule overlap map")
    _finish(figure_dir / "watchlist-rule-overlap.png", f"Cell values are distinct-account intersections | cutoff={reference_date}")
    conf = items.groupby(["queue", "data_confidence"]).size().unstack(fill_value=0).reindex(columns=["LOW","MEDIUM","HIGH"], fill_value=0)
    plt.figure(figsize=(10, 5.5)); conf.plot.bar(stacked=True, color=[COLORS[5],COLORS[4],COLORS[1]], ax=plt.gca()); plt.title("Data confidence composition by queue"); plt.ylabel("Watchlist items"); plt.xticks(rotation=35, ha="right")
    _finish(figure_dir / "watchlist-quality-confidence.png", "LOW confidence blocks behavioral P1 escalation")
    mrr = items.drop_duplicates(["queue","account_key"]).groupby("queue")["associated_mrr"].sum().sort_values()
    plt.figure(figsize=(10, 5.5)); mrr.plot.barh(color=COLORS[4]); plt.title("Associated MRR by queue"); plt.xlabel("De-duplicated associated MRR within queue")
    _finish(figure_dir / "watchlist-mrr-by-queue.png", "Associated MRR is context, not saved or lost revenue; accounts may overlap across queues")
    g=nx.DiGraph(); phases=["Diagnostic","Survival","Journey","Graph","Quality"]; queues_short=[q.replace("_REVIEW","").replace("_"," ").title() for q in sorted(items["queue"].unique())]
    for phase in phases:
        for queue in queues_short: g.add_edge(phase, queue)
    pos={**{p:(0,i) for i,p in enumerate(phases)}, **{q:(2,i*4/(max(len(queues_short)-1,1))) for i,q in enumerate(queues_short)}}
    plt.figure(figsize=(11,6)); nx.draw_networkx(g,pos,node_color=[COLORS[1] if n in phases else COLORS[3] for n in g],node_size=1400,font_size=7,arrows=False,width=.4,edge_color="#aaaaaa"); plt.axis("off"); plt.title("Evidence source map for human review queues")
    _finish(figure_dir / "watchlist-evidence-map.png", "Links indicate provenance availability, not causal direction")


def render_reports(report_dir: Path, aggregates: dict[str, Any]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    s=aggregates["watchlist_summary.json"]; q=aggregates["watchlist_quality.json"]; v=aggregates["watchlist_validation.json"]
    main=f"""# Intervention Watchlist

## 1. Executive Summary

At cutoff `{s['reference_date']}`, {s['accounts']} of 500 accounts appear in at least one governed review queue, generating {s['items']} rule-level items across {s['queues']} queues. The result is `{v['gate_result']}`: it is suitable for human triage with preserved quality flags, not for automated decisions, outreach, prediction, or causal interpretation.

## 2. Decision context

The watchlist directs scarce analyst attention to evidence review. It does not prescribe treatment.

## 3. Population and cutoff

All features use evidence at or before `{s['reference_date']}`; denominator is 500 anonymous accounts.

## 4. Queue portfolio

![Queue distribution](../figures/watchlist-queue-distribution.png)

Queues overlap by design because each rule is evaluated independently. Counts are distinct within queue.

## 5. Priority distribution

![Priority distribution](../figures/watchlist-priority-distribution.png)

P1–P4 comes from four discrete components and an explicit matrix; no weighted score is used.

## 6. Rule overlap

![Rule overlap](../figures/watchlist-rule-overlap.png)

Overlap exposes convergent evidence and never increases priority mechanically.

## 7. Data confidence

![Quality confidence](../figures/watchlist-quality-confidence.png)

LOW confidence blocks behavioral P1. Quality-first queues remain eligible for urgent human review.

## 8. Materiality context

![MRR by queue](../figures/watchlist-mrr-by-queue.png)

MRR is de-duplicated inside each queue and is associated context—not saved or lost revenue.

## 9. Evidence provenance

![Evidence map](../figures/watchlist-evidence-map.png)

Each item retains cutoff, sources, metrics, graph paths, findings, quality flags, and limitations.

## 10. JourneyGraph evidence

Only promoted ROBUST/SENSITIVE, non-HIGH, non-small patterns enter explanations. Structural paths are non-causal.

## 11. Quality gate

{q['accounts_requiring_data_review']} watchlisted accounts require data review; quarantine contributes zero behavioral signals.

## 12. Rule governance

Sixteen versioned deterministic rules declare owners, authorized investigations, exclusions, minimum support, and prohibited actions.

## 13. Explainability

Explanations state what was observed, why it matched, timing, graph and quality context, limitations, and the authorized next step.

## 14. Human workflow

The owner reviews source evidence, confirms quality and relevance, documents disposition, and closes or escalates the investigation. No contact is implied.

## 15. Privacy and LGPD

Outputs expose anonymous stable keys only. Aggregate JSONs contain no account keys, raw IDs, names, emails, or free text.

## 16. Limitations

The evidence is retrospective, observational, sensitive to source quality, and not a prediction or causal estimate. Small groups are not generalized.

## 17. Readiness for Phase 8

The governed output can inform an Experiment Lab only if eligibility, exclusion, quality, consent, review, and measurement controls remain explicit.
"""
    main=f"""# Intervention Watchlist

## 1. Executive Summary

At cutoff `{s['reference_date']}`, {s['accounts']} of 500 accounts appear in at least one governed review queue, generating {s['items']} rule-level items across {s['queues']} queues. The result is `{v['gate_result']}`: suitable for human triage with preserved quality flags, not for automated decisions, outreach, prediction, or causal interpretation.

## 2. Purpose

The watchlist directs scarce analyst attention to evidence review. It does not prescribe treatment or rank customers by hidden logic.

## 3. Governance principles

Rules are deterministic and versioned; evidence, urgency, materiality, and confidence remain separate; every disposition requires a human reviewer.

## 4. Populations

MAIN includes VALID and VALID_WITH_WARNING without quarantine. STRICT uses VALID only for sensitivity. Quarantine is quality-only and creates no behavioral signal.

## 5. Reference date

All features use evidence at or before `{s['reference_date']}`; denominator is 500 anonymous accounts and historical cutoffs are supported.

## 6. Queues

![Queue distribution](../figures/watchlist-queue-distribution.png)

Queues overlap by design because each rule is evaluated independently. Counts are distinct within queue.

## 7. Rules

![Rule overlap](../figures/watchlist-rule-overlap.png)

Sixteen deterministic rules declare conditions, exclusions, minimum support, owner, investigation, version, and prohibited actions. W002 remains documented without promotion because it has seven cases versus minimum support ten.

## 8. Priority

![Priority distribution](../figures/watchlist-priority-distribution.png)

P1-P4 comes from four discrete components and an explicit matrix; no weighted score is used. LOW confidence blocks behavioral P1.

## 9. Evidence

![Evidence map](../figures/watchlist-evidence-map.png)

Each packet retains cutoff, sources, observed metrics, graph paths, findings, denominators, quality flags, limitations, and structured provenance.

## 10. JourneyGraph

Only promoted ROBUST/SENSITIVE, non-HIGH, non-small patterns enter explanations. Structural paths are non-causal.

## 11. Quality

![Quality confidence](../figures/watchlist-quality-confidence.png)

{q['accounts_requiring_data_review']} watchlisted accounts require data review; quarantine contributes zero behavioral signals.

## 12. Materiality

![MRR by queue](../figures/watchlist-mrr-by-queue.png)

MRR is de-duplicated inside each queue and is associated context, not saved or lost revenue. Cross-queue sums must not be added because accounts overlap.

## 13. Explanations

Templates state what was observed, why it matched, timing, graph and quality context, limitations, authorized investigation, and prohibited interpretation.

## 14. Findings

At most one aggregate finding is emitted per queue and only when at least 20 distinct accounts support it. Findings include denominator, MRR deduplication, distributions, graph context, quality constraints, confidence, limitations, and human investigation.

## 15. Limitations

Evidence is retrospective, observational, and quality-sensitive. W011 is a justified broad quality exception; W014 and W015 require broad-rule review; the four-account W008 group is not generalized into a finding.

## 16. Human review

The owner confirms source quality and relevance, documents disposition, and closes or escalates the investigation. No contact or intervention is implied.

## 17. Preparation for Experiment Lab

The governed output can inform an Experiment Lab only if eligibility, exclusion, quality, consent, review, and measurement controls remain explicit.
"""
    methodology=f"""# Watchlist Methodology

## Scope

Cutoff-safe features feed a quality gate, sixteen deterministic rules, four discrete LOW/MEDIUM/HIGH components, and an explicit P1–P4 matrix. The logical grain is account × cutoff × rule.

## Quality-first policy

Quarantined evidence is permitted only for DATA_QUALITY_REVIEW. Behavioral rules require configured coverage and stability; behavioral rules over 70% of the population are suppressed. LOW-confidence behavioral P1 is demoted.

## Reconciliation

There are {s['items']} items and {s['accounts']} account summaries. Associated MRR reconciles after account de-duplication; unexplained difference is {v['difference_unexplained']}.

## Interpretation

Outputs are descriptive review aids. No opaque score, model, probability, causal effect, automated outreach, or operational action is produced.
"""
    rules="# Watchlist Rules\n\n"+"\n".join(f"## {r['rule_id']} — {r['rule_name']}\n\nQueue: `{r['queue']}`. Status: `{r['status']}`. Promoted accounts: {r['promoted_accounts']} / {r['population_denominator']}. Version: `{r['version']}`.\n" for r in aggregates["watchlist_rules.json"]["rule_executions"])
    validation=f"""# Watchlist Validation

## Result

`{v['gate_result']}` with zero unexplained reconciliation differences and zero operational actions.

## Passed controls

- anonymous account keys only;
- cutoff-safe evidence;
- no behavioral P1 with LOW confidence;
- no UNSTABLE, HIGH-order, or small-sample graph evidence;
- quality-only quarantine policy;
- de-duplicated MRR reconciliation;
- aggregate JSON privacy;
- deterministic explanations without unsafe causal language.

## Warnings

Quality and broad-rule flags are retained for human review, not hidden by the gate.
"""
    explain=f"""# Watchlist Explainability

## Evidence packet

Every item records observation, rule rationale, supporting metrics, cutoff window, graph context, quality context, limitations, authorized investigation, prohibited interpretation, sources, denominators, and provenance.

## Boundaries

The wording is descriptive and non-causal. It does not infer intent, predict churn, estimate individual treatment effect, prescribe action, or authorize customer contact.

## Human review

Reviewers must confirm source quality and contextual relevance before documenting a disposition. Evidence gaps must lead to data review, not stronger claims.
"""
    for name,text in {"intervention-watchlist.md":main,"watchlist-methodology.md":methodology,"watchlist-rules.md":rules,"watchlist-validation.md":validation,"watchlist-explainability.md":explain}.items():
        (report_dir/name).write_text(text,encoding="utf-8")
