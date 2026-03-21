# API Contract

Base URL local (default): `http://127.0.0.1:8787`
Porta pode ser alterada via `LEAD_SCORER_PORT`.

## Healthcheck
- `GET /health`
- Resposta `200`:

```json
{ "status": "ok" }
```

## Oportunidades (canônico)
- `GET /api/opportunities`
- Query params opcionais:
  - `region` (string)
  - `manager` (string)
  - `deal_stage` (string; estágios oficiais do challenge)
  - `limit` (int, default `20`, min `1`, max `200`)

Resposta `200`:

```json
{
  "total": 6,
  "items": [
    {
      "id": "OPP-001",
      "title": "Enterprise expansion",
      "seller": "Ana",
      "manager": "Marcos",
      "region": "Core",
      "deal_stage": "Engaging",
      "amount": 125000,
      "score": 65,
      "priority_band": "medium",
      "next_action": "...",
      "nextBestAction": "..."
    }
  ]
}
```

Compat legado:
- `GET /api/ranking` (mesmo contrato de listagem, mantido por compatibilidade)

## Detalhe
- `GET /api/opportunities/{opportunity_id}`

Respostas:
- `200` com detalhe e bloco de explicação:

```json
{
  "id": "OPP-001",
  "title": "Enterprise expansion",
  "seller": "Ana",
  "manager": "Marcos",
  "region": "Core",
  "deal_stage": "Engaging",
  "amount": 125000,
  "scoreExplanation": {
    "score": 65,
    "priority_band": "medium",
    "positive_factors": ["..."],
    "negative_factors": ["..."],
    "risk_flags": ["..."],
    "next_action": "..."
  }
}
```
- `404`:

```json
{ "detail": "Opportunity not found" }
```

## Dashboard
- `GET /api/dashboard/kpis`
- `GET /api/dashboard/filter-options`

`open_opportunities` soma linhas com `deal_stage` em `Prospecting` ou `Engaging`.

Exemplo `kpis`:

```json
{
  "total_opportunities": 6,
  "open_opportunities": 3,
  "won_opportunities": 2,
  "lost_opportunities": 1,
  "avg_score": 58.5
}
```

## Execução local

```powershell
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8787
```

Ou via task runner:

```powershell
$env:LEAD_SCORER_PORT=8791
python .\scripts\tasks.py dev
```

## Teste de contrato

```powershell
python -m pytest -q tests/test_api_contract.py
```
