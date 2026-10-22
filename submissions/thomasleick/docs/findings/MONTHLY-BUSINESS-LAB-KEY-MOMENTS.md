# Monthly Business Lab & Key Moments

**Scope:** complementary application for G4 AI Master Challenge 001. The executive paper remains the primary deliverable. This report records the monthly exploration and scenario bridge added to the existing four-chapter application.

## Architecture reused

- Canonical source remains `solution/analysis/daily_portfolio_churn/engine.py` and its saved output `solution/analysis/daily_portfolio_churn/outputs/g4-alignment/daily-portfolio-churn.json`.
- Grain is **ACCOUNT × PLAN_TIER × CIVIL_DAY**. `plan_tier` is a **PLAN-LEVEL PROXY**, not verified product identity. Interval reconstruction is conditional on `[start_date, end_date)`; source dates have no known timezone.
- The existing `GET /api/daily-portfolio-churn` response is extended additively with `key_moments`; the same endpoint already supplies monthly periods and daily movements. No duplicate endpoint or analytical engine was created.
- `solution/analysis/daily_portfolio_churn/key_moments.py` deterministically selects highlights from those 24 monthly periods. `MonthlyChurnView.tsx` consumes the typed response and the ledger movements. `MonthlyBusinessLab.tsx` reuses the observed period rows and existing scenario API.

## Monthly view and interaction

Chapter 02 retains all 24 monthly observations as the primary executive view. It distinguishes customer full-coverage loss from account–plan-tier coverage loss, gross loss from still-lost-at-close, and event rows from date-derived relation movements. Each rate retains its own opening-cohort numerator and denominator; January 2023 has no opening base, so its rates are `UNDEFINED`, not 0%.

The month inspector compares the selected month with the previous month and the same month one year earlier, preserving each measure's unit. Selecting a Key Moment highlights its month in the charts and reveals the observed value, numerator/denominator when defined, comparison, objective selection criterion, associated segments, account movement examples, evidence class and suggested investigation. The action opens that same month in the Monthly Business Lab.

## Key Moments rules and current results

The engine uses deterministic descriptive rules, not an LLM and not statistical significance tests:

- `RATE_PEAK`: maximum monthly opening-cohort plan-proxy loss rate, only among positive denominators; exact ties are retained.
- `LOSS_VOLUME_PEAK`: maximum count of date-derived plan-relation loss events across all relations active at some point in the month; this is not restricted to the opening cohort.
- `ACQUISITION_CHANGE`: largest absolute month-over-month count change, separately for new customers and new account–plan-tier relations.
- `RECOVERY_MOMENT`: monthly maxima for customer reactivations and plan-proxy reactivations, kept as separate units; ties are retained.
- `PORTFOLIO_CONTRACTION`: monthly maxima for portfolio contraction and possible downgrade candidates, reported separately. A possible transition is not a confirmed migration.
- `RATE_VS_VOLUME_DIVERGENCE`: adjacent months where gross event-count direction and opening-cohort rate direction differ, with valid rate denominators.
- `DATA_QUALITY_EVENT`: largest positive monthly difference between non-reactivation event rows and reconstructed complete-account coverage-loss events. Event rows are not linked to contracts without a key.

The current data produced **18 selectable moments across all seven types**. Peaks and largest changes are descriptive rule outputs. Small counts, ties, candidate classifications and conditional dates must be reviewed before commercial action.

### Required month checks

| Moment | Verified value | Meaning |
|---|---:|---|
| Oct 2024 `RATE_PEAK` | 9 / 1,073 = **0.83877%** (displayed 0.84%) | Nine relations in the opening cohort lost coverage at least once during October; highest valid monthly opening-cohort plan-proxy rate in the 24 months. |
| Dec 2024 `LOSS_VOLUME_PEAK` | **11 gross loss events** | Highest absolute count of date-derived plan-relation loss events; may include relations acquired after month opening. |
| Dec 2024 opening-cohort measure | 5 / 1,279 = **0.39093%** (displayed 0.39%) | Five opening-cohort relations lost coverage at least once; this is not the numerator 11 above. |

Values were read from the API's `key_moments` output generated from the current packaged CSVs and are asserted in API tests. The 24-row endpoint series is the same data passed to the charts.

## Observed and scenario modes

The existing Monthly Business Lab provides:

- **OBSERVED:** read-only date-reconstructed customer and plan-proxy baseline for the selected month.
- **SCENARIO:** editable hypothetical customer/plan movements and user-assumed per-plan/customer monthly values, uptake/lift, costs and horizon; submission is validated/calculated by the existing API. Scenario inputs do not overwrite observed rows. Users can reset to the observed baseline and export scenario output as JSON.
- Outputs distinguish customer-level and plan-level rates, modeled values, costs and net contribution. These are not accounting profit, observed recurring revenue, causal retention uplift or a forecast.
- Existing transition audit distinguishes explicit row flags from possible date/plan candidates. Plan ordering and contract-level migration links are not established; possible upgrades/downgrades are not added as extra churn events. Revenue expansion/contraction remains unknown unless comparable reconciled values exist.

## Validation performed

The source ledger metadata records the same SHA-256 values as the five current files in `solution/data/raw/`:

- accounts: `348d8ba906b7776894b5236b2e7aa91a503d41670dbc9aad30c37b503c9abef5`
- subscriptions: `dcf1d93ca9a35e0dcba0ab686d255f0e9ec26512970bbf0944cf19cbef2d751a`
- feature usage: `c081da2be8caf987d07f0f79ceb0619aba523d819529230ed6df77984fa21d4e`
- support tickets: `ba0006951479771ee9f93c98789c96bc5fec892cf11f867afb28194f0b76d220`
- churn events: `6391c41d8291b7b4845ec9a84d3837c2ed230a33a32a854ec33d4e66dc150940`

Current checks before Compose integration:

- API/analytics test image: **45 passed**, one Starlette deprecation warning.
- Ruff: **All checks passed**.
- Frontend Vitest: **9 passed** across 3 files.
- TypeScript/Vite build: **passed**.
- API tests assert 24 months, zero-base undefined behavior, October peak 9/1,073 and December 11 gross events vs 5/1,279 opening-cohort losses.
- Frontend integration test selects a Key Moment and opens the same month in the lab.

Docker runtime and browser validation are recorded in the sequential checkpoint. Browser review is not marked complete unless the running page is actually opened and exercised.

## Limitations and challenge fit

This is an optional, local decision-support companion, not a substitute for the written diagnosis. The public challenge's three questions are answered primarily in the executive paper and findings reports. The lab makes month-level movements explorable and supports transparent “what if” discussion; it does not establish causal drivers, calibrated future risk, a real product catalog, commercially certified customer churn, or reconciled recurring-revenue impact. No changes were made to the paper or source CSVs.
