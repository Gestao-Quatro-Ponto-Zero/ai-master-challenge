# Execution plan

Only mark a task complete after its acceptance criteria have evidence. Time
estimates and recommendations are not completed results. The brief suggests
4–6 hours for the challenge; keep preparation proportional and record actual
effort when known. Do not invent time spent or treat 8% as a fixed rule.

| ID | Task | Acceptance criteria | Evidence / destination |
| --- | --- | --- | --- |
| B01 | Shared foundation | Instructions, status, minimal OKF context, process policy, and checklist exist; document checks pass | This submission and `activity-log.md` |
| B02 | Adversarial foundation review | Strengths, failure scenarios, executed probes, limits, and prioritized adjustments recorded | [Review](../docs/architecture-review.md) and [baseline evidence](../docs/review-evidence/foundation-baseline.json) |
| B03 | Foundation controls | Challenge-conflict mutation rejected, changed dependencies invalidate evidence, explicit-path resumption checked | [Controls and limits](../docs/foundation-controls.md), [tests](../docs/review-evidence/foundation-tests.txt) and [receipt](../docs/review-evidence/foundation-current.json) |
| D01 | Data acquisition and audit | Sources, acquisition steps, versions and hashes recorded; schemas, units, actual sizes, missingness, duplicates and metric coverage inspected for both datasets (F05/F07) | [Manifest](../data/manifest.json), [audit](../docs/data-audit.md), [output](../data/audit.json), [reproduction](../data/README.md) |
| D02 | Dataset usage decision | Explain each dataset's role, limits, any valid mapping, and evaluation boundaries | [Authoritative decision and metric contract](../knowledge/dataset-usage.md) |
| R01 | Focused PR review | Declare sample and effort cap before browsing; identify repeated approaches and evidence gaps with links within that cap (F06) | [Research](../docs/pr-review.md) and [selection/source snapshot](../docs/review-evidence/pr-review-snapshot.json); no private baseline inspected |
| A01 | Operational diagnosis | Reproducible bottleneck/satisfaction findings; explicit populations, missingness, time units and active-effort assumptions; distinguish simulated from measured savings (F07) | [Diagnosis](../docs/operational-diagnosis.md), [computed metrics](../data/diagnosis.json), [all segments](../data/diagnosis-segments.csv) and [assumptions](../data/diagnosis-assumptions.json) |
| S01 | Automation and scope | Choose one useful automation; define handoff and failure rules, anomaly records/filters, review states, success measures and an explicit flow (F03) | [Authoritative contract](../knowledge/solution-scope.md) and [reviewer proposal/flow](../docs/automation-proposal.md) |
| V00 | Evaluation protocol before implementation | Baseline, entry-time inputs, group/duplicate separation, development/validation/test membership and selection criteria recorded; choose thresholds on validation, not final test (F02) | [Frozen protocol](../knowledge/evaluation-protocol.md), [manifest](../data/evaluation-manifest.json), [setup/checks](../docs/evaluation-protocol.md) and [receipt](../docs/review-evidence/evaluation-current.json) |
| I01 | Prototype | Demonstrate the selected automation using real data under V00; persist possible high/low anomalies and support reason/direction/review-state filters (F03); document setup and limitations | [Prototype/setup](../docs/prototype.md), [implementation](../knowledge/prototype.md), [development results](../data/triage-development.json) and [receipt](../docs/review-evidence/triage-current.json) |
| V01 | Validation | Meaningful software tests and separate AI evaluation; report failures and limitations | [Final report](../docs/final-evaluation.md), [frozen inputs](../data/final-evaluation-freeze.json), [aggregate results](../data/final-evaluation.json), [audit](../docs/review-evidence/final-evaluation-checks.json) and [receipt](../docs/review-evidence/final-evaluation-current.json) |
| E01 | Evidence and communication | Reviewer narrative, conversation coverage, decision history and useful CodeTour checked | [Reviewer map](../docs/review-guide.md), [CodeTour/Markdown route](../docs/code-tour.md), [capture coverage](../docs/conversation-coverage.md), [checks](../docs/review-evidence/reviewer-evidence-checks.json) and [receipt](../docs/review-evidence/reviewer-evidence-current.json) |
| R02 | Pre-submission investigation | Assess reviewer comprehension/human-AI attribution, reproduction, business decisions, useful immediate additions and future integrations; distinguish verified results from proposed features | [Five-principle review](../docs/pre-submission-review.md), [checks](../docs/review-evidence/pre-submission-review-checks.json) and [prioritized backlog](backlog.md) |
| M01 | Executive entry and attribution | One-page reviewer entry, human/AI evidence and guided demo | [Start here](../docs/start-here.md), [demo](../docs/demo-guide.md) |
| M02 | Management/results view | Distinct customer/IT/local populations, actions/owners/indicators and source-linked aggregates | [Implementation](../knowledge/management.md), [delivery checks](../docs/review-evidence/management-delivery-checks.json) |
| M03 | Reproduction clarity | Aggregate-only launcher, explicit prerequisites/objectives and consumed-test status; historical reports identified | [Setup](../docs/prototype.md), [delivery checks](../docs/review-evidence/management-delivery-checks.json) |
| M04 | Operational export | Filter reconciliation, case/run/metric/event counts, versioned schema and no original/free-text fields | [CSV contract](../knowledge/management.md), [tests](../tests/test_management.py) |
| M05 | Capacity simulator | Existing formula, editable assumptions, review/rework/fixed effort and negative/zero-volume scenarios | [Implementation](../solution/management_ui.py), [tests](../tests/test_management.py) |
| M06 | Audience-specific review and legibility | Company results-only view, Instructor guide/detail/demo, horizontal complete labels, CodeTour in entry and evidence-based quality interpretation | [Implementation](../knowledge/management.md), [audience checks](../docs/review-evidence/audience-delivery-checks.json), [entry](../docs/start-here.md) |
| P01 | Submission | Candidate details completed, reproducible setup, template satisfied, allowed diff scope, PR instructions followed | Final review checklist and eventual PR |

