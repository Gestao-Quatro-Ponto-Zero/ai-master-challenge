# RavenStack — Final Delivery Status

**Challenge:** G4 AI Master Challenge 001 — Churn Diagnosis  
**Status:** PARTIAL — local paper, lab, API, transition audit, tests, and runtime verified; rendered browser QA remains UNKNOWN.

## Phase status

| Phase | Status | Evidence |
|---|---|---|
| 1. Executive paper | PASS | Seven-page PDF; editable Markdown and generator; source manifest; seven rendered pages inspected in checkpoint 48. |
| 2. Monthly business laboratory | PASS | Observed and hypothetical scenario modes; 24-month source series; validated scenario contract; frontend/API integration. |
| 3. Upgrade/downgrade audit | PASS | Explicit row flags separated from date-derived possible pairs; API and product evidence panel. |
| Final visual QA | UNKNOWN | Browser access was unavailable. No visual review or screenshot is claimed. |

## Executive conclusion

The customer-churn KPI is not commercially certified by the available source semantics. The reproducible daily ledger is an `ACCOUNT × PLAN_TIER × CIVIL_DAY` **PLAN-LEVEL PROXY**, built under a conditional date reconstruction. For the 2024 opening cohort, it records 7 of 374 relationships lost at least once (1.87%), 3 of 374 without coverage at year-end (0.80%), and 0 of 190 opening accounts with complete coverage loss. These figures describe reconstructed plan coverage, not a verified customer churn rate.

There are 62 plan-proxy loss events over the 731-day observation window, 43 plan reactivations, and 8 complete account-coverage-loss events followed by return within the observation window. Daily plan and customer bridges have zero residuals. Arithmetic reconciliation does not certify commercial meaning.

The subscription source contains `upgrade_flag` and `downgrade_flag` (529 and 218 rows, with 23 rows carrying both). They are not linked to dated from/to pairs. The 52 possible upgrade-direction and 51 possible downgrade-direction date pairs within 30 days remain conditional candidates under an unverified plan order; no migration is confirmed. Effective-dated recurring-revenue expansion/contraction, causal churn drivers, intervention lift, and accounting ROI remain UNKNOWN.

## Final verification

- Python/API/analytics: **44 passed**, one Starlette deprecation warning.
- Frontend: **8 passed** across 3 test files.
- TypeScript/Vite production build: **passed**.
- Compose configuration and project runtime: previously validated; current observation showed API and web containers healthy.
- API health and frontend root: HTTP 200.
- Daily portfolio endpoint: **731 daily rows**, with **24 monthly rows** from 2023-01 through 2024-12.
- Scenario POST through frontend proxy: passed in checkpoint 50.
- Ruff: passed on touched API/transition audit files in checkpoint 50.
- PDF: **7 pages**; SHA-256 `7fb012e5af44d352155fb1791f2e4f2d8a6b57e0544641e935664b7b6b6fe7b1`.
- Browser visual QA: **UNKNOWN**.

Latest verification details: [checkpoint 51](../../process-log/checkpoints/51-final-delivery.md). The phase reports and historical evidence remain preserved.

## Local review

From `submissions/thomasleick/solution/`, run:

```bash
docker compose up --build
```

The currently observed local URLs are `http://localhost:15176/` (web) and `http://localhost:18201/api/health` (API). The API and web containers were healthy at the latest check.

The primary deliverable is [RAVENSTACK-THE-CHURN-PARADOX.pdf](../paper/RAVENSTACK-THE-CHURN-PARADOX.pdf), with editable source and numeric manifest in `docs/paper/`. The monthly laboratory and upgrade/downgrade audit complement the paper; they do not replace it.

## Remaining review items

1. Review the paper and local application as a human evaluator.
2. Complete viewport/browser QA when access is permitted.
3. Keep Git and publication actions pending separate authorization.

No Git initialization, commit, push, PR, deployment, or external publication was performed.
