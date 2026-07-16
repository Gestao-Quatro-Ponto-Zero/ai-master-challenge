# AI Master Challenge — Lead Scorer (G4)

## Objetivo
Ferramenta que o vendedor abre na segunda e sabe quais deals priorizar.
Prioriza por Valor Esperado = P(fechar) × valor potencial, com flag de
deals esfriando. Scoring derivado do histórico real, não de pesos chutados.

## Dados (em ./data/)
- accounts.csv (~85): account, setor, revenue, funcionários, localização
- products.csv (7): product, série, sales_price
- sales_teams.csv (35): sales_agent, manager, escritório regional
- sales_pipeline.csv (~8800): opportunity_id (liga tudo), sales_agent,
  product, account, deal_stage (Prospecting/Engaging/Won/Lost),
  engage_date, close_date, close_value (0 se Lost)

## Regras de trabalho
- Nunca carregar as 8800 linhas no contexto. Escrever script, rodar,
  ler só o resumo. Salvar resultados em ./analysis/.
- Não inventar pesos de scoring antes de olhar os dados.
- Reportar qualquer mismatch de join (nomes de produto/conta/agente).
