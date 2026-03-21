#!/usr/bin/env bash
# Deploy um app do monorepo para o service correspondente no Railway.
# Uso: ./scripts/railway-deploy-service.sh <portal|churn-dashboard|lead-scorer|social-dashboard|support-triage>
# Pré-requisito: railway link -p <project-id> já feito neste diretório.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ $# -lt 1 ]]; then
  echo "Uso: $0 <portal|churn-dashboard|lead-scorer|social-dashboard|support-triage> [-- flags extras para railway up]" >&2
  exit 1
fi

APP="$1"
shift

case "$APP" in
  portal)
    SERVICE_NAME="g4-ai-master"
    TOML="apps/portal/railway.toml"
    ;;
  churn-dashboard|lead-scorer|social-dashboard|support-triage)
    SERVICE_NAME="$APP"
    TOML="apps/${APP}/railway.toml"
    ;;
  *)
    echo "App desconhecido: $APP" >&2
    exit 1
    ;;
esac

if [[ ! -f "$TOML" ]]; then
  echo "Arquivo não encontrado: $TOML" >&2
  exit 1
fi

# Preserva o railway.toml mínimo na raiz (força Docker no Git) após o deploy
if [[ -f railway.toml ]]; then
  cp railway.toml railway.toml.bak.minimal
fi
cp "$TOML" railway.toml
echo "→ railway.toml ← $TOML"
echo "→ railway service $SERVICE_NAME"
railway service "$SERVICE_NAME"
# Garantir que data/ dos apps não fique excluída pelo .gitignore (ver .gitignore na raiz).
if [[ $# -eq 0 ]]; then
  set -- -c
fi

echo "→ railway up $*"
railway up "$@"

if [[ -f railway.toml.bak.minimal ]]; then
  mv railway.toml.bak.minimal railway.toml
  echo "→ railway.toml restaurado (config mínima na raiz)"
fi
