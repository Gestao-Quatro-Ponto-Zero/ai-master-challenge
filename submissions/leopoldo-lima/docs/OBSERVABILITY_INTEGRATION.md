# Observability Integration (UI + API)

Guia de observabilidade e estados de erro para a integracao entre frontend e servico Python.

## Correlation ID
- Header de entrada aceito: `x-request-id`
- Comportamento:
  - se vier no request, e propagado para a resposta
  - se nao vier, o backend gera um UUID
- Uso recomendado na depuracao:
  - UI/BFF registra o `x-request-id`
  - backend usa o mesmo valor no log estruturado

## Estados de erro mapeados

No backend/API:
- `404`: recurso nao encontrado
- `422`: validacao de query/path/body (contrato invalido)
- `500`: erro interno inesperado

No `ApiClient` Python:
- `ApiClientNotFoundError` para `404`
- `ApiClientValidationError` para `422`
- `ApiClientServerError` para `5xx`
- `ApiClientTimeoutError` para timeout/rede
- `ApiClientResponseError` para demais respostas nao-2xx

## O que a UI deve exibir vs servidor
- UI: mensagem amigavel e curta (ex.: "Nao foi possivel carregar oportunidades.")
- Servidor: detalhe tecnico no log estruturado com `request_id`, `path`, `status_code`, `duration_ms`
- Nao exibir tokens, payloads integrais nem dados sensiveis na UI

## Metricas minimas em `/metrics`
- `requests_total`
- `ranking_requests`
- `detail_requests`
- `errors_total`
- `status_404_total`
- `status_422_total`
- `status_500_total`

## Evidencia rapida
```powershell
python -m pytest -q tests/test_api_contract.py tests/test_api_client.py
```
