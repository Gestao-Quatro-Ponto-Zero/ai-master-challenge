# JourneyGraph Final Metric Snapshot

This snapshot repeats only canonical repository evidence. It introduces no new analytical metric and preserves the fixed historical boundary.

| Item | Value | Source | Last validated phase | Status |
|---|---:|---|---|---|
| Accounts | 500 | [Metric matrix](metric-consistency-matrix.md) | 10C | PASS |
| Processed events | 35,586 | [Event-log validation](event-log-validation.md) | 10C | PASS |
| Usable events | 13,927 | [Event-log validation](event-log-validation.md) | 10C | PASS |
| Quarantined records | 21,659 | [Quarantine report](quarantine-report.md) | 10C | PASS |
| Governed journeys | 4,221 | [Journey mining](journey-mining.md) | 10C | PASS |
| Promoted patterns | 435 | [Graph validation](graph-validation.md) | 10C | PASS |
| Promoted transitions | 43 | [Graph validation](graph-validation.md) | 10C | PASS |
| Review queues | 7 | [Watchlist validation](watchlist-validation.md) | 10C | PASS |
| Review items | 1,609 | [Watchlist methodology](watchlist-methodology.md) | 10C | PASS |
| Unique review accounts | 500 | [Watchlist methodology](watchlist-methodology.md) | 10C | PASS |
| Experiment designs | 8 | [Experiment validation](experiment-validation.md) | 10C | PASS |
| Experiment readiness | 1 `READY_FOR_REVIEW`; 1 `PILOT_ONLY`; 4 `UNDERPOWERED`; 2 `NOT_FEASIBLE` | [Experiment registry](experiment-registry.md) | 10C | PASS |
| Historical cutoff | `2024-12-31T19:00:00` | [Metric matrix](metric-consistency-matrix.md) | 10C | PASS |
| Python tests | 130/130 | Fase 10C technical gate | 10C | PASS |
| Vitest | 19/19 | Fase 10C technical gate | 10C | PASS |
| Playwright | 36/36 | Fase 10C technical gate | 10C | PASS |
| Documentation links | 67 local links checked | Documentation validator | 10C | PASS |
| Evidence links | 238 internal links checked | Process-evidence validator | 10C | PASS |
| Commits validated | 15 phase commits including Fase 10C | `git log` and post-commit gate | 10C | PASS |

## Interpretation Boundary

The values describe a fixed local snapshot. Quarantined records remain quality backlog, graph evidence remains associative, MRR remains context, review items are not customer rankings, and readiness is not an experiment outcome.
