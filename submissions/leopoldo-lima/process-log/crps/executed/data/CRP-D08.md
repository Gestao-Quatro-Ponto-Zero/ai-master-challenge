# CRP-D08 — View models para produto e explicabilidade

## Objetivo
Traduzir domínio técnico em payload útil para vendedor.

## Modelos alvo
- `OpportunityListItemView`
- `OpportunityDetailView`
- `ScoreExplanationView`

## Campos esperados
- score
- banda de prioridade
- fatores positivos
- fatores negativos
- flags de risco
- próxima ação sugerida
- dados essenciais da oportunidade

## Saídas
- `docs/VIEW_MODELS.md`
- contratos da API
- testes de serialização

## Definition of Done
- a UI não precisa entender regra de score
- o backend entrega explicação já pronta
- payload não vaza campo bruto desnecessário

## Prompt para o Cursor
```text
Implemente o CRP-D08: view models para produto e explainability.

Tarefa:
1. Criar view models para listagem, detalhe e explicação de score.
2. Garantir que a API entregue payload já orientado ao uso do vendedor.
3. Documentar em docs/VIEW_MODELS.md.
4. Adicionar testes de contrato/serialização.
5. Atualizar LOG.md.

Critérios:
- Nada de expor CSV cru para a UI
- Explicação do score precisa vir pronta
- Priorizar payload claro e coeso
```
