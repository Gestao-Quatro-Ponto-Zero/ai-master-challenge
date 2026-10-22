# Conventional churn analysis

This is an **independent, additive** analysis package. It does not alter the existing four-chapter application or the earlier investigation and its evidence. It reads the original five CSVs and writes only its own outputs and report.

## Run from the standalone solution root

```bash
python analysis/conventional/run.py --help
python analysis/conventional/run.py --data-dir data/raw --output-dir analysis/conventional/outputs
python -m unittest discover -s analysis/conventional/tests -v
```

The default data path resolves to `solution/data/raw`; the default output path is this module's `outputs/` directory. All paths can be overridden. The script requires only Python 3.10+ standard library. SVG charts are emitted directly, so no plotting package is required.

## Outcome definitions

Four outcomes are kept separate: supplied `accounts.churn_flag` (account-level operational indicator); any event row for an account (including reactivation); at least one event explicitly not marked as reactivation (does not prove final cancellation); and at least one subscription row with `churn_flag=True` (reported as account membership when compared to account attributes, and at subscription grain for billing characteristics). None is automatically interpreted as a historical churn rate.

The module does not de-duplicate the original data. It reports duplicate key groups and keeps raw usage totals. Valid-subscription-interval usage is a separate sensitivity; records outside subscription dates are excluded only for that sensitivity. Financial fields stay at subscription-row grain and are not summed into account MRR/ARR exposure.

Account-level characteristics use one row per account. Subscription and support analyses retain their own row grain. The tool avoids joining multiple one-to-many tables into a single wide relation. Prevalence intervals use Wilson's binomial interval; differences in account-level means use a deterministic 2,000-draw account bootstrap percentile interval. These are descriptive under each supplied label; they do not correct label errors, selection, or the synthetic data generation process.

## Output inventory

- `outputs/data-profile.json`: hashes, columns, null counts/rates, distributions, numeric summaries, duplicate IDs and whole-row duplicates.
- `outputs/analysis-summary.json`: label reconciliation, cardinalities, time counts, usage, support, finance, limitations and recommendations.
- CSVs provide account/subscription segmentation, use by label, feature adoption, support comparisons and account event-volume listing.
- SVGs compare observed label-positive counts and annual event-row counts. The latter explicitly is not a rate.
- `reports/conventional-churn-report.md`: executive answers to the three CEO questions and comparison with The Churn Paradox.

The account listing is ordered by recorded event volume, not estimated risk. No probability model, causal effect, revenue-at-risk amount, or ROI is produced.
