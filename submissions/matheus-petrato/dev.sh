#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${ROOT_DIR}/docker-compose.dev.yml"
ENV_FILE="${ROOT_DIR}/.env"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker nao encontrado. Instale o Docker Desktop ou engine."
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose nao encontrado. Instale o plugin docker-compose."
  exit 1
fi

if [ ! -f "${ENV_FILE}" ]; then
  echo "Arquivo .env nao encontrado em ${ROOT_DIR}."
  echo "Crie a partir do .env.example para padronizar as variaveis."
  exit 1
fi

echo "Subindo stack dev (backend + frontend + db)..."
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" up --build -d

echo "Aguardando frontend iniciar..."
docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" logs -f --tail=0 frontend
