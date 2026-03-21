# Submissão — Challenge 003 · Lead Scorer

**Arquivo histórico:** cópia da narrativa que existia em `submission/README.md` no repositório de trabalho. **Canónico para o PR:** [`../../README.md`](../../README.md) (raiz de `submissions/leopoldo-lima/`).

---

## Sobre mim

Participante na competição **Challenge 003 — Lead Scorer**. Entrega desenvolvida com apoio de ferramentas de IA (Cursor) e revisão humana contínua; detalhes de prompts e correções em [`PROCESS_LOG.md`](../../process-log/PROCESS_LOG.md) e [`docs/IA_TRACE.md`](../IA_TRACE.md).

---

## Executive Summary

- **Desafio:** 003 — Lead Scorer (priorização comercial com explicabilidade).
- **O que foi entregue:** **Focus Score Cockpit** — API FastAPI sobre os CSVs oficiais em `solution/data/`, motor de scoring v2 configurável, UI cockpit com ranking, filtros (incl. combobox de gestor), KPIs e painel de detalhe com explicações em linguagem comercial.
- **Diferencial auditável:** contratos documentados (`docs/API_CONTRACT_UI.md`, etc.), suíte `pytest`, `PROCESS_LOG.md` com trilhas CRP (incl. FIN e entrega), evidências em `process-log/` (JSON; PNG/vídeo se gerados).
- **Processo:** decisões, ferramentas de IA e evidências rastreáveis em [`process-log/`](../../process-log/).

---

## Solução

- **Backend:** `solution/src/api/app.py` — listagem `/api/opportunities`, detalhe, KPIs, `filter-options`, métricas e health.
- **Dados:** pipeline em `solution/src/serving/` a partir de `solution/data/*.csv`; modo padrão **`real_dataset`** (ver [`docs/RUNTIME_DEFAULTS.md`](../RUNTIME_DEFAULTS.md)).
- **Scoring:** `solution/config/scoring-rules.json` + `solution/src/scoring/engine.py`; explicações humanizadas na API de detalhe via [`solution/src/api/explanation_narrative.py`](../../solution/src/api/explanation_narrative.py).
- **Frontend:** `solution/public/` — cockpit servido em `/` e assets em `/ui/` (sem migração de stack).

---

## Abordagem

- **Arquitetura:** CSVs → serving → features → scoring → API → UI estática.
- **Método:** execução por CRPs com registo no process log; ADRs em `docs/ADR/`.
- **Uso de IA:** assistência à implementação e documentação; o detalhe de prompts, erros e julgamento humano **não** substitui o [`PROCESS_LOG.md`](../../process-log/PROCESS_LOG.md).

---

## Resultados / Findings

- **Como executar:** [`docs/SETUP.md`](../SETUP.md); `python solution/scripts/tasks.py install` → `build` → `dev` (porta padrão 8787).
- **O que foi validado:** `python -m pytest -q`; gates em `solution/scripts/tasks.py build`; fluxo real descrito em [`docs/TEST_STRATEGY_REAL_DATA.md`](../TEST_STRATEGY_REAL_DATA.md).
- **Demonstração:** [`docs/DEMO_SCRIPT.md`](../DEMO_SCRIPT.md); vídeo Chromium [`demo-cockpit.webm`](../../process-log/screen-recordings/demo-cockpit.webm); runbook [`docs/VIDEO_RUNBOOK.md`](../VIDEO_RUNBOOK.md); capturas `demo-01`…`demo-07` em [`screen-recordings/`](../../process-log/screen-recordings/).

---

## Recomendações

- Métricas persistentes (Prometheus) e E2E browser na CI.
- Calibração de pesos com dados de outcome (fora do escopo atual).

---

## Limitações

- UI propositadamente enxuta; score heurístico, não modelo supervisionado em produção.
- Docker e métricas dependem do ambiente local; ver [`README.md`](../../README.md) raiz.

---

## Ferramentas usadas

- Python 3.11+, FastAPI, Uvicorn, pytest, ruff, mypy.
- Cursor (agente IA) para iterações de código e docs.
- Playwright (Chromium) para capturas automatizadas e gravação de demo (ver runbook).

---

## Workflow

1. Carregar dependências e dados em `solution/data/`.
2. Subir API/UI (`solution/scripts/tasks.py dev` a partir de `solution/`).
3. Validar com pytest e, opcionalmente, `solution/scripts/record_demo_chromium.py` para evidência visual.

---

## Onde a IA errou e como corrigi

Exemplos consolidados em [`docs/IA_TRACE.md`](../IA_TRACE.md) — p.ex. ajustes de contrato de dados, gates de UI sem TypeScript, alinhamento de URLs em testes HTTP. O detalhe por CRP está no [`PROCESS_LOG.md`](../../process-log/PROCESS_LOG.md).

---

## O que eu adicionei que a IA sozinha não faria

- Julgamento sobre o que documentar como **parcial** vs **ok** no checklist do desafio.
- Recalibração de scoring para priorizar pipeline aberto (trilha FIN) com trade-offs explícitos.
- Arquivamento de packs metodológicos em `legacy/` para clareza da submissão.

---

## Process Log — Como usei IA

- arquivo canónico: [`PROCESS_LOG.md`](../../process-log/PROCESS_LOG.md).
- Resumo tabular: [`docs/IA_TRACE.md`](../IA_TRACE.md).
- Notas de decisão: [`process-log/decision-notes/`](../../process-log/decision-notes/).

---

## Evidências

- [`PROCESS_LOG.md`](../../process-log/PROCESS_LOG.md) e pasta [`process-log/`](../../process-log/)
- Inventário de entrega: [`docs/DELIVERY_INVENTORY.md`](../DELIVERY_INVENTORY.md)
- Notas de entrega: [`docs/DELIVERY_NOTES.md`](../DELIVERY_NOTES.md)
- Índice consolidado de evidências: [`docs/EVIDENCE_INDEX.md`](../EVIDENCE_INDEX.md)

---

## Submissão via PR

As alterações da entrega devem integrar-se via **Pull Request** na plataforma do desafio. Passos, comandos de verificação e lista de arquivos: [`docs/PR_HANDOFF.md`](../PR_HANDOFF.md).

---

## Checklist (template)

- [x] Secções obrigatórias presentes neste README.
- [x] `PROCESS_LOG.md` referenciado.
- [x] Comandos verificáveis em `docs/SETUP.md`.
- [ ] Substituir «Sobre mim» com nome/contato se o guia do challenge exigir identificação explícita no PR.
- [x] Secção «Submissão via PR» com link ao handoff (`docs/PR_HANDOFF.md`).
