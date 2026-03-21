# API Testing

Guia dos testes de contrato e simulacao HTTP da integracao UI/API na stack Python.

## Objetivo
- detectar quebra de contrato em payload, status e semantica de erro
- garantir que o `ApiClient` e o repositório reagem corretamente a cenarios reais de integração

## Estratégia
- testes de contrato do backend: `tests/test_api_contract.py` (FastAPI `TestClient`)
- simulacao HTTP do cliente com `pytest-httpx`: `tests/test_api_client_contract_http.py`
- testes unitarios do cliente/repositório continuam em:
  - `tests/test_api_client.py`
  - `tests/test_api_opportunity_repository.py`

## Cobertura mínima esperada
- listagem de oportunidades (happy path)
- detalhe de oportunidade (200 e 404)
- filtros de listagem (region/manager/status/q/sort)
- KPIs e filter-options
- erro de validacao (`422`)
- erro interno (`5xx`)
- timeout/rede
- payload invalido (quando aplicável)

## Comandos
```powershell
python -m pytest -q tests/test_api_contract.py tests/test_api_client.py tests/test_api_client_contract_http.py tests/test_api_opportunity_repository.py
```

## O que significa quebra de contrato
- mudar campos obrigatorios do JSON (nome/tipo) sem atualizar contrato
- alterar status esperado de erro (`404`, `422`, `500`) sem alinhamento
- remover/alterar semantica de `detail` sem revisão da camada cliente/UI
- mudar query params suportados sem atualizar docs e testes

## Atualizando fixtures simuladas
- sempre espelhar o contrato canônico em `docs/API_CONTRACT_UI.md`
- quando alterar `src/api/contracts.py`, atualizar fixtures e asserts no mesmo PR
- validar manualmente exemplos gerados por IA antes de aceitar no teste
