#!/usr/bin/env bash
# Diagnóstico de churn RavenStack — um comando, do download ao dashboard validado.
#
#   rodar.sh                 baixa os dados (se faltarem), analisa, gera e valida o dashboard
#   rodar.sh --atualizar     baixa de novo do Kaggle (o dataset é atualizado mensalmente)
#   rodar.sh --sem-validar   pula a validação no navegador
#   rodar.sh --servir        no fim, deixa o dashboard no ar em 0.0.0.0:5180
#
# Pasta da submissão: detectada a partir desta skill, ou CHURN_ROOT=/caminho.
set -euo pipefail

ATUALIZAR=0; VALIDAR=1; SERVIR=0
for a in "$@"; do
  case "$a" in
    --atualizar) ATUALIZAR=1 ;;
    --sem-validar) VALIDAR=0 ;;
    --servir) SERVIR=1 ;;
    -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
    *) echo "opção desconhecida: $a" >&2; exit 2 ;;
  esac
done

AQUI="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
ROOT="${CHURN_ROOT:-$(cd "$AQUI/../../.." && pwd)}"
SCR="$ROOT/solution/scripts"; OUT="$ROOT/solution/outputs"; DOCS="$ROOT/docs"; RAW="$ROOT/data/raw"; DASH="$ROOT/solution/dashboard"
PY="uv run --quiet --with pandas,scipy,statsmodels,matplotlib python -I"
etapa() { printf '\n\033[1m▸ %s\033[0m\n' "$*"; }

etapa "0/6 Ambiente"
for c in uv node npm; do command -v "$c" >/dev/null || { echo "falta '$c' no PATH" >&2; exit 1; }; done
[ -d "$SCR" ] || { echo "não achei $SCR — defina CHURN_ROOT" >&2; exit 1; }
echo "pasta: $ROOT"

etapa "1/6 Dados (Kaggle)"
if [ "$ATUALIZAR" = 1 ] || [ ! -f "$RAW/ravenstack_accounts.csv" ]; then
  [ -f "$HOME/.kaggle/access_token" ] || [ -n "${KAGGLE_API_TOKEN:-}" ] || { echo "sem token do Kaggle (~/.kaggle/access_token ou KAGGLE_API_TOKEN)" >&2; exit 1; }
  "$SCR/00_download.sh"
else
  echo "usando dados já baixados em $RAW (use --atualizar para baixar de novo)"
fi

etapa "2/6 Ligar as 5 tabelas e auditar (01)"
$PY "$SCR/01_build_dataset.py" "$RAW" "$OUT" "$DOCS" | head -1

etapa "3/6 Correlações por categoria e por assinatura (02, 03)"
$PY "$SCR/02_correlacoes.py" "$OUT" "$DOCS" > /dev/null
$PY "$SCR/03_correlacoes_assinatura.py" "$OUT" "$DOCS" > /dev/null
echo "ok"

etapa "4/6 Séries, safras, base × mês × uso, previsão, receita (04–08)"
$PY "$SCR/04_export_dashboard.py" "$RAW" "$OUT" "$DASH/src/data.json" | head -1
$PY "$SCR/05_teste_safras.py" "$RAW" > "$OUT/teste_safras.txt"
$PY "$SCR/06_cancelamentos_mes_uso.py" "$RAW" "$OUT" "$DASH/src/mes_uso.json" > "$OUT/cancelamentos_mes_uso.txt" 2>/dev/null
$PY "$SCR/07_sugestoes_previsao.py" "$RAW" "$OUT" "$DASH/src/sugestoes.json" | head -1
$PY "$SCR/08_auditoria_mrr.py" "$RAW" "$DASH/src/mrr.json" "$DOCS" > "$OUT/auditoria_mrr.txt"

etapa "5/6 Dashboard (build)"
cd "$DASH"
[ -d node_modules ] || npm ci --no-audit --no-fund
npm run build --silent 2>&1 | grep -E "built in|error" || true

if [ "$VALIDAR" = 1 ]; then
  etapa "6/6 Validação no navegador (Playwright)"
  npx vite preview --host 127.0.0.1 --port 4173 --strictPort > /tmp/churn-preview.log 2>&1 &
  PID=$!; trap 'kill $PID 2>/dev/null || true' EXIT
  for _ in $(seq 1 30); do curl -sf http://127.0.0.1:4173/ >/dev/null && break; sleep 0.5; done
  node scripts/validar.mjs "http://127.0.0.1:4173/" "$OUT/validacao"
  kill $PID 2>/dev/null || true; trap - EXIT
else
  etapa "6/6 Validação pulada (--sem-validar)"
fi

etapa "Resumo"
$PY "$AQUI/resumo.py" "$DASH/src"

if [ "$SERVIR" = 1 ]; then
  etapa "Dashboard no ar"
  echo "http://$(hostname -f 2>/dev/null || hostname):5180  (Ctrl+C para parar)"
  exec npx vite --host 0.0.0.0 --port 5180
fi
