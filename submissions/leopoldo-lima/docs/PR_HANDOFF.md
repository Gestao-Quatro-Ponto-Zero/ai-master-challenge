# Handoff — Pull Request final (CRP-SUB-03)

**Data:** 2026-03-21 · **Branch sugerida:** `main` (ou `feature/challenge-003-delivery` se preferir histórico isolado).

## Objetivo do PR

Integrar a **trilha de entrega** (DEL/DOC/SUB/VID): narrativa em [`README.md`](../README.md), documentação em `docs/`, script de vídeo Chromium em `solution/scripts/` e evidências em `process-log/` (e espelho técnico em `solution/artifacts/process-log/`).

## O que o revisor deve abrir primeiro

1. [`README.md`](../README.md) na pasta do candidato — narrativa alinhada ao template oficial do challenge.
2. [`PROCESS_LOG.md`](../process-log/PROCESS_LOG.md) — últimas entradas CRP-DEL / DOC / SUB / VID.
3. [`docs/EVIDENCE_INDEX.md`](EVIDENCE_INDEX.md) — mapa de evidências.

## Comandos de verificação (local)

```text
cd solution
python scripts/tasks.py install
python -m pytest -q
python scripts/tasks.py dev
```

Opcional (vídeo / capturas): ver [`docs/VIDEO_RUNBOOK.md`](VIDEO_RUNBOOK.md).

## Arquivos novos ou centrais nesta entrega (pacote `submissions/leopoldo-lima/`)

- `README.md` (raiz da submissão)
- `docs/DELIVERY_INVENTORY.md`, `docs/DELIVERY_NOTES.md`, `docs/EVIDENCE_INDEX.md`
- `docs/SUBMISSION_GUIDE_AUDIT.md`, `docs/SUBMISSION_TEMPLATE_AUDIT.md`
- `docs/VIDEO_SCRIPT.md`, `docs/VIDEO_RUNBOOK.md`
- `solution/scripts/record_demo_chromium.py`
- `process-log/` (PROCESS_LOG, chat-exports, decision-notes, test-runs, CRPs executados)
- _(Opcional / fora do pacote curado)_ packs metodológicos adicionais no repositório de trabalho
- _(Se gerados)_ `process-log/screen-recordings/` (`demo-cockpit.webm`, PNG `demo-01`…`demo-07`)

## Notas

- Não incluir em PR arquivos acidentais na raiz (`concat_repo_all_text.py`, notas pessoais) se não forem parte da submissão.
- Confirmar que `data/*.csv` segue a política do challenge (dataset oficial, sem dados sensíveis extra).

## Definition of Done (handoff)

- [ ] Diff revisto humanamente.
- [ ] `pytest` verde localmente.
- [ ] PR aberto na plataforma do desafio com descrição que referencia [`README.md`](../README.md) (raiz de `submissions/leopoldo-lima/`).
