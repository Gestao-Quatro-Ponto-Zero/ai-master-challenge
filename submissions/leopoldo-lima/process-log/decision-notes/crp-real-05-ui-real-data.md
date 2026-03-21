# CRP-REAL-05 — Evidência UI / dados reais

## Antes / depois (narrativa)
- **Antes:** tabela enxuta com “título” genérico, detalhe em JSON cru, sem KPIs visíveis; risco de parecer demo estática.
- **Depois:** colunas nomeadas como no negócio B2B (conta, produto, vendedor, escritório, valor de fecho), cabeçalho que cita o pipeline oficial, KPIs do endpoint real, detalhe com secções “Dados do pipeline” + “Score e explicação”.

## Screenshots (preencher manualmente)
- `crp-real-05-dashboard-real.png` — KPIs + tabela com IDs reais (ex.: `1C1I7A6R`).
- `crp-real-05-drawer-explain.png` — drawer com fatores de score.

## arquivos tocados (lista)
- `public/index.html`, `public/app.js`, `public/styles.css`
- `public/application/contracts/opportunity-repository.js`
- `public/infrastructure/repositories/api-opportunity-repository.js`, `mock-opportunity-repository.js`
- `public/infrastructure/mocks/fixtures/*.js`
- `src/api/contracts.py`, `src/infrastructure/http/dtos.py`, `src/api/app.py`
- `src/infrastructure/repositories/mock_opportunity_repository.py`
- `docs/UI_REAL_DATA_ALIGNMENT.md`, `docs/API_CONTRACT_UI.md`
- `tests/test_api_contract.py`, `tests/test_ui_smoke.py`, `tests/test_ui_front_coverage.py`
