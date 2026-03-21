# CRP-REAL-01 — Baseline runtime real (evidência)

## Diagnóstico (caminho demo dominante)

- **`src/api/app.py`** lia apenas `data/demo-opportunities.json` em todas as rotas de listagem/detalhe/KPIs — o avaliador que testasse a API sem ler o código veria sempre o snapshot sintético, apesar dos CSVs oficiais existirem e serem validados noutros scripts.
- **Ferramentas:** pesquisa no repositório (`demo-opportunities`, `_load_demo_rows`) e leitura de `sales_pipeline.csv` / `docs/DATA_CONTRACT.md`.
- **UI:** `public/infrastructure/repositories/repository-factory.js` já preferia API; o problema era o **backend** a servir JSON demo por defeito.
- **Erro/simplificação da IA (risco):** assumir que `LEAD_SCORER_REPOSITORY_MODE=api` já implicava “dados reais” — na verdade esse modo refere-se ao **cliente repositório Python**, não ao dataset do processo HTTP.

## Decisões humanas

- Introduzir **`LEAD_SCORER_DATA_SOURCE_MODE`** separado do modo repositório, para não misturar “chamar API remota” com “de onde vêm as linhas neste processo”.
- Manter **`demo_dataset`** para `tests/test_api_contract.py` (asserts sobre `OPP-001`, `Core`, etc.) via `tests/conftest.py`.
- Não remover `demo-opportunities.json` neste CRP (escopo: tornar real o padrão, não apagar legado).

## arquivos que ainda usam demo e porquê

| Artefato | Uso |
|----------|-----|
| `data/demo-opportunities.json` | Modo `demo_dataset` + testes de contrato API |
| `public/infrastructure/mocks/*` | UI em modo `mock` (JavaScript), isolado da factory principal |
| `src/infrastructure/repositories/mock_opportunity_repository.py` | `LEAD_SCORER_REPOSITORY_MODE=mock` (Python) |

## Evidência executável

- Testes: `python -m pytest -q tests/test_real_dataset_serving.py`
- Amostra de resposta (modo real): `artifacts/process-log/test-runs/crp-real-01-sample-ranking-real.json` (schema atualizado em **CRP-REAL-09** via `export-real-flow-evidence`: `deal_stage`, campos explícitos.)
- Log de arranque: evento `api_startup` com `lead_scorer_data_source_mode`

## Verificação humana sugerida

1. `python .\scripts\tasks.py dev` sem definir a variável → `GET /api/ranking?limit=1` deve devolver `total` ~8800 e `id` alfanumérico (não `OPP-001`).
2. `LEAD_SCORER_DATA_SOURCE_MODE=demo_dataset` → `GET /api/opportunities/OPP-001` → 200.

## Próximo CRP

**CRP-REAL-02** — ligar CSVs à serving layer com maior profundidade (este CRP já faz join mínimo; REAL-02 pode refinar modelagem, cache e alinhamento ao domínio).
