#!/usr/bin/env bash
# Define OPENROUTER_API_KEY nos 4 dashboards e URLs do Portal via ${{ service.RAILWAY_PUBLIC_DOMAIN }}.
# Pré-requisito: `railway link` neste diretório (solution/) apontando para o projeto Railway.
#
# Uso (recomendado — não deixa a key no histórico do shell):
#   export OPENROUTER_API_KEY='sk-or-v1-...'
#   ./scripts/railway-set-prod-vars.sh
#
# Ou em uma linha:
#   OPENROUTER_API_KEY='sk-or-v1-...' ./scripts/railway-set-prod-vars.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

KEY="${OPENROUTER_API_KEY:-}"
if [[ -z "$KEY" && -n "${1:-}" ]]; then
  KEY="$1"
fi
if [[ -z "$KEY" ]]; then
  echo "Defina OPENROUTER_API_KEY ou passe a key como primeiro argumento." >&2
  exit 1
fi

PORTAL_SERVICE="${PORTAL_SERVICE_NAME:-g4-ai-master}"

for svc in churn-dashboard lead-scorer social-dashboard support-triage; do
  echo "→ OPENROUTER_API_KEY em ${svc}"
  railway variable set -s "$svc" "OPENROUTER_API_KEY=${KEY}"
done

echo "→ Portal (${PORTAL_SERVICE}): URLs com template Railway (outros services)"
railway variable set -s "$PORTAL_SERVICE" \
  'URL_CHURN=https://${{churn-dashboard.RAILWAY_PUBLIC_DOMAIN}}' \
  'URL_LEAD_SCORER=https://${{lead-scorer.RAILWAY_PUBLIC_DOMAIN}}' \
  'URL_SOCIAL=https://${{social-dashboard.RAILWAY_PUBLIC_DOMAIN}}' \
  'URL_SUPPORT=https://${{support-triage.RAILWAY_PUBLIC_DOMAIN}}'

echo "Pronto. O Railway pode disparar redeploy dos services afetados."
