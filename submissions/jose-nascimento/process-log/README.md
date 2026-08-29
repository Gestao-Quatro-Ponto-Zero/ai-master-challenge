# Process Log — Challenge 001 (Diagnóstico de Churn · RavenStack)

**Entrada principal do process log** (Iteração 08; atualizado no fechamento da It09 — QA final integral e fechamento do gate 3x). Documenta, com evidência versionada, **como** a submissão de Jose Nascimento foi produzida: ferramentas, pipeline de agentes, decomposição cronológica It00–09, erros reais da IA com correção, decisões humanas vs de modelo, limitações e mapa de evidência. Este arquivo é curto de propósito — cada seção aponta para o artefato detalhado.

---

## 1. Escopo e ferramentas (e por quê)

| Ferramenta / papel | Modelo (runtime) | O que faz | Por quê |
|---|---|---|---|
| **Orquestrador** (OpenCode, sessão compartilhada) | `openai/gpt-5.6-sol` ("GPT 5.6 Sol Max", perfil de máxima capacidade) | Mantém contexto global/estado; decompõe em iterações; escreve prompts/contratos; arbitra divergências; controla gates e risco. **Não executa scripts nem edita a solução** — exceção única: visualizou os PNGs e descreveu problemas (inspeção ocular, It04) | Decompor o problema e escrever contratos é a decisão de maior alavancagem; o modelo de maior capacidade foi reservado a esse trabalho (decisão arquitetural desta execução) |
| **Executor** (1 por iteração, serial) | `deepseek-max` = DeepSeek V4 Flash, max reasoning, via OpenCode Go | Implementa a etapa com contexto novo/limpo e escopo fechado; testa; documenta; commit/push | Trabalho bounded e repetível no modelo mais rápido/eficiente; contexto limpo reduz ancoragem; 1 executor por vez mantém git linear |
| **Revisores** (3 por gate, paralelos, read-only) | `deepseek-max` (mesmo modelo, 3 instâncias) | Mesmo prompt, contextos separados, sandboxes fora do repo; 3 reports externos com veredicto + findings | Independência de **contexto/amostragem**, NÃO diversidade de modelo — erros correlacionados ainda são possíveis (declarado) |
| **Corretor** (sequencial, quando necessário) | `deepseek-max` (nova instância) | Lê os 3 reports, resolve findings materiais, testa/recalcula, registra review summary, commit/push | Um único passe de correção evita correções concorrentes |

**Detalhe completo:** [`management/orchestration-architecture.md`](management/orchestration-architecture.md) (papéis, permissões, rationale, limitações, fontes) — fonte atual de verdade de ferramenta/processo. Candidato definiu: escolha do Challenge 001, ferramenta, subagentes sequenciais, revisão 3x, originalidade, ângulos, inspeção visual e auditoria final — ver [decision ledger](decisions/decision-ledger.md).

## 2. Pipeline (diagrama)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ORQUESTRADOR — OpenCode · openai/gpt-5.6-sol ("GPT 5.6 Sol Max")          │
│ contexto global · decompõe · escreve prompt/contrato · arbitra · gates    │
│ NÃO executa scripts · NÃO edita a solução (exceção: inspeção ocular PNGs) │
└──────────────────────────────────────────────────────────────────────────┘
        │  prompt da etapa (escopo fechado, critérios, commit esperado)
        ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ EXECUTOR — exatamente 1 subagente deepseek-max por iteração (serial)      │
│ contexto novo/limpo · implementa → testa → documenta → commit/push        │
└──────────────────────────────────────────────────────────────────────────┘
        │  iteração CONCLUDED (validada pelo executor)
        ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ REVISÃO 3× — 3 subagentes deepseek-max INDEPENDENTES EM PARALELO          │
│ mesmo prompt · contexto separado · READ-ONLY (sandboxes fora do repo)     │
│ → 3 reports externos únicos (veredicto + findings)                        │
└──────────────────────────────────────────────────────────────────────────┘
        │  finding material? ── sim ──► FIXER (1 deepseek-max sequencial:
        │  não (gate CONCLUDED)          lê 3 reports · corrige · testa ·
        ▼                                registra summary · commit/push) ──► gate
   próxima iteração (serial)            └───────────────────────────────┘
