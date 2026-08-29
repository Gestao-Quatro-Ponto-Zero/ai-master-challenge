# Evidence Index — paths versionados da submissão (todos os links relativos resolvem)

- **Tipo:** artefato obrigatório do process log (Iteração 08)
- **Escopo:** índice completo dos arquivos versionados em `submissions/jose-nascimento/` (branch `submission/jose-nascimento`), com links relativos. Links relativos resolvem a partir **deste arquivo** (`process-log/`); o verificador (`../solution/src/06_verify_pipeline.py`, gates G1–G11) confere presença e resolução a cada execução.
- **Sobre os reports brutos de revisão (não copiados):** cada gate 3x (It00–08) produziu 3 reports externos read-only dos revisores (27 no total) em working artifacts **fora do repo** — eles não são versionados de propósito (evidência fora da pasta permitida e fora do controle de versão). A evidência persistente é: (a) os **9 review summaries** versionados em `reviews/` (veredictos, matriz finding→ação→arquivo:linha, recálculos, gate); (b) os **fix reports**; (c) os **prompts transcritos**; (d) o **git history**. Os 27 reports brutos são material de trabalho citável apenas por referência aos summaries.
- **Paths de máquina históricos:** summaries antigos (It00–07) podem conter, em células de tabela, metadados literais de diretórios temporários onde viveram os reports externos dos revisores — são registros históricos pré-política F2 (a política exige zero **links** para diretórios temporários e zero paths de máquina em **docs novos**; ver gates G3/G4).
- **Git history:** 26 commits do candidato no HEAD `9e60315` (commit do process log); **27 no fechamento da It08** (após o commit do fixer do gate) + 5 commits de base do repo oficial; todos os hashes citados abaixo resolvem (`git rev-parse`).

---

## 1. Entradas

| Path | Papel |
|---|---|
| [`../README.md`](../README.md) | README da submissão no template oficial (executive summary, solução, process log, evidências, data `pendente`) |
| [`README.md`](README.md) | **Este process log — entrada principal** (escopo, ferramentas, pipeline, decomposição It00–08, erros, evidence map) |
| [`../run.sh`](../run.sh) | Pipeline em 1 comando (`./run.sh`; estágios 01–05 + 07 + verificador 06) |
| [`../Makefile`](../Makefile) | `make all` == `./run.sh`; `make verify`; `clean-derived` (40 arquivos, contagem derivada) |
| [`../requirements.txt`](../requirements.txt) | Dependências mínimas pinadas (pandas==3.0.5, matplotlib==3.11.1) |
| [`../solution/README.md`](../solution/README.md) | Documentação da solução (setup, outputs, estrutura, tempo/memória, troubleshooting) |

## 2. Governança de processo (`management/`)

| Path | Papel |
|---|---|
| [`management/execution-plan.md`](management/execution-plan.md) | Plano de execução: regras 1–8, política de contenção §2, iterações com status e evidência |
| [`management/orchestrator-checklist.md`](management/orchestrator-checklist.md) | Checklist interno do orquestrador (A–F; estados `PENDING/OPEN/CONCLUDED`) |
| [`management/orchestration-architecture.md`](management/orchestration-architecture.md) | **Fonte atual de verdade de ferramenta/processo**: papéis, modelos runtime, contexto, permissões, limitações, fontes |

## 3. Prompts transcritos fielmente (`prompts/`) — 20 arquivos (snapshot no fechamento da It08)

Prompts recebidos pelos agentes (executor/corretor) e pelo adendo, transcritos fielmente; a partir da It08 com **paths operacionais normalizados** (política F2/It08 — categorias e motivo na nota do próprio `iteration-08-prompt.md`; prompts de It00–07 são transcrições integrais com exceção histórica documentada no checklist F2). Contagem = snapshot no fechamento da It08; re-derivar na It09/10.

