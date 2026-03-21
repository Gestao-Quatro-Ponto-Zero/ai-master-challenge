# Pacote final de submissão (CRP-FIN-12)

## O que entra na avaliação
| Área | Conteúdo |
|------|-----------|
| Produto | `src/api/` (FastAPI), `public/` (cockpit), `config/scoring-rules.json` |
| Dados | `data/*.csv` (oficial), serving em `src/serving/` |
| Docs | `README.md`, `docs/SETUP.md`, `docs/API_CONTRACT_UI.md`, `docs/SCORING_V2.md`, `docs/RUNTIME_DEFAULTS.md`, `PROCESS_LOG.md` |
| Evidências | `artifacts/process-log/` (notas, screenshots-guides, test-runs) |

## O que fica à margem (não é o caminho principal)
- `legacy/` — packs de CRP, ferramentas antigas, materiais de construção.
- Scripts utilitários não necessários à demo (ex.: `concat_repo_all_text.py` na raiz, se existir).

## Checklist antes do PR
1. `python -m pytest -q`
2. `python scripts/tasks.py dev` e smoke manual (filtros, detalhe, ranking).
3. `PROCESS_LOG.md` e `LOG.md` atualizados na trilha FIN.

## Estado
**Pronto para PR** após revisão humana final do diff e confirmação de dataset local.
