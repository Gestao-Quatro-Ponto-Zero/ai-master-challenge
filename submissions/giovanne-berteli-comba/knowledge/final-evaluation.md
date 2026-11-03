---
type: Evaluation Record
title: Frozen-version final IT benchmark and runtime validation
description: V01 final-test exposure, acceptance, assisted errors/workload, runtime sample and reproducibility limits.
status: draft
sources:
  - id: protocol
    resource: ../data/evaluation-protocol.json
  - id: execution-plan
    resource: ../data/final-evaluation-plan.json
  - id: pre-exposure-freeze
    resource: ../data/final-evaluation-freeze.json
  - id: results
    resource: ../data/final-evaluation.json
  - id: recorded-output-audit
    resource: ../docs/review-evidence/final-evaluation-checks.json
---

# Authority and exposure state

V01 is complete for `it-triage-final-v1`. The [result JSON](../data/final-evaluation.json)
owns computed results. V00's original numerical protocol is unchanged; the V01
plan owns execution populations, and the pre-exposure freeze owns exact input,
model/policy/reference/driver/test hashes and 64 runtime case IDs. The source commit
before this work was `cb01264`. The 72 software tests passed before freeze and
prediction; only synthetic fixtures were used to develop/test the evaluator.

The final_test reservation has now been consumed: 7,175 IT cases were predicted.
Never describe this membership as an unseen test for a later model/threshold choice.
Any later change informed by these results needs an explicitly exploratory version
or genuinely new evaluation data. App/demo examples remain train-only. Do not
rebuild model/gate/reference after seeing the final results. No classifier was fitted
or retuned in V01; no app/inference source or existing model artifact was changed.

The driver provides `freeze` then `evaluate`. Exclusive attempt creation prevents
silent reuse of an interrupted exposure. A completed identical command validates
and returns the saved result without predicting again; changed inputs/results fail.
Do not delete attempts or overwrite the freeze to claim another clean evaluation.

# Populations and measured behavior

All 7,175 cases were scored by the selected logistic C=2 and the two frozen baselines,
not the unselected logistic candidate. Features were transformed in batch without
fit. All model classes are validated in the fixed eight-label order. Macro F1 and
per-class/confusion metrics use all eight classes, including zero support/errors
where appropriate. Classifier metrics include mathematical predictions on every
text; usable suggestion coverage/errors use the separate production core policy.

The selected score vectors then passed through the production TriageService/core
and repository via an explicit precomputed-score adapter: 7,175 attempted/stored
runs, 14,350 metric records, no failed outcomes. This checks decisions/persistence,
not cold worker startup or timeout performance. Truth labels are evaluation inputs
only, absent from model features, routing and saved inference inputs.

The frozen 64-case sample used the actual subprocess and a separate SQLite DB,
sequentially with no warmups/retries/replacements. External timing included process
startup/load/transform/predict/coordinator and commit, excluding UI/human review.
All 64 were stored, no failed outcomes, 128 metrics and zero decision discrepancies
against batch execution. p50≈ 587.20 ms, p95≈ 600.84 ms, max≈ 618.66 ms on this host.
This small deterministic sample is not a production SLA, throughput test or proof
of representative latency under contention. Individual external-clock observations
were not persisted; only their driver-computed aggregates are available. SQLite
elapsed_ms uses a different pre-persistence clock and cannot reconstruct them.

Nine separately labeled synthetic automated failure fixtures all behaved as
specified. Eight attempts were saved; the forced persistence failure was visibly
unsaved with no partial run/metric. These fixture failures are not observed runtime
failure rates on real held-out cases. Existing software/AppTest fixtures additionally
cover high/low/equal/constant/insufficient reference, filters and review revisions.
No fixture or agent interaction is human anomaly adjudication.

# Results and limits

Macro F1: selected 0.844612, text baseline 0.646094, majority 0.055387. Selected overall
accuracy 0.849199. All six predeclared numerical quality checks passed, as did the
execution/persistence/parity/fault checks. This is offline target attainment under
agent-defined assumptions, not human business approval or production readiness.

Standard suggestions: 1,951/7,175 (27.19%), with 1,884 matching supplied labels and 67
errors (96.57% agreement; Wilson 95% lower bound 95.66%). Specialist 1,977; triage 3,247.
All destinations require confirmation. Critically, 50 of the 67 wrong standard
suggestions have true labels in the specialist-policy classes: Access 16,
Administrative rights 12, HR Support 15, Purchase 7. The policy acts on predicted
category and cannot protect every true specialist case. Preserve this limitation;
do not weaken mandatory confirmation or silently retune against these errors.

Administrative rights has the weakest class F1≈ 0.762105 and recall≈ 0.685606,
support 264. Hardware attracts many confusions: 120 HR Support, 101 Miscellaneous,
80 Access and 71 Administrative-rights cases are labeled Hardware by the classifier.
These are label-based benchmark disagreements, not independently adjudicated
business errors or causes. The public report exports aggregate counts, no raw text.

There are 338 distinct possibly anomalous cases, 345 flagged metric assessments
(193 score, 152 length); 7 cases have both. No insufficient/not-evaluated metric
occurred in this test. The numerical comparison is not a confirmed-issue or false-
alert rate. The fixed dimensionless mean review/error proxy is≈ 0.957449, not minutes,
money, measured staffing savings or a customer-operation transfer estimate.

Whole-group splitting only addresses the declared token similarity. Public processed
text provenance, prospective entry-time availability, entity independence, within-
group dependence and source-label semantics remain limitations. The Wilson bound
is the frozen operational criterion; its nominal independent-binomial interpretation
is limited by the grouped/template data. No cross-domain accuracy or production
performance follows from this retrospective benchmark.

# Verification and handoff

`scripts/check_final_evaluation.py` verifies frozen/local hashes, replays all 7,175
decisions from cached scores without model load/prediction, reconciles confusion
metrics for all three models, assisted denominators and acceptance. It audits the
recorded execution; it does not perform another held-out inference or timing run.
The result/freeze/attempt and ignored prediction/SQLite outputs are registered in
the [current evaluation receipt](../docs/review-evidence/final-evaluation-current.json).
Hashes identify a version, not truth or business acceptance.

Public artifacts are plan/freeze/aggregate result, audit and tests. Original inputs,
score vectors and evaluation databases remain ignored under data/raw or
data/processed; no final-test text enters the app's default DB. Read-only aggregate
reports can be inspected without loading serialized models. The evaluator is not
called by the one-command app launcher.

E01 has now packaged the stable narrative/evidence/CodeTour; see the
[reviewer guide](../docs/review-guide.md). Next: P01 final candidate
details/setup/scope/submission review. A reproduction on another environment is a
new recorded reproduction with disclosed exposure, not permission to replace this
freeze or choose a better candidate from its final errors. Exact artifact hashes
and timings need not reproduce across environments; retain this first result.
