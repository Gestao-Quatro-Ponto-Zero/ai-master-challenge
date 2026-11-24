#!/usr/bin/env bash
# Baixa o dataset RavenStack (River @ Rivalytics, Kaggle) para submissions/.../data/raw.
# Requer o token do Kaggle em ~/.kaggle/access_token ou KAGGLE_API_TOKEN.
set -euo pipefail
DIR="$(cd "$(dirname "$0")/../.." && pwd)/data/raw"
mkdir -p "$DIR"
uvx --with six kaggle datasets download -d rivalytics/saas-subscription-and-churn-analytics-dataset -p "$DIR" --unzip
ls -l "$DIR"
