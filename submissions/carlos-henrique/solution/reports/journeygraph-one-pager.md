# JourneyGraph — Governed Retention Intelligence from Temporal Customer Journeys

## Executive Summary

- **Fragmented SaaS records become trustworthy only after temporal governance.** JourneyGraph reconciles account, subscription, usage, support, churn, and reactivation evidence without an unsafe consolidated join.
- **The product turns governed history into explainable customer journeys.** A canonical event log, quarantine, MAIN/STRICT sensitivity, journey mining, and a promoted graph preserve provenance and limitations.
- **The operating model is review before action.** Deterministic queues support human investigation, while eight experiment designs remain `UNTESTED` and are classified by readiness rather than outcome.
- **The current deliverable is a reproducible local demonstration.** It uses a fixed historical snapshot through December 31, 2024, local JSON evidence, no external services at runtime, and no automatic customer action.

## Why Conventional Retention Views Fail

SaaS data usually arrives at incompatible grains. Direct joins can multiply rows and inflate totals; account-level flags can erase recurrent churn and reactivation; parseable timestamps can still violate lifecycle order. JourneyGraph makes those failure modes visible before business interpretation.

## What JourneyGraph Delivers

1. Audited source relationships and immutable raw inputs.
2. A canonical temporal event log with explicit quarantine.
3. Customer journeys and descriptive churn/survival evidence across MAIN and STRICT populations.
4. Stable journey patterns promoted into a local NetworkX-first graph.
5. Seven deterministic human-review queues with evidence packets.
6. Eight governed experiment designs with power, feasibility, guardrails, and `UNTESTED` status.
7. A pt-BR dashboard built from deterministic local snapshots.

## Canonical Evidence

| Evidence | Value | Interpretation |
|---|---:|---|
| Accounts | 500 | Anonymous fixed analytical population |
| Processed events | 35,586 | Event opportunities before quality gates |
| Usable events | 13,927 | MAIN behavioral population |
| Quarantined records | 21,659 | Preserved quality backlog, excluded from behavior |
| Governed journeys | 4,221 | Histories across declared scopes |
| Promoted patterns / transitions | 435 / 43 | Stable, supported descriptive graph evidence |
| Review items | 1,609 | Rule-level items across seven queues |
| Experiment designs | 8 | Planning artifacts; none has an observed effect |

## Business Use

Customer Success can investigate anonymous histories; Product can convert observations into falsifiable tests; leadership can see the evidence boundary; and Data/AI teams can audit provenance and reproducibility. The product does not issue a predictive score, authorize contact, or execute an intervention.

## Recommended Next Steps

1. Record the bounded three-minute demo using the approved routes and script.
2. Deploy only after the readiness runbook, privacy checks, and public URL validation pass.
3. Add final URLs to the registry, Pull Request draft, video description, and submission form.
4. Perform the final human publication gate before any external action.

## Further Questions

- Which deployment platform and public-access policy will the owner approve?
- Which experiment, if any, should enter a separately governed feasibility review?
- What upstream corrections could safely reduce the quarantine population?

## Caveats and Assumptions

All product evidence is historical and descriptive at the fixed cutoff `2024-12-31T19:00:00`. Associated MRR is contextual, graph structure is non-causal, queue membership requires human review, and experiment readiness is not effectiveness.

Primary evidence: [main README](../../README.md), [metric consistency matrix](metric-consistency-matrix.md), [human judgment](../../process-log/HUMAN_JUDGMENT.md), and [evidence map](../../process-log/EVIDENCE_MAP.md).
