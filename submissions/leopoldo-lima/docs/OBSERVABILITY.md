# Observabilidade mínima

## Objetivo
Garantir rastreabilidade operacional básica da API sem expor dados sensíveis.

## O que foi instrumentado
- Middleware HTTP com:
  - `x-request-id` (propagado do header ou gerado)
  - log estruturado JSON por requisição
  - duração em ms
  - status code
- Métricas mínimas em memória no endpoint `GET /metrics`:
  - `requests_total`
  - `ranking_requests`
  - `detail_requests`
  - `errors_total`
- Log de duração da computação de ranking (`event=ranking_computed`).

## Campos de log
- `event`
- `request_id`
- `method`
- `path`
- `status_code`
- `duration_ms`

## O que NÃO é logado
- payload completo de requisição
- dados sensíveis/segredos
- conteúdo integral dos registros de oportunidade

## Exemplo sanitizado de log

```json
{"event":"http_request","request_id":"req-123","method":"GET","path":"/api/ranking","status_code":200,"duration_ms":4}
```

## Como validar

```powershell
python .\scripts\tasks.py dev
```

Em outro terminal:

```powershell
python -c "import urllib.request, json; print(urllib.request.urlopen('http://127.0.0.1:8787/metrics').read().decode())"
```

## Limitações
- Métricas são em memória (reiniciam ao reiniciar processo).
- Sem backend de telemetria externa neste estágio.
