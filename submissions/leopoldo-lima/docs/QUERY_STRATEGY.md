# Query Strategy (UI Dashboard)

Estratégia de carregamento de dados do dashboard na UI shell para cenários reais.

## Objetivo
- padronizar chaves de consulta
- tratar erro por operação com retry mínimo
- reduzir corridas entre requests com cancelamento

## Implementação
- query keys:
  - `public/shared/query/query-keys.js`
- camada de coordenação de dados do dashboard:
  - `public/presentation/hooks/use-dashboard-data.js`
- consumo na apresentação:
  - `public/app.js`

## Comportamento
- `loadRanking(filters)`
  - cancela request anterior de ranking se houver
  - executa retry simples (1 tentativa adicional)
- `loadDetail(id)`
  - cancela request anterior de detalhe se houver
  - executa retry simples (1 tentativa adicional)

## Mensagens de erro na UI
- ranking: "Erro ao carregar ranking."
- detalhe: "Erro ao carregar detalhe."

## Limites do snapshot
- sem cache persistente de query em cliente (React Query não aplicável neste repo atual)
- estratégia pensada para evolução futura mantendo stack JS atual
