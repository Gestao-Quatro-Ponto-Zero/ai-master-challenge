# Contract churn forensics

This isolated standard-library analysis examines 2024 opening subscription exits, account continuity, and account-level churn events. It never assigns a churn event to a subscription because the event table has no `subscription_id` key.

From the standalone `solution/` directory:

```bash
python analysis/contract_churn/investigate.py
python -m unittest discover -s analysis/contract_churn/tests -v
```

Override source and output paths with `--data-dir` and `--output-dir`. The default output is `analysis/contract_churn/outputs/` and includes:

- `contract-churn-forensics.json`: summaries, the full 66-row subscription inventory, 443 conflicting event rows, account reconciliation, financial descriptors and source hashes.
- `ended-opening-subscriptions-2024.csv`: row-level subscription audit.
- `conflicting-nonreactivation-events-2024.csv`: row-level event/date context; no event-contract link is inferred.
- `opening-account-reconciliation-2024.csv`: one row per opening account with indicator crosswalk.
- `reactivation-marked-events-2024.csv`: account-level reactivation markers and nearby same-account lifecycle evidence.

## Definitions

- Opening subscription: `start_date <= 2024-01-01` and (`end_date` absent or `end_date > 2024-01-01`), matching the supplied data README's blank-end-date description.
- Ended opening subscription: an opening `subscription_id` with a valid `end_date` before 2025-01-01.
- Active at date: `[start_date, end_date)` interval; an open end is treated as active only as a source-documented conditional assumption.
- Account coverage: at least one linked subscription interval is active. Concurrent records count once for account continuity.
- Conflicting event: a 2024 non-reactivation event whose account has at least one date-active subscription on the event date. This is a conflict between source labels/grains, not proof the event is false.
- End-date proximity uses absolute distance to any same-account subscription end date in 2024. It is not a foreign-key match or causal window.

Money values are descriptive row attributes. MRR/ARR row sums are deliberately labeled non-authoritative and never exposed as lost revenue. Event refunds are not joined to contracts.
