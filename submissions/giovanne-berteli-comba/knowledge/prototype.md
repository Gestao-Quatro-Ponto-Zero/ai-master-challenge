---
type: Implementation Record
title: Local IT assisted triage prototype
description: I01 components, owned artifacts, review persistence, setup and validation-only selection results.
status: draft
sources:
  - id: contract
    resource: solution-scope.md
  - id: frozen-evaluation
    resource: evaluation-protocol.md
  - id: development-results
    resource: ../data/triage-development.json
  - id: prototype-setup
    resource: ../docs/prototype.md
  - id: persistence
    resource: https://scikit-learn.org/stable/model_persistence.html
  - id: app-tests
    resource: https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest
---

# Implementation and authority

I01 implements the S01 local assisted flow, not external routing or resolution.
S01 still owns expected behavior, V00 owns numeric choices/selection, and
`data/triage-development.json` owns the computed TRAIN/VALIDATION development
results. This record owns component/setup interpretation. No final-test prediction
or performance was computed. V01 remains pending; there is no production or
cross-domain quality claim, human-adjudicated anomaly accuracy, or measured savings.

# Components

- `solution/triage/core.py`: normalization, empirical quantiles, two metric
  assessments, score validation and shared queue/decision precedence. It accepts no
  true labels. Selection and online execution use these same decisions.
- `solution/train_triage.py`: checks the frozen data hashes, selects train/validation
  rows only, performs exactly four candidate fits with one numerical thread, reports
  all declared candidates and 42 gate pairs. No validation refit or target relaxation.
  A checked completed attempt is reused without fitting; exclusive creation prevents an accidental second training run
  over the existing bundle. A failed run must be inspected, not automatically retried.
- `solution/triage/artifacts.py`: fixed owned directory, expected filenames,
  dependency/file hashes, exact installed lock, class order, selected parameters,
  comparable references and explicit manual fallback validation before loading.
- `solution/predict_worker.py`: one JSON stdin/stdout request; imports/deserializes
  only the hash-checked selected local pickle, transforms text, checks feature count
  through the coordinator and returns scores/versions. It has no database access.
- `solution/triage/runtime.py`: input/context guards, unique request identity,
  subprocess timeout (5s including startup/load/transform/predict), validated decision
  and sole call to the durable writer. `subprocess.run` terminates/waits on timeout;
  no late callback can write. The production default is 5s; a shorter injected budget
  exercises a real slow process in a test. BLAS/OpenMP threads are limited to one.
- `solution/triage/repository.py`: short parameterized SQLite transactions, atomic
  case/run/two-metric writes, idempotent delivery, conflicting request detection,
  append-only reviews and AND-combined metric/latest-state filters. Latest state is
  selected by monotonic event sequence, not timestamp ordering. Connections close
  after each transaction. Original predictions/values are never rewritten by review.
- `solution/app.py`, `solution/triage_cli.py`: local entry points sharing the service.
  Streamlit form submission is explicit; rerenders do not infer or review. The UI
  uses only three training examples and provides original result/history, review
  forms, status/direction/reason/state/category/metric/model filters and distinct
  case/run/metric counts. Operators and automated fixtures identify their type;
  self-declared labels do not establish authenticated or verified human approval.

Database: ignored `data/runtime/triage.sqlite3`. Bundle: ignored
`data/models/it-triage-v1/`. This includes four estimators, policy, reference,
train examples, validation score vectors, bundle and exclusive attempt record.
`normalization_sha256` hashes the normalization version identifier; the bundle
separately binds the core implementation bytes.
The public aggregate report records their hashes, no individual input/validation
predictions. Only locally generated pickles are supported. Hashes detect accidental
changes against a local manifest, not an attacker who can rewrite both manifest
and files. There is no artifact upload path or remote inference service.

# Development result and frozen handoff

