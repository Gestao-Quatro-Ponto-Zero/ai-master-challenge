# CRP-CBX-04 — Navegação por teclado e UX mínima decente

## Objetivo
Não criar um pseudo-combobox ruim.

## Fazer
- suportar:
  - foco
  - seta para baixo/cima
  - Enter para selecionar
  - Esc para fechar
  - Tab sem quebrar o formulário
- exibir placeholder claro:
  - “Selecione o escritório”
  - “Digite 3 letras para buscar gestor”
- mostrar estado vazio:
  - “Nenhum gestor encontrado”

## Definition of Done
- campo funciona sem mouse
- estado vazio existe
- interação é previsível
- validação humana registrada

## Evidência
- checklist de teclado no `PROCESS_LOG.md`
- screenshot do estado vazio
- nota de correção se a IA tiver quebrado foco/navegação
