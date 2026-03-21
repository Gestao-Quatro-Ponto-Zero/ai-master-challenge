# CRP-CBX-02 — Substituir textbox por campo de seleção adequado

## Objetivo
Parar de usar textbox livre onde o usuário precisa escolher valor conhecido.

## Fazer
- trocar:
  - `ESCRITÓRIO REGIONAL`
  - `GESTOR COMERCIAL`
- por:
  - `select` simples, se a lista for curta
  - ou `combobox`, se a lista for maior e precisar busca
- manter “Todos” como opção explícita
- preservar compatibilidade com o modelo de filtros atual

## Definition of Done
- não há textbox livre para região e manager
- usuário consegue selecionar por lista
- “Limpar filtros” continua funcionando
- screenshot do antes/depois registrada

## Evidência
- captura da tela
- teste manual com filtro aplicado
- nota de decisão humana: select vs combobox
