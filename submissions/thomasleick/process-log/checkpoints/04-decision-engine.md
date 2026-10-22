CHECKPOINT: 04 — Retention decision engine
STATUS: PASS (conditional scenario engine tested)
OBJECTIVE: Provide interpretable account evidence and transparent conditional intervention scenarios without false risk or ROI claims.
WORK COMPLETED:
- Scenario calculation constrains selected accounts by eligible population, operational capacity, and budget.
- Effectiveness, contact cost, monthly retained value and horizon are explicit user inputs.
- Outputs label expected retention and financial amounts hypothetical; if monthly value is absent, value and net benefit return null/UNKNOWN.
- Account review returns records with conflicting churn labels, not a risk score; raw subscription-row MRR sums are explicitly caveated.
- Added a validation experiment proposal with verified eligibility, account randomization, 90-day retention outcome and guardrails in the executive report/UI.
FILES CREATED: solution/apps/api/src/main.py scenario endpoint, Pydantic contracts, UI Decision Room, backend tests and frontend scenario arithmetic tests.
FILES MODIFIED: None outside candidate package.
COMMANDS EXECUTED: API pytest suite, HTTP scenario POSTs, invalid-input validation and browser scenario recalculation; see checkpoints 05 and 07.
TESTS EXECUTED: Six API tests at the point of scenario validation; final API suite is seven tests.
TEST RESULTS: Scenario arithmetic returns 25 selected, 2.5 hypothetical retained, cost 2,500, and net value 1,250 under supplied assumptions. Missing retained value returns UNKNOWN; invalid effectiveness returns HTTP 422. Final pytest 7/7 passed.
EVIDENCE LEVEL: LOCAL_RUNTIME.
BUSINESS FINDINGS: NONE.
UNKNOWN: Intervention effectiveness and recurring value; no impact is empirically estimated.
BLOCKERS: None for conditional scenario arithmetic; commercial inputs remain unknown.
RISKS: Sensitivity factors are illustrative arithmetic, not confidence intervals or historical uplift.
NEXT STEP: Leadership must validate the inputs and assign pilot owners; no causal uplift is known.
