# API Contract UI/Backend

Fonte de verdade para integração entre frontend e serviço Python.

## Convenções
- Base URL local: `http://127.0.0.1:8787`
- Formato: JSON UTF-8
- Erro padrão estável:

```json
{ "detail": "<mensagem>" }
```

## Endpoints mínimos (canônicos)

### `GET /api/opportunities`
Lista oportunidades para a UI.

Query params:
- `region`: `string` (opcional)
- `manager`: `string` (opcional)
- `deal_stage`: `string` (opcional; valores oficiais: `Prospecting`, `Engaging`, `Won`, `Lost`)
- `q`: `string` (opcional; texto em **título**, **ID** da oportunidade ou **nome de conta** — CRP-UX-07)
- `priority_band`: `high|medium|low` (opcional; filtra após scoring — CRP-UX-07)
- `sort_by`: `score|amount|title|deal_stage` (default: `score`)
- `sort_order`: `asc|desc` (default: `desc`)
- `limit`: `int` (`1..200`, default `20`)
- `page`: `int` (opcional, reservado para paginacao)
- `page_size`: `int` (opcional, reservado para paginacao)

Resposta `200`:
- `total: int`
- `items: OpportunityListItemResponse[]`

**`OpportunityListItemResponse` (campos principais — CRP-REAL-05):** `id`, `title`, `seller`, `manager`, `region`, `deal_stage`, `amount`, `score`, `priority_band`, `next_action`, `nextBestAction`, e **campos explícitos do dataset** `account`, `product`, `sales_agent`, `regional_office`, `close_value` (espelho do valor de fecho; `amount` mantido por compatibilidade).

### `GET /api/opportunities/{id}`
Detalhe para painel lateral/modal da UI.

Respostas:
- `200`: `OpportunityDetailResponse` (inclui `account`, `product`, `sales_agent`, `regional_office`, `close_value`, `engage_date`, `close_date`, `product_series`, além de `scoreExplanation`)
- `404`: `{ "detail": "Opportunity not found" }`

### `GET /api/dashboard/kpis`
Resumo para cards de dashboard.

Resposta `200`:
- `total_opportunities: int`
- `open_opportunities: int`
- `won_opportunities: int`
- `lost_opportunities: int`
- `avg_score: float`

### `GET /api/dashboard/filter-options`
Opções de filtros populadas pelo backend.

Resposta `200`:
- `regional_offices: string[]` — valores únicos de escritório regional, **deduplicados** (case-insensitive) e **ordenados** (CRP-CBX-01)
- `managers: string[]` — gestores únicos, mesma regra de normalização/ordenação
- `deal_stages: string[]` — estágios presentes nos dados (subconjunto dos oficiais `Prospecting`, `Engaging`, `Won`, `Lost`), deduplicados e ordenados
- `regions: string[]` — **legado / compat**: espelho de `regional_offices` (mesmo conteúdo); a UI deve preferir `regional_offices` quando existir

## Compatibilidade
- `GET /api/ranking` permanece disponível como endpoint legado e retorna o mesmo contrato de listagem de `GET /api/opportunities`.

## Modelos Python do contrato
- `src/api/contracts.py`
  - `OpportunityListItemResponse`
  - `OpportunitiesListResponse`
  - `OpportunityDetailResponse`
  - `DashboardKpisResponse`
  - `DashboardFilterOptionsResponse`
  - `ApiError`

## Validação humana (UI entende / Python serve)
- UI atual usa listagem, detalhe e **KPIs** (`public/app.js` → `getDashboardKpis`).
- Contrato foi validado com `pytest` em `tests/test_api_contract.py`, incluindo `filter-options` (`regional_offices` + `regions`), endpoints de dashboard e erro `404` estável.
- Alinhamento visual/narrativa: `docs/UI_REAL_DATA_ALIGNMENT.md`.
