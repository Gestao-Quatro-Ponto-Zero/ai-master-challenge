# CRP-UX-08 — Estados de loading, erro e vazio com cara de produto

## Objetivo
Dar acabamento profissional aos estados transitórios e de exceção.

## Problema
Mesmo uma boa solução perde força se loading, erro e vazio parecem acidentes de infraestrutura.

## Tarefas
1. Revisar loading state.
2. Revisar error state com retry útil.
3. Revisar empty state orientado a ação.
4. Revisar not found/detail failure.
5. Garantir consistência visual com o restante da interface.

## Impacto na Submissão
- Melhora percepção de robustez.
- Ajuda a demonstrar maturidade de produto.

## Evidências obrigatórias
- screenshots dos estados
- evidência do retry
- diff dos componentes/handlers
- nota humana explicando acabamento adotado

## Atualizações obrigatórias de process log
Registrar:
- estados existentes
- estados melhorados
- comportamento funcional de retry/empty/error
- evidências visuais

## Atualizações obrigatórias de README/Submission
- adicionar pelo menos uma menção a tratamento de estados relevantes, se isso aparecer no demo/README

## Definition of Done
- loading claro
- erro claro com retry
- vazio claro e útil
- detalhe sem quebra feia
- `PROCESS_LOG.md` atualizado
- evidências salvas
- README atualizado quando aplicável
- verificação humana explícita realizada