| Iteração | Prompt da etapa | Prompt da correção (fixer) |
|---|---|---|
| It00 | [`prompts/iteration-00-prompt.md`](prompts/iteration-00-prompt.md) | [`prompts/iteration-00-review-fix-prompt.md`](prompts/iteration-00-review-fix-prompt.md) |
| It01 | [`prompts/iteration-01-prompt.md`](prompts/iteration-01-prompt.md) | [`prompts/iteration-01-review-fix-prompt.md`](prompts/iteration-01-review-fix-prompt.md) |
| It02 | [`prompts/iteration-02-prompt.md`](prompts/iteration-02-prompt.md) | [`prompts/iteration-02-review-fix-prompt.md`](prompts/iteration-02-review-fix-prompt.md) |
| It03 | [`prompts/iteration-03-prompt.md`](prompts/iteration-03-prompt.md) | [`prompts/iteration-03-review-fix-prompt.md`](prompts/iteration-03-review-fix-prompt.md) |
| It04 | [`prompts/iteration-04-prompt.md`](prompts/iteration-04-prompt.md) | [`prompts/iteration-04-review-fix-prompt.md`](prompts/iteration-04-review-fix-prompt.md) |
| It05 | [`prompts/iteration-05-prompt.md`](prompts/iteration-05-prompt.md) | [`prompts/iteration-05-review-fix-prompt.md`](prompts/iteration-05-review-fix-prompt.md) |
| It06 | [`prompts/iteration-06-prompt.md`](prompts/iteration-06-prompt.md) | [`prompts/iteration-06-review-fix-prompt.md`](prompts/iteration-06-review-fix-prompt.md) |
| It07 | [`prompts/iteration-07-prompt.md`](prompts/iteration-07-prompt.md) | [`prompts/iteration-07-review-fix-prompt.md`](prompts/iteration-07-review-fix-prompt.md) |
| It08 | [`prompts/iteration-08-prompt.md`](prompts/iteration-08-prompt.md) | [`prompts/iteration-08-review-fix-prompt.md`](prompts/iteration-08-review-fix-prompt.md) (gate 3x `CONCLUDED` — findings LOW documentais) |
| Especiais | [`prompts/orchestration-architecture-addendum-prompt.md`](prompts/orchestration-architecture-addendum-prompt.md) · [`prompts/orchestrator-visual-correction-prompt.md`](prompts/orchestrator-visual-correction-prompt.md) | — |

## 4. Reports (`reports/`) — 20 arquivos (snapshot no fechamento da It08)

| Path | Papel |
|---|---|
| [`reports/iteration-00-planning-report.md`](reports/iteration-00-planning-report.md) · [`reports/iteration-00-review-fix-report.md`](reports/iteration-00-review-fix-report.md) | Planejamento/governança + correção do gate It00 |
| [`reports/iteration-01-ingest-audit-report.md`](reports/iteration-01-ingest-audit-report.md) · [`reports/iteration-01-review-fix-report.md`](reports/iteration-01-review-fix-report.md) | Auditoria dos 5 datasets + correção do gate It01 |
| [`reports/iteration-02-reconciliation-report.md`](reports/iteration-02-reconciliation-report.md) · [`reports/iteration-02-review-fix-report.md`](reports/iteration-02-review-fix-report.md) | Reconciliação/contrato + correção do gate It02 |
| [`reports/iteration-03-root-cause-report.md`](reports/iteration-03-root-cause-report.md) · [`reports/iteration-03-review-fix-report.md`](reports/iteration-03-review-fix-report.md) | Causa raiz/coortes + correção do gate It03 |
| [`reports/iteration-04-lifecycle-watchlist-report.md`](reports/iteration-04-lifecycle-watchlist-report.md) · [`reports/iteration-04-review-fix-report.md`](reports/iteration-04-review-fix-report.md) | Jornada/watchlist + correção do gate It04 |
| [`reports/iteration-05-actions-impact-report.md`](reports/iteration-05-actions-impact-report.md) · [`reports/iteration-05-review-fix-report.md`](reports/iteration-05-review-fix-report.md) | Ações/impacto + correção do gate It05 |
| [`reports/iteration-06-reproducibility-report.md`](reports/iteration-06-reproducibility-report.md) · [`reports/iteration-06-review-fix-report.md`](reports/iteration-06-review-fix-report.md) | Pipeline reproduzível + correção do gate It06 |
| [`reports/iteration-07-executive-report.md`](reports/iteration-07-executive-report.md) · [`reports/iteration-07-review-fix-report.md`](reports/iteration-07-review-fix-report.md) | Relatório executivo + correção do gate It07 |
| [`reports/iteration-08-process-log-report.md`](reports/iteration-08-process-log-report.md) · [`reports/iteration-08-review-fix-report.md`](reports/iteration-08-review-fix-report.md) | **Esta iteração** (método de inventário, decisões, números, validações, handoff It09) + fixer do gate 3x (findings→ações, reconciliação F11, snapshots) |
| [`reports/orchestration-architecture-addendum-report.md`](reports/orchestration-architecture-addendum-report.md) · [`reports/orchestrator-visual-correction-report.md`](reports/orchestrator-visual-correction-report.md) | Adendo de arquitetura + correção visual pós-gate It04 |

