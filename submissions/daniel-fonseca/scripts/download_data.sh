#!/usr/bin/env bash
# Baixa os dois datasets do Challenge 002 (Kaggle, licença CC0) para data/raw/.
# O endpoint público de download do Kaggle não exige credencial para estes datasets.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RAW="$ROOT/data/raw"
mkdir -p "$RAW"
cd "$RAW"

fetch() { # slug destino
  curl -fsSL -o "$2.zip" "https://www.kaggle.com/api/v1/datasets/download/$1"
  mkdir -p "$2" && unzip -o -q "$2.zip" -d "$2" && rm "$2.zip"
}

fetch suraj520/customer-support-ticket-dataset ds1_customer_support
fetch adisongoh/it-service-ticket-classification-dataset ds2_it_tickets

ls -la ds1_customer_support ds2_it_tickets
