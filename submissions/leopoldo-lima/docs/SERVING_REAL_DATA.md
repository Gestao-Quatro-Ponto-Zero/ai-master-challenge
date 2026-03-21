# Serving com dataset real (CRP-REAL-02)

Este documento descreve como os **cinco CSVs oficiais** em `data/` alimentam a API HTTP (`/api/opportunities`, `/api/ranking`, detalhe e dashboard) no modo **`LEAD_SCORER_DATA_SOURCE_MODE=real_dataset`** (padrão).

## Onde ficam os arquivos

Todos os arquivos abaixo devem existir em **`data/`** na raiz do repositório (mesmo nível que `src/`, `public/`, `pyproject.toml`):

| arquivo | Papel |
|----------|--------|
| `data/sales_pipeline.csv` | Fact table: oportunidades (PK `opportunity_id`). |
| `data/sales_teams.csv` | Dimensão: `sales_agent` → `manager`, `regional_office`. |
| `data/accounts.csv` | Dimensão: `account` → `office_location` (e enriquecimento quando há conta). |
| `data/products.csv` | Dimensão: `product` → `series`, `sales_price` (preço de lista). |
| `data/metadata.csv` | Dicionário de campos (linhagem); carregado e indexado no arranque do pipeline. |

## Caminho de execução (modo real)

1. **`src/api/dataset_loader.py`** — decide `real_dataset` vs `demo_dataset`.
2. **`src/serving/opportunity_pipeline.py`** — `build_serving_opportunities()`:
   - lê os 5 CSVs via `src/raw/reader.py` (`load_raw_rows`);
   - normaliza `product` com `config/normalization-map.json` (`normalize_value`);
   - valida FKs mínimas antes de servir: agente ∈ `sales_teams`, produto canónico ∈ `products`, e se `account` estiver preenchido, conta ∈ `accounts`;
   - faz join explícito com `products` para `product_series` e `product_sales_price`;
   - mapeia `deal_stage` → `Open` / `Won` / `Lost` para o contrato UI.
3. **`src/serving/models.py`** — `ServingOpportunity` (modelo canónico) → `to_api_row()` (dicionário consumido por `src/api/app.py`).
4. **Scoring e view models** — `src/api/app.py` consome linhas com `deal_stage` canónico (`Prospecting`/`Engaging`/`Won`/`Lost`) além de `id`, `title`, `seller`, `manager`, `region`, `amount`. Ver `docs/DOMAIN_ALIGNMENT.md`.

## Cache

Para evitar reler e reprocessar ~8,8k linhas a **cada** pedido HTTP, o pipeline mantém cache in-memory invalidado pelo **mtime** dos cinco CSVs. Função de limpeza: `src.serving.opportunity_pipeline.clear_serving_cache()`.

## Fallback demo

`LEAD_SCORER_DATA_SOURCE_MODE=demo_dataset` ignora o pipeline e lê só `data/demo-opportunities.json` (testes determinísticos). Não é o caminho principal.

## Verificação

```powershell
python -m pytest -q tests/test_serving_pipeline_integration.py tests/test_real_dataset_serving.py
python .\scripts\tasks.py dev
Invoke-RestMethod "http://127.0.0.1:8787/api/opportunities/1C1I7A6R"
```

O identificador `1C1I7A6R` provém directamente de `sales_pipeline.csv` (primeiras linhas do dataset).

## UI

A UI estática em `public/` chama a mesma API; com o servidor em modo real, a tabela e o detalhe mostram contas/agentes/regiões do CSV (sem alteração de código front obrigatória neste CRP).

## Relação com outros documentos

- Visão geral do fluxo HTTP: `docs/RUNTIME_DATA_FLOW.md`
- Contrato estrutural dos CSVs: `docs/DATA_CONTRACT.md`, `contracts/repository-data-contract.json`
- Integridade referencial (relatório): `artifacts/data-validation/referential-integrity-report.json`
