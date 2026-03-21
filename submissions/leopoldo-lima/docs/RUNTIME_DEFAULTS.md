# Runtime padrão (CRP-FIN-09)

## Backend (FastAPI)
| Variável | Omisso / padrão | Explícito alternativo |
|----------|-----------------|------------------------|
| `LEAD_SCORER_DATA_SOURCE_MODE` | **`real_dataset`** (CSVs em `data/`) | `demo_dataset` → `data/demo-opportunities.json` |

Implementação: `get_data_source_mode()` em `src/api/dataset_loader.py`.

## Frontend (cockpit em `public/`)
| Mecanismo | Padrão | Alternativo |
|-----------|--------|-------------|
| `window.LEAD_SCORER_REPOSITORY_MODE` | **`api`** (HTTP para a mesma origem) | `mock` → `MockOpportunityRepository` + fixtures |

Implementação: `createOpportunityRepository()` em `public/infrastructure/repositories/repository-factory.js`.

## Conclusão
Não há fallback silencioso para demo: é preciso **definir** `demo_dataset` ou `mock` para sair do caminho principal.
