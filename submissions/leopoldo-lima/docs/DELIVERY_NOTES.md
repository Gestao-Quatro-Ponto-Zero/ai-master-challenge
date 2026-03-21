# Notas de entrega (CRP-DOC-02)

## O que está a ser entregue

Solução **Focus Score Cockpit** para o Challenge 003 — Lead Scorer: API + UI + scoring explicável sobre o dataset oficial em `data/`, com testes, documentação e process log auditável.

## Como correr

1. `python scripts/tasks.py install`
2. `python scripts/tasks.py dev` → `http://127.0.0.1:8787/`
3. Detalhe em [`docs/SETUP.md`](SETUP.md) e [`README.md`](../README.md).

## Como validar

- `python -m pytest -q`
- Opcional: `python scripts/tasks.py build`
- Demo: [`docs/DEMO_SCRIPT.md`](DEMO_SCRIPT.md)
- Vídeo reproduzível: [`docs/VIDEO_RUNBOOK.md`](VIDEO_RUNBOOK.md) + `scripts/record_demo_chromium.py`

## Evidências que acompanham a submissão

- [`docs/EVIDENCE_INDEX.md`](EVIDENCE_INDEX.md)
- [`PROCESS_LOG.md`](../process-log/PROCESS_LOG.md)
- `artifacts/process-log/` (notas, PNG, JSON, gravações)

## Método de trabalho e *Vibecoding Industrial*

A execução seguiu **disciplina de artefactos** (CRPs, process log, evidências versionadas, commits pequenos), inspirada na ideia de engenharia com IA **estruturada e auditável** descrita na obra **Vibecoding Industrial** — útil como referência de método, sem substituir o critério humano nem o guia oficial do challenge.

Referência editorial (catálogo; confirme a edição na sua região):  
[Vibecoding Industrial — pesquisa na Amazon](https://www.amazon.com/s?k=Vibecoding+Industrial)

Não é endosso comercial: o repositório permanece avaliado pelos critérios técnicos do desafio e pelo conteúdo verificável dos arquivos.
