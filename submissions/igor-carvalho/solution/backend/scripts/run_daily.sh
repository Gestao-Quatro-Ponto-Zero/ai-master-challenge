#!/usr/bin/env bash
# Treino diário: lê os dados atuais de G4_DATA_DIR, treina, avalia e promove se passar no portão.
# Depois, se G4_API_URL estiver definido, manda a API recarregar o modelo ativo (POST /admin/refresh).
set -euo pipefail
cd "$(dirname "$0")/.."

# Lê só as variáveis necessárias do .env (sem "source", para não quebrar valores com [ ] e aspas).
envval() { [ -f .env ] && grep -E "^$1=" .env | tail -1 | cut -d= -f2- || true; }
for v in G4_DATA_DIR G4_ARTIFACT_DIR G4_DB_PATH G4_API_URL; do
  [ -z "${!v:-}" ] && [ -n "$(envval $v)" ] && export "$v=$(envval $v)"
done

mkdir -p var/logs
LOCK=var/train.lock
if ! mkdir "$LOCK" 2>/dev/null; then echo "$(date -Iseconds) treino já em execução; saindo" >&2; exit 0; fi
trap 'rmdir "$LOCK"' EXIT

PY=${PYTHON:-python3}; [ -x .venv/bin/python ] && PY=.venv/bin/python
LOG="var/logs/train-$(date +%F).log"
echo "=== $(date -Iseconds) início ===" >> "$LOG"
PYTHONPATH=src "$PY" -m lead_trainer train >> "$LOG" 2>&1
RESULT=$(tail -n 1 "$LOG")
echo "$(date -Iseconds) $RESULT" | tee -a var/logs/summary.log

if [ -n "${G4_API_URL:-}" ]; then
  TOKEN=$(curl -fsS -X POST "$G4_API_URL/api/v1/auth/login" -H 'Content-Type: application/json' \
          -d '{"user_key":"revops"}' | "$PY" -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
  curl -fsS -X POST "$G4_API_URL/api/v1/admin/refresh" -H "Authorization: Bearer $TOKEN" >> "$LOG" 2>&1 \
    && echo "$(date -Iseconds) API recarregada" | tee -a var/logs/summary.log
fi
