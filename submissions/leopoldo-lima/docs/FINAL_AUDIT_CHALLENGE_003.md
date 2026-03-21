# Auditoria final — Challenge 003 (Lead Scorer)

**CRP:** CRP-REAL-10
**Data:** 2026-03-20
**Fonte de requisitos:** checklist de aderência do pacote gap-closure (`legacy/focus-score-challenge-gap-closure-pack/checklists/final_submission_checklist.md`) + critérios já mapeados em `docs/CHALLENGE_CHECKLIST.md`.

Legenda de status:

| Status | Significado |
|--------|-------------|
| **ATENDE** | Evidência verificável no repo; alinhado ao espírito do requisito. |
| **ATENDE PARCIALMENTE** | Funciona com ressalvas documentadas (ambiente, escopo ou gap menor). |
| **NÃO ATENDE** | Gap bloqueante ou ausência de evidência. |

---

## 1. Matriz — solução (produto)

| # | Requisito | Evidência | Status | Notas |
|---|-----------|-----------|--------|-------|
| S1 | Aplicação roda localmente com instruções claras | `docs/SETUP.md`, `docs/RUNBOOK.md`, `README.md` (Setup/Demo), `python .\scripts\tasks.py dev` | **ATENDE** | Docker opcional em `docs/RUNBOOK.md`. |
| S2 | Runtime principal usa dados reais do dataset | `src/api/dataset_loader.py` (default `real_dataset`), `data/*.csv`, `docs/SERVING_REAL_DATA.md`, `docs/RUNTIME_DATA_FLOW.md` | **ATENDE** | `demo_dataset` só para testes (`tests/conftest.py`). |
| S3 | Ranking / priorização de oportunidades | `GET /api/opportunities`, `GET /api/ranking` ordenados por score; `src/api/app.py`; UI em `public/` | **ATENDE** | ~8800 linhas em modo real. |
| S4 | Score explicável | `scoreExplanation` em detalhe (`src/api/view_models.py`, `src/scoring/engine.py`); `docs/SCORING_V2.md` | **ATENDE** | Fatores positivos/negativos, riscos, próxima ação. |
| S5 | UI ajuda a decidir onde focar | KPIs + tabela + detalhe em `public/`; `docs/UI_REAL_DATA_ALIGNMENT.md` | **ATENDE PARCIALMENTE** | Shell funcional e claro; sem E2E browser nem analytics avançados. |
| S6 | Filtros por vendedor, manager, região e estágio | API/UI: `region`, `manager`, `deal_stage` (`src/api/app.py`, `public/app.js`); pesquisa `q` em título e campos explícitos `sales_agent` / `seller` no payload | **ATENDE PARCIALMENTE** | **Gap incremental:** não há parâmetro HTTP dedicado `sales_agent`; o fluxo principal já cobre manager, região, estágio e pesquisa textual, sem invalidar a solução funcional nem a explicabilidade. |
| S7 | Scoring não é mera ordenação por valor | `config/scoring-rules.json` v2, `src/scoring/engine.py`, `src/features/engineering.py`, `tests/test_scoring_v2_features.py` | **ATENDE** | Estágio, idade no pipeline, conta, produto/região, qualidade de datas, etc. |

---

## 2. Matriz — repositório e framing

| # | Requisito | Evidência | Status | Notas |
|---|-----------|-----------|--------|-------|
| R1 | README como submissão final | `README.md`, `docs/README_DECISIONS.md` (CRP-REAL-07) | **ATENDE** | Secções exigidas + links para docs. |
| R2 | Sem artefatos residuais que confundam | `legacy/` isolado, `docs/REPO_SHAPE.md`, `legacy/README.md` | **ATENDE PARCIALMENTE** | Avaliador deve ignorar `legacy/` para o produto; está documentado. |
| R3 | Secção honesta de limitações | `README.md` (Limitações), `docs/SCORING_V2.md`, `PROCESS_LOG.md` | **ATENDE** | |
| R4 | Roteiro de demo | `docs/DEMO_SCRIPT.md` (fluxo real), `artifacts/process-log/ui-captures/REAL-09-SCREENSHOT-GUIDE.md` | **ATENDE** | Exports JSON: `python .\scripts\tasks.py export-real-flow-evidence`. |

---

## 3. Matriz — qualidade

