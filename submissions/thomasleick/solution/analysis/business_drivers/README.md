# Business-driver investigation

Independent, additive analysis of acquisition/ICP, activation proxy, adoption, support, cohorts, economics and account-level reconciliation candidates. It reads the original five CSVs and does not alter `analysis/conventional/` or the existing application history.

Run from the standalone `solution/` directory:

```bash
python analysis/business_drivers/run.py --help
python analysis/business_drivers/run.py --data-dir data/raw --output-dir analysis/business_drivers/outputs/g4-alignment
python -m unittest discover -s analysis/business_drivers/tests -v
```

The script uses Python 3.10+ standard library only. The default input resolves relative to this script's solution package. Output defaults to the module's `outputs/` folder; both paths can be overridden. The G4-alignment reproduction uses the isolated `outputs/g4-alignment/` path so historical output artifacts remain intact. It writes a JSON API artifact plus CSVs for segment labels, signup cohort label diagnostics, monthly/yearly calendar-usage trends, usage groups, feature adoption and account investigation candidates.

Four account outcome indicators are kept separate: account `churn_flag`, any event row (including reactivation), a non-reactivation event row, and account membership with any flagged subscription. Their counts are not churn rates or calibrated risk. The signup-quarter table contains retrospective label composition, not retention by elapsed period. The script intentionally emits no retention heatmap.

Usage rows are joined to one subscription by `subscription_id`. Raw calendar totals preserve source volume; interval-bounded totals are a separate sensitivity using this module's inclusive end-date convention. This does not establish a pre-cancellation window. Support measurements are shown at ticket grain and as account-cluster summaries so accounts with many tickets do not appear to be independent customers. Satisfaction and escalation missingness are included. Subscription financial fields stay at row grain; revenue totals remain unavailable.

The JSON and CSV outputs are generated from the source CSVs. Do not edit them manually; rerun the command after changing source data or analysis logic.
