#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
PY=.venv/bin/python
if [[ ! -x "$PY" ]]; then
  printf '%s\n' 'BLOQUEADO · ambiente .venv ausente. Siga as instruções de instalação.' >&2
  exit 2
fi
mode="${1:-}"
if [[ -n "$mode" && "$mode" != "--sem-dados" ]]; then
  printf '%s\n' 'Uso: bash scripts/validate.sh [--sem-dados]' >&2
  exit 2
fi
trap 'echo "FALHOU · veja a etapa e a saída acima" >&2' ERR
.venv/bin/ruff check src scripts tests app.py
.venv/bin/ruff format --check src scripts tests app.py
printf '%s\n' 'PASSOU · lint e formato'
"$PY" -m pip check
if [[ "$mode" == "--sem-dados" ]]; then
  "$PY" -m pytest -q -m 'not oficial'
  printf '%s\n' 'NÃO EXECUTADO · integração oficial e reconciliação foram excluídas explicitamente.'
  exit 0
fi
for f in data/raw/customer_support_tickets.csv data/raw/all_tickets_processed_improved_v3.csv artifacts/local/model.json artifacts/local/splits.csv artifacts/local/test-predictions.csv; do
  if [[ ! -f "$f" ]]; then
    printf 'BLOQUEADO · falta %s. Rode acquire, audit, train e evaluate.\n' "$f" >&2
    exit 2
  fi
done
"$PY" -m pytest -q
"$PY" scripts/reconcile.py
printf '%s\n' 'PASSOU · validação automatizada P0'
