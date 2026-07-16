#!/usr/bin/env bash
# SPEC-10: Dashboard, API e Visualização
# Testes para REST API layer e geração de relatório

set -euo pipefail
cd "$(dirname "$0")/.."

PASS=0
FAIL=0

pass() { ((PASS++)) || true; }
fail() { echo "FAIL: $*"; ((FAIL++)) || true; }

# ── 10-001: API deve iniciar e responder /health ──────────────────
echo "=== SPEC-10-001: Health endpoint ==="
PYTHONPATH=src python3 -c "
from fastapi.testclient import TestClient
from churn_platform.api import create_app
app = create_app(output_dir='output')
client = TestClient(app)
r = client.get('/health')
assert r.status_code == 200, f'Status {r.status_code}'
data = r.json()
assert data['status'] == 'ok', f'Status not ok: {data}'
print('OK: /health responde 200 com status ok')
print(f'  versão: {data[\"version\"]}')
print(f'  uptime: {data[\"uptime_seconds\"]}s')
" && pass || fail "API health endpoint"

# ── 10-002: POST /api/v1/run deve executar pipeline ──────────────
echo "=== SPEC-10-002: POST /api/v1/run ==="
PYTHONPATH=src python3 -c "
from fastapi.testclient import TestClient
from churn_platform.api import create_app
app = create_app(output_dir='output')
client = TestClient(app)
r = client.post('/api/v1/run', params={'config_path': 'config/ravenstack.yaml'})
assert r.status_code == 200, f'Status {r.status_code}: {r.text}'
data = r.json()
assert data['status'] == 'completed', f'Status not completed: {data}'
assert 'run_id' in data, f'No run_id: {data}'
assert 'overall_stats' in data.get('results', {}), f'No stats: {data}'
print(f'OK: Pipeline executado — run_id={data[\"run_id\"]}')
print(f'  contas: {data[\"results\"][\"overall_stats\"][\"total_accounts\"]}')
print(f'  churn_rate: {data[\"results\"][\"overall_stats\"][\"churn_rate\"]:.1%}')
" && pass || fail "POST /api/v1/run"

# ── 10-003: GET /api/v1/runs deve listar execuções ───────────────
echo "=== SPEC-10-003: GET /api/v1/runs ==="
PYTHONPATH=src python3 -c "
from fastapi.testclient import TestClient
from churn_platform.api import create_app
app = create_app(output_dir='output')
client = TestClient(app)
client.post('/api/v1/run', params={'config_path': 'config/ravenstack.yaml'})
r = client.get('/api/v1/runs')
assert r.status_code == 200
data = r.json()
assert len(data['runs']) > 0, f'Nenhum run encontrado'
print(f'OK: {len(data[\"runs\"])} runs listados')
" && pass || fail "GET /api/v1/runs"

# ── 10-004: GET /api/v1/accounts/risk deve retornar contas ──────
echo "=== SPEC-10-004: GET /api/v1/accounts/risk ==="
PYTHONPATH=src python3 -c "
from fastapi.testclient import TestClient
from churn_platform.api import create_app
app = create_app(output_dir='output')
client = TestClient(app)
client.post('/api/v1/run', params={'config_path': 'config/ravenstack.yaml'})
r = client.get('/api/v1/accounts/risk?limit=5&llm_explain=false')
assert r.status_code == 200, f'Status {r.status_code}: {r.text}'
data = r.json()
assert 'accounts' in data, f'No accounts: {data}'
assert len(data['accounts']) > 0, f'No accounts returned'
print(f'OK: {len(data[\"accounts\"])} contas retornadas')
for a in data['accounts'][:2]:
    print(f'  {a[\"account_id\"]}: {a[\"health_score\"]} — {a[\"health_tier\"]}')
" && pass || fail "GET /api/v1/accounts/risk"

# ── 10-005: Relatório HTML deve ser gerado ───────────────────────
echo "=== SPEC-10-005: Relatório HTML ==="
PYTHONPATH=src python3 -c "
import pandas as pd
import json
from churn_platform.analysis import descriptive, segmentation
from churn_platform.datamodel import account_view as dv
from churn_platform.pipeline import loader, cleaner, merger, validator
from churn_platform.scoring import health_score
from churn_platform.report import html_report
import yaml

with open('config/ravenstack.yaml') as f:
    cfg = yaml.safe_load(f)
sources = loader.load_all_sources(cfg, '.')
sources = cleaner.run(sources)
with open('config/schemas/ravenstack_schema.yaml') as f:
    schemas = yaml.safe_load(f)
dqr = validator.run(sources, schemas, 'output')
merged = merger.run(sources, cfg.get('merges', {}))
df = dv.build(sources, merged)
stats = descriptive.overall_stats(df)
seg_results = segmentation.run(df, cfg)
desc_results = descriptive.run(df, cfg)
scored = health_score.run(df, cfg)
path = html_report.build_report(df, stats, seg_results, desc_results, scored, 'output/test_report.html')
with open(path) as f:
    content = f.read()
assert '<!DOCTYPE html>' in content, 'HTML tag não encontrada'
assert 'Diagnóstico de Churn' in content, 'Título não encontrado'
assert 'plotly' in content.lower() or 'chart-' in content, 'Charts não encontrados'
import os
os.remove(path)
print(f'OK: Relatório HTML gerado corretamente')
" && pass || fail "Relatório HTML"

# ── Results ──────────────────────────────────────────────────────
echo ""
echo "╔════════════════════════════════════╗"
echo "║  SPEC-10: API e Visualização       ║"
echo "║  Passed: $PASS / $((PASS+FAIL))                ║"
echo "╚════════════════════════════════════╝"
exit $FAIL