- [x] B01 — Prepare and check the foundation. Evidence: [document checks](activity-log.md).
- [x] B02 — Review the foundation adversarially. Evidence: [review and open adjustments](../docs/architecture-review.md).
- [x] B03 — Implement and validate foundation controls. Evidence: [controls](../docs/foundation-controls.md).
- [x] D01 — Audit both datasets. Evidence: [audit and limitations](../docs/data-audit.md).
- [x] D02 — Decide complementary dataset usage. Evidence: [roles, limits and evaluation boundaries](../knowledge/dataset-usage.md).
- [x] R01 — Review a bounded sample of Challenge 002 PRs. Evidence: [three confirmed PRs and implications](../docs/pr-review.md).
- [x] A01 — Complete the operational diagnosis. Evidence: [findings, scenarios and limits](../docs/operational-diagnosis.md).
- [x] S01 — Define one automation and its human intervention rules. Evidence: [scope, flow and acceptance](../knowledge/solution-scope.md).
- [x] V00 — Record the evaluation protocol before prototype implementation. Evidence: [grouped splits, bounded selection and tested environment](../docs/evaluation-protocol.md); zero classifier fits.
- [x] I01 — Build the functional prototype. Evidence: [local triage/review, frozen-protocol selection, software and smoke checks](../docs/prototype.md); final test was reserved at that development stage (subsequently consumed in V01).
- [x] V01 — Run and document software tests and AI evaluation. Evidence: [7,175 frozen-test cases, 72 software tests, actual 64-case runtime and separate faults](../docs/final-evaluation.md); no fit/retuning, exposure consumed.
- [x] E01 — Complete evidence, narrative, and CodeTour. Evidence: [template narrative, 11 passive anchors and capture inventory with limits](../docs/review-guide.md); no source/model/test-exposure changes.
- [x] R02 — Investigate the five user-defined principles before P01. Evidence: [findings, business actions, immediate priorities and future dependencies](../docs/pre-submission-review.md); historical proposals subsequently delivered in M01–M05.
- [x] M01 — Deliver executive entry, human/AI attribution and guided demonstration. Evidence: [one-page entry](../docs/start-here.md) and [demo](../docs/demo-guide.md).
- [x] M02 — Deliver source-linked management and benchmark views. Evidence: [aggregate/UI checks](../docs/review-evidence/management-delivery-checks.json).
- [x] M03 — Separate consultation and reproduction; correct platform/exposure wording. Evidence: [setup](../docs/prototype.md) and [no-raw/model launch](../docs/review-evidence/management-delivery-checks.json).
- [x] M04 — Export filtered cases, assessments and review history. Evidence: [schema/filter tests](../tests/test_management.py) and [demo instructions](../docs/demo-guide.md).
- [x] M05 — Deliver editable capacity simulation and retained negative results. Evidence: [UI/zero-volume tests](../tests/test_management.py).
- [x] M06 — Respond to direct UI/reviewer feedback: separate audiences, readable group labels and explicit CodeTour/quality guidance. Evidence: [81 tests, browser screenshots and tour replay](../docs/review-evidence/audience-delivery-checks.json); no new model-quality evaluation.
- [ ] P01 — Prepare the final submission and PR.

Coordination source for F01–F07:
[official review table](../docs/architecture-review.md#lista-oficial-para-validação).
B02 records completion of the review, not implementation of its adjustments.
Keep review decisions and adjustment state in that table only. V00 must precede
I01; V01 evaluates the implemented version. Process logs are recruitment evidence,
excluded from normal execution context; keep current decisions in operational owners.

S01 selects the stack and operational contract, not a trained model. V00 freezes
candidate/split/selection/acceptance procedures and exact tested environment before
I01; I01 computes model and gate/reference parameters from development/validation
only. V01 evaluates the selected frozen version on reserved test data.

The planned data sequence is D01 followed by D02. PR review may inform differentiation but cannot
substitute for understanding the datasets. See [backlog](backlog.md) for optional
ideas and [validation strategy](../docs/validation-strategy.md) for planned checks.

R01 scope declared before browsing: at most three publicly accessible Challenge
002 submission PRs, at most 20 minutes of wall time, whichever limit is reached
first. Select by latest update at the search timestamp, excluding this candidate;
record the query, timestamp, returned ordering, eligibility and inaccessible links.
Inspect approach and supporting evidence only; do not execute other submissions
or copy their implementation. Record gaps as unknown rather than infer failure.
Stop at the cap even if fewer than three PRs are usable, then proceed to A01.

R01 executed on 2026-11-02: PRs #211, #209 and #205, each confirmed as Challenge
002 in its title and README. Source-inspection window: 18:26:42–18:30:01 UTC,
199 seconds. Stopped after three; no fourth PR inspected. Administrative writing
and local validation after that window are recorded separately from source research.


I01 setup correction after user testing: `bash run.sh` supplies the local runtime
without system ensurepip/python3-venv and reuses completed verified training.
[Clean install/offline repeat/server evidence](../docs/review-evidence/setup-reproduction.json)
and [explicit provenance compatibility check](../docs/review-evidence/setup-binding.json)
cover this correction; no original-workspace refit or final-test prediction.


E01 discovery correction after user feedback: `bash review.sh` opens the proper
VS Code workspace without manual directory configuration; actual extension-host
integration reproduced the root failure and navigated all 11 editor anchors.
See [evidence](../docs/review-evidence/codetour-discovery.json); the Markdown
route remains an alternative, not a substitute for testing actual discovery.
