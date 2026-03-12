#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${ROOT_DIR}/docker-compose.dev.yml"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker nao encontrado. Instale o Docker Desktop ou engine."
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose nao encontrado. Instale o plugin docker-compose."
  exit 1
fi

echo "Subindo stack dev (backend + frontend + db)..."
docker compose -f "${COMPOSE_FILE}" up --build
