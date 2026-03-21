# CRP-UI-05 — Endurecer TypeScript e quality gates

## Objetivo
Sair do modo permissivo e aproximar o frontend do padrão industrial.

## Escopo
- Endurecer tsconfig.app.json e tsconfig.json
- Revisar eslint
- Adicionar typecheck dedicado
- Adicionar format check
- Configurar pre-commit opcional

## Entregáveis
- tsconfig(s) revisados
- script npm run typecheck
- script npm run ci:check
- docs/QUALITY_GATES_UI.md

## Critérios de aceite
- strict mais rígido sem quebrar build final
- pipeline local detecta regressões de tipagem
