# Runbook UI/API Integration

Guia operacional para subir UI e backend Python de forma reproduzivel, sem suposicoes.

## Objetivo
- executar fluxo ponta a ponta (`health`, `listagem`, `detalhe`, `filtro`)
- explicitar diferenca entre modo `api` e modo `mock`
- reduzir tempo de troubleshooting em ambiente novo

## Pré-requisitos
- Python `3.11+`
- dependencias instaladas: `python -m pip install -e .[dev]`
- porta de API livre (`8787` por padrao)

## Variáveis de ambiente
- `LEAD_SCORER_REPOSITORY_MODE=api` (padrao recomendado para integracao)
- `LEAD_SCORER_API_BASE_URL=http://127.0.0.1:8787`
- `LEAD_SCORER_API_TIMEOUT_SECONDS=5`
- `LEAD_SCORER_PORT=8787` (opcional, para subir API em outra porta)
- `LEAD_SCORER_API_CORRELATION_ID` (opcional)

Referencias:
- `docs/RUNTIME_MODES.md`
- `docs/API_CONTRACT_UI.md`
- `docs/OBSERVABILITY_INTEGRATION.md`

## Subindo backend + UI shell
1. Instalar dependencias:
```powershell
python -m pip install -e .[dev]
```
2. Subir API/UI:
```powershell
python .\scripts\tasks.py dev
```
3. Abrir:
- UI: `http://127.0.0.1:8787/`
- Health: `http://127.0.0.1:8787/health`

## Smoke E2E (checklist reproduzivel)
Execute com API em execucao:

```powershell
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8787/health').read().decode())"
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8787/api/opportunities?limit=3').read().decode())"
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8787/api/opportunities/OPP-001').read().decode())"
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8787/api/opportunities?region=Core&limit=3').read().decode())"
```

Checklist:
- [ ] `health` retorna `{"status":"ok"}`
- [ ] listagem retorna `items` nao vazio
- [ ] detalhe de `OPP-001` retorna `scoreExplanation`
- [ ] filtro por `region` retorna itens coerentes

## Modo `mock` vs modo `api`
- `api` (padrao): fluxo de integracao real via `ApiOpportunityRepository` e `ApiClient`
- `mock`: somente para demo/testes controlados

Troca explicita:
```powershell
$env:LEAD_SCORER_REPOSITORY_MODE="mock"
python -m pytest -q tests/test_repository_factory.py
```

## Troubleshooting
- Porta ocupada:
  - definir `LEAD_SCORER_PORT=8791` antes de `tasks.py dev`
- `422` em filtros:
  - revisar `sort_by` e `sort_order` conforme `docs/API_CONTRACT_UI.md`
- timeout de cliente:
  - aumentar `LEAD_SCORER_API_TIMEOUT_SECONDS`
- correlação:
  - enviar `x-request-id` e confirmar retorno no header de resposta
- CORS:
  - nao aplicavel ao shell atual (UI servida pelo mesmo backend); se separar hosts, habilitar politica CORS no backend

## Evidências para submissão
- salvar output do smoke e anexar em `artifacts/process-log/test-runs/`
- capturar UI carregando listagem/detalhe/filtro e anexar em `artifacts/process-log/ui-captures/`
- referenciar evidencias no `PROCESS_LOG.md`
