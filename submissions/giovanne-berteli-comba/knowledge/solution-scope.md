---
type: Solution Contract
title: Local assisted IT triage and anomaly review
description: S01 scope, input/output contracts, human handoff, failure handling, anomaly persistence and success measures.
status: draft
sources:
  - id: dataset-roles
    resource: dataset-usage.md
  - id: diagnosis
    resource: operational-findings.md
  - id: pipeline
    resource: https://scikit-learn.org/stable/modules/compose.html
  - id: table-ui
    resource: https://docs.streamlit.io/develop/api-reference/data/st.dataframe
  - id: ui-state
    resource: https://docs.streamlit.io/develop/concepts/architecture/session-state
  - id: local-storage
    resource: https://docs.python.org/3.12/library/sqlite3.html
---

# Decision and implementation boundary

S01 selects one automation: suggest an IT ticket category and prepare a local human
review queue, recording numerical anomalies and their review history. Every result
requires human confirmation; nothing is sent to a customer or external helpdesk.
This is an agent design decision under the instruction to advance, not additional
human approval, a production policy or an implemented capability.

D02's separate populations remain binding. Customer data supplies diagnosis and
assumed effort scenarios; IT Document/Topic_group supplies the future benchmark.
No customer-category mapping, reply generation, payment/access execution, real
priority assignment, external integration, public deployment or dashboard is in I01.

[V00](evaluation-protocol.md) has frozen grouped splits, candidates, selection
procedure, assumed error costs and acceptance targets before I01. I01 then trains/selects using development/validation only;
V01 evaluates the selected version on the reserved test. This document is the
behavior contract; [I01 implementation](prototype.md) and its separate development
report now record completed training/selection, not final-test validation.

# Stack and components

Use Python 3.12, scikit-learn for a text Pipeline, Streamlit for two local views
(Triage; Review/anomalies), and standard-library sqlite3 for durable records.
The first learned candidate is TF-IDF plus logistic regression; V00 owns the
bounded candidate set and comparison to majority/simple-text baselines. A candidate
is not a selected winner, and its score is not a calibrated correctness probability.

