# Test Strategy

## Objetivo
Garantir que o fluxo crítico do challenge (`dados -> scoring -> API -> UI shell`) seja verificável com comandos curtos e repetíveis.

## Comando único

```powershell
python -m pytest -q
```

**Dataset real vs demo:** ver [`TEST_STRATEGY_REAL_DATA.md`](./TEST_STRATEGY_REAL_DATA.md) — o fluxo principal do challenge é coberto por testes que carregam os CSVs oficiais; `test_api_contract.py` permanece em modo `demo_dataset` (determinístico).

Comando equivalente no fluxo do projeto:

```powershell
python .\scripts\tasks.py test
python .\scripts\tasks.py build
```

## Pirâmide mínima aplicada
- **Unidade (`tests/test_scoring_engine.py`)**
  - determinismo do scoring para mesma entrada
  - risco e penalidade para `account` ausente
- **Integração/contrato API (`tests/test_api_contract.py`)** — modo **`demo_dataset`** (fixture em `conftest.py`)
  - ranking ordenado por score
  - detalhe por ID e `404` para oportunidade inexistente
  - filtros (`region`, `manager`, `deal_stage`) afetando resultado
- **Integração API + CSVs reais (`tests/test_real_dataset_main_flow.py`, `test_real_dataset_serving.py`, `test_serving_pipeline_integration.py`)**
  - volume, filtros, `q`, KPIs, explainability e pipeline de serving
- **Smoke UI (`tests/test_ui_smoke.py`)**
  - assets da UI existem
  - script da UI aponta para endpoints corretos
  - rota `/` entrega HTML principal
  - rota inexistente retorna `404`
- **Cobertura UI (`tests/test_ui_front_coverage.py`)**
  - estados críticos de loading/erro/vazio/not found/cancelamento
  - acessibilidade básica de teclado e persistência de seleção
  - contrato mínimo de fixtures mock

## Escopo crítico coberto
1. Regras de score com explicabilidade.
2. Payload HTTP consumível para demo.
3. Fluxo principal de navegação da UI shell.
4. Comportamento esperado para casos de erro (`404`).
5. Regressões visíveis de UX operacional no dashboard.

## Fora de escopo (por agora)
- Testes E2E com navegador real.
- Testes de performance/carga.
- Cobertura de todas as regras futuras de dados/normalização.

Detalhes da trilha UI em `docs/TEST_STRATEGY_UI.md`.

## Evidência para submissão
- Referenciar no `PROCESS_LOG.md`:
  - comando executado
  - resultado verde
  - falhas encontradas e correções
  - revisão humana final da suíte
