# ADR 0004 — Contrato HTTP UI/API canônico

## Status
Aceito

## Contexto
A trilha UI/API exige contrato HTTP estável entre frontend e backend Python para evitar deriva de payload, nomes de filtros e corpos de erro.

## Decisão
- Definir como endpoints canônicos:
  - `GET /api/opportunities`
  - `GET /api/opportunities/{id}`
  - `GET /api/dashboard/kpis`
  - `GET /api/dashboard/filter-options`
- Manter `GET /api/ranking` como compat legado.
- Formalizar modelos de resposta/erro no backend com Pydantic em `src/api/contracts.py`.
- Documentar contrato para UI em `docs/API_CONTRACT_UI.md`.

## Consequências
- UI tem contrato explícito para listagem, detalhe, KPIs e filtros.
- Testes de contrato cobrem endpoints mínimos e erro `404` estável.
- Evoluções futuras devem versionar o contrato se houver quebra de compatibilidade.
