# CRP-UI-06 — Refinar hook de dashboard para casos reais

## Objetivo
Evoluir useDashboardData para suportar erro, retry, cancelamento e composição mais limpa.

## Escopo
- Consolidar query keys em constants/factory
- Adicionar tratamento de erro com mensagem por operação
- Preparar staleTime/cacheTime adequados
- Evitar que três queries soltas virem gargalo de integração

## Entregáveis
- src/presentation/hooks/useDashboardData.ts refatorado
- src/shared/query/queryKeys.ts
- docs/QUERY_STRATEGY.md

## Critérios de aceite
- Query keys padronizadas
- Hook preparado para backend real
