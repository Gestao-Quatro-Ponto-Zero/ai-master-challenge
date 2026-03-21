# Data Contract Frontend

Contrato de dados consumido pela UI shell, alinhado ao dataset real exposto pelo backend neste repositório.

## Objetivo
Evitar divergência entre tipos/expectativas de frontend e o payload realmente servido pela API.

## Entidades relevantes para a UI
- `OpportunityListItemResponse`
- `OpportunityDetailResponse`
- `DashboardKpisResponse`
- `DashboardFilterOptionsResponse`

Fonte de verdade:
- `src/api/contracts.py`
- `docs/API_CONTRACT_UI.md`

## Estágios (`deal_stage`): alinhamento com dataset real (CRP-REAL-03)

### Dataset raw (pipeline)
- estágio canônico de negócio: `Prospecting`, `Engaging`, `Won`, `Lost`

### Contrato atual UI/API
- campo exposto para listagem, detalhe e filtros: **`deal_stage`**
- não expor o agregado legado `Open` na API nem na UI

### Regras no backend
- `normalize_deal_stage` garante um dos quatro valores; legado `Open` → `Engaging`
- KPI `open_opportunities` = contagens em `Prospecting` + `Engaging`

## Implicação para frontend
- filtrar e exibir por **`deal_stage`** (query `deal_stage`, coluna “Estágio”)
- não reintroduzir `Open` como valor de domínio sem ADR/contrato
- ver também `docs/DOMAIN_ALIGNMENT.md`

## Checklist de consistência
- [ ] `docs/API_CONTRACT_UI.md` atualizado se o contrato mudar
- [ ] testes de contrato HTTP cobrindo forma e valores esperados
- [ ] README e runbook atualizados quando houver impacto visível na demo
