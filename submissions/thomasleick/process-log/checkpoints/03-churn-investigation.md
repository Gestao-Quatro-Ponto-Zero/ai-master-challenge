CHECKPOINT: 03 — Churn investigation
STATUS: PASS (descriptive diagnosis); predictive and causal criteria UNKNOWN
OBJECTIVE: Investigate the CEO narrative using all five source tables, preserving entity grain, denominators, temporal ordering, and uncertainty.
WORK COMPLETED:
- Revalidated the prior profile and analysis scripts on copies; regenerated output hashes exactly match the preserved staging outputs.
- Implemented the same descriptive findings in a deterministic API analytics engine. It reads all five source tables and avoids multiplying subscription money through one-to-many usage, ticket, or event joins.
- Did not fit an ML model because outcome, time eligibility, and point-in-time features are not valid enough.
FILES CREATED: solution/apps/api/src/analytics/engine.py; docs/methodology/analysis.md; docs/findings/executive-report.md; process-log/evidence/initial-data-profile.json and initial-analysis-summary.json are preserved copies.
FILES MODIFIED: This checkpoint report refreshed for the current authorized workspace.
COMMANDS EXECUTED:
- Reexecuted copies of staging audit_data.py and analyze.py against original inputs into /tmp/ravenstack-validation; exact regenerated evidence hashes match.
- Dataset/profile SHA checks and source directory diff.
TESTS EXECUTED: Data artifact reproducibility checks and final API response-contract suite (checkpoint 05).
TEST RESULTS:
- 600 event rows touch 352 accounts; account churn_flag=True occurs for 110/500.
- Cross-tab: 75 flag+event, 35 flag only, 277 event only, 113 neither; 312/500 conflicts.
- Event rows are 73 in 2023 and 527 in 2024. Denominators and lifecycle rules are unresolved, so this is not a churn rate.
- Usage: 19,142/25,000 rows before linked subscription start; 290 after a non-null end; 21 duplicate IDs.
- Satisfaction: 825/2,000 missing. All-time scored-ticket means: 3.980 (n=815, accounts with any event) vs 3.983 (n=360, no-event accounts); no pre-event or causal interpretation.
- All-time ticket summaries: event-history group 1,395 tickets / 347 accounts, median first response 89 minutes, median resolution 35 hours, 71/1,395 escalated (5.09%); no-event group 605 tickets / 145 accounts, 87 minutes, 35 hours, 24/605 escalated (3.97%). These are retrospective ticket aggregates, not pre-churn effects.
- Event refund field sum is USD 8,652.25, not recurring revenue lost.
- 486/5,000 subscription rows have end dates, but every account has at least one null-end row. Exact logo churn, GRR, NRR, recurring revenue exposure, causal drivers and recoverable revenue remain UNKNOWN.
EVIDENCE LEVEL: LOCAL_RUNTIME for source analysis and final API contract execution.
BUSINESS FINDINGS: Recorded event volume rose; actual churn-rate increase is not established. Usage/satisfaction narratives are not confirmed at eligible-account level. No cause is demonstrated.
UNKNOWN: Whether churn events encode repeat cancellation/reactivation records; true period eligibility and account loss; valid historical MRR; causal effect of usage, support or proposed intervention.
BLOCKERS: None for descriptive diagnosis. Defensible risk scoring and ML are not supported by available labels/timestamps.
RISKS: Reason codes are descriptive; segment comparisons depend on conflicting outcomes; do not use for customer targeting.
NEXT STEP: Preserve the unresolved lifecycle/revenue definitions and validate any future pilot on an eligible cohort.
