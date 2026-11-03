---
type: Implementation Record
title: Management views, reviewer journey and operational exports
description: M01–M05 presentation scope, aggregate-only entry, capacity inputs and CSV contract.
status: draft
sources:
  - id: review
    resource: ../docs/pre-submission-review.md
  - id: diagnosis
    resource: ../data/diagnosis.json
  - id: benchmark
    resource: ../data/final-evaluation.json
  - id: interface
    resource: ../solution/management_ui.py
  - id: projections
    resource: ../solution/management.py
---

# Implemented scope

The user authorized points 1–4 of R02, including M01–M05, and requested point 5
remain visible as future ideas outside this delivery. This is scope prioritization;
future integrations are not presented as implemented or failed experiments.

- M01: one-page executive entry, human/AI attribution and guided demo.
- M02: aggregate diagnosis, actions/owners/pilot indicators and IT benchmark view.
- M03: `run.sh --overview`, platform/objective-specific instructions and corrected
  consumed-test setup wording. First environment install still needs network;
  overview does not invoke acquisition, training, inference or a runtime DB.
- M04: explicit filtered CSV exports in the review tab.
- M05: editable capacity inputs through the existing `diagnose_support.scenario`
  formula, mandatory review share 1, negative/zero-volume outcomes retained.

# Boundaries and entry points

`solution/overview_app.py` loads only three public JSON aggregates through
`management.load_reports`; it does not load a model or individual final-test cases.
`solution/app.py` adds these views to the existing triage/review interface. Missing
local models/DB must not prevent aggregate-only review. Customer diagnosis, IT
benchmark and local activity are distinct populations; no cross-domain performance
or operational-savings claim is introduced.

The simulator submits editable values explicitly, shows confirmed assumptions and
downloads them with its output. It reuses analysis code without changing saved
diagnosis/configuration. Currency is a hypothetical valuation of capacity, not
realized cash savings or financial ROI. No future integration is executed.

# Export v1

`management.operational_export` consumes the already filtered metric rows and
projects repository results/review events without mutating the database:

- `cases`: one row per selected run ID, not necessarily a unique case; original
  category/queue/model plus latest case review state, correction and reviewer type.
- `metrics`: exactly the filtered assessments with their latest metric review state.
- `reviews`: all historical events for the selected runs, not only the metric
  selected by the filter; stable event/run/case IDs and timestamp retained.

Headers are defined by `EXPORT_FIELDS`. Original text, reviewer names and free-text
review reasons are excluded. UTF-8 BOM supports spreadsheet import; formula-like
string cells get a leading apostrophe. Download widgets use `on_click="ignore"`;
exporting does not submit another inference or review.

# Evaluation

The frozen engine, models, policy, references and final outputs stay unchanged.
New software/UI tests cover projection/filter/privacy/count boundaries, independent
aggregate entry and capacity interaction. They do not validate a new classifier.
The V01 test remains consumed. See the M01–M05 delivery evidence referenced from
the execution plan for actual test/setup/browser results.

# M06 audience/legibility refinement

After direct user feedback, both entry points default to a Company presentation:
operational diagnosis/actions and capacity only. Instructor selection adds a guide,
method/evidence/benchmark details and future scope; the full app also enables the
existing triage/review demo. Company mode returns before creating a repository or
loading model metadata. The selector is presentation, not role authentication.
Group and queue charts use horizontal labels without ellipsis/rotation, with queue
counts duplicated in a table. No classifier, policy or reference changes are made.

The start-here entry and Instructor guide now explicitly explain the CodeTour
launcher/11 steps and Markdown alternative. The guide distinguishes retrospective
classification improvement from still-unmeasured operational benefit and partial
answers to temporal/causal diagnosis; it does not assign a recruitment grade.
