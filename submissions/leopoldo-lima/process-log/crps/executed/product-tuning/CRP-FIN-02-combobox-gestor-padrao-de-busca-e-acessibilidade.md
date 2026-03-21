# CRP-FIN-02 — Combobox de Gestor: padrão de busca, empty state e acessibilidade

## Objetivo
Tirar o combobox do “quase pronto” e fechar os comportamentos mínimos profissionais.

## Fazer
- definir regra clara de busca:
  - abrir lista completa ao focar
  - priorizar prefix match
  - fallback para contains
- implementar estado vazio: “Nenhum gestor encontrado”
- suportar Esc, Enter, setas e clique fora
- revisar atributos semânticos mínimos (`aria-expanded`, `role`, etc.)

## Impacto na submissão
Mostra acabamento de produto e não apenas proof-of-concept técnico.

## Evidências obrigatórias
- screenshot com “Nenhum gestor encontrado”
- evidência de navegação por teclado
- evidência de clique fora fechando a lista

## Atualizações obrigatórias de process log
Registrar:
- regra final de busca escolhida
- comportamento de teclado
- problemas de acessibilidade encontrados e resolvidos

## Definition of Done
- estado vazio existe
- teclado funciona
- clique fora fecha
- comportamento do combobox é previsível