V00 selected `logistic_c20` by validation macro F1, approximately 0.852554 versus
0.652147 for the text baseline and 0.055396 for majority. All four fits completed
without captured warnings. The selected score threshold is 0.80, reference tail 0.01,
and minimum comparable reference support 100. Every result still requires confirmation.
On the 7,177 validation cases: 2,053 standard, 1,935 specialist and 3,189 triage;
1,977/2,053 standard suggestions matched labels (76 errors), with Wilson 95% lower
bound 0.953911. There were 291 distinct cases with a possible anomaly and one with
not_evaluated metrics (zero known features). These are not final-test estimates.

The same validation population calibrates references and selects model/gate: its
metrics are optimistic development evidence, not independent generalization proof.
No human has adjudicated the flagged values. The assumed cost 0.946092 and doubled
specialist-error sensitivity 0.983015 are dimensionless proxies, not time or money.

The current bundle binds model/preprocessing/classes, policy, references, frozen
protocol/split/lock and inference/training source hashes. UI/CLI use that bundle;
changes invalidate readiness rather than silently serving stale results. A V01
driver must freeze its own software receipt before predicting reserved final_test.
Do not modify source bindings to conceal a changed implementation, re-fit after
validation, tune on final-test errors, or refresh receipts without rerunning checks.

# Verification and limits

[Software tests](../docs/review-evidence/triage-tests.txt) include deterministic
automated fixtures for high/low/equal/constant/insufficient reference, routing,
invalid input/output, unavailable/stale artifacts, no known features, real process
timeout, duplicate/concurrent delivery, atomic rollback, parameterized filters,
review revisions and UI rerenders. Fixture reviews are typed automated_test.
Streamlit AppTest simulates UI widgets; it is not visual browser inspection.
All 64 tests passed in the locked environment with the owned trained bundle,
without skipped cases or additional fits.

[Functional smoke](../docs/review-evidence/triage-smoke.json) uses a temporary DB,
three real TRAIN examples plus synthetic invalid/unknown requests. Seven unique
requests plus one duplicate produce seven runs and 14 metrics. A separate forced
write-failure fixture produces no saved run and a visible unsaved failure. Its tiny
latency sample includes DB commit and is not a throughput/SLA benchmark. Stored
`elapsed_ms` measures coordinator work before the final persistence call; use an
external driver clock for end-to-end performance, as this smoke does.

[Server check](../docs/review-evidence/triage-server.json) verifies actual HTTP health
on loopback and termination afterward. Default Streamlit config binds 127.0.0.1 and
disables usage telemetry; no public deployment occurred. The local workbench has
no authenticated enterprise role system, migrations for arbitrary older schemas,
concurrent-model serving, remote API or validated production data-retention policy.
These are outside the selected local prototype, not demonstrated capabilities.


# One-command setup correction

Use `bash run.sh` inside the submission, or invoke its absolute path from any
other working directory. It resolves its own directory, locks preparation, reuses
valid environments/artifacts and starts Streamlit. `--prepare-only` exits after
preparation. The supported bootstrap is Linux x86_64/glibc with Bash/curl-or-wget,
tar/sha256sum/flock and initial network/disk access. No system Python, ensurepip,
python3-venv, pip or sudo is required: pinned checksum-verified uv 0.9.7 supplies
managed Python 3.12.3 when needed. All runtime/cache/backups remain under ignored
`.runtime/`. Existing incompatible venvs are preserved there, not deleted.

`solution/setup_triage.py` validates existing frozen input/member hashes before
training. `solution/triage/setup_state.py` reuses completed verified attempts and
preserves/diagnoses interrupted, orphaned or stale attempts without refitting.
The direct training command now has this same friendly idempotence behavior.
No CLI force-reset is provided. Concurrent setup is prevented with an OS file lock.

Changing the training entry point's guard changed its source hash, not the fitting
calculation: the original training source/bundle/report were preserved under local
model provenance. The compatibility evidence checks unchanged calculation AST and
estimator/reference/policy bytes; public `input_sha256` still describes the actual
original fitting inputs, `serving_input_sha256` describes the current runtime binding.
No original classifier was refitted. An isolated clean-install reproduction did
perform its own four fixed fits, not a new selection experiment or final-test use.
See the [setup reproduction](../docs/review-evidence/setup-reproduction.json) and
[explicit binding revision](../docs/review-evidence/setup-binding.json).
