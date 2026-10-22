# Daily commercial churn ledger

This module reconstructs daily **account × plan-tier proxy** coverage from the original subscription CSV. The source contains no stable product or service key; `plan_tier` is not presented as product identity.

## Reproduce

From the standalone `solution/` directory:

```bash
PYTHONPATH=analysis python3.12 -m daily_portfolio_churn \
  --data-dir data/raw \
  --output-dir analysis/daily_portfolio_churn/outputs
```

The command writes a JSON evidence bundle, one daily ledger CSV, a movement CSV, plan-proxy summary CSV, and weekly/monthly/quarterly/semiannual/annual summaries. It does not change source CSVs.

## Temporal and commercial interpretation

- Source dates are civil dates; timezone is unknown.
- Candidate coverage uses `[start_date, end_date)`: `end_date` is the first inactive date. The source README says it is the date a subscription ended, but does not specify same-day inclusivity; results therefore remain `CONDITIONAL_DATE_RECONSTRUCTION`.
- Null end dates are treated as open only through the last observed source date and are right-censored there.
- The overall observation window is derived from dates in the five source tables: 2023-01-01 through 2024-12-31. The first subscription start is 2023-01-09.
- Rows with nonpositive intervals are retained in `invalid_intervals` and excluded from coverage; no dates are repaired.
- Intervals are unioned by `(account_id, plan_tier)`. Overlapping and contiguous same-plan rows are consolidated, so one subscription ID ending is not a plan-proxy loss if same-plan coverage continues.
- Subscription records do not expose a durable product key, contract lineage, renewal key or replacement link. A plan change is not proof of migration.
- `upgrade_flag` and `downgrade_flag` are reported as source flags. Possible tier transitions use the name-based order Basic < Pro < Enterprise and 0/1/7/30-day windows; this hierarchy and pair linkage are not verified, so they remain candidates.
- MRR/ARR fields are not aggregated into revenue outcomes. Currency, effective periods and row/snapshot semantics are not reconciled. Revenue expansion, contraction and churn are `UNKNOWN`.
- Event rows link to accounts only. A same-day or nearby event is contextual association, not an event-to-plan relationship or causal explanation.

## Metrics

Daily plan-proxy churn count is the number of active account-plan proxy relations that lose coverage on that transition date. Its daily rate divides by relations active immediately before date transitions; an empty opening base has an undefined rate. Period summaries derive from the same daily movements and provide gross events, unique affected opening relations, opening-cohort losses any time, opening-cohort losses at close, reactivations, acquisitions and closing balance. Daily percentages are never averaged to obtain a period rate.

Customer churn counts a complete loss of every active plan-tier proxy for an account. The same-day change is not complete customer churn if another plan proxy remains active. All account-level churn outputs are conditional on the date model and source identity limitations.

## G4 context

The [G4 cohort-analysis article](https://g4educacao.com/blog/analise-de-coorte) describes time-based customer groups, tracking their behavior at equal elapsed periods, and comparing cohorts to inform acquisition and retention decisions. This module applies longitudinal tracking as an implementation choice; the daily account-plan ledger is not represented as a proprietary G4 formula.
