# API Client (Python)

Cliente HTTP centralizado para consumo do contrato UI/API.

## Implementação
- `src/infrastructure/http/api_client.py`
- `src/infrastructure/http/errors.py`

Classe principal:
- `ApiClient`

Config:
- `ApiClientConfig.from_env()`

## Variáveis de ambiente
- `LEAD_SCORER_API_BASE_URL` (default: `http://127.0.0.1:8787`)
- `LEAD_SCORER_API_TIMEOUT_SECONDS` (default: `5`)
- `LEAD_SCORER_API_AUTH_TOKEN` (opcional)
- `LEAD_SCORER_API_CORRELATION_ID` (opcional)

## Métodos
- `list_opportunities(...)`
- `get_opportunity(opportunity_id)`
- `get_dashboard_kpis()`
- `get_dashboard_filter_options()`

`list_opportunities(...)` suporta:
- `region`, `manager`, `deal_stage`
- `q`
- `sort_by`, `sort_order`
- `limit`
- `page`, `page_size` (reservados para extensao de paginacao)

Serializacao de query params usa ordem estavel via:
- `src/infrastructure/http/filter_params.py`

## Tratamento de erro
- `ApiClientTimeoutError`: timeout/rede
- `ApiClientNotFoundError`: `404`
- `ApiClientValidationError`: `422`
- `ApiClientServerError`: `5xx`
- `ApiClientResponseError`: fallback para outros `4xx`

## Exemplo

```python
from src.infrastructure.http import ApiClient, ApiClientConfig

cfg = ApiClientConfig.from_env()
with ApiClient(cfg) as client:
    data = client.list_opportunities(limit=20)
    print(data.total)
```

## Testes

```powershell
python -m pytest -q tests/test_api_client.py
python -m pytest -q tests/test_api_client_contract_http.py
```