## 5. Review summaries (`reviews/`) — 9 ledgers versionados (evidência persistente dos gates 3x; snapshot no fechamento da It08)

| Gate | Veredictos | Ledger |
|---|---|---|
| It00 | PASS_WITH_FIXES ×3 | [`reviews/iteration-00-review-summary.md`](reviews/iteration-00-review-summary.md) |
| It01 | PASS_WITH_FIXES ×3 | [`reviews/iteration-01-review-summary.md`](reviews/iteration-01-review-summary.md) |
| It02 | PASS ×2 + PASS_WITH_FIXES ×1 | [`reviews/iteration-02-review-summary.md`](reviews/iteration-02-review-summary.md) |
| It03 | PASS_WITH_FIXES ×3 | [`reviews/iteration-03-review-summary.md`](reviews/iteration-03-review-summary.md) |
| It04 | PASS_WITH_FIXES ×3 | [`reviews/iteration-04-review-summary.md`](reviews/iteration-04-review-summary.md) |
| It05 | PASS_WITH_FIXES ×3 | [`reviews/iteration-05-review-summary.md`](reviews/iteration-05-review-summary.md) |
| It06 | PASS_WITH_FIXES / PASS / PASS_WITH_FIXES | [`reviews/iteration-06-review-summary.md`](reviews/iteration-06-review-summary.md) |
| It07 | PASS_WITH_FIXES ×2 + PASS | [`reviews/iteration-07-review-summary.md`](reviews/iteration-07-review-summary.md) |
| It08 | PASS_WITH_FIXES ×3 (fixer aplicado; gate `CONCLUDED`) | [`reviews/iteration-08-review-summary.md`](reviews/iteration-08-review-summary.md) |

## 6. Decisões (`decisions/`) e hipóteses (`hypotheses/`)

| Path | Papel |
|---|---|
| [`decisions/decision-ledger.md`](decisions/decision-ledger.md) | **Este ledger consolidado** (candidato vs orquestrador vs executor vs revisores) |
| [`decisions/iteration-02-analytical-contract-decisions.md`](decisions/iteration-02-analytical-contract-decisions.md) | D1–D10 do contrato analítico (lentes, grão, winner, política `closed_at`) |
| [`decisions/iteration-03-root-cause-decisions.md`](decisions/iteration-03-root-cause-decisions.md) | D1–D6 + adendos D7–D11 (pico, tenure, suporte, bucket 0d, NO-GO) |
| [`decisions/iteration-04-watchlist-decisions.md`](decisions/iteration-04-watchlist-decisions.md) | D1–D9 pré-especificados (backtest point-in-time, watchlist operational priority) |
| [`decisions/iteration-05-action-impact-assumptions.md`](decisions/iteration-05-action-impact-assumptions.md) | Premissas de ação/impacto/medição commitadas ANTES do cálculo |
| [`decisions/iteration-06-reproducibility-decisions.md`](decisions/iteration-06-reproducibility-decisions.md) | D1–D5 da reprodutibilidade (1 comando, verificador, hygiene) |
| [`decisions/iteration-07-executive-report-outline.md`](decisions/iteration-07-executive-report-outline.md) | Narrativa do relatório executivo decidida ANTES da redação (+ adendos §13–§15) |
| [`hypotheses/iteration-03-root-cause-hypotheses.md`](hypotheses/iteration-03-root-cause-hypotheses.md) | H1–H10 com thresholds fixados ANTES da análise (commit `8cb93c3`) |

## 7. Erros reais (`errors/`)

| Path | Papel |
|---|---|
| [`errors/ai-errors-and-corrections.md`](errors/ai-errors-and-corrections.md) | **8 erros materiais** (E1–E8) com causa raiz, detecção, correção, validação e commit |

## 8. Solução (`solution/`)

