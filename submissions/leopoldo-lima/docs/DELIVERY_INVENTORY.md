# Inventário final da entrega (CRP-DEL-01)

**Data:** 2026-03-21 · **Repositório:** Challenge 003 — Lead Scorer / Focus Score Cockpit

## Artefatos presentes (pacote de submissão)

| Item | Path / referência | Notas |
|------|-------------------|--------|
| Solução API + UI | `src/api/`, `public/` | FastAPI + cockpit estático |
| Dados oficiais | `data/*.csv` | Modo padrão `real_dataset` |
| Scoring configurável | `config/scoring-rules.json`, `src/scoring/` | v2 + narrativa no detalhe |
| README raiz (produto) | `README.md` | Narrativa técnica completa |
| Process log | `PROCESS_LOG.md`, `LOG.md` | Trilhas CRP incl. FIN |
| Evidências — notas | `artifacts/process-log/decision-notes/*.md` | Decisões auditáveis |
| Evidências — PNG | `artifacts/process-log/ui-captures/cbx-08/*.png` | Combobox gestor |
| Evidências — JSON test runs | `artifacts/process-log/test-runs/crp-real-09-*.json` | Fluxo real reproduzível |
| Guias de captura | `artifacts/process-log/ui-captures/*-GUIDE.md` | REAL-09, CBX-08, UX |
| Demo script | `docs/DEMO_SCRIPT.md` | Roteiro 3–5 min |
| Estratégia / checklist | `docs/SUBMISSION_STRATEGY.md`, `docs/CHALLENGE_CHECKLIST.md` | |
| IA trace | `docs/IA_TRACE.md` | Consolidado S07 |
| Runtime | `docs/RUNTIME_DEFAULTS.md`, `.env.example` | Default real explícito |
| Pacote FIN | `docs/SUBMISSION_PACKAGE.md`, `docs/FIN-11_AUDIT_CHECKLIST.md` | |
| Esqueleto submissão | `docs/README_SUBMISSION_SKELETON.md` | Base do template |

## Lacunas (antes da trilha DEL/DOC/SUB/VID)

| Lacuna | Responsável | CRP que fecha |
|--------|-------------|----------------|
| README **no template oficial** em `submissions/leopoldo-lima/README.md` | Autor | **CRP-DOC-01** |
| Notas de entrega + referência sóbria ao método | Autor | **CRP-DOC-02** |
| Índice único de evidências | Autor | **CRP-DOC-03** |
| Auditoria explícita ao submission guide | Autor | **CRP-SUB-01** |
| Auditoria template × README submissão | Autor | **CRP-SUB-02** |
| Handoff de PR | Autor | **CRP-SUB-03** |
| Roteiro de vídeo versionado | Autor | **CRP-VID-01** |
| Script + runbook Chromium | Autor | **CRP-VID-02** |
| Vídeo `.webm`/`.mp4` + screenshots-chave no repo | Autor | **CRP-VID-03** |
| `artifacts/process-log/screenshots/` (PNG demo geral) | Autor | Parcialmente **VID-03**; guia REAL-09 |
| `artifacts/process-log/chat-exports/` | Autor | Opcional; **faltante** se não exportar chats |

## Referência cruzada CRP → entrega

- **DEL-01** — este arquivo.  
- **DOC-01 … DOC-03** — documentação e índice.  
- **SUB-01 … SUB-03** — auditorias e PR.  
- **VID-01 … VID-03** — vídeo reproduzível em Chromium.

## Definition of Done (DEL-01)

- [x] Tabela presente / ausente publicada  
- [x] Gaps ligados a CRPs de fecho  
- [x] `LOG.md` e `PROCESS_LOG.md` atualizados  

## Estado após trilha DEL/DOC/SUB/VID (2026-03-21)

As lacunas listadas acima foram fechadas com: `submissions/leopoldo-lima/README.md`, `docs/DELIVERY_NOTES.md`, `docs/EVIDENCE_INDEX.md`, auditorias `SUBMISSION_*_AUDIT.md`, `docs/PR_HANDOFF.md`, roteiro e runbook de vídeo, `solution/scripts/record_demo_chromium.py`, e artefatos em `process-log/screen-recordings/` ou `solution/artifacts/process-log/screen-recordings/` quando gerados (`demo-cockpit.webm` + PNG). `chat-exports/` com exports em Markdown quando disponíveis.
