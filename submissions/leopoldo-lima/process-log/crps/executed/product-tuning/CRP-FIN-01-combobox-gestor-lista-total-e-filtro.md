# CRP-FIN-01 — Combobox de Gestor Comercial: mostrar todos e filtrar

## Objetivo
Fazer o campo **Gestor Comercial** funcionar como combobox real:
- abrir lista completa quando focado/clicado
- permitir filtro incremental ao digitar
- manter ordenação alfabética
- suportar seleção por mouse e teclado

## Fazer
- usar a lista real da API de filtros
- mostrar todos os gestores quando o dropdown abrir
- aplicar filtro em tempo real conforme o usuário digita
- manter valor selecionado no estado do filtro
- preservar opção de limpar seleção

## Impacto na submissão
Melhora diretamente a usabilidade do cockpit para um gestor/vendedor de verdade. Reduz a cara de formulário técnico e reforça que a solução é utilizável amanhã.

## Evidências obrigatórias
- screenshot do dropdown aberto com todos os gestores
- screenshot com filtro aplicado após digitar
- evidência de seleção via mouse
- evidência de seleção via teclado

## Atualizações obrigatórias de process log
Registrar:
- por que textbox era insuficiente
- como foi implementada a lista completa + filtro incremental
- qualquer erro de foco/teclado e correção

## Definition of Done
- campo não é mais textbox simples
- lista abre com todos os gestores ordenados
- digitação filtra a lista
- seleção funciona com mouse e teclado
- limpar filtros reseta o campo
