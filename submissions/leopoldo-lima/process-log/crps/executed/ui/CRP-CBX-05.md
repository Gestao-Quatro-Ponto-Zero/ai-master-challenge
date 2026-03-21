# CRP-CBX-05 — Fonte única de opções e ordenação defensiva no frontend

## Objetivo
Evitar drift entre backend e UI.

## Fazer
- centralizar no frontend uma função utilitária para:
  - normalizar
  - ordenar
  - deduplicar defensivamente
- usar essa função no carregamento de `filter-options`
- impedir que cada campo trate lista de um jeito

## Definition of Done
- uma única função de ordenação/normalização
- campos usam o mesmo comportamento
- sem lógica duplicada espalhada

## Evidência
- diff da função utilitária
- referência do uso nos dois campos
- revisão humana registrada
