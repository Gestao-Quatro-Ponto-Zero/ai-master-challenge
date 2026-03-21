# CRP-UI-02 — Alinhar contratos de domínio ao dataset real

## Objetivo
Ajustar os tipos de frontend para refletirem o contrato real do projeto e não a visão genérica do Lovable.

## Escopo
- Revisar src/domain/models/types.ts
- Remover ou reclassificar estágios que não existem no dataset real
- Garantir aderência a Opportunity, OpportunityListItem, OpportunityDetailView, DashboardKpis e FilterOptions
- Preparar contracts para payload vindo da API real

## Atenções
O type DealStage atual inclui Proposal e Negotiation, mas o dataset real do challenge trabalha com Prospecting, Engaging, Won e Lost.

## Entregáveis
- src/domain/models/types.ts revisado
- docs/DATA_CONTRACT_FRONTEND.md
- ADR de alinhamento frontend/dataset

## Critérios de aceite
- Nenhum type contradiz o dataset real
- UI continua compilando
- StageBadge e filtros seguem contrato único
