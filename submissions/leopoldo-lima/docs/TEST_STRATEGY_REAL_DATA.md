# Estratégia de testes — caminho principal com dataset real (CRP-REAL-08)

## Objetivo

Garantir que a suíte **protege o fluxo que importa para o challenge**: serving a partir dos **CSVs oficiais** em `data/`, não apenas o snapshot JSON de demo.

## Comando

```powershell
python -m pytest -q
```

## arquivos e papel

| arquivo | O quê |
|----------|--------|
| `tests/test_real_dataset_main_flow.py` | **Fluxo HTTP principal** em modo `real_dataset` (default): filtros, `q`, detalhe com explainability, KPIs, `/api/ranking` + `/api/opportunities`. |
| `tests/test_real_dataset_serving.py` | Smoke inicial REAL-01: volume do ranking, detalhe round-trip, filter-options, regressão modo demo. |
| `tests/test_serving_pipeline_integration.py` | Pipeline `build_serving_opportunities`, FKs, detalhe API para ID conhecido do CSV. |
| `tests/test_api_contract.py` | Contrato **determinístico** com `demo_dataset` (fixture em `conftest.py`) — IDs/regiões do JSON fixo. |

## O que está coberto (real)

- Carga implícita dos CSVs via `load_opportunity_rows_for_serving()` / pipeline (validada também em `test_serving_pipeline_integration.py`).
- Ranking e listagem com **grandes volumes** (`total` ≥ 8000) em `test_real_dataset_serving.py`.
- **Filtros** `region`, `manager`, `deal_stage` consistentes entre `/api/opportunities` e `/api/ranking`.
- **Pesquisa** `q` sobre título com needle derivado de amostra real.
- **Explainability**: `scoreExplanation` com tipos e `priority_band` esperados no detalhe (`1C1I7A6R`).
- **Dashboard KPIs**: soma `open + won + lost` = `total_opportunities`.

## O que ainda não está coberto (gaps conscientes)

- E2E com browser; performance/carga.
- Todos os cantos de normalização de produto/conta (parcialmente em outros testes de domínio).
- CI remota obrigatória (validação local + workflows no repo).

## Evidência

- Output verde de `python -m pytest -q`.
- Nota de decisão: `artifacts/process-log/decision-notes/crp-real-08-real-data-tests.md`.

## Relação com demo

`tests/conftest.py` força `LEAD_SCORER_DATA_SOURCE_MODE=demo_dataset` **apenas** para `test_api_contract.py`, para não quebrar asserções em `OPP-001` / regiões do demo. O caminho principal do produto continua validado pelos testes **real** acima.
