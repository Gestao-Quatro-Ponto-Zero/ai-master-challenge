---
type: Evaluation Protocol
title: Frozen IT evaluation protocol before model fitting
description: V00 split ownership, candidate budget, selection, error proxies and reserved-test boundaries.
status: draft
sources:
  - id: machine-protocol
    resource: ../data/evaluation-protocol.json
  - id: membership-manifest
    resource: ../data/evaluation-manifest.json
  - id: runtime-contract
    resource: solution-scope.md
  - id: exact-set-join
    resource: https://www.vldb.org/pvldb/vol9/p636-mann.pdf
  - id: validation
    resource: https://scikit-learn.org/stable/modules/cross_validation.html
---

# Authority and exposure

The [JSON protocol](../data/evaluation-protocol.json) owns numerical settings,
candidate definitions and selection rules. This document owns their interpretation
and execution order. The [manifest](../data/evaluation-manifest.json) owns computed
membership counts and hashes. S01 owns runtime behavior; D02 owns dataset roles.
These are agent-defined offline assumptions under the instruction to advance,
not human-approved business costs or measured quality. Protocol version: `it-triage-v1`.
Freeze before fitting. Any later change must disclose timing and affected results.

V00 prepared splits and dependencies; it fitted **zero classifiers**. I01 may fit
the four declared models on train and select using validation. V01 evaluates the
frozen selected artifacts once on final_test. Never fit vocabulary on validation
or test; use a separate scikit-learn Pipeline for each text estimator. Do not refit
the selected model using validation: scores/reference would then change.

The full public source was already audited. Grouping reads all texts without using
labels for similarity; allocation uses labels for class balance. Aggregate support
is inspected. Reserved test means no prediction, performance inspection, tuning or
UI examples before V01, not a claim that source text was physically unread or secret.
Use only train examples in development/UI. Validation labels are for selection,
never inference features. Customer labels are never used for IT performance.

# Whole-group separation

`prepare_evaluation.py` checks the frozen IT CSV hash and NFKC/casefold/space
normalization. Token-set Jaccard >=17/20 defines similar pairs. Identical token sets
are compressed, then an exact prefix/length-filtered join verifies remaining pairs
using integer arithmetic. This follows the filtering principle in
[Mann et al., section 2](https://www.vldb.org/pvldb/vol9/p636-mann.pdf), not approximate LSH.
Global token frequency orders this label-blind join only; it is not a model vocabulary.
Connected components stay whole, including transitive links and mixed-label groups.
Grouping ignores token order/repetition; this conservative rule does not establish
semantic, customer or entity independence. Entity identifiers are unavailable.

Components with empty/no-token/oversized input or conflicting labels on identical
normalized text are quarantined; source rows/labels remain intact. Similar but
different texts with different labels are retained together, not declared mistakes.
No quarantine was needed in this source version. Seeded deterministic group order
and greedy class balance target 70/15/15; whole groups take priority over exact ratios.

The local membership CSV identifies each 1-based source row, case, group, partition
and normalized-text hash. It stays ignored under `data/processed/`. Its public hash
and generating source are enough to reproduce membership; no raw text is published.
All eight classes appear in each partition. The clean reproduction and membership
checks are recorded in [evaluation-checks.json](../docs/review-evidence/evaluation-checks.json).
Unit tests compare the join against exhaustive search, including exact boundaries.

Document is already processed; no provenance establishes entry-time availability.
A train-only literal outcome-word probe is recorded in the checks. Such terms may
describe requests or outcomes; their counts cannot certify chronology or fix leakage.
The benchmark remains retrospective. No production entry-time claim is allowed.

# Selection and costs

Train majority, TF-IDF/MultinomialNB and two TF-IDF/logistic candidates (C=.5 and2).
The budget is four fits, no hyperparameter search beyond these declarations. A
logistic candidate must satisfy all three validation macro-F1 criteria in JSON.
Choose highest eligible macro F1, exact ties prefer C=.5. No eligible model means
no quality-qualified model and explicit review-needed fallback, not relaxed targets.

For the winner, evaluate 42 declared score-threshold/reference-tail pairs on
validation. Build reference distributions from validation predictions, grouped by
context/model/predicted category/normalization/metric, never true category. Compare
unrounded values against inclusive empirical linear quantiles. Minimum support100;
insufficient support is not_evaluated and requires triage, not an ordinary value.
Anomaly share counts distinct scored cases with at least one possible anomaly,
not the number of metric rows. Report not_evaluated separately. A high score is
not calibrated correctness; a high/low deviation is not adjudicated invalidity.

Compute every standard/specialist/triage mask through the S01 core rules, including
context, readiness, feature coverage, output validity, references and anomalies.
Standard coverage is standard cases / all scored validation cases. Standard accuracy
uses only those standard cases; the Wilson lower bound is a selection constraint,
not a guarantee after trying 42 choices. Final-test assessment is still required.
All outcomes require human confirmation, including standard/specialist suggestions.

Choose feasible pairs by assumed mean queue review + wrong-standard-category cost.
The dimensionless weights are explicit illustrative proxies, not measured minutes,
money, staffing or perfect human adjudication. Costs distinguish a wrong standard
suggestion whose true category needs a specialist. True labels are available for
offline costing only. Report the predefined cost sensitivity on validation without
changing the primary choice. Tie rules and feasibility thresholds are in JSON and
pure arithmetic helpers; no feasible pair means all predictions need triage review.

Reference calibration and gate selection reuse validation: validation outcomes are
development results, not independent estimates. After selection, freeze model,
preprocessing, class order, threshold, references and software hashes. The same
artifacts must drive evaluation and UI. Do not derive reference bounds from test.

# Final evaluation and implementation handoff

I01 implements S01 persistence, filters, append-only reviews, failures, timeout and
UI, plus frozen-protocol training/selection. V01 reports baseline and selected-model
performance on the same reserved membership, all eight classes including zeros,
coverage alongside errors, queue workload, metric directions/support, attempted vs
stored requests, latency and technical failures. A failed gate or quality target
must remain visible; there is no automatic deployment or clean retest after tuning.
If final-test results influence a new choice, version it as exploratory and disclose
the contaminated reservation. Software fixtures do not establish AI quality or
actual human adjudication. No business savings or cross-domain accuracy follows.

See [tested environment/setup](../docs/evaluation-protocol.md),
[environment evidence](../docs/review-evidence/evaluation-environment.json) and
[version receipt](../docs/review-evidence/evaluation-current.json). Hash matching
identifies inputs; it does not prove model quality or business acceptance.
