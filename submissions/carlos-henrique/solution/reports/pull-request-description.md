# JourneyGraph — Carlos Henrique
**Tagline:** Governed Retention Intelligence from Temporal Customer Journeys.


## Summary

JourneyGraph is a governed retention-intelligence product that reconstructs customer journeys from fragmented SaaS data, promotes stable sequence evidence into a graph, organizes explainable human-review queues, and converts observations into `UNTESTED` experiment designs.

## Problem

Accounts, subscriptions, usage, support, churn, and reactivation have different grains and temporal semantics. Direct joins can inflate measures, invalid chronology can enter behavior, and terminal labels can erase recurrent churn and return episodes.

## Solution

The submission establishes a canonical temporal contract, preserves quality failures in quarantine, compares MAIN and STRICT populations, reconstructs governed journeys, promotes only supported graph evidence, and keeps operational decisions under human review.

## Key Deliverables

- Audited source relationships and immutable raw-data policy.
- Canonical event log, temporal rules, quarantine, and episode model.
- Descriptive churn, survival, journey, and revenue-context diagnostics.
- Journey mining, taxonomy, stability controls, and NetworkX-first graph.
- Seven deterministic review queues with evidence packets.
- Eight experiment designs with eligibility, power, guardrails, and `UNTESTED` status.
- Local pt-BR dashboard built from deterministic JSON snapshots.
- Human-judgment, AI-collaboration, pitch, video, deployment, and submission evidence.

## Key Results

| Metric | Value |
|---|---:|
| Accounts | 500 |
| Processed / usable / quarantined events | 35,586 / 13,927 / 21,659 |
| Governed journeys | 4,221 |
| Promoted patterns / transitions | 435 / 43 |
| Review queues / items | 7 / 1,609 |
| Experiment designs | 8, all `UNTESTED` |

All values describe the fixed historical snapshot through December 31, 2024.

## Product Walkthrough

1. `/` — Executive evidence pipeline and interpretation boundary.
2. `/quality` — MAIN, STRICT, warnings, and quarantine.
3. `/journeys` — Anonymous ordered histories with recurrent churn and reactivation.
4. `/graph` — Bounded promoted JourneyGraph evidence.
5. `/watchlist` — Deterministic queues and reviewer evidence.
6. `/experiments` — Readiness, power, safeguards, and `UNTESTED` designs.
7. `/governance` — Privacy, temporal, causal, and operational controls.

## Technical Architecture

Python builds governed analytical artifacts and 15 deterministic JSON snapshots. NetworkX is the local reference graph runtime; Neo4j is an optional export. The Next.js application reads local snapshots and statically prerenders evaluator routes. Runtime requires no external API, database, credential, or AI service.

## Human Judgment

The candidate documented 18 material decisions, including rejection of the mega-join, quarantine over silent repair, recurrent lifecycle modeling, MAIN/STRICT sensitivity, no Cox result, stable graph promotion, deterministic queues, manual review, controlled localization, anonymized UI aliases, and a cross-platform evaluator command.

## AI Collaboration

An AI coding assistant supported decomposition, drafts, alternatives, tests, review, and corrections. Suggestions did not become accepted evidence until human review and deterministic validation passed. Errors and rejected hypotheses are documented with linked artifacts.

## Governance and Safety

- Historical descriptive evidence only.
- Explicit cutoff `2024-12-31T19:00:00`.
- Quarantine excluded from behavioral evidence.
- No displayed raw operational account IDs or free text.
- No predictive score or automated customer action.
- Associated MRR is descriptive context.
- Every experiment remains `UNTESTED`.
- External publication steps require user approval and verification.

## Validation

- Python pytest: 130/130 PASS.
- Vitest: 19/19 PASS.
- Playwright: 36/36 PASS.
- Production build: PASS, ten static routes including not-found.
- Production dependency audit: zero vulnerabilities.
- Documentation and process-evidence validators: PASS.
- Deterministic dashboard rebuild: 15/15 files, zero divergence.

## How to Run

```bash
cd submissions/carlos-henrique/solution/app
npm ci
npm run build:data
npm run dev
```

Open `http://localhost:3000`.

## Limitations

The snapshot is fixed and historical. Quality warnings materially affect some analyses; the graph is bounded and descriptive; the review queues require manual interpretation; experiment readiness is not effectiveness; and public deployment has not yet been performed.

## Reviewer Guide

- Start with the [main README](../../README.md).
- Use the [reviewer guide](reviewer-guide.md) for two-, five-, or fifteen-minute paths.
- Inspect [human judgment](../../process-log/HUMAN_JUDGMENT.md) and the [evidence map](../../process-log/EVIDENCE_MAP.md).
- Reproduce the result using the Quick Start and validation commands.

## Submission Checklist

- [x] README and architecture documented
- [x] Seven final screenshots present
- [x] Cross-platform Quick Start validated
- [x] Analytical and process evidence linked
- [x] Privacy, temporal, causal, and human-review boundaries documented
- [x] Internal tests and validators passed
- [ ] Public demo added
- [ ] Demo video added
- [ ] Final external links verified

External placeholders remain in [external-link-registry.md](external-link-registry.md) until user verification.
