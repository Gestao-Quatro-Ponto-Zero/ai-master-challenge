# UI — alinhamento ao dataset real (CRP-REAL-05)

## Objetivo
A superfície visível do **Focus Score Cockpit** deve deixar explícito que o produto opera sobre o **pipeline oficial** do challenge (CSVs em `data/`), não sobre um protótipo genérico.

## Antes → depois (resumo)

| Área | Antes | Depois |
|------|--------|--------|
| Cabeçalho | Subtítulo genérico | Copy B2B + referência ao dataset oficial (`sales_pipeline` + dimensões) |
| Tabela | ID, “Título”, estágio, score | **ID oportunidade**, **Conta**, **Produto**, **Vendedor**, **Gestor**, **Escritório regional**, **Estágio**, **Valor fecho**, score |
| Filtros | Placeholders “Core” / “Marcos” | Exemplos alinhados ao CSV real (**Central**, **Dustin Brinkmann**, **Engaging**) + texto explicando mapeamento API |
| KPIs | Não exibidos | Faixa de KPIs via `GET /api/dashboard/kpis` (totais do pipeline servido) |
| Detalhe | JSON bruto em `<pre>` | Secções estruturadas: factos do pipeline + score com listas de fatores/ riscos |
| Modo mock | Nomes “Demo” | Rótulos **explicitamente** “modo mock” / ilustrativo para não confundir com produção |

## Campos exibidos vs dataset

| Campo na UI | Origem API / CSV |
|-------------|------------------|
| ID oportunidade | `sales_pipeline.opportunity_id` → `id` |
| Conta | `accounts.account` (join) → `account`; fallback `title` quando conta ausente no modo demo |
| Produto | Produto canónico pós-normalização → `product` |
| Vendedor | `sales_teams.sales_agent` → `sales_agent` / `seller` |
| Gestor | `sales_teams.manager` → `manager` |
| Escritório | `sales_teams.regional_office` → `regional_office` (fallback `region` na UI) |
| Estágio | `deal_stage` oficial |
| Valor fecho | `close_value` / `amount` |
| Explicação | `scoreExplanation` (motor v2) |

## Decisões de UX
- **Sem `fetch` em `app.js`:** KPIs e listas passam pelo repositório (`getDashboardKpis`), mantendo o gate `validate_ui_quality.py`.
- **Moeda:** formatação `Intl` USD para consistência com `close_value` numérico do dataset (ajustável se o challenge fixar outra moeda).
- **IA / rótulos genéricos:** propostas do tipo “Core/Marcos” como única narrativa foram substituídas por texto que distingue **exemplo de filtro** vs **campos reais** e por placeholders do CSV.

## Evidências
- Capturas com `LEAD_SCORER_DATA_SOURCE_MODE` omisso ou `real_dataset`: tabela com IDs do `sales_pipeline`, KPIs coerentes com ~8k linhas.
- Captura do detalhe com listas de fatores positivos/negativos.
- Nota comparativa: `artifacts/process-log/decision-notes/crp-real-05-ui-real-data.md`.

## Verificação
```powershell
python -m pytest -q tests/test_ui_smoke.py tests/test_ui_front_coverage.py tests/test_api_contract.py
python .\scripts\validate_ui_quality.py
```
