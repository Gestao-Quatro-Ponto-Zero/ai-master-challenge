# CRP-API-01 — Definir contrato HTTP do frontend

## Objetivo
Definir o que a UI espera das APIs reais antes de trocar a implementação.

## Escopo
- Formalizar endpoints
- Definir query params de filtro
- Definir payloads de listagem, detalhe, KPIs e filter options
- Mapear erros HTTP esperados

## Endpoints mínimos
- GET /api/opportunities
- GET /api/opportunities/{id}
- GET /api/dashboard/kpis
- GET /api/dashboard/filter-options

## Entregáveis
- docs/API_CONTRACT_FRONTEND.md
- schemas zod para respostas
- ADR de contrato UI/API
