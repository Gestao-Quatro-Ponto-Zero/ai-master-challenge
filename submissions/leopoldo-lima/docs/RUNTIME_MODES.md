# Runtime Modes

Alternância de **repositório Python** (cliente HTTP vs mock) e, em separado, **fonte de dados do serving HTTP** (CSVs oficiais vs JSON demo).

## Fonte do serving HTTP (`src/api/app.py`)

- `LEAD_SCORER_DATA_SOURCE_MODE`
  - `real_dataset` (**padrão**): `sales_pipeline.csv` + joins documentados em `docs/RUNTIME_DATA_FLOW.md`
  - `demo_dataset`: `data/demo-opportunities.json` (testes determinísticos / dev controlado)

Detalhe: `docs/RUNTIME_DATA_FLOW.md`

---

Alternancia de repositório por configuração, em um único ponto de decisão.

## Flag principal
- `LEAD_SCORER_REPOSITORY_MODE`
  - `api` (default): usa `ApiOpportunityRepository` + `ApiClient`
  - `mock`: usa `MockOpportunityRepository` apenas para demo/testes controlados

Factory:
- `src/infrastructure/repositories/repository_factory.py`
- função: `create_opportunity_repository(...)`

## Variáveis relacionadas (modo `api`)
- `LEAD_SCORER_API_BASE_URL`
- `LEAD_SCORER_API_TIMEOUT_SECONDS`
- `LEAD_SCORER_API_AUTH_TOKEN` (opcional)
- `LEAD_SCORER_API_CORRELATION_ID` (opcional)

## Segurança e operação
- produção/staging: manter `LEAD_SCORER_REPOSITORY_MODE=api`
- desenvolvimento/demo local: `mock` apenas quando explicitamente necessário
- evitar uso acidental de mock em ambiente real via validação de pipeline/deploy
- factory com import lazy evita carregar módulos de mock quando o modo selecionado é `api`

## Evidência de alternância

```powershell
$env:LEAD_SCORER_REPOSITORY_MODE="api"
python -m pytest -q tests/test_repository_factory.py

$env:LEAD_SCORER_REPOSITORY_MODE="mock"
python -m pytest -q tests/test_repository_factory.py
```