| Path | Papel |
|---|---|
| [`../solution/report-executivo.md`](../solution/report-executivo.md) | Relatório executivo (CEO) — números 100% derivados em runtime, 6 gráficos, 41 links relativos |
| [`../solution/docs/analytical-contract.md`](../solution/docs/analytical-contract.md) | Contrato analítico (definição de churn, grão, métricas, lentes R1/R2, invariantes) |
| [`../solution/evidence/01_audit_report.md`](../solution/evidence/01_audit_report.md) · [`02_consistency_report.md`](../solution/evidence/02_consistency_report.md) · [`03_root_cause_report.md`](../solution/evidence/03_root_cause_report.md) · [`04_lifecycle_watchlist_report.md`](../solution/evidence/04_lifecycle_watchlist_report.md) · [`05_action_plan.md`](../solution/evidence/05_action_plan.md) | Evidence das It01–05 (gates PASS, números rastreáveis) |
| [`../solution/src/01_ingest_audit.py`](../solution/src/01_ingest_audit.py) · [`02_reconcile_churn.py`](../solution/src/02_reconcile_churn.py) · [`03_root_cause.py`](../solution/src/03_root_cause.py) · [`04_lifecycle_watchlist.py`](../solution/src/04_lifecycle_watchlist.py) · [`05_actions_impact.py`](../solution/src/05_actions_impact.py) · [`06_verify_pipeline.py`](../solution/src/06_verify_pipeline.py) · [`07_generate_executive_report.py`](../solution/src/07_generate_executive_report.py) | Estágios 01–05 + verificador + gerador do relatório |
| [`../solution/data/raw/README.md`](../solution/data/raw/README.md) + 5 CSVs | Dados brutos commitados (origem, licença MIT, MD5, contagens 500/5.000/25.000/2.000/600) |
| [`../solution/data/processed/README.md`](../solution/data/processed/README.md) + [`account_month.csv`](../solution/data/processed/account_month.csv) | Painel account-month (5.807 linhas; checksum; README com semântica) |
| [`../solution/out/tables/`](../solution/out/tables/) (26 CSVs t01–t21) | Tabelas de auditabilidade (séries, KM, onboarding, jornada, backtest, watchlist, ações, impacto) |
| [`../solution/out/charts/`](../solution/out/charts/) (exatamente 6 PNGs) | `a_monthly_events_and_rate.png` · `b_km_by_signup_quarter.png` · `c_onboarding_exposure_by_duration.png` · `d_usage_volume_vs_intensity.png` · `It04_c_lifecycle_vs_current_mrr.png` · `It04_d_backtest_lift.png` (4 PNGs pruned NÃO podem reaparecer — gate A6) |

## 9. Git history (branch `submission/jose-nascimento`)

26 commits do candidato no HEAD do process log (`9e60315`); **27 no fechamento da It08** (commit do fixer do gate 3x); + 5 de base do repo oficial. Hashes resolvem via `git rev-parse` (verificador G9). Mapeamento por iteração (commit de etapa → commit de correção do gate):

| Iteração | Commits (curtos) |
|---|---|
| Base (repo oficial) | `d91427f` · `d4c8fc7` · `4b55509` · `bcdfd2e` · `4aed364` |
| It00 | `1f3017a` · `efdec24` → fix `9907024` |
| It01 | `a40e129` · `80f6a3f` → fix `b9823da` |
| It02 | `9305e2e` → fix `9378a86` (+ registro `6e7be69`) |
| It03 | `8cb93c3` (hipóteses) · `9e02e18` (análise) → fix `12ff47c` |
| It04 | `adbbad7` · `fb9d2de` → fix `1517a73` → visual `617e4ac` (pós-gate) |
| It05 | `dc5748f` (premissas) · `a8a6ca6` → fix `e0c6b7e` |
| It06 | `9357c20` → fix `fa6572f` |
| It07 | `1bbec67` (outline) · `a726cb4` (relatório) → fix `a1e99cb` |
| It08 | `docs: consolidate AI process log and evidence` (`9e60315`) → fix do gate `docs: reconcile process log review evidence` |

## 10. Cobertura do índice

- **Total de arquivos versionados na pasta (snapshot no fechamento da It08):** 114 antes da It08 → 120 no commit do process log (`9e60315`) → **123** após o fixer do gate 3x (review summary, fix prompt, fix report).
- **Glob de cobertura:** todo path listado acima existe em `git ls-files` (verificador G1/G7/G8 re-checa a cada execução); todo link relativo deste arquivo e dos demais docs novos resolve (G3).
- **Não incluídos (working artifacts):** os 27 reports brutos de revisão externos (fora do repo, read-only) — evidência persistente nos 9 summaries (§5); sandboxes e logs de validação fora do repo.