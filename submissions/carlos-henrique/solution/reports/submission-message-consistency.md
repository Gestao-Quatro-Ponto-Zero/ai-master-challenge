# JourneyGraph Submission Message Consistency

**Gate: PASS.** The evaluator-facing materials use one product identity, one evidence snapshot, one governance boundary, and one experiment-readiness classification.

## Canonical Message

- **Name:** JourneyGraph.
- **Tagline:** Governed Retention Intelligence from Temporal Customer Journeys.
- **Operating boundary:** fixed historical and descriptive evidence for human investigation and test design.
- **Decision boundary:** queues require human review; the application cannot initiate customer contact.
- **Experiment boundary:** eight designs remain `UNTESTED`: one `READY_FOR_REVIEW`, one `PILOT_ONLY`, four `UNDERPOWERED`, and two `NOT_FEASIBLE`.
- **Cutoff:** `2024-12-31T19:00:00`.

## Cross-Material Review

| Item | Surfaces compared | Canonical result | Status |
|---|---|---|---|
| Product name | README, one-pager, pitches, video, form, PR, reviewer guide, dashboard | JourneyGraph | PASS |
| Tagline | README, one-pager, form draft, PR draft, video assets | Governed Retention Intelligence from Temporal Customer Journeys | PASS |
| Accounts | README, dashboard, metric matrix, snapshot, form, PR | 500 anonymous accounts | PASS |
| Events | README, dashboard, pitches, video, matrix, snapshot | 35,586 processed; 13,927 usable; 21,659 quarantined | PASS |
| Journeys and graph | README, dashboard, pitch, video, form, PR, snapshot | 4,221 journeys; 435 promoted patterns; 43 promoted transitions | PASS |
| Review evidence | README, dashboard, video, form, PR, snapshot | Seven queues; 1,609 rule-level items; 500 unique accounts | PASS |
| Experiment readiness | README, dashboard, video, form, PR, snapshot | Eight `UNTESTED` designs with the canonical 1/1/4/2 readiness split | PASS |
| Temporal boundary | README, one-pager, video, matrix, snapshot, dashboard | Fixed cutoff `2024-12-31T19:00:00` | PASS |
| Causality | README, one-pager, pitches, video, form, PR, dashboard | Historical associations do not establish treatment effects | PASS |
| Revenue language | README, one-pager, video, form, PR, dashboard | Associated MRR is context, not a forecast or protected value | PASS |
| Human governance | README, video, watchlist, form, PR, dashboard | Review is mandatory and no customer action is initiated | PASS |
| Runtime boundary | README, architecture, app guide, form, PR | Validated local JSON snapshot; no external runtime service | PASS |
| External state | README, form, PR, registry, checklist | Recording, deployment, upload, PR creation, form completion, and publication remain user-controlled | PASS |

## Surface Coverage

The review included the README, one-pager, both pitches, main video script, form draft, PR description, reviewer guide, seven screenshots, metric matrix, final metric snapshot, and the local dashboard data contract. Screenshots were inspected as immutable evidence from the validated Fase 9 state; no screenshot was regenerated for this phase.
