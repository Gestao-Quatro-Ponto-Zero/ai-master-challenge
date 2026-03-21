# CRP-CBX-03 — Autocomplete a partir de 3 letras

## Objetivo
Permitir busca rápida sem exigir scroll inútil.

## Fazer
- implementar comportamento:
  - antes de 3 letras: mostrar estado neutro ou lista inicial curta
  - a partir de 3 letras: filtrar opções em tempo real
- aplicar em:
  - manager
  - regional office
- debounce leve, se necessário
- busca case-insensitive e por prefixo; opcionalmente contains

## Definition of Done
- digitou 3 letras, a lista já afunila
- resultado aparece ordenado
- funciona com teclado
- sem regressão no submit do filtro

## Evidência
- gif/screenshot do fluxo
- registro no `PROCESS_LOG.md` do comportamento implementado
- prova manual com 2 ou 3 exemplos reais
