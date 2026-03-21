# CRP-API-03 — Criar DTOs e mappers

## Objetivo
Separar resposta da API do modelo de domínio/UI.

## Escopo
- DTOs para listagem, detalhe, kpis e filters
- Mappers dto -> domain/view model
- Normalização de nomes/campos
- Guardrails para valores inesperados

## Entregáveis
- src/infrastructure/http/dtos/*
- src/infrastructure/http/mappers/*
- testes dos mappers
