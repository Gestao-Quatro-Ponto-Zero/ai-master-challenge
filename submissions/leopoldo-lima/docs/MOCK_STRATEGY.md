# Mock Strategy (UI)

Mocks da UI são fixtures de demo e fallback controlado, nunca fonte primária de integração.

## Princípios
- modo padrão da UI: `api`
- modo `mock` somente para demo local controlada
- apresentação não importa fixtures diretamente
- fixtures seguem contrato de `docs/API_CONTRACT_UI.md`

## Localização
- `public/infrastructure/mocks/fixtures/`
- `public/infrastructure/repositories/mock-opportunity-repository.js`

## Isolamento de camadas
- `public/app.js` importa apenas `repository-factory.js`
- `repository-factory.js` decide `api` vs `mock`
- fixtures só são lidas pela implementação mock

## Smoke de mocks
- verificar seleção de modo:
  - `window.LEAD_SCORER_REPOSITORY_MODE = "mock"`
- validar que listagem e detalhe retornam estrutura compatível
- manter `tests/test_ui_smoke.py` cobrindo existência dos arquivos e acoplamentos permitidos
