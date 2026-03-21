# API Opportunity Repository

Implementação concreta de acesso HTTP para oportunidades/dashboard.

## Arquivos
- `src/infrastructure/repositories/api_opportunity_repository.py`
- `src/infrastructure/repositories/__init__.py`

## Responsabilidades
- centralizar operações:
  - `list_opportunities`
  - `get_opportunity`
  - `get_dashboard_kpis`
  - `get_dashboard_filter_options`
- delegar transporte ao `ApiClient`
- mapear erro de integração para erro de repositório

## Matriz erro -> comportamento
- `ApiClientResponseError(status=404)` em `get_opportunity` -> `OpportunityNotFoundError`
- qualquer `ApiClientError` em métodos do repo -> `OpportunityRepositoryError`

## Endpoints usados
- `GET /api/opportunities`
- `GET /api/opportunities/{id}`
- `GET /api/dashboard/kpis`
- `GET /api/dashboard/filter-options`

## Testes

```powershell
python -m pytest -q tests/test_api_opportunity_repository.py
```
