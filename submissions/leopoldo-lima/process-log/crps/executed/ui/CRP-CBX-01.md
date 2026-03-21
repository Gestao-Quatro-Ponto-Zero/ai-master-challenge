# CRP-CBX-01 — Contrato dos filtros ordenados

## Objetivo
Garantir que a API entregue opções ordenadas e limpas para os comboboxes.

## Fazer
- revisar `/api/dashboard/filter-options`
- garantir arrays para:
  - `regional_offices`
  - `managers`
  - `deal_stages`
- ordenar alfabeticamente no backend
- remover duplicados e nulos
- documentar contrato em `docs/API_CONTRACT_UI.md`

## Definition of Done
- endpoint retorna listas ordenadas
- sem duplicados
- contrato documentado
- `PROCESS_LOG.md` atualizado com evidência de chamada real

## Evidência
- resposta JSON do endpoint
- diff do contrato
- print ou curl/httpie do retorno
