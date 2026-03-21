# CRP-REAL-09 — Guia de capturas da UI (fluxo **real_dataset**)

Gravar com **`LEAD_SCORER_DATA_SOURCE_MODE` não definido** (ou `real_dataset`) e API em `python .\scripts\tasks.py dev`.

## Onde guardar

| arquivo sugerido | Conteúdo |
|-------------------|----------|
| `artifacts/process-log/screenshots/real-09-dashboard-kpis-table.png` | Vista inicial: KPIs + tabela com IDs alfanuméricos (não `OPP-*`). |
| `artifacts/process-log/screenshots/real-09-detail-explanation.png` | Drawer ou detalhe com **scoreExplanation** e ID real (ex. `1C1I7A6R`). |
| `artifacts/process-log/screenshots/real-09-filters-central.png` | *(Opcional)* Filtro aplicado (ex. região Central) com linhas coerentes. |

## O que **não** colocar na submissão como “produto real”

- Capturas obtidas com `LEAD_SCORER_DATA_SOURCE_MODE=demo_dataset` (lista curta, IDs `OPP-001`…).
- Screenshots antigos que mostrem campo `status` em vez de **deal_stage** na UI, se já não refletirem o build atual.

## Revisão humana (checklist)

- [ ] URL visível ou documentada (`127.0.0.1:8787`).
- [ ] Pelo menos um ID com formato do `sales_pipeline.csv`.
- [ ] Texto de explicabilidade legível (fatores / próxima ação).

## Evidência API complementar

JSON exportados automaticamente (sem captura):

```powershell
python .\scripts\tasks.py export-real-flow-evidence
```

Saída: `artifacts/process-log/test-runs/crp-real-09-*.json`.