Keep one core decision function shared by CLI/evaluation/UI, one SQLite repository,
thin UI, and offline training/evaluation scripts. No separate API service or remote
model provider is required. Streamlit provides tabular UI; session state is for
form intent only, not durable history. SQLite is the persistence authority.
[Pipeline](https://scikit-learn.org/stable/modules/compose.html),
[tables](https://docs.streamlit.io/develop/api-reference/data/st.dataframe),
[session state](https://docs.streamlit.io/develop/concepts/architecture/session-state),
[SQLite](https://docs.python.org/3.12/library/sqlite3.html).

Bind the future UI to loopback. V00 pinned and checked an isolated environment;
see [setup and import/constructor limits](../docs/evaluation-protocol.md). These
V00 checks did not demonstrate UI or trained-model behavior; I01 supplies separate
[software/functional evidence](../docs/prototype.md), with final evaluation pending.
Existing audit/diagnosis commands retain their standard-library-only setup.

# Input and readiness

- Input: original ticket text and declared context `it_service_en`,
  `customer_support` or `unknown`. The IT dataset loader supplies its known source;
  manual input context is an operator declaration, not automatic domain detection.
- Model feature: text only. Topic_group is a target, never an input. Status,
  resolution, rating, customer identity and true labels are not inference features.
- Normalize with NFKC, casefold and whitespace collapse (`nfkc-casefold-space-v1`),
  preserving the original valid text locally. Reject blank/non-string input and
  raw or normalized text over 10,000 characters; do not silently truncate it.
  This cap is a design convention, not a learned quality boundary.
- Class labels are exactly the eight observed IT categories. Validate an eight-
  component finite score vector in [0,1], summing to one within 1e-6. Unknown label,
  shape mismatch or nonfinite output is a technical failure, not a category.
- Verify owned model/configuration/reference manifests and hashes before loading.
  No uploaded or downloaded serialized model is accepted. Missing artifacts or
  unselected handoff/anomaly parameters mean not ready, not permissive defaults.
- Processed Document text does not prove entry-time availability. Manual declared
  IT context and a high score cannot prove in-domain or prospective validity.

# Decision precedence and output

Each explicit submission gets an immutable run_id and request_id; a case may have
multiple runs. Streamlit reruns never create an inference/review event by themselves.
Persist a unique request_id so duplicate delivery returns the original saved result.

| Condition | Outcome / queue | Prediction handling and reason |
| --- | --- | --- |
| Empty, non-string or oversized input | review_needed / triage_review | No prediction; invalid_input |
| Declared customer/unknown context | review_needed / triage_review | Do not apply IT model; unsupported_context |
| Missing/stale artifacts or incomplete selection parameters | failed / triage_review | No prediction; not_ready |
| No known features after vectorization | review_needed / triage_review | No prediction; no_known_features |
| Timeout, inference exception or invalid output | failed / triage_review | No usable prediction; timeout, inference_error or invalid_model_output |
| Score below frozen validation-selected threshold, anomaly high/low, or insufficient comparable reference | review_needed / triage_review | Retain valid original prediction; low_score, anomaly_review or insufficient_reference |
| Otherwise category in Access, Administrative rights, Purchase or HR Support | review_needed / specialist_review | Retain prediction; policy_human_category |
| Otherwise valid in-context prediction | suggested / standard_review | Retain prediction; standard_confirmation |

These queues are local suggested destinations, not integrations or proof of role
authorization. The four-category escalation is a design convention for access,
administration, purchases and people-related requests, not a finding of actual
business loss. Low-score/anomaly rules take precedence over class-based destinations;
retain all applicable reasons even when only one primary queue is selected.

The model worker has a 5-second per-request budget including load/transform/predict;
this is a timeout policy, not measured latency. The coordinator alone writes the
database and discards late worker results. Persistence failure must show an unsaved
failure and no normal/saved success; retry is explicit. V01 counts attempted versus
stored requests from its driver so failed writes cannot disappear from error rates.

The result contract contains: schema_version, case_id, request_id, run_id, UTC
created_at, context, source dataset/partition when known, text hash, outcome,
review_queue, reason_codes, nullable predicted_category/score, elapsed_ms,
model/policy/normalization/reference versions and hashes, metric evaluations and
persisted flag. All outcomes require human confirmation. Numeric values are kept
at original precision; display rounding must not govern decisions. Failure/unknown
scores are null, never invented zeros. Serialize without NaN/Infinity.

# Anomaly method and comparability (F03)

Evaluate two metrics per attempted run: `model_score` and normalized `text_chars`.
For a scored IT ticket compare only with validation predictions from the same
domain/language, chosen pipeline, predicted category, normalization and metric
definition. Version the frozen reference and its membership. Do not mix model
versions, classes, raw versus normalized lengths, customer data or future reviews.

Use empirical lower/upper quantiles with linear interpolation at (n-1)*q. V00
predeclares how tail quantiles are selected for review workload; I01 fits the
reference on validation only, then freezes it before final-test use. A minimum of
100 comparable reference records is required per group/metric. This is a
conservative design convention, not statistical certification. If a group has
fewer, record insufficient_reference rather than pool incompatible groups.

- `value < lower`: possible_anomaly, direction low; `value > upper`: possible_anomaly,
  direction high. Bounds are inclusive ordinary values; a constant reference with
  value equal to both bounds is ordinary.
- Enough reference and value inside bounds: ordinary; no anomaly review required.
- Missing/insufficient reference, invalid input or no valid prediction: not_evaluated,
  direction null, with an explicit reason. A known text length may be retained even
  when no class-comparable reference exists; it does not create a fabricated score.
- Every attempt has a metric record for each metric, including null values and
  not_evaluated states. A high score can be valid; a low score can also trigger
  the separate low-confidence rule. Numerical rarity never means confirmed error.

The explicit handoff policy sends possible_anomaly or insufficient_reference to
triage_review, preserving the category/value. It requests investigation, not
rejection or correction of the ticket. All results still require human confirmation.
Alert workload and valid-but-flagged cases must be reported, not hidden by changing
bounds after seeing the final test.

# Persistence, review and filters

Use a local SQLite database under ignored `data/runtime/`; model artifacts belong
under ignored `data/models/`. Store valid original text locally so cases remain
reviewable after reload, without separate customer identity fields. For oversized
invalid input retain lengths/hash and reason, not an unlimited text payload. Do not
publish the database or raw text in default exports. No remote inference call.

Persist case input; immutable runs with all versioned decisions; one metric
evaluation per run/metric; append-only review events. Save a run and its two
metric records atomically. Store metric name/value, group/reference identifiers,
n, lower/upper bounds, method/tail parameters, direction, reason and rule version.
Use bound SQL parameters and short transactions; UI selection state is not a
substitute for database history. [SQLite reference](https://docs.python.org/3.12/library/sqlite3.html).

Case decisions are pending, accepted, corrected or deferred. Store a corrected
category separately from the original prediction. For anomaly assessments use
pending, confirmed_valid, confirmed_issue or deferred; ordinary metrics start
not_required. Changes of judgment append an explicit revision event.
For unsupported context, accept/defer the manual handoff without forcing an IT
category; clarifying/changing context creates a new explicit run. A corrected IT
category is only meaningful within the IT task.
Insufficient-reference assessments remain visible and can be deferred/annotated;
human judgment does not retroactively establish a statistical reference.
Record reviewer label/type, UTC time, reason and the targeted run/metric. Revisions
append events and expose a latest-state projection; do not overwrite original values.

The local workbench has no authenticated business-role enforcement. Operator labels
are self-reported; automated fixtures must identify as automated_test. Do not infer
verified human review from an agent clicking the UI or from a supplied label.
Reviews never retrain a model, update references, rewrite final-test labels or
change benchmark membership automatically.

Filters combine with AND: evaluation status, high/low direction, reason and latest
review state; also expose category, metric and version. Show not_evaluated as distinct
from ordinary. A run with two metric flags appears as two assessments; case/run
counts deduplicate identifiers and do not add filter row counts as ticket totals.

# Success measures and I01/V01 acceptance

| Layer | Required evidence |
| --- | --- |
| Utility | New in-context text or a development example yields a category suggestion or explicit human handoff, with reason and durable history |
| Software | All listed input, readiness, zero-feature, timeout, invalid-output and persistence-failure fixtures satisfy the contract; no late/duplicate success |
| Persistence | Reload preserves runs; high/low/ordinary/insufficient-reference fixtures and combined filters return the expected records; reviews preserve original values |
| Model | Majority/simple-text baseline, macro F1 across eight classes, per-class support/errors and confusion; precise numeric criteria frozen in V00 |
| Selection/workload | Error among high-score standard suggestions alongside coverage, review-needed volume, policy-specialist volume and technical failures; all remain human-confirmed |
| Anomalies | Reference support, high/low/not-evaluated coverage, review workload and manually adjudicated valid/issue counts; no false-alert accuracy claim without that adjudication |
| Performance | End-to-end local latency distribution, failures and attempted/stored counts; no claim that timeout policy is achieved latency |
| Business | No measured savings or consumer-domain accuracy claim; A01 capacity figures remain hypotheses for a later operational pilot |

Review of model errors, anomaly validity and live input availability needs actual
adjudication. Automated fixture reviews prove software behavior only. There is no
claim of quality, integration or production readiness until the required work exists.

# V00 handoff

V00 is now prepared in the [evaluation protocol](evaluation-protocol.md), with no
classifier fitting. The following constraints continue to govern I01/V01.
Freeze IT membership/group/near-duplicate rules, entry-input limitations, candidate
budget, error costs, model/gating criteria, tail-selection procedure and evaluation
denominators. Keep live/demo examples in development; do not expose held-out text
or labels in the UI before the evaluation protocol permits it. Pin and check exact
dependency versions without fitting a model in V00. I01 implements this contract;
V01 reports the chosen model and failure/error behavior on the reserved evaluation.
