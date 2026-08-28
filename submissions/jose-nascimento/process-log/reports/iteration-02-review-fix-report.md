# Report — Iteração 02 · Correção do review gate 3x (agente corretor sequencial)

- **Iteração:** 02 (reconciliação de churn e contrato analítico) — correção pós-gate
- **Data:** 2026-08-28
- **Executor:** exatamente um subagente `deepseek-max` (via OpenCode Go), sob orquestração do opencode — agente corretor sequencial do review gate (execution-plan, regra 2/4)
- **Base sob correção:** `9305e2edcdea7506feab0af75e0f29401becf6b7` (HEAD esperado confirmado antes de qualquer alteração; working tree limpo)
- **Commit desta correção:** `fix: strengthen revenue churn contract` (hash completo no §12)
- **Ledger do gate:** [`process-log/reviews/iteration-02-review-summary.md`](../reviews/iteration-02-review-summary.md)
- **Prompt integral desta correção:** [`process-log/prompts/iteration-02-review-fix-prompt.md`](../prompts/iteration-02-review-fix-prompt.md)
- **Tempo de relógio (F11):** ~1h40min (leitura das 3 revisões + exploração de dados para fixar o algoritmo de saídas ocultas + implementação + verificação independente + sandbox + documentos) — acumulado analítico ~4h30min; orquestrador mantém o controle (política de contenção §2 do plano)

---

## 1. Status

**PASS** — todas as correções materiais aplicadas e verificadas; nenhum blocker remanescente; gate It02 `CONCLUDED` no checklist; Iteração 03 **não** iniciada.

## 2. Matriz dos 3 reviews

| Revisor | Veredicto | Findings | Tratamento |
|---|---|---|---|
| R1 (`review-9d3b7e05.md`) | `PASS` | LOWs L1–L5 (G10 parcial; quantis; tie-break; §9 diário vs mensal; código morto + "Acumulado") | LOWs baratos corrigidos (L2–L5); L1 aceito como trade-off documentado |
| R2 (`review-6c2f9a41.md`) | `PASS` | LOWs/INFO L1–L7 (código morto; erro nº5; G5/G6 autorreferentes; trocas valor-neutras; "Acumulado"; ""↔NaN; pinning) | L1/L5 corrigidos; demais aceitos com justificativa |
| R3 (`review-8b41e9c2.md`) | `PASS_WITH_FIXES` | **M1** (lente de revenue churn degenerada: 18.507 vs 398.462 ocultos vs 1.179.139 lente B); **M2** (números de qualidade hardcoded); LOWs L1–L6 (closed_at; "Acumulado"; ""↔NaN; D4; código morto; trocas valor-neutras) | **M1/M2 corrigidos**; L1 (closed_at) elevado a correção material; L2/L4/L5 corrigidos; L3/L6 aceitos |

## 3. Fórmulas finais e novos números (janela 2023-01..2024-12)

**R1 — gross subscription ending MRR** (exposição contratual bruta; NÃO é "receita perdida" automática — pode ser troca/replacement/sobreposição):
- Σ MRR das assinaturas com `end_date` no período = **1.179.139** (486 assinaturas; 312 contas); por conta×mês nas colunas novas `mrr_ended_in_month`/`n_ended_in_month` (427 conta×mês com encerramento; 56 com apenas trials encerrados — MRR 0 —, por isso a contagem é separada); reconciliada à fonte pelo invariante **G14**.

**R2 — net account-state MRR loss** (perda líquida do estado/winner entre snapshots de fim de mês):
- (a) **churn-to-inactive** = Σ winner_mrr(m−1) de contas ativas em m−1 e inativas em m = **18.507** em 2 transições (2023-10→2023-11: 12.736 — A-180abf; 2024-08→2024-09: 5.771 — A-0baac2; ambas com exatamente 1 assinatura ativa em m−1, logo winner = naive, sem subestimação nesses casos);
- (b) **active contraction** = Σ [winner_mrr(m−1) − winner_mrr(m)] de contas ativas com queda = **150.817** em 36 transições;
- Total líquido = **169.324**. Contexto: expansões ativas +2.287.279 em 590 transições — a maior parte das saídas é compensada dentro da conta (estado é líquido, não contratual).

