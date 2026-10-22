# G4-oriented customer churn reconstruction

This module is isolated from the historical and contract-level analyses. It computes unique-account opening populations, conditional interval-based diagnostics, account-label comparisons and first-subscription-start cohort diagnostics from the original account, subscription and churn-event CSVs.

The primary customer churn KPI intentionally remains `UNKNOWN`: 2024 date-derived account coverage has no full-account loss among 191 opening accounts, while 103 of those accounts have at least one non-reactivation event and 443/472 2024 non-reactivation rows occur during date-active subscriptions. The data do not establish which status represents a commercial customer departure.

Run from the `solution/` directory:

```bash
python analysis/g4_customer_churn/analyze.py
python -m unittest discover -s analysis/g4_customer_churn/tests -v
```

The default output directory is this module's `outputs/`. To use another source folder or output location:

```bash
python analysis/g4_customer_churn/analyze.py --data-dir data/raw --output-dir analysis/g4_customer_churn/outputs
```

Outputs are JSON plus CSV diagnostics. Cohort and interval-derived values are marked conditional; they are not validated customer retention or churn rates. The API serves the same deterministic calculations at `GET /api/g4-customer-churn`.
