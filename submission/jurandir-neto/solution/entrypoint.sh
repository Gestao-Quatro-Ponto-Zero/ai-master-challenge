#!/bin/bash
set -e

# Roda o pipeline se os parquets gold ainda não existirem
if [ ! -f "data/gold/gold_dashboard_fact.parquet" ]; then
    echo "Rodando pipeline de dados..."
    uv run python pipeline/bronze/run_bronze.py
    uv run python pipeline/silver/run_silver.py
    uv run python pipeline/gold/run_gold.py
fi

# Sobe o dashboard
exec uv run streamlit run app/dashboard/main.py \
    --server.port=8501 \
    --server.address=0.0.0.0
