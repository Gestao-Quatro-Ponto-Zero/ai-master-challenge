# CRP-REAL-08 — Evidência: testes no caminho real

**Data:** 2026-03-20  
**CRP:** CRP-REAL-08 (`legacy/focus-score-challenge-gap-closure-pack/crps/CRP-REAL-08-upgrade-tests-to-real-dataset-path.md`)

## Output de testes

Executar na raiz do repositório:

```powershell
python -m pytest -q
```

Esperado: suíte verde (inclui `tests/test_real_dataset_main_flow.py`).

## Prova de exercício sobre CSV real

- `test_real_dataset_main_flow` usa `monkeypatch.delenv("LEAD_SCORER_DATA_SOURCE_MODE")` → modo **`real_dataset`**.
- Dados vêm de `src/api/dataset_loader.py` → `build_serving_opportunities()` → arquivos em `data/*.csv`.
- ID fixo `1C1I7A6R` alinhado a `tests/test_serving_pipeline_integration.py` e ao dataset.

## Resumo coberto / não coberto

Ver `docs/TEST_STRATEGY_REAL_DATA.md`.

## Gaps antigos de teste (registo)

- Contrato API (`test_api_contract.py`) corria quase só sobre **demo**; o fluxo “challenge” (milhares de linhas reais) dependia de poucos testes dispersos — consolidado com `test_real_dataset_main_flow.py`.

## Validação humana

- Cenários críticos: filtros coerentes com uma linha real; `q` com substring existente; KPIs somando estágios; explainability com estrutura estável.

## Artefatos

- `tests/test_real_dataset_main_flow.py`
- `docs/TEST_STRATEGY_REAL_DATA.md`
- `docs/TEST_STRATEGY.md`, `README.md`, `LOG.md`, `PROCESS_LOG.md`