**Gap R1 vs R2 — saídas ocultas não-dominantes** (algoritmo final documentado; 4 condições): assinatura com `end_date` em `m` tal que (1) conta ativa no fim de `m`; (2) não era o winner no fim de `m−1`; (3) estava ativa no fim de `m−1`; (4) winner_mrr(m) ≥ winner_mrr(m−1):
- **274 assinaturas / 422.691** (winner_mrr inalterado=242; reduzido=0; aumentado=32); visão episódio conta-mês: **254 / 422.691** (226 inalterados; 0 reduzidos; 28 aumentados);
- Razão vs churn-to-inactive = **22,8×**; razão gross ending vs churn-to-inactive = **63,7×**;
- **Exemplo material:** A-5a215a em 2024-12 — 2 assinaturas de 17.313 (34.626 no total) encerram com a conta ativa; winner S-75cba6 → S-75cba6 (17.313 → 17.313); perda 100% invisível à lente de estado.
- **Diferença vs R3 (255/398.462), com causa:** o reviewer reportou uma variante da mesma família de definições (granularidade/agregação de episódios limítrofes; script não commitado); as **226 saídas com winner_mrr inalterado coincidem exatamente** na visão conta-mês, e 0 reduzidas em ambas; a conclusão material (gap ≈ 21–23×; exemplo A-5a215a) é invariante. O exemplo do R3 ("assinatura de 34.626") corresponde, na base real, a duas assinaturas de 17.313 encerrando em 2024-12.

**Winner:** preservado como **estado/risco** (determinístico; reconstrução independente 0 divergências em 5.807 linhas); **PROIBIDO** seu uso isolado como total de churn contratual (contrato §5/§6; decisão D9).

## 4. Como M1 foi corrigido (lentes de receita)

1. `revenue_lenses()` no script calcula R1, R2 (a/b), ocultas (sub + episódios), razões e o exemplo material — tudo em runtime (contrato §5/§6; report §7).
2. Report ganhou a seção **§7 "Lentes de receita: gross ending MRR vs net account-state MRR loss"** com tabela de definições, gap, efeito no winner_mrr, razões, expansão de contexto e exemplo material; §8 (registros inválidos), §9 (checks) e §10 (proveniência) renumerados.
3. Contrato §4 (pergunta de receita), §5 (fórmulas R1/R2 + PROIBIDO), §6 (escopo do winner), §8 (desfechos rotulados), §12 (D9) atualizados; nenhum uso isolado do winner como "receita perdida" permanece.
4. Colunas auditáveis `mrr_ended_in_month`/`n_ended_in_month` adicionadas ao `account_month.csv` (README processado atualizado), rotuladas como desfechos e **proibidas como features do próprio mês** (contrato §8); invariante **G14** reconcilia soma (1.179.139), contagem (486) e conta×mês (427) à fonte.

## 5. Como M2 foi corrigido (números hardcoded)

`quality_metrics()` deriva em runtime: partição de uso (19.142/290/5.568 de 25.000), pcts (76,6%/22,3%), uso/tickets pré-signup (13.198/1.077), eventos fora da vida de assinaturas (53/90/143), tickets/closed_at (2.000/0), CSAT (825/41,2%/domínio {3,4,5}/denominador 1.175), reason (95), feedback (148), assinaturas por conta (2–19, mediana 10), violações end↔flag (0). Varredura sistemática adicional parametrizou 110/312/352 (contrato §4/§12), 35/277/125 (contrato §4) e a descrição do G7 (600/352/486/312/110). Constantes de regra/janelas/tolerância permanecem nomeadas (`ALIGNMENT_WINDOWS_DAYS`, quantis, tolerância 0).

## 6. Como `closed_at` foi corrigido (decisão D10)

- Política no contrato §7 (semântica) e §10 (detalhe): tickets existem por `submitted_at`; métricas de resolução/CSAT usam APENAS tickets fechados com informação observável até a data índice; `closed_at` nulo exclui o ticket com denominador explícito (1.175 tickets com nota na base); **nunca imputar fechamento futuro**.
- `closed_at` promovida a coluna mínima (REQUIRED), parseada (novo D01) e verificada pelo gate **G15** (0 nulos na base; PASS; vira WARN se nulos aparecerem).

## 7. LOWs endereçados (baratos/factuais)

Quantis com nota de arredondamento + valores subjacentes (report §4); tie-break do matching explícito (primeira ocorrência na ordem estável do CSV, `idxmin`); coluna "Acumulado" removida; código morto do G5 removido; redação D4 precisada e nota de grão diário vs mensal no report §8/contrato §9. Demais LOWs aceitos com justificativa (review summary §5).

