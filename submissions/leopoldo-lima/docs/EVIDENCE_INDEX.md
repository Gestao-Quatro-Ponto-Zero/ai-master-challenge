# Índice consolidado de evidências (CRP-DOC-03)

Legenda: **presente** | **faltante** (path reservado, sem arquivo)

## Processo e IA

| Item | Path | Estado |
|------|------|--------|
| Process log | [`PROCESS_LOG.md`](../process-log/PROCESS_LOG.md) | presente |
| Changelog operacional | [`LOG.md`](../process-log/LOG.md) | presente |
| Rastreabilidade IA | [`docs/IA_TRACE.md`](IA_TRACE.md) | presente |
| Estratégia submissão | [`docs/SUBMISSION_STRATEGY.md`](SUBMISSION_STRATEGY.md) | presente |

## Notas de decisão

| Área | Path | Estado |
|------|------|--------|
| Notas `process-log/decision-notes/` | `process-log/decision-notes/*.md` | presente (dezenas) |
| Inventário entrega | [`docs/DELIVERY_INVENTORY.md`](DELIVERY_INVENTORY.md) | presente |

## Screenshots (UI)

| Item | Path | Estado |
|------|------|--------|
| Combobox gestor (CBX-08) | `process-log/ui-captures/cbx-08/*.png` | presente |
| Guias REAL-09 / CBX-08 / UX | `process-log/ui-captures/*GUIDE.md` | presente |
| Capturas demo (geradas por Playwright em `solution/`) | `solution/artifacts/process-log/screen-recordings/demo-0*.png` | presente |
| Screenshots destacadas no README | `process-log/screenshots/*.png` | presente |

## Vídeo e gravação

| Item | Path | Estado |
|------|------|--------|
| Roteiro | [`docs/VIDEO_SCRIPT.md`](VIDEO_SCRIPT.md) | presente |
| Runbook Chromium | [`docs/VIDEO_RUNBOOK.md`](VIDEO_RUNBOOK.md) | presente |
| Script Playwright | [`scripts/record_demo_chromium.py`](../solution/scripts/record_demo_chromium.py) | presente |
| Gravação `.webm` | `process-log/screen-recordings/demo-cockpit.webm` | faltante no pacote curado (opcional; gerar com `solution/scripts/record_demo_chromium.py`) |

## Test runs (HTTP / dataset real)

| Item | Path | Estado |
|------|------|--------|
| Exports crp-real-09 | `process-log/test-runs/crp-real-09-*.json` | presente |
| Outros JSON | `process-log/test-runs/*.json` | presente |

## Chat exports

| Item | Path | Estado |
|------|------|--------|
| Exportações de conversas IA | `process-log/chat-exports/*.md` | presente |

## Git / commits

Histórico relevante na branch `main` (trilhas FIN, CBX-08, entrega DEL/DOC/SUB/VID). Sem tag de release obrigatória.

## README de submissão

| Item | Path | Estado |
|------|------|--------|
| README da submissão | [`README.md`](../README.md) | presente |
