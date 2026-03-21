# CRP-API-07 — Estados de erro e observabilidade da integração

## Objetivo
Dar visibilidade a falhas de API e tornar a UI depurável.

## Escopo
- Mensagens de erro por operação
- Logging mínimo e correlation id quando houver header
- Tratamento diferenciado para 404, 422, 500 e timeout
- Instrumentar eventos básicos de falha e latência

## Entregáveis
- error mapping
- docs/OBSERVABILITY_FRONTEND.md
- componentes de erro refinados
