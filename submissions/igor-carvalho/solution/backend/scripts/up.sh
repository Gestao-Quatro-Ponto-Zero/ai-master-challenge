#!/usr/bin/env bash
# Sobe tudo: build (treina o modelo), cron diário e API. Uso: ./scripts/up.sh
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose up --build -d
echo "Aguardando a API..."
for i in $(seq 1 60); do
  curl -fsS http://localhost:8000/api/v1/health/ready >/dev/null 2>&1 && { echo "OK: http://localhost:8000/docs"; exit 0; }
  sleep 2
done
echo "A API não ficou pronta; veja: docker compose logs app" >&2; exit 1
