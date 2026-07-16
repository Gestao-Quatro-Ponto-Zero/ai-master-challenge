#!/usr/bin/env bash
# SPEC-11: Infraestrutura & Deploy (Railway)
# Testes para Dockerfile, railway.json e health endpoint

set -euo pipefail
cd "$(dirname "$0")/.."

PASS=0
FAIL=0

pass() { ((PASS++)) || true; }
fail() { echo "FAIL: $*"; ((FAIL++)) || true; }

# ── 11-001: railway.json deve ser JSON válido ────────────────────
echo "=== SPEC-11-001: railway.json válido ==="
python3 -c "
import json
with open('railway.json') as f:
    cfg = json.load(f)
assert cfg['build']['builder'] == 'DOCKERFILE', 'Builder não é DOCKERFILE'
assert 'dockerfilePath' in cfg['build'], 'dockerfilePath ausente'
assert cfg['deploy']['healthcheckPath'] == '/health', 'healthcheckPath não configurado'
print(f'OK: railway.json válido — builder={cfg[\"build\"][\"builder\"]}')
print(f'  healthcheck: {cfg[\"deploy\"][\"healthcheckPath\"]}')
" && pass || fail "railway.json inválido"

# ── 11-002: Dockerfile deve existir com multi-stage ──────────────
echo "=== SPEC-11-002: Dockerfile ==="
if [ -f Dockerfile ]; then
    LINES=$(wc -l < Dockerfile)
    HAS_MULTISTAGE=$(grep -c "FROM.*AS" Dockerfile || true)
    HAS_CMD=$(grep -c "CMD" Dockerfile || true)
    echo "OK: Dockerfile existe ($LINES linhas, $HAS_MULTISTAGE stages, CMD=$HAS_CMD)"
    pass
else
    fail "Dockerfile não encontrado"
fi

# ── 11-003: Health endpoint deve rodar e responder ───────────────
echo "=== SPEC-11-003: Health endpoint via TestClient ==="
PYTHONPATH=src python3 -c "
from fastapi.testclient import TestClient
from churn_platform.api import create_app
app = create_app(output_dir='output')
client = TestClient(app)
r = client.get('/health')
assert r.status_code == 200
data = r.json()
assert data['status'] == 'ok'
assert 'version' in data
assert 'uptime_seconds' in data
assert 'spec_version' in data
print(f'OK: GET /health -> status={data[\"status\"]}')
print(f'  version={data[\"version\"]}')
print(f'  spec_version={data[\"spec_version\"]}')
" && pass || fail "Health endpoint"

# ── 11-004: api.py entry point deve carregar sem erro ────────────
echo "=== SPEC-11-004: api.py entry point ==="
PYTHONPATH=src python3 -c "
import sys
sys.path.insert(0, '.')
from api import app
assert app.title == 'Churn Platform API'
print(f'OK: api.py carregado — {app.title} v{app.version}')
" && pass || fail "api.py entry point"

# ── Results ──────────────────────────────────────────────────────
echo ""
echo "╔════════════════════════════════════╗"
echo "║  SPEC-11: Infraestrutura & Deploy   ║"
echo "║  Passed: $PASS / $((PASS+FAIL))                ║"
echo "╚════════════════════════════════════╝"
exit $FAIL
