# CRP-D04 — Integridade referencial entre fato e dimensões

## Objetivo
Garantir que `sales_pipeline` conversa corretamente com contas, produtos e equipe.

## Tarefas
- validar joins:
  - `sales_pipeline.account -> accounts.account`
  - `sales_pipeline.product -> products.product` via normalização
  - `sales_pipeline.sales_agent -> sales_teams.sales_agent`
- classificar desvios em bloqueante, warning e esperado

## Achados já conhecidos
- contas batem
- agentes batem
- produto falha sem normalização
- 5 agentes existem na dimensão e não aparecem no pipeline

## Saídas
- `docs/REFERENTIAL_INTEGRITY.md`
- testes de integridade
- relatório simples de cobertura

## Definition of Done
- joins críticos passam
- sobras de dimensão viram warning, não erro
- pipeline falha se aparecer chave órfã inesperada

## Prompt para o Cursor
```text
Implemente o CRP-D04: integridade referencial.

Tarefa:
1. Validar os joins entre sales_pipeline e as dimensões.
2. Considerar a normalização de produto antes do join.
3. Classificar desvios:
   - erro bloqueante
   - warning
   - esperado
4. Documentar em docs/REFERENTIAL_INTEGRITY.md:
   - relacionamento
   - taxa de match
   - exceções conhecidas
5. Adicionar testes automatizados.
6. Atualizar LOG.md.

Critérios:
- Não mascarar chave órfã
- Separar ausência de uso de quebra de join
- Saída deve ser legível e útil para a equipe
```
