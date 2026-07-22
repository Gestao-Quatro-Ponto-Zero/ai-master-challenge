# JourneyGraph Process Evidence Map

## Purpose

This map lets an evaluator move from a major claim to its primary proof, a secondary control, the introducing commit, and the current validation state. All paths are repository-relative and all commits are present in local history.

## Evidence Register

| Evidence ID | Claim | Primary artifact | Secondary artifact | Commit | Validation status |
|---|---|---|---|---|---|
| EV-HJ-001 | A canonical event log precedes downstream analysis | [Event-log validation](../solution/reports/event-log-validation.md) | [Temporal rules](../solution/reports/temporal-rules.md) | `75be8ef0663f0f49b425092735ffe0a3c6ed65f6` | PASS |
| EV-HJ-002 | Fatal temporal cases are preserved in quarantine and excluded from behavior | [Quarantine report](../solution/reports/quarantine-report.md) | [Data contract](../docs/data-contract.md) | `75be8ef0663f0f49b425092735ffe0a3c6ed65f6` | PASS |
| EV-HJ-003 | MAIN and STRICT populations expose quality sensitivity | [Survival sensitivity](../solution/reports/survival-sensitivity.md) | [Journey stability](../solution/reports/journey-stability.md) | `83d9b16a270e2227bd67c52e4ebf3ce4aae3eb61` | PASS |
| EV-HJ-004 | Recurrent churn and explicit reactivation remain distinct events | [Churn diagnostic](../solution/reports/churn-diagnostic.md) | [Event-log validation](../solution/reports/event-log-validation.md) | `dd1f013cc502d9e690a1790331397897729edfd3` | PASS |
| EV-HJ-005 | Only stable, supported patterns are promotable | [Journey stability](../solution/reports/journey-stability.md) | [Graph methodology](../solution/reports/graph-methodology.md) | `1c31ae22632d27ac45137af5b55acee1d6f19f86` | PASS |
| EV-HJ-006 | JourneyGraph is local, governed, and structurally descriptive | [JourneyGraph report](../solution/reports/journeygraph.md) | [Graph validation](../solution/reports/graph-validation.md) | `1c31ae22632d27ac45137af5b55acee1d6f19f86` | PASS |
| EV-HJ-007 | Review queues use deterministic rules and require human disposition | [Intervention watchlist](../solution/reports/intervention-watchlist.md) | [Watchlist methodology](../solution/reports/watchlist-methodology.md) | `1ed6655cf86f9068f56a10af25537ea8747a25b1` | PASS |
| EV-HJ-008 | Experiment status describes readiness while all causal statuses remain `UNTESTED` | [Experiment registry](../solution/reports/experiment-registry.md) | [Experiment validation](../solution/reports/experiment-validation.md) | `3e96b07e9f113c15ec2a9635324054c3e7b27b00` | PASS |
| EV-HJ-009 | Evaluator-facing data contains no PII-like fields or raw operational account IDs | [Dashboard validation](../solution/reports/dashboard-validation.md) | [Dashboard data contract](../solution/reports/dashboard-data-contract.md) | `fb6f09a34be2a77b3917b798ec22ed9fd56728ff` | PASS |
| EV-HJ-010 | Future leakage is blocked by explicit cutoffs and builder checks | [Temporal rules](../solution/reports/temporal-rules.md) | [Dashboard validation](../solution/reports/dashboard-validation.md) | `fb6f09a34be2a77b3917b798ec22ed9fd56728ff` | PASS |
| EV-HJ-011 | Product claims remain historical and non-causal | [Dashboard validation](../solution/reports/dashboard-validation.md) | [Experiment governance](../solution/reports/experiment-governance.md) | `fb6f09a34be2a77b3917b798ec22ed9fd56728ff` | PASS |
| EV-HJ-012 | Internal account and pattern keys are not rendered to evaluators | [Localization validation](../solution/reports/localization-validation.md) | [Dashboard validation](../solution/reports/dashboard-validation.md) | `de4ca14c66d33319af15aae492d04caadb910ff1` | PASS |
| EV-HJ-013 | The final interface is consistently localized to pt-BR | [Localization validation](../solution/reports/localization-validation.md) | [Main README](../README.md) | `de4ca14c66d33319af15aae492d04caadb910ff1` | PASS |
| EV-HJ-014 | Dashboard snapshots rebuild deterministically from governed inputs | [Metric consistency matrix](../solution/reports/metric-consistency-matrix.md) | [Dashboard data contract](../solution/reports/dashboard-data-contract.md) | `bffa9a29b3b471f876d02e5fb784fc2bb5fa7c4d` | PASS |
| EV-HJ-015 | The official Quick Start uses a cross-platform `build:data` path | [Main README](../README.md) | [App README](../solution/app/README.md) | `8f785e25d3652068a356f213fc6f596d76f8b266` | PASS |

## Validation Boundary

`PASS` means the linked artifact and commit support the stated repository claim. It does not extend the claim to live production data, customer treatment, a future snapshot, or an executed experiment. [Process evidence validation](../solution/reports/process-evidence-validation.md) checks paths, commits, required fields, links, language, and README/index integration.

## Limitations

The map verifies traceability, not universal validity. Each claim remains bounded to its linked historical artifact, fixed snapshot, and documented method; future data or operational use requires revalidation.