## 8. Testes e invariantes

| Validação | Resultado |
|---|---|
| Syntax/import | `py_compile` OK; execução OK (stdlib + pandas; offline) |
| Baseline ×2 (idempotência) | exit 0; 31 PASS / 1 WARN / 0 FAIL; 4 outputs byte-a-byte idênticos (report `33b50369913c3b9e2a7e95d30b2bfe81`; contrato `702fa1b5f69bf22ab49860a610439359`; CSV `b718c4f842609ee14eb56d5d4edcf012`; README `d30e27900f5a70839cc7403e1b5e36ac`) |
| Outputs commitados vs regenerados | 4/4 byte-a-byte idênticos |
| Verificação independente (implementação própria, `verify_final.py` fora do repo) | 46/46 checks OK: painel reconstruído do zero e comparado célula-a-célula (22 colunas, 5.807 linhas, 0 divergências de conteúdo); 1.179.139/486/312; 18.507/2; 150.817/36; 169.324; 274/422.691 (242/0/32) + 254 episódios (226/0/28); razões 22,8×/63,7×; A-5a215a (34.626, winner S-75cba6 inalterado 17.313); qualidade completa; MV-A/B/C com as novas colunas; G14 (soma/contagem/conta×mês) e demais invariantes |
| MV-A/B/C | 3/3 PASS (A-00bed1; A-0baac2 2024-09 mrr_ended=5.771 e 2024-12 mrr_ended=2.786; A-956988 2024-12) |
| Invariantes G1–G15 | 31 PASS / 1 WARN (G12 esperado) / 0 FAIL; G14 reconcilia gross ending à fonte; G15 valida closed_at |
| FAIL estrutural ×3 (sandbox) | coluna `churn_date` renomeada; arquivo `churn_events.csv` ausente; coluna `signup_date` renomeada → exit 1; report regravado com "Falha estrutural"; 5 FAILs estruturados; sem traceback; outputs de dados NÃO regenerados (MD5 preservados — anti-stale); idempotente no caminho de FAIL; falha combinada acidental também comportou-se corretamente |
| Hardcode scan | zero números de dados de qualidade no render; restam apenas constantes de regra nomeadas |
| Hygiene/git | `git diff --check` limpo; escopo 100% `submissions/jose-nascimento/`; grep `/tmp|/home|ubuntu` = 0 fora do prompt arquivado; Markdown/links conferidos |

## 9. Arquivos alterados/criados (somente dentro de `submissions/jose-nascimento/`)

| Arquivo | Ação |
|---|---|
| `solution/src/02_reconcile_churn.py` | Alterado: `revenue_lenses`/`quality_metrics` novas; `mrr_ended_in_month`/`n_ended_in_month` no painel; G14/G15; REQUIRED com `closed_at`; D01 de `closed_at`; G7 parametrizado; código morto removido; renders (report §4/§7/§8, contrato §2–§12, README processado) parametrizados e com as duas lentes |
| `solution/evidence/02_consistency_report.md` | Regenerado (31 PASS / 1 WARN; seção §7 de lentes de receita; §4 com tie-break/quantis; §8 parametrizado) |
| `solution/docs/analytical-contract.md` | Regenerado (§5 R1/R2 + PROIBIDO; §6 escopo do winner; §7/§10 closed_at; §8 desfechos; §9/§10 números runtime; §11 G1–G15; §12 D4/D9/D10) |
| `solution/data/processed/account_month.csv` | Regenerado (22 colunas — novas `mrr_ended_in_month`, `n_ended_in_month`) |
| `solution/data/processed/README.md` | Regenerado (novas colunas; G1–G15) |
| `process-log/prompts/iteration-02-review-fix-prompt.md` | Criado (transcrição fiel deste prompt) |
| `process-log/reviews/iteration-02-review-summary.md` | Criado (ledger do gate) |
| `process-log/reports/iteration-02-review-fix-report.md` | Criado (este report) |
| `process-log/reports/iteration-02-reconciliation-report.md` | Alterado (estado do gate; handoff §10.2 com R1/R2/D9/D10; adendo §11) |
| `process-log/decisions/iteration-02-analytical-contract-decisions.md` | Alterado (D4 wording; D9 e D10 novos) |
| `process-log/management/execution-plan.md` | Alterado (It02 com gate 3x concluído e correções) |
| `process-log/management/orchestrator-checklist.md` | Alterado (B3/B10/F11; notas D2–D5) |

