# CRP-D09 — Testes de dados e quality gates no CI

## Objetivo
Fazer o pipeline barrar regressão de dados e de mapeamento.

## Gates obrigatórios
- schema validation
- quality rules
- referential integrity
- normalization tests
- smoke da geração de features

## Ferramentas possíveis
- Python: `pytest`, `pandera`, `pydantic`, `ruff`, `mypy`
- TS: `vitest/jest`, `zod`, `eslint`, `tsc`

## Saídas
- workflow de CI
- `docs/QUALITY_GATES.md`
- badge/status no README

## Definition of Done
- PR falha se quebrar regra crítica de dados
- PR falha se quebrar normalização ou join
- build não aprova sem teste de features

## Prompt para o Cursor
```text
Implemente o CRP-D09: quality gates de dados no CI.

Tarefa:
1. Integrar validações de dados e de domínio ao pipeline de CI.
2. Rodar, no mínimo:
   - lint
   - format check
   - type check
   - testes
   - validação de schema
   - validação de qualidade dos dados
   - integridade referencial
   - smoke de features
3. Criar docs/QUALITY_GATES.md.
4. Atualizar README e LOG.md.

Critérios:
- Pipeline com falha rápida
- Nome das etapas claro
- Nada de gate decorativo
```
