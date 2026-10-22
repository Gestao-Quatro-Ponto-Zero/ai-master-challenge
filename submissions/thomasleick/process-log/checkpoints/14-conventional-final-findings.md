CHECKPOINT: 14 — Conventional analysis and findings
STATUS: PARTIAL — independent analysis complete; product/API integration not performed
OBJECTIVE: Answer the three CEO questions from calculated outputs, compare with The Churn Paradox, validate the analytical package and report residual requirements.
WORK COMPLETED:
- Produced the independent conventional report with definitions, labels, segment and account tables, source metrics, uncertainty, recommendations and a comparison to the prior findings.
- Added deterministic CLI defaults, explicit data/output options, no third-party runtime dependency, two SVG graphics and eight automated tests.
- Preserved the four existing chapters, API, source CSVs, historical reports and checkpoints; new evidence lives under the isolated module.
- Did not integrate an additional UI chapter because safe integration would require changing the existing consolidated frontend/API and browser/runtime validation is not presently demonstrated. The conventional package remains usable independently.
FILES CREATED: See README and output inventory in `solution/analysis/conventional/`; `reports/conventional-churn-report.md`; checkpoints 11–14 and `process-log/conventional-analysis-progress.md`.
FILES MODIFIED: NONE of the existing application, datasets, reports, or history. Existing candidate README/analysis/docs not changed.
COMMANDS EXECUTED: `python3 .../run.py --help`; full source analysis command; `python3 -m unittest discover -s .../tests -v`; independent CSV/hash/cardinality and output reconciliation reads. Docker status inspection returned permission denied for `/var/run/docker.sock`; no container was started or changed.
TESTS EXECUTED: Eight conventional analysis unit/invariant tests. No frontend/API/Docker tests because application files were not changed and Docker daemon access is unavailable.
TEST RESULTS: 8 tests passed. CLI help works, outputs were generated, source row sums and hashes reconcile, all tested foreign-key relationships have zero orphans. The output run and tests used actual source CSVs.
EVIDENCE LEVEL: LOCAL_RUNTIME / UNIT; no Docker/application integration evidence in this checkpoint.
BUSINESS FINDINGS: (1) Cause not established; reason codes are descriptions. (2) Label-specific observed segment prevalence and account event histories are exposed, not future risk. (3) Lifecycle instrumentation, reason-code interviews, and a randomized pilot after defining eligibility are justified; financial impact and ROI remain UNKNOWN.
UNKNOWN: True logo/subscription churn rate, causal root cause, eligible risk population, recurring revenue exposure, intervention uplift, product-in-app visibility of conventional outputs.
BLOCKERS: No Docker daemon permission in this execution. No code changes to frontend/API were authorized in this constrained analysis-only integration boundary; standalone results are complete.
RISKS: Synthetic dataset limits external validity; conflicting labels and dates prevent causal/predictive interpretations. The account list is historical event volume only.
NEXT STEP: If desired, review the standalone report and outputs; a separate, explicitly scoped product integration can surface these calculated artifacts without altering the original four chapters.

## CEO answers

1. **What causes churn?** Unknown. Reason-code volume and small descriptive differences do not establish cause.
2. **Which segments/accounts are most at risk?** There is no defensible predictive ranking. Label-conditioned segments and repeated event accounts are listed for investigation with clear definitions.
3. **What should RavenStack do?** Reconcile prospective lifecycle truth, validate customer-reported reasons, then test adoption/support outreach by randomized eligible-account pilot. Costs, recovered revenue and causal uplift are not estimable here.