## 10. Riscos residuais (monitorar; não bloqueiam)

1. **Definição de saídas ocultas** — família de variantes de granularidade; algoritmo fixado no contrato (4 condições) com ambas as visões reportadas.
2. **G10 parcial** — regressão de bucketing futuro em uso/tickets não seria capturada; mitigado por construção e reconstrução independente (It06 pode reforçar).
3. **Uso indevido de desfechos rotulados** (`mrr_ended_in_month`, `n_ended_in_month`, `churn_event_in_month`, `status`) como features do próprio mês em It03/04 — contrato §8.
4. **Mau uso do snapshot flag** como série — contrato §8 + G10.
5. **Determinismo vs versão de pandas** — pinning na It06.
6. **Trocas valor-neutras de winner** — preferir `winner_mrr` a atributos categóricos do winner em features (It04).
7. **`closed_at` com nulos em base futura** — política documentada; G15 vira WARN.

## 11. Handoff explícito para a Iteração 03

**Ao orquestrador (opencode):** o review gate 3x da Iteração 02 está `CONCLUDED` com correções. Disparar o próximo agente executor `deepseek-max` para a **Iteração 03 — Causa raiz, coortes e onboarding economics**, com:

1. **Entradas:** `solution/docs/analytical-contract.md` (contrato congelado — agora com as lentes R1/R2, política de `closed_at` e desfechos rotulados), `solution/data/processed/account_month.csv` (22 colunas; schema no `data/processed/README.md`), `solution/evidence/02_consistency_report.md` (incl. §7 de lentes de receita), `solution/evidence/01_audit_report.md`, CSVs raw.
2. **Regras obrigatórias do contrato:** lente de eventos para diagnóstico (primeiro evento por conta, censura no corte 2024-12); **receita com duas lentes nomeadas** — R1 gross ending MRR (exposição; nunca apresentar como perda sem declarar a lente) e R2 net account-state MRR loss (churn-to-inactive + active contraction; nunca usar winner isoladamente como churn contratual — §5/§6, D9); features de risco apenas com dados ≤ data índice (alvo vs feature no mesmo mês proibido — §8, incl. `mrr_ended_in_month`/`n_ended_in_month` como desfechos); uso/tickets com variante bruta vs alinhada declarada (§9); resolução/CSAT apenas com tickets fechados e sem imputar fechamento futuro (§7/§10); CSAT/reason/feedback apenas sugestivos (§10); nenhuma comparação entre lentes (§4).
3. **Atenções para It03:** 352 contas com evento (175 multi-evento; 61 reativações em 55 contas); 2 contas com ciclo ativo→inativo→(re)ativo (A-0baac2, A-180abf); 0 contas inativas no corte por assinatura; 76,6% de uso fora da janela; gap de receita 22,8× (ocultas) e 63,7× (exposição) vs 18.507 capturados pela lente de estado; hipóteses registradas ANTES da análise.
4. **Restrições:** nada fora de `submissions/jose-nascimento/`; sem conclusão causal sem rótulo; pipeline offline; números re-executados.
5. **Critérios de aceitação objetivos (execution-plan §Iteração 03):** hipóteses versionadas antes da execução; veredito com número por hipótese; análises com censoring e alinhamento temporal; premissas do onboarding economics nomeadas e em faixa; correlação vs causalidade rotulada.
6. **Retorno ao orquestrador:** report estruturado com Status PASS/BLOCKED, commit hash, validações, riscos — sem conclusão simulada se algo bloquear.

## 12. Git

- Antes da correção: HEAD `9305e2edcdea7506feab0af75e0f29401becf6b7` confirmado; working tree limpo; branch `submission/jose-nascimento` tracking `origin` up to date.
- Commit: `fix: strengthen revenue churn contract` — hash completo **`9378a86e5697dbeb2aaa1fdc96ed7d418155aa05`**.
- Push para `origin/submission/jose-nascimento` realizado; HEAD local == remoto (`9378a86`); working tree limpo após o push (re-execução do pipeline pós-commit reproduz os 4 outputs byte-a-byte); `git diff --check` limpo; `git add -f` apenas nos paths pretendidos; sem amend/force/config/destrutivo.