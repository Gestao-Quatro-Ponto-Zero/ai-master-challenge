# Repository Strategy (UI)

Separação entre contrato da camada de apresentação e implementações concretas de acesso a dados.

## Objetivo
- remover acoplamento direto de `public/app.js` com fetch/endpoint concreto
- manter um único ponto de troca entre modo API e modo mock

## Estrutura
- contrato:
  - `public/application/contracts/opportunity-repository.js`
- implementações:
  - `public/infrastructure/repositories/api-opportunity-repository.js`
  - `public/infrastructure/repositories/mock-opportunity-repository.js`
- composição/factory:
  - `public/infrastructure/repositories/repository-factory.js`

## Regra de dependência
- `public/app.js` depende apenas da factory e do contrato implícito.
- camada de apresentação não importa implementação concreta.

## Seleção de implementação
- padrão: `api`
- fallback demo: `mock` quando `window.LEAD_SCORER_REPOSITORY_MODE = "mock"`

## Fixtures de demo
- mocks isolados em `public/infrastructure/mocks/fixtures/`
- detalhes em `docs/MOCK_STRATEGY.md`

## Benefícios
- facilita migração para backend real sem retrabalho na UI
- reduz risco de mock “vazando” no fluxo principal
- deixa DI explícita mesmo na stack JS simples do snapshot atual
