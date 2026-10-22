# Historical churn reconstruction

This independent module reconstructs account and subscription activity from the original account, subscription and churn-event CSV files. It uses only the Python standard library and does not modify source data or prior analyses.

Run from the standalone `solution/` directory:

```bash
python analysis/historical_churn/reconstruct.py --help
python analysis/historical_churn/reconstruct.py
python -m unittest discover -s analysis/historical_churn/tests -v
```

Optional paths are supported with `--data-dir PATH` and `--output-dir PATH`. The default output is `analysis/historical_churn/outputs/` and consists of:

- `historical-churn.json`: snapshots, annual calculations, source hashes, event/date conflicts and a conditional monthly-cohort series.
- `annual-reconciliation.csv`: annual account and subscription denominators, reported label comparisons, and movement residuals.
- `monthly-reconstruction.csv`: monthly opening and closing bases, conditional logo gaps, reactivation after a gap, and subscription exits.
- `cohort-retention-conditional.csv`: month-age activity for first-valid-subscription cohorts.

## Definitions

The source data README says a null `end_date` means the subscription is active and a true subscription `churn_flag` means it ended. The calculation applies the half-open interval `[start_date, end_date)`, equivalent to `start_date <= snapshot_date and (end_date is null or end_date > snapshot_date)`. A logo is active when any linked subscription interval is active. Multiple rows are collapsed to distinct `account_id` for logo counts.

For an opening customer, a gross date-derived logo exit occurs when the union of its subscription intervals has a gap during the year. Subscription churn counts opening subscription IDs not active at the next-year boundary. These definitions are **conditional** because event and account churn labels materially conflict with the interval interpretation.

The cohort anchor is the earliest positive-length subscription interval start by account, grouped by calendar month. Retention at each month-age boundary counts cohort accounts with at least one active linked subscription. This is an audit diagnostic, not validated retention: the data have open-ended rows for every account, event dates often conflict with active subscriptions, and reactivation can make cohort activity non-monotonic.

No metric from this module is a causal effect, calibrated future-risk probability, or verified finance KPI.
