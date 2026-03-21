# CRP-003 — Modelo de domínio e contrato dos dados

## Objetivo
Formalizar entidades, chaves, campos críticos, joins e regras de validação.

## Entregáveis
- `docs/DATA_CONTRACT.md`
- schemas/DTOs/types/interfaces no código
- validação de entrada

## Tarefas
1. Descobrir tabelas/arquivos/fontes do challenge
2. Mapear relacionamentos e chaves
3. Documentar anomalias, nulls, outliers e inconsistências
4. Introduzir tipagem/validação compatível com o stack

## Critérios de aceite
- Contrato de dados claro
- Tipagem condizente com o código real
- Sem inventar semântica inexistente

## DoD
- DATA_CONTRACT.md criado
- validação implementada
- LOG.md atualizado
