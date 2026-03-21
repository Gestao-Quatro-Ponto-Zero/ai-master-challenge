# CRP-API-05 — Trocar factory de mock para API por flag/config

## Objetivo
Permitir alternância limpa entre demo local e backend real.

## Escopo
- Criar seleção via env/config
- Default claro por ambiente
- Evitar espalhar if de mock/api pelo código

## Entregáveis
- repository-factory.ts atualizado
- docs/RUNTIME_MODES.md
- .env.example
