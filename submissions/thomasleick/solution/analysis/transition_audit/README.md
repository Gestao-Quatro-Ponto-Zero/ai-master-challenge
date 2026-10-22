# Subscription transition flag audit

Run from the standalone `solution/` directory:

```bash
python analysis/transition_audit/audit.py \
  --data-dir data/raw \
  --ledger analysis/daily_portfolio_churn/outputs/g4-alignment/daily-portfolio-churn.json \
  --output-dir analysis/transition_audit/outputs
```

The source CSV explicitly contains `upgrade_flag` and `downgrade_flag`. This audit counts those row flags and compares them with the daily engine's candidate transition pairs. It does not infer confirmed migrations: the CSV has no dated transition key that joins the flags to a source and target subscription pair, and the plan hierarchy is not a documented rank field.
