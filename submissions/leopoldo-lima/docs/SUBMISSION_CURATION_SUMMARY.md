# Resumo de curadoria — submissão `leopoldo-lima`

**Data:** 2026-03-21  
**Origem:** `C:\Projetos\build-003-lead-scorer`  
**Destino:** `C:\Projetos\ai-master-challenge\submissions\leopoldo-lima\`

## O que foi copiado (por grupo)

| Grupo | Destino | Origem no projeto-fonte |
|-------|---------|-------------------------|
| Código Python e pacotes | `solution/src/` | `src/` |
| Frontend | `solution/public/` | `public/` |
| Dados | `solution/data/` | `data/` |
| Configuração | `solution/config/`, `contracts/` | `config/`, `contracts/` |
| Scripts e automação | `solution/scripts/` | `scripts/` |
| Testes | `solution/tests/` | `tests/` |
| Artefatos técnicos | `solution/artifacts/` | `artifacts/` (sem caches) |
| CI | `solution/.github/` | `.github/` |
| Container | `solution/Dockerfile`, `docker-compose.yml`, `.dockerignore` | raiz |
| Dependências / ambiente | `pyproject.toml`, `requirements-audit.txt`, `.env.example`, `.gitignore`, `.pre-commit-config.yaml` | raiz |
| Documentação | `docs/` | `docs/` (todos os `.md` e `ADR/`) |
| Process log principal | `process-log/PROCESS_LOG.md`, `LOG.md` | raiz |
| Evidências process log | `process-log/*` (exceto arquivos já na raiz) | `artifacts/process-log/` |
| Exports de chat | `process-log/chat-exports/` | `export-conversa-focus-score.md`, `cursor_crp_000_prompt_file_discussion.md` na raiz |
| Índice CRP | `process-log/indexes/crp-index.csv` | `indexes/crp-index.csv` |
| CRPs executados | `process-log/crps/` | `crps/` |
| Legado interno da pasta `submission/` (repo de trabalho) | [`docs/archive/README_LEGACY_SUBMISSION_FOLDER.md`](archive/README_LEGACY_SUBMISSION_FOLDER.md) | `submission/README.md` (histórico) |

## Duplicidade (estado após faxina 2026-03-21)

- **`docs/`**, **`process-log/`** e **`process-log/crps/`** existem **só** ao lado de `solution/` (sem cópias dentro de `solution/`).
- **`solution/scripts/tasks.py`** usa `SUBMISSION_ROOT = ROOT.parent` para validar `docs/`, `process-log/PROCESS_LOG.md` e `process-log/crps/executed` no smoke `test`.
- **`solution/artifacts/process-log/`** mantém apenas `.gitkeep`, `README.md` e saídas **geradas localmente** por scripts; evidências entregues no PR ficam em **`process-log/`**.

## O que foi excluído de propósito

| Excluído | Motivo |
|----------|--------|
| `.git/`, `.git` | Proibido / irrelevante na submissão |
| `node_modules/`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/` | Ruído e caches |
| `*.zip` | Proibido |
| `legacy/` | Pacotes metodológicos e legado explicitamente fora do runtime (README do projeto-fonte) |
| `archive/` | Material superseded / listas planas antigas de CRP |
| `submission/` (pasta no repo de trabalho) | Substituído por `submissions/leopoldo-lima/README.md` + legado em [`docs/archive/`](archive/README.md) |
| `00-START-HERE.md`, `01-ROADMAP.md`, `concat_repo_all_text.py`, `repo_concat_all.md` | Ferramentas ou dumps internos, pouco úteis ao avaliador |
| Raiz `README.md` do projeto-fonte | Narrativa incorporada no `README.md` desta pasta + documentos em `docs/` |
| `indexes/` na raiz da submissão | Só o CSV foi copiado para `process-log/indexes/` |

## Ajustes feitos após a cópia

- Links relativos em vários `docs/*.md` (paths para `process-log/`, `solution/scripts/`, etc.).
- `docs/SETUP.md`: nota para executar a partir de `solution/`.
- `process-log/README.md`, `process-log/crps/README.md`, `process-log/decision-notes/video-script.md`: caminhos alinhados ao layout da submissão.
- `docs/EVIDENCE_INDEX.md`, `docs/PR_HANDOFF.md`, `docs/IA_TRACE.md`: coerência com pastas reais; legado movido para `docs/archive/`.
- Remoção de `__pycache__/` e `*.egg-info` gerados localmente após testes (respeitando `.gitignore`).

## Pendências / verificações sugeridas

1. **Título do PR:** formato `[Submission] Leopoldo Lima — Challenge 003` (ver `CONTRIBUTING.md` na raiz do repositório `ai-master-challenge`).
2. **Evidências binárias:** confirmar `process-log/screen-recordings/` e `process-log/ui-captures/`; regenerar com `solution/scripts/` se necessário (ver [`EVIDENCE_INDEX.md`](EVIDENCE_INDEX.md)).

## Verificação local pós-curadoria

```powershell
cd submissions\leopoldo-lima\solution
python -m pytest -q
```

(Executado com sucesso após limpeza de caches.)

---

## Faxina final 2026-03-21 (repo `ai-master-challenge`)

- Removidos `solution/docs/`, `solution/crps/`, `solution/PROCESS_LOG.md`.  
- `tasks.py` atualizado com `SUBMISSION_ROOT`.  
- `solution/artifacts/process-log/` reposto como pasta mínima para outputs de scripts + README explicativo.  
- README principal reforçado (template, guide, challenge 003, LinkedIn, navegação).  
- Referências `submission/README.md` → `submissions/leopoldo-lima/README.md` na documentação de apoio.  
- `INTERNAL_SUBMISSION_README_LEGACY.md` → [`docs/archive/README_LEGACY_SUBMISSION_FOLDER.md`](archive/README_LEGACY_SUBMISSION_FOLDER.md).
