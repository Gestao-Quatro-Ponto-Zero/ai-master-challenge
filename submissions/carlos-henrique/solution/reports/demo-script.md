# Guided Demo Script - 3:10

The app also contains an eight-step in-product Guided Demo at `/demo`. This presenter script is designed for a 2-4 minute evaluation.

| Time | Route | Click | Presenter line | Metric/evidence | Transition |
|---|---|---|---|---|---|
| 0:00-0:20 | `/` | Open Overview | "Retention intelligence starts by turning fragmented historical events into governed evidence, not by jumping to a prediction." | 500 accounts; 35,586 processed events | "First, let us see what survived the quality gates." |
| 0:20-0:45 | `/quality` | Data & Quality in navigation | "Only 13,927 events are usable. The 21,659 excluded records remain a quality backlog and never become behavioral signal." | MAIN/STRICT populations; warning coverage; quarantine separation | "With the evidence boundary clear, we can inspect actual journeys." |
| 0:45-1:15 | `/journeys` | Choose `DEMO_B`, then `DEMO_C` | "`DEMO_B` shows recurring observed churn; `DEMO_C` shows a reactivation with usage return. These are anonymous historical examples, not ranked accounts." | 4,221 governed journeys; three real demo accounts | "Repeated journey evidence can now be explored as a bounded knowledge graph." |
| 1:15-1:45 | `/graph` | Change Graph mode to Pattern explorer; select a node | "Only promotable ROBUST or SENSITIVE evidence is present. The view is reduced, filtered, and explicitly descriptive." | 435 promoted patterns; 43 promoted transitions; max 35 nodes/80 edges | "The same governed evidence can support human review queues." |
| 1:45-2:20 | `/watchlist` | Filter a queue; click View evidence | "Seven queues organize investigation. Priority is a transparent matrix of discrete components, never a score or probability. Every item requires a human decision." | Seven queues; anonymous 500-account source population; associated MRR only | "Potential actions are hypotheses, so the next step is experiment design." |
| 2:20-2:50 | `/experiments` | Open the first experiment detail | "Eight designs specify eligibility, sample requirements, metrics, SAP, safeguards, and stopping rules. Every causal status is `UNTESTED`; nothing was executed." | Eight experiments; 119 Phase 8 tests before dashboard work | "We close by making the controls as visible as the opportunity." |
| 2:50-3:10 | `/governance` | Open an Explain this disclosure | "The demo has zero raw PII, future leakage, scores, automated interventions, executed experiments, and causal claims. Each number keeps its source, denominator, cutoff, and limitation." | 15 deterministic JSONs; fixed cutoff 2024-12-31 19:00 | "The result is ready for documentation and submission, not live operations." |

## Demo accounts

- `DEMO_A` - low engagement, no observed churn.
- `DEMO_B` - recurring observed churn.
- `DEMO_C` - observed reactivation followed by usage return.

These labels map to three real anonymous analytical accounts selected deterministically. Never reveal or narrate the underlying account keys.

## Presenter safeguards

Say "observed", "associated", "historical", "descriptive", and "requires human review". Do not say "will churn", "caused", "revenue at risk", "saved revenue", "recommended action", or "successful experiment". If asked about production use, state that authentication, live data, observability, interventions, and experiment execution are intentionally outside Phase 9.
