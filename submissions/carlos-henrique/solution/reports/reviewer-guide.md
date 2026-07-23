# JourneyGraph Reviewer Guide

## 2-Minute Review

1. Open the [main README](../../README.md) and read the Executive Summary.
2. Inspect the [executive screenshot](screenshots/01-executive-overview.png).
3. Scan [Key Results](../../README.md#key-results).
4. Compare JourneyGraph with a conventional dashboard in [What Makes JourneyGraph Different](../../README.md#what-makes-journeygraph-different).

**Expected answer:** JourneyGraph transforms fragmented historical SaaS data into governed journeys, stable graph evidence, manual review queues, and experiment-readiness artifacts.

## 5-Minute Review

1. Run or inspect the application routes: `/`, `/quality`, `/journeys`, `/graph`, `/watchlist`, `/experiments`, and `/governance`.
2. Read the 18 decisions in [Human Judgment](../../process-log/HUMAN_JUDGMENT.md).
3. Use the [Evidence Map](../../process-log/EVIDENCE_MAP.md) to trace major claims.
4. Confirm privacy, temporal, causal, and operational boundaries in [Governance](dashboard-validation.md).

**Expected answer:** The product is a deterministic investigation aid, not an individual forecast or automated intervention system.

## 15-Minute Technical Review

1. Read [Architecture](../../docs/architecture.md) and [Data Contract](../../docs/data-contract.md).
2. Inspect [event-log validation](event-log-validation.md), [journey methodology](journey-methodology.md), [graph methodology](graph-methodology.md), [watchlist methodology](watchlist-methodology.md), and [experiment methodology](experiment-methodology.md).
3. Review test and build commands in the [app README](../app/README.md).
4. Run [documentation validation](../scripts/validate_documentation.py), [process-evidence validation](../scripts/validate_process_evidence.py), and [final-submission validation](../scripts/validate_final_submission.py).
5. Inspect [AI Trace](../../process-log/AI_TRACE.md), [Errors and Corrections](../../process-log/AI_ERRORS_AND_CORRECTIONS.md), and [Rejected Hypotheses](../../process-log/REJECTED_HYPOTHESES.md).
6. Follow the Quick Start:

```bash
cd submissions/carlos-henrique/solution/app
npm ci
npm run build:data
npm run dev
```

**Expected answer:** Metrics reconcile at explicit grains and cutoffs; quality, stability, privacy, and interpretation gates are versioned and reproducible.

## Evidence Shortcuts

| Question | Primary path |
|---|---|
| What problem is solved? | [One-pager](journeygraph-one-pager.md) |
| Are metrics consistent? | [Metric consistency matrix](metric-consistency-matrix.md) |
| What did the candidate decide? | [Human Judgment](../../process-log/HUMAN_JUDGMENT.md) |
| How was AI used? | [AI Trace](../../process-log/AI_TRACE.md) |
| What failed or was rejected? | [Errors](../../process-log/AI_ERRORS_AND_CORRECTIONS.md) and [Rejected Hypotheses](../../process-log/REJECTED_HYPOTHESES.md) |
| Can it be reproduced? | [Clean-room validation](clean-room-validation.md) |
| What remains external? | [External Link Registry](external-link-registry.md) |

## Interpretation Boundary

All evidence is historical through December 31, 2024. Quarantined rows do not support behavior, graph paths are descriptive, queues require human review, and experiment designs have no measured effect.
