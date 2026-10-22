#!/usr/bin/env bash
# Roda todo o pipeline em Python a partir da raiz do repositório.
# Pré-requisito: outputs/accounts_master.csv (gerado por sql/build_accounts_master.sql
# no PostgreSQL/Supabase; uma cópia já vem no repositório).
set -euo pipefail
cd "$(dirname "$0")"
python src/evidence.py                 # evidence.csv e at_risk_accounts.csv
python src/build_monthly_trend.py      # monthly_trend.csv
python src/feature_channel_analysis.py # feature_trends.csv e channel_churn_analysis.csv
python src/churn_model.py              # model_*.csv e model_scores_2025-01-01.csv
python src/cs_risk_tool.py             # cs_*.csv (fila da ferramenta de CS)
echo "Pronto: arquivos gerados em outputs/"
