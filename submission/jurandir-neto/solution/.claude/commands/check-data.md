# /check-data

Valida a integridade dos dados em todos os layers: raw CSVs, bronze, silver e gold.

## O que este comando faz

1. Verifica se os CSVs em `data/raw/` existem e têm as colunas esperadas
2. Verifica se os Parquets existem em `data/bronze/`, `data/silver/` e `data/gold/`
3. Reporta contagem de registros e possíveis problemas

## Script de validação

Execute o seguinte script Python:

```python
import duckdb
import os

con = duckdb.connect()
issues = []

# ── RAW CSVs ──────────────────────────────────────────────────
expected_schemas = {
    "data/raw/ravenstack_accounts.csv": [
        "account_id", "account_name", "industry", "country",
        "signup_date", "referral_source", "plan_tier", "seats",
        "is_trial", "churn_flag"
    ],
    "data/raw/ravenstack_subscriptions.csv": [
        "subscription_id", "account_id", "start_date", "end_date",
        "plan_tier", "seats", "mrr_amount", "arr_amount", "is_trial",
        "upgrade_flag", "downgrade_flag", "churn_flag",
        "billing_frequency", "auto_renew_flag"
    ],
    "data/raw/ravenstack_feature_usage.csv": [
        "usage_id", "subscription_id", "usage_date", "feature_name",
        "usage_count", "usage_duration_secs", "error_count", "is_beta_feature"
    ],
    "data/raw/ravenstack_support_tickets.csv": [
        "ticket_id", "account_id", "submitted_at", "closed_at",
        "resolution_time_hours", "priority", "first_response_time_minutes",
        "satisfaction_score", "escalation_flag"
    ],
    "data/raw/ravenstack_churn_events.csv": [
        "churn_event_id", "account_id", "churn_date", "reason_code",
        "refund_amount_usd", "preceding_upgrade_flag",
        "preceding_downgrade_flag", "is_reactivation", "feedback_text"
    ],
}

print("=== RAW CSVs ===")
for path, expected_cols in expected_schemas.items():
    if not os.path.exists(path):
        issues.append(f"MISSING: {path}")
        print(f"  MISSING  {path}")
        continue
    actual_cols = con.execute(f"SELECT * FROM read_csv_auto('{path}') LIMIT 0").df().columns.tolist()
    missing = [c for c in expected_cols if c not in actual_cols]
    extra = [c for c in actual_cols if c not in expected_cols]
    n = con.execute(f"SELECT COUNT(*) FROM read_csv_auto('{path}')").fetchone()[0]
    status = "OK" if not missing else "SCHEMA ERROR"
    print(f"  {status}  {path} ({n:,} rows)")
    if missing:
        issues.append(f"Missing columns in {path}: {missing}")
        print(f"    Missing cols: {missing}")
    if extra:
        print(f"    Extra cols (ok): {extra}")

# ── PARQUET LAYERS ─────────────────────────────────────────────
import glob

print("\n=== PARQUET LAYERS ===")
for layer in ["bronze", "silver", "gold"]:
    files = glob.glob(f"data/{layer}/*.parquet")
    print(f"  {layer}: {len(files)} file(s)")
    for f in files:
        n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{f}')").fetchone()[0]
        size = os.path.getsize(f)
        print(f"    {os.path.basename(f)}: {n:,} rows, {size:,} bytes")
    if not files:
        issues.append(f"No Parquets found in data/{layer}/")

# ── SUMMARY ───────────────────────────────────────────────────
print(f"\n=== SUMMARY ===")
if issues:
    print(f"  {len(issues)} issue(s) found:")
    for i in issues:
        print(f"    - {i}")
    print("\n  Run /run-pipeline to generate missing Parquets.")
else:
    print("  All checks passed. Data is ready.")
```

## Interpretando os resultados

| Status | Significado | Ação |
|--------|-------------|------|
| `OK` | CSV existe e tem todas as colunas esperadas | Nenhuma |
| `MISSING` | Arquivo não encontrado | Verificar `data/raw/` |
| `SCHEMA ERROR` | Colunas ausentes no CSV | Verificar fonte dos dados |
| Layer sem Parquets | Pipeline não foi executado | Rodar `/run-pipeline` |

## Verificação rápida (só existência)

```bash
ls -la data/raw/*.csv data/bronze/*.parquet data/silver/*.parquet data/gold/*.parquet 2>&1
```
