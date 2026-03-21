# CRP-004 — Motor de scoring v0

## Objetivo
Construir um baseline funcional, simples e explicável.

## Entregáveis
- módulo de score
- pesos configuráveis
- testes unitários iniciais
- `docs/SCORING.md`

## Tarefas
1. Criar scoring engine isolado
2. Retornar score, fatores positivos, fatores negativos, riscos e next best action
3. Externalizar pesos quando possível
4. Cobrir casos principais com testes

## Critérios de aceite
- Score determinístico
- Explicabilidade nítida
- Nada de lógica espalhada pela UI

## DoD
- engine implementada
- testes básicos verdes
- SCORING.md criado
- LOG.md atualizado
