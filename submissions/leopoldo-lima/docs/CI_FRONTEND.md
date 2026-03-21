# CI Frontend

Pipeline dedicada para gates de frontend/UI shell.

## Workflow
- arquivo: `.github/workflows/frontend-ci.yml`
- gatilhos:
  - `pull_request`
  - `workflow_dispatch`

## Jobs
- `UI Quality Gates`
  - instala dependências (`python -m pip install -e .[dev]`)
  - executa `python scripts/tasks.py ui-tests`
  - executa `python scripts/tasks.py ui-quality`

## Objetivo
- fazer regressões de UX/acoplamento falharem cedo em PR
- expor um sinal de qualidade específico para a trilha de frontend

## Evidência esperada na submissão
- screenshot do run verde em Actions
- referência no `PROCESS_LOG.md` com data e commit/PR
