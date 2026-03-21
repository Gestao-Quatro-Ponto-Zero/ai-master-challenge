# Mock Fixtures (Demo)

Fixtures de demo da UI, isoladas da camada de apresentação.

## Estrutura
- `fixtures/opportunity-list.js`
- `fixtures/opportunity-detail.js`

## Regras
- `public/app.js` nunca importa fixtures diretamente.
- somente `mock-opportunity-repository.js` pode consumir fixtures.
- fixtures devem respeitar o contrato em `docs/API_CONTRACT_UI.md`.

## Uso
Ativar modo mock no browser antes de carregar a página:

```js
window.LEAD_SCORER_REPOSITORY_MODE = "mock";
```
