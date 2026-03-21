# Alinhamento de domínio (challenge build-003)

**CRP-REAL-03** — taxonomia única de estágio de negócio em runtime, API, UI e testes.

## Estágios oficiais (`deal_stage`)

Valores canónicos (campo `sales_pipeline.deal_stage` / metadados do challenge):

| Valor | Significado |
|--------|-------------|
| `Prospecting` | Pipeline aberto — fase inicial |
| `Engaging` | Pipeline aberto — em progresso |
| `Won` | Fechado ganho |
| `Lost` | Fechado perdido |

Implementação: `src/domain/deal_stage.py` (`OFFICIAL_DEAL_STAGES`, `normalize_deal_stage`, `is_pipeline_open_stage`).

## O que foi removido do fluxo principal

- Agregado **`Open`** na superfície HTTP/UI (substituído pela semântica explícita `Prospecting` + `Engaging`).
- Campo paralelo **`ui_status`** no modelo de serving (`ServingOpportunity`).

## Compatibilidade legada

- Payloads com `status: "Open"` (snapshot demo antigo ou wire legado) são normalizados para **`Engaging`** nos DTOs (`src/infrastructure/http/dtos.py`) e na leitura de linhas em `src/api/app.py` (`_row_deal_stage`).
- Query string histórica `?status=` **não** é aceite; usar `?deal_stage=`.

## KPIs

- `open_opportunities` em `/api/dashboard/kpis` conta oportunidades com `deal_stage` em **`Prospecting` ou `Engaging`** (`is_pipeline_open_stage`).

## Filtros

- `GET /api/dashboard/filter-options` expõe `deal_stages` (lista ordenada segundo a ordem oficial, apenas estágios presentes nos dados).
- Listagem: `deal_stage` em query e em cada item; `sort_by` inclui `deal_stage`.

## Verificação

```powershell
python -m pytest -q tests/test_deal_stage.py tests/test_api_contract.py
```

Captura da UI: coluna **Estágio** e filtro **Estágio (deal stage)** devem refletir os quatro valores acima (evidência em `artifacts/process-log/`).