| # | Requisito | Evidência | Status | Notas |
|---|-----------|-----------|--------|-------|
| Q1 | Testes no caminho principal com dados reais | `tests/test_real_dataset_main_flow.py`, `tests/test_real_dataset_serving.py`, `tests/test_serving_pipeline_integration.py`, `docs/TEST_STRATEGY_REAL_DATA.md` | **ATENDE** | |
| Q2 | Validação de dados e integridade referencial | `scripts/validate_data_quality.py`, `scripts/validate_referential_integrity.py`, `docs/DATA_QUALITY_RULES.md`, `docs/REFERENTIAL_INTEGRITY.md`, `artifacts/data-validation/` | **ATENDE** | |
| Q3 | Smoke do produto principal | `tests/test_ui_smoke.py`, `tests/test_api_contract.py` (demo), gates em `scripts/tasks.py build` | **ATENDE** | |
| Q4 | Evidência executável no PR | `artifacts/process-log/test-runs/crp-real-09-*.json`, testes `pytest`, `export-real-flow-evidence` | **ATENDE PARCIALMENTE** | PR remoto/GitHub Actions: depende de integração no remoto (`CHALLENGE_CHECKLIST` já marca parcial). |

---

## 4. Matriz — process log

| # | Requisito | Evidência | Status |
|---|-----------|-----------|--------|
| P1 | `PROCESS_LOG.md` atualizado por CRP | `PROCESS_LOG.md` (CRP-000…CRP-REAL-10, CRP-S*, etc.) | **ATENDE** |
| P2 | Evidências em `artifacts/process-log/` | `decision-notes/`, `test-runs/`, guias UI | **ATENDE** |
| P3 | Erros da IA e correções humanas registados | Entradas “Erro / limitação da IA”, “Decisões humanas”, `docs/IA_TRACE.md` | **ATENDE** |
| P4 | Iterações relevantes documentadas | Decomposição por CRP no `PROCESS_LOG.md` | **ATENDE** |

---

## 5. Pendências

### Bloqueantes para uma submissão mínima honesta
- **Nenhuma** identificada no estado atual do repositório (execução local + documentação + evidências em `artifacts/`).

### Não bloqueantes (melhorias)
- Filtro HTTP explícito por **vendedor / `sales_agent`** (hoje: manager, região, estágio e `q` já cobrem o fluxo principal; o parâmetro dedicado seria refinamento incremental).
- Capturas adicionais da UI para casos específicos de navegação, se o PR beneficiar de mais detalhe visual além das screenshots já incluídas na submissão.
- **CI remota** verde e badges públicos.
- **E2E** com browser.

---

## 6. Divergências (IA vs revisão humana)

| Tema | Risco da IA | Revisão humana (REAL-10) |
|------|-------------|---------------------------|
| Aderência ao challenge | Declarar “100% aderente” sem matriz | Esta página força **status por linha** e **PARCIAL** onde há gap incremental (filtro vendedor dedicado, CI remoto, profundidade de UI). |
| Demo | Misturar `OPP-001` com narrativa real | Corrigido em REAL-09; auditoria confirma uso de exemplos reais na demo principal. |

---

## 7. Parecer final de prontidão

**Decisão:** **SUBMETER** — o repositório está **pronto para submissão** no sentido do challenge 003, com **ressalvas explícitas** mas **não bloqueantes** (filtro vendedor dedicado e CI remota).

Recomendação operacional: abrir **PR** citando CRP-REAL-10; anexar ou referenciar este arquivo e os JSON em `artifacts/process-log/test-runs/crp-real-09-*.json`.

---

## 8. Checklist espelho (preenchido)

Referência: `legacy/focus-score-challenge-gap-closure-pack/checklists/final_submission_checklist.md`.

- [x] Aplicação roda localmente com instruções claras
- [x] Runtime principal usa dados reais
- [x] Ranking / priorização
- [x] Score explicável
- [x] UI ajuda a focar (com ressalva de profundidade)
- [x] Filtros manager, região, estágio; vendedor **parcial** (`q` + payload explícito / sem parâmetro dedicado)
- [x] Scoring ≠ só valor
- [x] README submissão final
- [x] Artefatos confusos mitigados (`legacy/` + docs)
- [x] Limitações explícitas
- [x] Roteiro de demo
- [x] Testes caminho real
- [x] Validação dados / integridade
- [x] Smoke produto
- [x] Evidência executável (local; PR remoto parcial)
- [x] Process log + evidências + IA/correções + iterações
