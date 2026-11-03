# Backlog

These are proposals, not approved implementation requirements. Promote an item
only when its value, effort, dependencies, and acceptance criteria are clear.

| Idea | Trigger for implementation | Current state |
| --- | --- | --- |
| Internal analysis/test dashboard | Reviewer cannot connect operational findings, benchmark and decisions in one view | Delivered in M02; aggregate-only consultation also available |
| Component gallery | Multiple reusable UI components need isolated inspection or demonstration | Deferred |
| Additional skills | A recurring workflow warrants reusable instructions beyond AGENTS.md | Deferred |
| Help-desk integration | Needed to demonstrate a specific business flow and feasible within scope | Deferred |
| Advanced simulations | Baseline works and a concrete failure mode needs investigation | Deferred |

The prototype now includes M01–M05 following the user’s explicit request. R02
recorded the proposals; their implementation is tracked in the execution plan. The
[review](../docs/pre-submission-review.md) owns the rationale, sources and acceptance
details. Priority reflects expected benefit, not measured interviewer performance.

| ID | Priority / proposal | Benefit / dependencies | Acceptance and current state |
| --- | --- | --- | --- |
| M01 | Delivered: executive entry and guided demo | Short path from problem and human decisions to evidence and working flow; use existing results | One-page entry and five-minute proposed demo, explicit attribution and sources; delivered — see [M01–M05](../knowledge/management.md) |
| M02 | Delivered: read-only management/results view | Surface business findings, actions and evaluation without searching JSON; reuse aggregates and existing UI stack | Separate customer diagnosis, IT benchmark and local activity; useful without a model/local runs, no final-test examples or new fits; delivered — see [M01–M05](../knowledge/management.md) |
| M03 | Delivered: setup and historical-status clarity | Linux/platform prerequisites, preparation stages, entry context and consumed-test status | Correct reserved-test console wording and historical next-step ambiguity; check affected paths without changing frozen calculations; delivered — see [M01–M05](../knowledge/management.md) |
| M04 | Delivered: defined operational export | Move filtered cases/review events into a spreadsheet workflow | IDs, versions and counts reconcile with filters; default omits original text and distinguishes cases/metric rows; delivered — see [M01–M05](../knowledge/management.md) |
| M05 | Delivered: capacity simulator | Test review/rework assumptions and break-even using the existing formula | Positive and negative hypothetical outcomes visible; no IT-to-customer coverage substitution; delivered — see [M01–M05](../knowledge/management.md) |
| FUT01 | Future: prospective pilot and event/effort capture | Validate workflow, labels and net benefit with representative new data | Define baseline, quality/workload acceptance and measurement before observing outcomes; proposed |
| FUT02 | Future: metric-grounded AI analyst | Explain computed metrics and flag inconsistencies with traceable evidence | Deterministic calculations/checks, source/population/version for claims and separate narrative-quality evaluation; proposed |
| FUT03 | Future: Google Sheets | Team queue/review workflow following local export | Authorized access, stable IDs, idempotent delivery and reconciliation; proposed |
| FUT04 | Future: email/channel summaries | Notify meaningful changes, failures or action-needed states | Configured recipients, deduplication, authenticated reachable app and observable delivery; proposed |
| FUT05 | Future: interactive bot | Case lookup, assignment and review in the team's existing channel | Adopt only for a real workflow with authentication/roles and audit; proposed |
| FUT06 | Future: helpdesk integration and controlled improvement | Bring representative ticket events and human corrections into daily use | Validated entry-time text/taxonomy, event contracts and new-data evaluation by model version; proposed |

M01–M05 were authorized and delivered before P01. FUT01–FUT06 remain planned
ideas outside this delivery; [reviewer roadmap](../docs/future-roadmap.md).
Architecture review IDs F01–F07 remain owned exclusively by the official
architecture review table.
