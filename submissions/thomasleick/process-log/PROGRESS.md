# RavenStack final delivery progress

**Current mission:** G4 executive paper → monthly business laboratory → upgrade/downgrade audit.

**Checkpoint 53 — Final editorial patch (2026-10-22): PASS for the three requested paper corrections.** Q1 now states the 62/54 coverage finding and the declared feature/support/budget hypotheses without causal overclaim. The monthly chart calls out October's peak opening-cohort rate and December's highest gross loss count while keeping their numerators distinct. Page 6 identifies the 60 historical accounts as an assumed scenario pool, not verified current eligibility. Seven paper tests pass; the regenerated seven-page PDF hash matches both manifests; all seven renders and the revised pages were inspected. See `process-log/checkpoints/53-final-editorial-patch.md`.

**Checkpoint 52 — Executive Paper Recovery (2026-10-22): PASS for the paper deliverable.** The seven-page PDF was regenerated from verified local outputs, the numerical manifest was refreshed, and the final 160-dpi render set was inspected. Six paper evidence tests pass. January 2023 is explicitly undefined at a zero opening denominator. This status does not certify commercial customer churn, causal drivers, recurring-revenue loss, future risk, or intervention uplift. See `docs/findings/PAPER-EXECUTIVE-ACCEPTANCE-REVIEW.md` and `process-log/checkpoints/52-executive-paper-recovery.md`.

| Phase | Status | Evidence |
|---|---|---|
| 1. Executive paper | PASS | Seven-page A4 PDF; Markdown source and ReportLab generator; seven rendered pages inspected; numerical evidence manifest parses and includes source hashes. |
| 2. Monthly business laboratory | PASS | Observed/Scenario modes, immutable selected-month baseline, validated movement bridges, unit-neutral model, tests and API contract; scenario POST passed through the frontend proxy. |
| 3. Upgrade/downgrade audit | PASS | Explicit flags and candidate transitions separately audited; transition API and in-product panel; 44 Python/API tests and Ruff pass. |
| Final visual/browser review | UNKNOWN | Local browser access was denied during the prior visual-QA attempt. No bypass or visual PASS is claimed. |
| Final delivery consolidation | PARTIAL | Checkpoint 51 revalidated source hashes, 24 monthly API rows, 7-page paper hash, test suites, builds, and healthy local services; browser visual QA is still UNKNOWN. |

## Key current conclusions

- Primary executive deliverable is `docs/paper/RAVENSTACK-THE-CHURN-PARADOX.pdf`; source and reproduction files are in `docs/paper/`.
- Churn of verified customer/product identity remains UNKNOWN. The time-based daily engine is a conditional account × plan-tier proxy.
- Monthly scenarios are hypothetical. The observed baseline is loaded from the daily ledger and cannot be changed by the scenario request.
- The dataset has explicit upgrade/downgrade row flags (529/218; 23 rows carry both), but no linked dated from/to transition proof. There are 52/51 possible interval pairs within 30 days under a name-order assumption; confirmed migrations remain zero.
- Recorded recurring revenue movement, causal uplift, and profit are not identified.

## Remaining

1. Human review of the executive PDF and standalone package.
2. Optional browser visual review once allowed; currently UNKNOWN because prior local browser access was denied.
3. Fork/branch/PR operations require separate user authorization and remain unperformed.

Final delivery record: `docs/findings/RAVENSTACK-FINAL-DELIVERY-STATUS.md`.

No Git or remote publication effects have been performed.

**Checkpoint 54 — Monthly Business Lab & Key Moments (2026-10-22): PARTIAL.** Added deterministic key moments to the existing monthly API output, made month selection navigate into the same month in the existing scenario lab, and documented the evaluator path from the paper to monthly evidence and scenarios. Current data reproduce October 2024 at 9/1,073 = 0.83877% (monthly opening-cohort plan proxy peak) and December 2024 at 11 gross losses versus 5/1,279 = 0.39093% (opening-cohort loss). All five CSV hashes match. Backend 45 tests, Ruff, frontend 9 tests, Vite build, Compose build/health, HTTP proxy and scenario smoke tests passed. Browser permission was denied by policy; no workaround was attempted, so visual browser QA remains UNKNOWN. See `docs/findings/MONTHLY-BUSINESS-LAB-KEY-MOMENTS.md` and `process-log/checkpoints/54-monthly-business-lab-key-moments.md`.
