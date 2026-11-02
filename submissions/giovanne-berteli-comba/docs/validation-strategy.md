# Validation strategy

This is a plan, not a test report. Dataset roles, metric populations and evaluation
boundaries are owned by [D02](../knowledge/dataset-usage.md). The selected stack,
runtime/anomaly contracts and acceptance cases are owned by
[S01](../knowledge/solution-scope.md). V00 freezes numerical criteria and selection
procedures before implementation. Do not report a planned check as a passing test.

| Layer | Meaningful checks | Evidence |
| --- | --- | --- |
| Data audit | Actual schema and units, nulls, duplicates, invalid durations, label distribution, source/version | Audit outputs and data manifest |
| Unit | Metric calculations, denominators, routing rules, exception behavior, cost assumptions | Focused automated test results |
| Integration | Input → preprocessing → selected automation → user-visible result or human handoff; invalid input and unavailable dependencies | Tests with reproducible fixtures |
| Anomalies (F03) | Comparable references; high/low deviations; ordinary and insufficient-reference cases; persisted reasons, versions and review state; filter correctness | Reproducible cases and saved anomaly/review records |
| AI evaluation | Baseline comparison, held-out split, duplicate separation, label support, per-class errors, macro F1 when appropriate | Versioned evaluation outputs and error analysis |
| Operational | Coverage versus errors under different handoff thresholds, realistic failure modes, measured latency/cost if used | Evaluation or simulation results with assumptions |
| Submission | Setup, evidence links, allowed file scope, readable Portuguese narrative, working CodeTour when implemented | Final reviewer checklist |

Choose numerical quality targets after inspecting data and defining the
business cost of errors. A model score is not automatically a calibrated
probability. Evaluate cross-domain use separately and disclose its limitations.
The first supervised benchmark uses IT Document/Topic_group only; customer
Ticket Type labels are not IT targets. No pooled metrics or invented mapping.
Unlabeled customer-domain probes cannot establish accuracy, F1 or OOD recall.
Provided processed text does not prove entry-time availability of every word.
Avoid using resolutions or other outcome information as inputs to entry-time
triage. Estimate active effort saved separately from elapsed ticket duration.

Define and record the evaluation protocol in V00, before I01: baseline, entry-time
inputs, duplicate/group separation, development/validation/test membership, business
error costs and selection criteria. Select model, prompt and handoff/anomaly limits
using development/validation data. Reserve the final test for the chosen version;
disclose any reuse that influences a later choice. Keep domain-transfer evaluation
separate. Audit actual data before choosing numerical targets or anomaly limits.

For F03, distinguish numerical rarity, uncertainty and technical failure. A high
score is not inherently an error or an anomaly. Compare only compatible metric
definitions, scales, model/rule versions and ticket groups. With too little reference
data, record insufficient reference rather than inventing a normal range.

Persist case/run identifiers, metric/value, comparison reference, direction,
reason, rule version, timestamp and review state without unnecessary personal data.
These are operational solution records, separate from recruitment process logs.
Allow filtering by high/low direction, reason and review state. Preserve original
values; do not silently discard outliers or convert a review decision into training
data. Test recording plus retrieval/filtering end to end. Measure false alerts and
review workload alongside automation errors and coverage. Any handoff action must
follow an explicit rule; an anomaly flag alone does not define that action.

S01 now supplies that explicit policy and the required I01/V01 fixtures. Verify
normal suggestion, invalid/oversized input, unsupported context, missing/stale
artifacts, zero known features, timeout, invalid/nonfinite output and failed writes.
Verify high/low/equal-bound/constant-reference/insufficient-reference metric cases,
atomic run+metric persistence, idempotent delivery/reloads, combined filters and
append-only review revisions preserving original predictions/values. All suggested
categories still require confirmation; coverage is not autonomous resolution.
Automated fixture reviewers must be identified as tests, not human adjudication.

For F05/F07, acquire data with a versioned manifest and hashes, validate time units
and report relevant populations, missing satisfaction responses and open tickets.
Distinguish elapsed time, active effort, and assumed versus measured savings.

Start with saved test and evaluation reports. Add a dashboard only if it makes
repeated analysis or simulations materially easier. The foundation itself needs
document/link/frontmatter checks and regression probes for its consistency and
receipt-invalidation rules, rather than application tests. See the
[foundation controls](foundation-controls.md) for runnable commands and limits.
