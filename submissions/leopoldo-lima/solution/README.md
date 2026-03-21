# Solução — Challenge 003 · Lead Scorer (Focus Score Cockpit)

Código, dados, scripts e artefatos técnicos da solução. Execute **a partir desta pasta** (`solution/`), para que caminhos como `data/`, `src/` e `artifacts/` coincidam com o que o `pyproject.toml` e `scripts/tasks.py` esperam.

A documentação (`docs/`) e o process log (`process-log/`) vivem **ao lado** de `solution/`; o smoke `python scripts/tasks.py test` confirma que existem na pasta pai (`SUBMISSION_ROOT`).

## Início rápido

```powershell
cd solution
python .\scripts\tasks.py install
python .\scripts\tasks.py build
python .\scripts\tasks.py dev
```

- **URL:** `http://127.0.0.1:8787` (variável `LEAD_SCORER_PORT` para alterar).
- **Docker:** na raiz desta pasta, `docker compose up --build`.

## Documentação

- Visão geral da submissão e process log: [`../README.md`](../README.md)
- Setup detalhado, demo e contratos: pasta [`../docs/`](../docs/)

## Testes

```powershell
cd solution
python -m pytest -q
```
