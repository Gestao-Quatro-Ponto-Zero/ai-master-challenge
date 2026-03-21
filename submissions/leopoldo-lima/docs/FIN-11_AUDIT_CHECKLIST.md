# Auditoria final UI / dados / ranking (CRP-FIN-11)

**Data:** 2026-03-21 · Execução: revisão no código + `pytest`

## KPIs e API
- [x] `/api/dashboard/kpis` alinhado a linhas servidas (`real_dataset`).
- [x] `/health` e `/metrics` disponíveis.

## Ranking e filtros
- [x] Listagem `/api/opportunities` ordenável por score; filtros `region`, `manager`, `deal_stage`, `q`, `priority_band` coerentes com `docs/FILTER_EXECUTION_MODEL.md`.
- [x] UI: select escritório/estágio; combobox gestor com lista completa + filtro; limpar filtros repõe estado.

## Detalhe e explicações
- [x] Detalhe devolve `scoreExplanation` com fatores humanizados (`explanation_narrative`).
- [x] Próxima ação diversificada por contexto (`actions_by_context`).

## Modo padrão
- [x] Backend `real_dataset` por omissão; UI `api` por omissão (`docs/RUNTIME_DEFAULTS.md`).

## Idioma e labels
- [x] UI em PT-BR nos filtros principais; colunas alinhadas ao dataset real (conta, escritório, etc.).

## Inconsistências tratadas nesta auditoria
- Nenhuma divergência bloqueante encontrada após trilha FIN; regressão coberta por `python -m pytest -q`.

## Evidência
- Suíte verde local; capturas opcionais: `artifacts/process-log/ui-captures/` (guias existentes).
