# CRP-009 — CI forte em PR

## Objetivo
Bloquear PR ruim antes da branch principal.

## Entregáveis
- pipeline de CI
- cache de dependências
- badges no README

## Tarefas
1. Rodar lint, format, typecheck, testes, scan e build
2. Organizar jobs legíveis
3. Falhar rápido
4. Publicar artefatos úteis quando fizer sentido

## Critérios de aceite
- YAML legível
- pipeline reprodutível
- branch principal protegida por processo, não por fé

## DoD
- workflow criado
- README atualizado
- LOG.md atualizado
