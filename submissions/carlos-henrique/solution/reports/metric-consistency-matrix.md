# Metric Consistency Matrix

## Result

**Gate: PASS.** The evaluator-facing README, the local dashboard snapshot, and the governed analytical reports reconcile at the fixed cutoff `2024-12-31T19:00:00`. The cross-platform wrapper changes only how the existing Python builder is invoked; it does not change analytical inputs, JSON content, metrics, or interpretation.

## Governed Metrics

| Metric | Authorized value | README | Dashboard JSON | Primary evidence | Status |
|---|---:|---:|---:|---|---|
| Accounts | 500 | 500 | 500 | [Dashboard validation](dashboard-validation.md) | PASS |
| Processed events | 35,586 | 35,586 | 35,586 | [Event-log validation](event-log-validation.md) | PASS |
| Usable events | 13,927 | 13,927 | 13,927 | [Event-log validation](event-log-validation.md) | PASS |
| Quarantined records | 21,659 | 21,659 | 21,659 | [Quarantine report](quarantine-report.md) | PASS |
| Customer journeys | 4,221 | 4,221 | 4,221 | [Journey mining](journey-mining.md) | PASS |
| Promoted journey patterns | 435 | 435 | 435 | [JourneyGraph](journeygraph.md) | PASS |
| Promoted transitions | 43 | 43 | 43 | [JourneyGraph](journeygraph.md) | PASS |
| Review queues | 7 | 7 | 7 | [Intervention watchlist](intervention-watchlist.md) | PASS |
| Review items | 1,609 | 1,609 | 1,609 | [Watchlist methodology](watchlist-methodology.md) | PASS |
| Unique accounts in review | 500 | 500 | 500 | [Watchlist methodology](watchlist-methodology.md) | PASS |
| Experiment designs | 8 | 8 | 8 | [Experiment registry](experiment-registry.md) | PASS |
| Ready for review | 1 | 1 | 1 | [Experiment registry](experiment-registry.md) | PASS |
| Pilot only | 1 | 1 | 1 | [Experiment registry](experiment-registry.md) | PASS |
| Underpowered | 4 | 4 | 4 | [Experiment registry](experiment-registry.md) | PASS |
| Not feasible | 2 | 2 | 2 | [Experiment registry](experiment-registry.md) | PASS |

## Snapshot and Semantic Controls

| Control | Expected | Observed | Status |
|---|---|---|---|
| Historical cutoff | `2024-12-31T19:00:00` | Direct in 14 resources; `demo_story.json` inherits the global `metadata.json` cutoff | PASS |
| JSON inventory | 15 files | 15 files | PASS |
| Inventory SHA-256 | Stable across rebuilds | `be5d2d2edcc6992de678b5ef0d7d18d16ce39f423421ec5f6805aaebc664b61b` | PASS |
| Builder input gate | 25 governed input hashes | 25 hashes verified | PASS |
| PII-like fields | 0 | 0 | PASS |
| Raw operational IDs | 0 | 0 | PASS |
| Prohibited product language | 0 | 0 | PASS |
| Non-finite values | 0 | 0 | PASS |
| Executed experiment or synthetic outcome | 0 | 0 | PASS |
| Causal claims | 0 | 0 | PASS |
| Associated MRR semantics | Context only | Not revenue at risk, saved revenue, or attributed impact | PASS |

## Rebuild Interpretation

Two consecutive `npm run build:data` executions must retain the 15 filenames, byte sizes, individual SHA-256 hashes, inventory digest, cutoff, and governed metrics above. A wrapper-only tooling change requires no hash update when the generated content is unchanged. Any future content divergence blocks documentation approval until the matrix and source evidence are reconciled.
