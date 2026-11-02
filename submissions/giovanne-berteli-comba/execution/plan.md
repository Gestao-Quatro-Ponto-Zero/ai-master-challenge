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
| R01 | Focused PR review | Declare sample and effort cap before browsing; identify repeated approaches and evidence gaps with links within that cap (F06) | Future research notes; no claim that private baselines are accessible |
| A01 | Operational diagnosis | Reproducible bottleneck/satisfaction findings; explicit populations, missingness, time units and active-effort assumptions; distinguish simulated from measured savings (F07) | Future analysis scripts and report |
| S01 | Automation and scope | Choose one useful automation; define handoff and failure rules, anomaly records/filters, review states, success measures and an explicit flow (F03) | Future solution decision and scope record |
| V00 | Evaluation protocol before implementation | Baseline, entry-time inputs, group/duplicate separation, development/validation/test membership and selection criteria recorded; choose thresholds on validation, not final test (F02) | Future versioned protocol following `docs/validation-strategy.md` |
| I01 | Prototype | Demonstrate the selected automation using real data under V00; persist possible high/low anomalies and support reason/direction/review-state filters (F03); document setup and limitations | Future `solution/` implementation |
| V01 | Validation | Meaningful software tests and separate AI evaluation; report failures and limitations | Future test/evaluation outputs |
| E01 | Evidence and communication | Reviewer narrative, conversation coverage, decision history and useful CodeTour checked | Process log, report and future tour |
| P01 | Submission | Candidate details completed, reproducible setup, template satisfied, allowed diff scope, PR instructions followed | Final review checklist and eventual PR |

- [x] B01 — Prepare and check the foundation. Evidence: [document checks](activity-log.md).
- [x] B02 — Review the foundation adversarially. Evidence: [review and open adjustments](../docs/architecture-review.md).
- [x] B03 — Implement and validate foundation controls. Evidence: [controls](../docs/foundation-controls.md).
- [x] D01 — Audit both datasets. Evidence: [audit and limitations](../docs/data-audit.md).
- [x] D02 — Decide complementary dataset usage. Evidence: [roles, limits and evaluation boundaries](../knowledge/dataset-usage.md).
- [ ] R01 — Review a bounded sample of Challenge 002 PRs.
- [ ] A01 — Complete the operational diagnosis.
- [ ] S01 — Define one automation and its human intervention rules.
- [ ] V00 — Record the evaluation protocol before prototype implementation.
- [ ] I01 — Build the functional prototype.
- [ ] V01 — Run and document software tests and AI evaluation.
- [ ] E01 — Complete evidence, narrative, and CodeTour.
- [ ] P01 — Prepare the final submission and PR.

Coordination source for F01–F07:
[official review table](../docs/architecture-review.md#lista-oficial-para-validação).
B02 records completion of the review, not implementation of its adjustments.
Keep review decisions and adjustment state in that table only. V00 must precede
I01; V01 evaluates the implemented version. Process logs are recruitment evidence,
excluded from normal execution context; keep current decisions in operational owners.

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
