#!/bin/bash
# Atualiza a VM com o último commit do branch e reconstrói. Rode na VM:  sudo bash update.sh
set -euo pipefail
cd "$(dirname "$0")"
git -C /opt/g4 pull --ff-only
docker compose -f docker-compose.prod.yml up -d --build
docker image prune -f
