#!/bin/sh
set -e
cd /app
mkdir -p var/logs
# O cron não herda o ambiente: grava o que o run_daily.sh precisa.
printf 'G4_DATA_DIR=%s\nG4_ARTIFACT_DIR=%s\nG4_DB_PATH=%s\nG4_API_URL=http://localhost:8000\n' \
  "$G4_DATA_DIR" "$G4_ARTIFACT_DIR" "$G4_DB_PATH" > /app/.env
# Se o volume veio vazio por algum motivo, treina antes de subir.
[ -f "$G4_ARTIFACT_DIR/CURRENT" ] || python -m lead_trainer train
cron
exec python -m lead_api --host 0.0.0.0 --port 8000
