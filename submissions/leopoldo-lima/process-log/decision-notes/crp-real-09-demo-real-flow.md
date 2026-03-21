# CRP-REAL-09 — Demo e evidências alinhadas ao fluxo real

**Data:** 2026-03-20  
**CRP:** CRP-REAL-09 (`legacy/focus-score-challenge-gap-closure-pack/crps/CRP-REAL-09-refresh-demo-and-evidence-on-real-flow.md`)

## O que mudou na demo

- `docs/DEMO_SCRIPT.md`: roteiro principal usa **dataset oficial** e IDs reais (ex. `1C1I7A6R`); **`OPP-001` removido** do trilho principal da API.
- Comando **`export-real-flow-evidence`** para gerar JSON reproduzíveis em `artifacts/process-log/test-runs/crp-real-09-*.json`.

## Por que substituir / atualizar evidências antigas

- Amostras com campo **`status`** em vez de **`deal_stage`** e sem campos explícitos (`account`, `product`, …) **não refletem** o contrato atual.
- `crp-real-01-sample-ranking-real.json` e `crp-real-02-detail-1C1I7A6R.json` são **regenerados** pelo mesmo script para manter consistência histórica + schema atual (ver `scripts/export_real_flow_evidence.py`).

## Screenshots

- Não foram anexados PNG binários neste passo (dependem de captura local).  
- Guia: `artifacts/process-log/ui-captures/REAL-09-SCREENSHOT-GUIDE.md`.

## Revisão humana

- Roteiro revisto para eliminar ambiguidade “demo JSON vs CSV real”.
- Exemplos de URL da API verificáveis contra exports JSON.

## Artefatos

- `docs/DEMO_SCRIPT.md`, `scripts/export_real_flow_evidence.py`, `scripts/tasks.py` (task `export-real-flow-evidence`)
- `artifacts/process-log/test-runs/crp-real-09-*.json` (+ refresh REAL-01/02)
- `artifacts/process-log/ui-captures/REAL-09-SCREENSHOT-GUIDE.md`
- `README.md`, `LOG.md`, `PROCESS_LOG.md`
