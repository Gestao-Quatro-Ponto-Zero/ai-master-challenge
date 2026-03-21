# CRP-UI-04 — Isolar mocks como fixture de demo

## Objetivo
Manter os mocks apenas como suporte de demo e fallback controlado.

## Escopo
- Reorganizar src/infrastructure/mocks/mock-data.ts em arquivos menores por entidade/view
- Adicionar README de fixtures
- Impedir que componentes importem mocks diretamente
- Garantir que mocks respeitam o contrato revisado

## Entregáveis
- pasta src/infrastructure/mocks/ organizada
- docs/MOCK_STRATEGY.md
- smoke test dos mocks

## Critérios de aceite
- Mock continua servindo demo local
- Mock não vaza para camada de apresentação
