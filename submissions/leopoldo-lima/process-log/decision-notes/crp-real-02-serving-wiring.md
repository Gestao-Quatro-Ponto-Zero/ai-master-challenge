# CRP-REAL-02 — Evidência: wiring CSV → serving

## Endpoint real (ID do `sales_pipeline.csv`)

- `GET /api/opportunities/1C1I7A6R` → 200, `title` = conta **Cancity**, `seller` = **Moses Frase**.
- Corpo JSON arquivado: `artifacts/process-log/test-runs/crp-real-02-detail-1C1I7A6R.json`.

## UI (verificação humana)

1. `python .\scripts\tasks.py dev` (sem `demo_dataset`).
2. Abrir `http://127.0.0.1:8787/`.
3. Confirmar que a listagem não usa IDs `OPP-00x` e que o detalhe de uma linha bate com conta/agente do CSV.

## Testes automatizados

- `tests/test_serving_pipeline_integration.py` — contagens, join produto/série/preço, API detalhe.
- `tests/test_real_dataset_serving.py` — smoke modo real (mantido do REAL-01).

## Notas

- Cache in-memory do pipeline invalida quando muda o mtime dos 5 CSVs; testes chamam `clear_serving_cache()` para isolamento.