```

Estados: `PENDING` (não iniciado) / `OPEN` (executor trabalhando) / `CONCLUDED` (implementação validada pelo executor). O review gate 3x é rastreado **separadamente** (B3 no checklist; summaries em `reviews/`).

## 3. Decomposição cronológica (It00–09)

> Cada iteração = 1 executor serial + prompt arquivado + report; ao fim, gate 3x read-only (+ fixer se findings materiais). Contagens derivadas de git/artefatos na §7.

| It | Objetivo | IA usada | Decisão/julgamento-chave | Output | Commit / evidência |
|---|---|---|---|---|---|
| **00** | Planejamento e governança (plano, checklist, ferramenta real) | executor `deepseek-max` + gate 3x | Corrigir ferramenta alegada no scaffold; política de contenção; estados do plano | plano, checklist, prompt, report | `efdec24` → fix `9907024`; [report](reports/iteration-00-planning-report.md), [review](reviews/iteration-00-review-summary.md) |
| **01** | Ingestão e auditoria dos 5 datasets (contagens, schema, nulos, sinteticidade) | executor + gate 3x | Erro E1 corrigido (schema → KeyError + stale); parecer de sinteticidade com evidência | 5 CSVs commitados, `01_ingest_audit.py`, evidence 01 | `a40e129`/`80f6a3f` → fix `b9823da`; [review](reviews/iteration-01-review-summary.md) |
| **02** | Reconciliação das lentes de churn + contrato analítico (grão, winner, invariantes) | executor + gate 3x | Erro E2 corrigido (winner escondia 422.691); lentes R1/R2; política `closed_at` | `02_reconcile_churn.py`, contrato, account_month | `9305e2e` → fix `9378a86`; [review](reviews/iteration-02-review-summary.md), [decisões](decisions/iteration-02-analytical-contract-decisions.md) |
| **03** | Causa raiz, coortes, onboarding economics — hipóteses **antes** da análise | executor + gate 3x | Erros E3/E4 corrigidos (janela pré-signup; KM degrau); vereditos H1–H10; NO-GO de modelo preditivo | `03_root_cause.py`, evidence 03, 4 PNGs, 13 tabelas | `8cb93c3` (hipóteses) · `9e02e18` → fix `12ff47c`; [review](reviews/iteration-03-review-summary.md), [hipóteses](hypotheses/iteration-03-root-cause-hypotheses.md) |
| **04** | Jornada da conta, backtest point-in-time, watchlist top-20 | executor + gate 3x + correção visual | Erro E5 corrigido (R_D↔R_F invertido, inspeção ocular); watchlist = operational priority; pruning de 4 PNGs | `04_lifecycle_watchlist.py`, t11–t17, 2 PNGs | `adbbad7`/`fb9d2de` → fix `1517a73` → visual `617e4ac`; [review](reviews/iteration-04-review-summary.md), [visual](reports/orchestrator-visual-correction-report.md) |
| **05** | Ações priorizadas, impacto em faixa, plano de medição — premissas **antes** do cálculo | executor + gate 3x | Erro E6 corrigido (GO 3 estados com poder/IC); annualized removido; faixa ≠ CI; SLA ACT-03 | `05_actions_impact.py`, t18–t21, evidence 05 | `dc5748f` (premissas) · `a8a6ca6` → fix `e0c6b7e`; [review](reviews/iteration-05-review-summary.md), [premissas](decisions/iteration-05-action-impact-assumptions.md) |
| **06** | Pipeline reproduzível em 1 comando (`run.sh`/`make all`) + verificador | executor + gate 3x | Erro E7 corrigido (categórico inválido → crash+stale; pycache do verificador); 45/45 byte-idênticos; 68 PASS | `run.sh`, `Makefile`, `06_verify_pipeline.py`, solution README | `9357c20` → fix `fa6572f`; [review](reviews/iteration-06-review-summary.md) |
| **07** | Relatório executivo CEO — narrativa **antes** da redação + verifier F1–F8 | executor + gate 3x | Erro E8 corrigido (drift/truncamento/word count); markdown único; gates de honestidade | `07_generate_executive_report.py`, `report-executivo.md`, README preenchido | `1bbec67` (outline) · `a726cb4` → fix `a1e99cb`; [review](reviews/iteration-07-review-summary.md), [outline](decisions/iteration-07-executive-report-outline.md) |
| **08** | **Process log final e evidências** (esta iteração) | executor + gate 3x `CONCLUDED` | 4 artefatos navegáveis; 8 erros com causa raiz; decisões candidato vs IA; verifier com gates de processo; fixer do gate reconciliou wording/aritmética F11/snapshots/detecção | este README, [erros](errors/ai-errors-and-corrections.md), [decisões](decisions/decision-ledger.md), [índice](evidence-index.md), [report](reports/iteration-08-process-log-report.md), [gate](reviews/iteration-08-review-summary.md) | `docs: consolidate AI process log and evidence` → fix `docs: reconcile process log review evidence` |
| **09** | **QA final integral e prontidão de submissão** | executor + gate 3x `CONCLUDED` | Auditoria git/escopo vs upstream/fork; re-execução em clone fresco (88 PASS/0 FAIL); re-derivação independente 59/59; originalidade/links/markdown/hygiene; readiness checklist criado; 4 fixos de hygiene/stale; gate fechado com correções L1–L3 (links, word counts, aritmética F11) | [prompt](prompts/iteration-09-prompt.md), [report](reports/iteration-09-final-qa-report.md), [readiness checklist](management/submission-readiness-checklist.md), [gate](reviews/iteration-09-review-summary.md), [fix report](reports/iteration-09-review-fix-report.md) | `chore: complete pre-submission quality assurance` → fixer `chore: close pre-submission QA gate` (gate 3x da It09 `CONCLUDED`) |

## 4. Como o problema foi entendido ANTES de promptar

Pré-registro é a prática central: **decisões e narrativa commitadas antes de qualquer código/análise**, para que a IA teste hipóteses em vez de inventar conclusões:

1. **Hipóteses It03** — H1–H10 com thresholds fixados ANTES de ver resultados: [`hypotheses/iteration-03-root-cause-hypotheses.md`](hypotheses/iteration-03-root-cause-hypotheses.md), commit `8cb93c3` precede a análise `9e02e18` (timeline no report It03 §2); arquivo intacto após o gate (correções em decisões, nunca nas hipóteses).
2. **Premissas It05** — ações/impacto/medição congeladas ANTES do cálculo: [`decisions/iteration-05-action-impact-assumptions.md`](decisions/iteration-05-action-impact-assumptions.md), commit `dc5748f` precede `a8a6ca6` (cronologia git prova a separação).
3. **Outline It07** — mensagem central, 3 provas, ask, claims permitidos/proibidos, 6 gráficos e word budget decididos ANTES da redação: [`decisions/iteration-07-executive-report-outline.md`](decisions/iteration-07-executive-report-outline.md), commit `1bbec67` precede `a726cb4`; não reescrito retroativamente (revisões geram adendos §13–§15).
4. **Decisões It04** — regras do backtest e da watchlist fixadas antes dos resultados (com nota de transparência: commitadas no mesmo commit do código; pré-especificação atestada por conteúdo interno): [`decisions/iteration-04-watchlist-decisions.md`](decisions/iteration-04-watchlist-decisions.md).
5. **Contrato analítico It02** — definições, grão, invariantes e lentes congelados antes das It03–05: [`../solution/docs/analytical-contract.md`](../solution/docs/analytical-contract.md).

## 5. Onde a IA errou (resumo)

8 erros materiais reais, com causa raiz, detecção, correção, validação e commit — ver **[`errors/ai-errors-and-corrections.md`](errors/ai-errors-and-corrections.md)** (E1–E8):

- **E1** It01 — schema ausente → `KeyError` + relatório stale (3/3 revisores) · `b9823da`
- **E2** It02 — lente de revenue por winner escondia encerramentos não dominantes (422.691 vs 18.507) · `9378a86`
- **E3** It03 — meses pré-signup como zeros artificiais (H4; Δ 13,7 → 9,0 p.p.) · `12ff47c`
- **E4** It03 — KM por tempo exato com células vazias + gráfico B cortado · `12ff47c`
- **E5** It04 — mapping visual R_D↔R_F invertido, detectado por **inspeção ocular do orquestrador** apesar dos validadores programáticos passarem · `617e4ac`
- **E6** It05 — GO ≥10% por ponto sem poder/IC (falso-GO ≈24%) · `e0c6b7e`
- **E7** It06 — valor categórico inválido → crash + stale; pycache gerado pelo próprio verificador · `fa6572f`
- **E8** It07 — drift de contagens, truncamento de tabela, word count no teto · `a1e99cb`

Nenhuma iteração relatou "não houve erros". Detecção (derivada dos summaries/gates): 7/8 pelos revisores — **E1** 3/3 (It01 summary §2); **E2** 1/3 material (revisor R3, review-8b41e9c2; os 3 concordaram na correção); **E3** 1/3 material (review-4c090c69; confirmado no recálculo pelos demais); **E4** parcial — KM por tempo exato 3/3 (L5/INFO-1/#6) e gráfico B 1/3 (#5); **E6** 3/3; **E7** 2/3 (review-18199ddc + review-f1fa7caa); **E8** 3/3 (LOWs convergentes) — 1/8 pela inspeção ocular do orquestrador (E5).

## 6. O que candidato/orquestrador adicionaram que um prompt único não faria

Um prompt único geraria uma análise plausível, mas sem as seguintes camadas (detalhe no [decision ledger](decisions/decision-ledger.md)):

- **Pré-registro** de hipóteses/premissas/narrativa antes do código (§4) — impede p-hacking e conclusões pós-hoc.
- **Lente por pergunta e regra do winner** (não misturar 110/312/352/600; sem double-counting 2,16×) — decisão de ângulo do candidato, operacionalizada pelo executor com invariantes G1–G15.
- **Gates de honestidade**: faixa ≠ CI; exposição ≠ perda (R1 não é "receita perdida"); hipótese ≠ prova; impacto em faixa com premissas nomeadas; "afetados" ≠ "evitados".
- **Watchlist nomeada operational priority/exposure** em vez de score (critério pré-registrado lift > 1,15 × 3 cutoffs).
- **Revisão 3x read-only com contexto separado + corretor serial** — exigência do candidato; pegou 7 dos 8 erros materiais.
- **Inspeção visual e auditoria final** como regras de processo (exigência do candidato); a inspeção ocular executada pelo orquestrador pegou E5, que validadores programáticos deixaram passar.
- **Contenção de tempo** com stop conditions e trims formais (F11).

## 7. Contagens derivadas — **snapshot no fechamento da It09** (definições e fontes)

> Todos os valores abaixo são um snapshot versionado no fechamento da It09 (após o QA final integral e o fechamento do gate 3x da It09). **It10: re-derivar antes de citar** (globs/git são a fonte; nenhum total final estático deve ser mantido).

| Métrica | Valor | Definição e fonte |
|---|---|---|
| Iterações executadas | **10** (It00–09) | Etapa orquestrada com prompt arquivado, executor único e report; derivado de `prompts/` + `reports/` (globs) |
| Review gates 3x concluídos | **10** (It00–09) | Ledgers em `reviews/` (10 summaries versionados) |
| Revisores (instâncias) | **30** | 10 gates × 3 revisores read-only (reports externos working artifacts; summaries versionados) |
| Correções sequenciais commitadas | **11** | Definição: 1 fixer (correção sequencial de um gate) = 1 correção. 8 fixers de gate (`9907024`, `b9823da`, `9378a86`, `12ff47c`, `1517a73`, `e0c6b7e`, `fa6572f`, `a1e99cb`) + 1 correção visual pós-gate It04 (`617e4ac`) + 1 fixer do gate It08 (executado em 5 commits) + 1 fixer do gate It09 (fechamento 2026-08-29) — `git log` |
| Erros materiais registrados | **8** (E1–E8) | [`errors/ai-errors-and-corrections.md`](errors/ai-errors-and-corrections.md) |
| Prompts arquivados | **22** | 20 (It00–08 + 2 especiais) + `iteration-09-prompt.md` + `iteration-09-review-fix-prompt.md` — glob de `prompts/` |
| Reports versionados | **22** | 20 (It00–08 + 2 especiais) + `iteration-09-final-qa-report.md` + `iteration-09-review-fix-report.md` — glob de `reports/` |
| Review summaries | **10** (It00–09) | glob de `reviews/` |
| Decisões registradas | **6 arquivos** (It02–07) + ledger consolidado | glob de `decisions/` |
| Hipóteses pré-registradas | **1 arquivo** (H1–H10) | `hypotheses/` |
| Commits do candidato | **33** (31 no fechamento da It08 → 32 no fechamento da It09 → **33 após o fixer do gate It09**, incl. `chore: close pre-submission QA gate`) | `git log --author="Jose Nascimento"` |
| Verificador | **88 PASS / 0 FAIL** (mesmo conjunto de checks; G10/inventário alinhados ao fechamento da It09: It08/09 `CONCLUDED`, It10 `PENDING`, gate It08/09 `CONCLUDED`) | `../solution/src/06_verify_pipeline.py` |

## 8. Limitações do processo (declaradas)

1. **Mesmo modelo nos 3 reviews** — independência de contexto/amostragem, não de modelo; erros correlacionados possíveis (na prática: E3 foi achado por 1/3 e E5 por nenhum revisor — ambos pegos por outras vias).
2. **Revisão não substitui validação executável** — veredicto de revisor é leitura crítica; por isso cada iteração mantém re-execuções, sandboxes de FAIL estrutural e recálculos independentes.
3. **O orquestrador também erra** — prompts/arbitragem/gates são de modelo; mitigado pela revisão 3x do resultado de cada etapa.
4. **IDs não verificáveis publicamente** — `openai/gpt-5.6-sol` e "max reasoning" são metadata do harness da sessão (distinção runtime vs external em `management/orchestration-architecture.md` §8).
5. **Time budget excedido, honestamente:** o oficial é 4–6h; a execução documentada totaliza uma **faixa de ~24–28h no fechamento da It09** (F11 no checklist — a It08 registrou ~2h30 + ~1h30 do fixer; a It09 registrou ~2h30 de QA final; as fatias por iteração são estimativas de sessão `~`, **não aditivas**: há sobreposições de relógio e sessões sem fatia própria; a soma bruta das 16 fatias listadas ≈ 27h40, com o teto da faixa acima da soma bruta por definição — incerteza das estimativas `~` e sessões sem fatia própria; os marcos pontuais anteriores foram removidos por inconsistência aritmética). O gatilho de contenção (§2.5b) foi ultrapassado na It04 — **decisão consciente de revisão** (gates 3x obrigatórios, adendo de arquitetura, escopo completo das It04/05 e o item eliminatório do process log), com trims formais a partir da It05 (pruning de PNGs, markdown único, sem dashboard). Nenhum claim de conformidade ao orçamento é feito.
6. **Working artifacts fora do repo** — os 27 reports brutos de revisão (9 gates × 3) e sandboxes não são versionados; a evidência persistente é a versão consolidada (`reviews/`, `reports/`, `prompts/`, git).

## 9. Evidence map (navegação)

| O que você quer ver | Onde |
|---|---|
| Ferramentas/arquitetura (papéis, modelos, rationale) | [`management/orchestration-architecture.md`](management/orchestration-architecture.md) |
| Plano, regras, política de tempo | [`management/execution-plan.md`](management/execution-plan.md) |
| Checklist do orquestrador (estados por item) | [`management/orchestrator-checklist.md`](management/orchestrator-checklist.md) |
| Prompts transcritos fielmente de todas as etapas/correções | [`prompts/`](prompts/) (22 arquivos — snapshot It09 pós-gate) |
| Reports de cada iteração | [`reports/`](reports/) (22 arquivos — snapshot It09 pós-gate) |
| Review summaries (gates 3x, matrizes finding→ação) | [`reviews/`](reviews/) (10 ledgers — snapshot It09 pós-gate) |
| Decisões e hipóteses pré-registradas | [`decisions/`](decisions/) · [`hypotheses/iteration-03-root-cause-hypotheses.md`](hypotheses/iteration-03-root-cause-hypotheses.md) |
| Erros reais da IA com correção | [`errors/ai-errors-and-corrections.md`](errors/ai-errors-and-corrections.md) |
| Índice completo de paths versionados | [`evidence-index.md`](evidence-index.md) |
| Relatório executivo (CEO) | [`../solution/report-executivo.md`](../solution/report-executivo.md) |
| Solução completa (código, dados, outputs) | [`../solution/`](../solution/README.md) |
| Git history (commits semânticos, autor do candidato) | `git log --author="Jose Nascimento"` na branch `submission/jose-nascimento` |

---

**Próximo passo:** Iteração 09 `CONCLUDED` (QA final integral + **review gate 3x da It09 `CONCLUDED`** — ver [report](reports/iteration-09-final-qa-report.md), [readiness checklist](management/submission-readiness-checklist.md) e [gate](reviews/iteration-09-review-summary.md)); Iteração 10 (`PENDING`): data final, commit final e PR `[Submission] Jose Nascimento — Challenge 001`.