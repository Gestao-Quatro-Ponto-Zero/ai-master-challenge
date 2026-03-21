# Fluxo de dados no runtime (HTTP serving)

Documento orientado ao **CRP-REAL-01** e **CRP-REAL-02**: de onde vêm as oportunidades servidas por `/api/opportunities`, `/api/ranking`, `/api/dashboard/*` e detalhe.

## Modo de fonte (`LEAD_SCORER_DATA_SOURCE_MODE`)

| Valor | Comportamento |
|--------|----------------|
| `real_dataset` (**padrão**) | Pipeline em `src/serving/opportunity_pipeline.py`: os **5 CSVs** em `data/` (incl. `products.csv` e `metadata.csv`), joins, validação de FKs e modelo `ServingOpportunity`. Detalhe: `docs/SERVING_REAL_DATA.md`. |
| `demo_dataset` | Lê apenas `data/demo-opportunities.json` (snapshot pequeno, determinístico). |

Implementação: `src/api/dataset_loader.py` → `src/serving/opportunity_pipeline.py`
Consumidor: `src/api/app.py` (todas as rotas que listam oportunidades).

## Pipeline (modo real)

1. **Ingestão:** `load_raw_rows` nos cinco CSVs oficiais.
2. **Validação:** FKs agente/produto (e conta se preenchida) antes de servir.
3. **Joins:** `products` (série, preço de lista), `sales_teams`, `accounts`; `metadata.csv` indexado para linhagem.
4. **Modelo canónico:** `ServingOpportunity` → `to_api_row()` (`id`, `title`, `seller`, `manager`, `region`, `deal_stage`, `amount`, mais campos opcionais ignorados pelo contrato mínimo).
5. **Scoring:** `src/scoring/engine.py` com payload derivado da linha (via `src/api/app.py`).
6. **Cache:** invalidação por mtime dos CSVs (ver `docs/SERVING_REAL_DATA.md`).

## Distinção vs `LEAD_SCORER_REPOSITORY_MODE`

- **`LEAD_SCORER_DATA_SOURCE_MODE`:** o que o **processo FastAPI** usa para montar respostas HTTP quando o cliente chama esta API.
- **`LEAD_SCORER_REPOSITORY_MODE`:** usado pela **factory Python** (`repository_factory.py`) quando código consome oportunidades via `ApiOpportunityRepository` / `MockOpportunityRepository` (integração cliente→outra instância da API ou mock).

Para a demo típica (`python scripts/tasks.py dev`), UI + API no mesmo host: o browser fala com esta API; o modo relevante para “dados reais vs demo” no browser é **`LEAD_SCORER_DATA_SOURCE_MODE`**.

## Arranque

No startup da app é emitido log JSON com `event=api_startup` e `lead_scorer_data_source_mode`.

## Verificação rápida

```powershell
# Padrão (real)
python .\scripts\tasks.py dev
# noutro terminal:
Invoke-RestMethod "http://127.0.0.1:8787/api/ranking?limit=2"

# Demo explícito
$env:LEAD_SCORER_DATA_SOURCE_MODE="demo_dataset"
python .\scripts\tasks.py dev
```

## Testes

- Contratos que assumem `OPP-001` / região `Core`: `tests/test_api_contract.py` força `demo_dataset` via `tests/conftest.py`.
- Fluxo real: `tests/test_real_dataset_serving.py`.
