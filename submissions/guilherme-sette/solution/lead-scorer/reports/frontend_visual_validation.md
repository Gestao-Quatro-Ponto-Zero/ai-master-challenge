# Frontend Visual Validation

Data da validacao: 2026-06-23

Validacao feita com Google Chrome headless via terminal, sem usar o browser in-app.

## Screenshots

### Portal do vendedor

![Portal do vendedor](./frontend-current-seller.png)

Checks observados:

- portal exibido: `Portal do vendedor`;
- abas de gerente ocultas no portal do vendedor;
- tabela renderizada com 80 linhas visiveis no DOM;
- breakdown compacto do score visivel;
- sem overflow horizontal no body.

### Portal do gerente - Cenario

![Portal do gerente - Cenario](./frontend-current-manager-scenario.png)

Checks observados:

- portal exibido: `Portal do gerente`;
- abas `Cenario` e `Aprovacoes` visiveis;
- tabela renderizada com 80 linhas visiveis no DOM;
- coluna `Especialista consultivo` presente;
- sem overflow horizontal no body.

### Portal do gerente - Aprovacoes

![Portal do gerente - Aprovacoes](./frontend-current-manager-approvals.png)

Checks observados:

- titulo da fila: `Fila de decisões do gerente`;
- contador: `23 pendentes` no gerente usado na captura;
- 18 cards de aprovacao renderizados no primeiro lote;
- painel lateral oculto na aba de aprovacoes;
- sem overflow horizontal no body.

## Limitacao

Esta validacao cobre viewport desktop de 1440x1050. Nao substitui teste manual completo em mobile, navegadores diferentes ou uso real com dados persistidos em CRM.
