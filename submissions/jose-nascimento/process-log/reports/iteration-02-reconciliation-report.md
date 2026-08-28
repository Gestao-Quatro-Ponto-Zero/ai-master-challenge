# Report — Iteração 02 · Reconciliação das definições/grãos de churn e contrato analítico

- **Iteração:** 02 (reconciliação de churn e contrato analítico)
- **Data:** 2026-08-28
- **Executor:** exatamente um subagente `deepseek-max` (via OpenCode Go), sob orquestração do opencode — opencode gerencia agentes/git/evidências; o subagente executou esta iteração (semântica no execution-plan, regra 4)
- **Estado da iteração:** `CONCLUDED` (validação do executor concluída; review gate 3x realizado em 2026-08-28 com correções — ver `process-log/reviews/iteration-02-review-summary.md` e `process-log/reports/iteration-02-review-fix-report.md`)
- **Prompt integral desta iteração:** [`process-log/prompts/iteration-02-prompt.md`](../prompts/iteration-02-prompt.md) (transcrição fiel)
- **Decisões registradas:** [`process-log/decisions/iteration-02-analytical-contract-decisions.md`](../decisions/iteration-02-analytical-contract-decisions.md)
- **Tempo de relógio (F11):** ~1h55min (leitura da governança + exploração read-only + script + 7 correções reais + 3 verificações manuais + sandbox + validações) — acumulado da submissão até aqui: Iteração 00 (governança+gate) + Iteração 01 (~55min) + esta etapa; orquestrador mantém o controle (política de contenção §2 do plano)

---

## 1. Objetivo

Reconciliar as três fontes de "churn" (`accounts.churn_flag`, `subscriptions.churn_flag/end_date`, `churn_events`), quantificar divergências, fixar a lente primária por pergunta de negócio no contrato analítico, construir a base-mestre account-month determinística (sem MRR dobrado por sobreposição) e provar invariantes executáveis. Sem causa raiz (Iteração 03) e sem recomendações (Iteração 05).

## 2. Workflow executado

1. **Inspeção do repo** (antes de editar): `git status` (working tree limpo), branch `submission/jose-nascimento` tracking `origin` up to date, `git log --oneline -15` (HEAD `b9823da` = esperado), `git remote -v`. Nada a reverter.
2. **Leitura integral**: instruções oficiais (README, CONTRIBUTING, submission-guide, challenge README, template), execution-plan, orchestrator-checklist, prompts/reports/reviews da It00/It01 (incl. fix M1 da It01), `solution/evidence/01_audit_report.md`, `solution/src/01_ingest_audit.py`, 5 CSVs (headers/amostras).
3. **Iteração 02 marcada `OPEN`** no plano (início lógico da etapa; estado final `CONCLUDED` após validação — mesma prática da It01).
4. **Exploração read-only** dos CSVs (sessões `python3` fora do script): lentes (110/486-312/600-352), Venn 2-way/3-way, alinhamento temporal, sobreposição de assinaturas (2–19 por conta; mediana 10), candidatos para verificações manuais.
5. **Implementação de `solution/src/02_reconcile_churn.py`**: stdlib + pandas; paths relativos; sem rede; saída determinística (sem timestamp; ordenações estáveis). Gera `evidence/02_consistency_report.md`, `docs/analytical-contract.md`, `data/processed/account_month.csv` e `data/processed/README.md`.
6. **Execução + correções reais** (7, listadas em §7) até exit 0 (28 PASS / 1 WARN / 0 FAIL).
7. **Idempotência**: 2 execuções → todos os outputs byte-a-byte idênticos (MD5 no §9).
8. **3 verificações manuais independentes** (MV-A/B/C, §5).
9. **Sandbox de falha estrutural** (3 cenários, §6) — lição M1 da It01 aplicada.
10. **Evidência de processo**: prompt arquivado; decisions file; este report; `.gitkeep` de `docs/` removido (substituído por `analytical-contract.md`).
11. **Atualização de governança**: execution-plan (It02 `CONCLUDED`; artefatos/commit reais sincronizados) e orchestrator-checklist (D2–D5 `CONCLUDED`; F2/F10/F11 desta iteração); validações finais; commit e push.

## 3. Decisões desta iteração (julgamento do executor vs output da IA)

Resumo; detalhe completo (problema → opções → evidência → decisão → trade-off) no decisions file.

| Decisão | Julgamento do executor | Output/contexto da IA | Onde |
|---|---|---|---|
| D1 — Lente primária por pergunta (eventos p/ diagnóstico; assinaturas p/ receita; flag só como snapshot; painel p/ risco) | Nenhuma fonte resolve tudo; contrato impede mistura | Prompt: "definir um contrato canônico por pergunta de negócio" | contrato §4; decisions D1 |
| D2 — Grão-mestre account×mês (painel do signup ao corte; estado no fim do mês) | Painel completo de 5.807 linhas justifica o CSV commitado (utilidade > tamanho) | Prompt: "base account-month preferencialmente commitada se a utilidade justificar" | contrato §2/§3; decisions D2 |
| D3 — Winner (não-trial, max MRR, start recente, id) vs soma ingênua (2,16×) vs start recente (13,5M) | Soma ingênua rejeitada p/ receita; preservada como `mrr_sum_naive` p/ auditoria | Prompt: "compare pelo menos duas regras, quantifique impacto, justifique" | contrato §6; decisions D3 |
| D4 — [start, end] inclusive; ativo no fim do mês | Regra determinística sem look-ahead intra-mês | Prompt: "semântica de intervalos (inclusive/exclusive)" | contrato §7; decisions D4 |
| D5 — Registros inválidos: política dupla (bruto/alinhado), nada descartado silenciosamente | 76,6% fora da janela é estrutura da base; quantificar e declarar variante | Prompt: "não descarte 76,6% silenciosamente; análise de sensibilidade" | contrato §9; decisions D5 |
| D6 — `churn_flag_snapshot_2024_12_31` incluído, proibido em features de risco | Rótulo do corte explícito + invariante G10 + regra alvo-vs-feature | Prompt: "nenhum campo pós-data índice em features de risco" | contrato §8; decisions D6 |
| D7 — CSAT/reason/feedback = evidência sugestiva | Domínio {3,4,5}, 41,2% nulos: nunca prova causal | Prompt: "evidência sugestiva conforme qualidade" | contrato §10; decisions D7 |
| D8 — Bloqueio estrutural total com FAILs precisos (R01–R04) em schema quebrado | Base parcial violaria o schema do contrato; relatório sempre regravado, sem stale, sem traceback | Prompt: "FAIL estrutural deve exit 1 + report atualizado, sem stale/traceback (reutilize a lição It01)" | decisions "Decisão de processo" |

## 4. Arquivos criados/alterados (somente dentro de `submissions/jose-nascimento/`)

| Arquivo | Ação |
|---|---|
| `solution/src/02_reconcile_churn.py` | Adicionado (reconciliação + painel + invariantes + relatório + contrato; stdlib + pandas; sem rede) |
| `solution/evidence/02_consistency_report.md` | Adicionado (gerado; regenerável) |
| `solution/docs/analytical-contract.md` | Adicionado (gerado; regenerável) |
| `solution/data/processed/account_month.csv` | Adicionado (gerado; 5.807 linhas; MD5 `38ae8772e46edf0215a938c6dc2999eb`) |
| `solution/data/processed/README.md` | Adicionado (gerado; schema + checksum) |
| `process-log/prompts/iteration-02-prompt.md` | Adicionado (transcrição fiel) |
| `process-log/decisions/iteration-02-analytical-contract-decisions.md` | Adicionado (D1–D8) |
| `process-log/reports/iteration-02-reconciliation-report.md` | Adicionado (este report) |
| `process-log/management/execution-plan.md` | Alterado (It02 `CONCLUDED`; artefatos e commit reais sincronizados; demais iterações `PENDING`) |
| `process-log/management/orchestrator-checklist.md` | Alterado (D2–D5 → `CONCLUDED`; F2/F10/F11 desta iteração) |
| `solution/docs/.gitkeep` | Removido (substituído por `analytical-contract.md`) |

Nenhum arquivo fora da pasta do candidato foi alterado.

## 5. Resultados (reconciliação — números do `02_consistency_report.md`)

- **Lente A (accounts.churn_flag):** 110 de 500 contas (22,0%).
- **Lente B (subscriptions):** 486 assinaturas encerradas/flagadas (9,7% de 5.000); 312 contas únicas (62,4%); 4.514 ativas; MRR das encerradas = 1.179.139 vs ativas = 10.159.608 (referência de receita em risco).
- **Lente C (churn_events):** 600 eventos; 352 contas únicas (70,4%); 175 contas com >1 evento (máx 5); 61 eventos `is_reactivation` (55 contas).
- **Interseções/diferenças (recalculadas, não copiadas):** flag∩eventos=75; flag∩assinatura=72; assinatura∩eventos=227; as três=50; somente flag=13; somente assinatura=63; somente eventos=100; flag+assinatura sem evento=22; flag+eventos sem assinatura=25; assinatura+eventos sem flag=177; nenhuma lente=50; ≥1 lente=450. Divergências It01 conferidas: 35 / 277 / 125 (+ assinatura churn sem evento=85).
- **Alinhamento `churn_date` vs `end_date`:** 386 de 600 eventos têm assinatura encerrada na conta; matches por janela |lag|≤d: 0d=6; 3d=31; 7d=47; 15d=81; 30d=126 (21,0%); 60d=193; 90d=222; 180d=305; 365d=369; lag sinalizado: exatos=6, antes do fim=268, depois=112; quantis [10,25,50,75,90]% = [-267, -133, -34, 6, 57]. Sensibilidade documentada (report §4): nenhuma janela razoável alinha a maioria — lentes decopladas.
- **Estado no corte:** 110 flagadas; 0 contas inativas por assinatura no corte; 553 linhas account-mês inativas em 279 contas (majoritariamente entre signup e 1ª assinatura); 2 contas com ciclo ativo→inativo→(re)ativo (A-0baac2, A-180abf); 352 de 352 contas com evento seguem ativas no corte (episódio ≠ conta perdida).
- **Base account-month:** 5.807 linhas; 5.254 com ≥1 assinatura ativa; 4.686 (89,2%) com >1 ativa (sobreposição); soma ingênua 62.216.507 vs winner 28.766.224 (razão 2,16×; diferença 33.450.283 = 53,8% da soma ingênua); variante start-recente 13.516.561 (sensibilidade).
- **Invariantes:** G1–G13 — 13 PASS; 1 WARN esperado (G12 — uso fora da janela, 76,6%, quantificado); 0 FAIL; resumo geral 28 PASS / 1 WARN / 0 FAIL, exit 0.

## 6. Verificações manuais independentes (3, diretamente nos CSVs e no painel)

Metodologia: sessões `python3` com pandas **independentes do script**, lendo `solution/data/raw/*.csv` e `solution/data/processed/account_month.csv`, com `assert` contra os valores do painel. Nenhum caso é usado para afirmar causa raiz.

| # | Caso | Cálculo independente | Resultado |
|---|---|---|---|
| MV-A | Divergência flag/evento — `A-00bed1` | 1 evento `C-5689de` (2024-01-03); 10 assinaturas, 0 com `churn_flag`/`end_date`; `accounts.churn_flag=False`. Derivado: 1 assinatura ativa em 2024-01-31. Painel 2024-01: `status=active`, `churn_event_in_month=1`, `n_events_in_month=1`, `winner_mrr=1159` | PASS — evento sem flag em nenhuma lente; painel registra o evento no mês sem marcar a conta como inativa (sem dupla contagem) |
| MV-B | Múltiplos churns/reativação — `A-0baac2` | 4 eventos (2024-07-15, 2024-09-30, 2024-10-18, 2024-12-24); assinatura `S-3c3a3e` (MRR 5771) terminou 2024-09-13 (`churn_flag=True`); reativação em out (winner `S-21ebb6`, MRR 6169). Derivado: status 2024-05..12 = inactive/active/active/active/inactive/active/active/active — idêntico ao painel; eventos por mês {2024-07:1, 2024-09:1, 2024-10:1, 2024-12:1} idênticos | PASS — ciclo ativo→inativo(2024-09)→ativo reproduzido; eventos em meses ativos E no mês inativo; sem dupla contagem |
| MV-C | Subscriptions sobrepostas — `A-956988` em 2024-12 | 12 assinaturas ativas em 2024-12-31 (derivado); soma ingênua = 29.407; winner (não-trial, max MRR) = `S-c069ab` MRR 10.945. Painel 2024-12: `n_active_subs=12`, `winner_subscription_id=S-c069ab`, `winner_mrr=10945`, `mrr_sum_naive=29407` | PASS — sobreposição resolvida pelo winner (razão 2,69× no mês); soma preservada para auditoria |

## 7. Erros reais encontrados e corrigidos (pelo executor, durante a execução — nenhum inventado)

1. **G8 — precedência em `int(series).min()`** — `TypeError` na primeira execução. Causa: `int(...)` aplicado à Series antes do `.min()`. Correção: cálculo em duas etapas (`months_per_acc` → min/máx). Resultado: exit 0.
2. **G10 — `month_end` string vs `Timestamp`** — `TypeError: Invalid comparison between dtype=str and Timestamp`. Causa: painel grava `month_end` como ISO string; gate comparava com `DATA_CUT`. Correção: `pd.to_datetime(panel["month_end"])` e `pd.Timestamp(prow["month_end"])`. Resultado: gate executável.
3. **`run_gates` sem `use`/`tic`** — `NameError`. Causa: G12 usa `feature_usage` e `support_tickets`, não passados. Correção: assinatura e chamada atualizadas. Resultado: gate executável.
4. **Render do relatório — precedência `int(mask).sum()`** — `TypeError` no §3.2. Correção: parênteses em `int(((mask1) & (mask2)).sum())`. Resultado: relatório gerado.
5. **G6 — identidade de MRR quebrada (23 meses)** — FAIL real de invariante. Causa: decomposição add/rem/exp/contr classificava por `MRR==0`; contas ATIVAS com assinaturas só-trial têm `winner_mrr=0` e eram contadas como add/rem. Correção: classificação por `status` (active/inactive), não por MRR. Resultado: 0 meses quebrados (tolerância 0).
6. **Janelas de alinhamento erradas (todas = 220)** — `pd.to_numeric` sobre `Timedelta` devolve nanossegundos (3 dias → 259.200.000.000), não dias; comparações contra janelas em dias ficaram sem sentido. Correção: `min_lag.dt.days`. Resultado: 6/31/47/81/126/193/222/305/369 — valores conferidos manualmente (§6 do report, G11).
7. **Exploração pré-script com comparação ao INÍCIO do mês** — contou 5.257 linhas account-mês e MRR 63,3M vs painel final 5.254/62,2M (diferença de 3 linhas e ~1,07M). Causa: na exploração, `end_date >= m` (1º dia do mês) em vez de `end_date >= último dia`; assinaturas terminando no meio do mês contavam como ativas no mês. Correção: semântica do contrato (fim do mês) aplicada no script; números finais conferem com a regra fixada (D4). Nenhum número do script foi ajustado para "bater" — a regra foi fixada primeiro e os números decorrem dela.

## 8. Comandos de validação executados

| Validação | Comando | Resultado |
|---|---|---|
| Syntax/import | `python3 -m py_compile solution/src/02_reconcile_churn.py`; execução de módulo | OK; import OK (stdlib + pandas apenas) |
| Execução | `python3 -W ignore solution/src/02_reconcile_churn.py` (workdir = pasta da submissão) | exit 0; 28 PASS / 1 WARN / 0 FAIL |
| Idempotência | 2 execuções; `md5sum` dos 4 outputs | byte-a-byte idênticos: report `189efc31…`; contrato `b570c43b…`; CSV `38ae8772…`; README `5371c274…` |
| Offline | inspeção de imports (stdlib + pandas; nenhuma chamada de rede) | sem rede |
| Sandbox — coluna `churn_date` renomeada | cópia da solução em sandbox fora do repo; rename; 2 execuções | exit 1; 5 FAILs (S01 + R01–R04); relatório regravado com seção "Falha estrutural"; sem traceback; idempotente |
| Sandbox — arquivo ausente | remoção de `ravenstack_churn_events.csv` | exit 1; 5 FAILs; sem traceback |
| Sandbox — coluna `signup_date` renomeada | segundo sandbox fora do repo | exit 1; 5 FAILs; sem traceback |
| Verificações manuais | 3 sessões pandas independentes com `assert` (MV-A/B/C) | 3/3 PASS |
| Hygiene | `git diff --check` (após staging) | limpo |
| Escopo | `git status`/`git diff` | somente arquivos de `submissions/jose-nascimento/` |
| Paths pessoais/segredos | grep por `/tmp`, `/home`, `ubuntu` nos artefatos da solução | zero ocorrências fora do prompt arquivado (exceção documentada, regra 8 do plano) |

## 9. Riscos e pendências

1. **Revisão 3x da Iteração 02** — obrigatória (regra 2 do plano); orquestrador deve disparar 3 agentes `deepseek-max` read-only; ledger `process-log/reviews/iteration-02-review-summary.md` a criar. Review gate permanece `PENDING`.
2. **Determinismo vs versão de pandas** — outputs idênticos com pandas 3.0.5; pinning é objeto da Iteração 06.
3. **Mau uso do rótulo snapshot** — `churn_flag_snapshot_2024_12_31` pode vazar se usado como série; mitigado por contrato §8, G10 e nome da coluna; revisores devem conferir o uso nas It03–04.
4. **Sobreposição massiva de assinaturas** — 89,2% das linhas account-mês têm >1 assinatura; qualquer análise que ignore a regra do winner duplica MRR (2,16×); risco monitorado no handoff It03/It04.
5. **Alinhamento temporal fraco** — eventos e `end_date` decoplados; análises de tempo-ao-churn devem escolher a lente declarada (contrato §4) e reportar censura.
6. **76,6% de uso fora da janela** — análises de atividade devem declarar variante bruta vs alinhada (contrato §9).
7. **Push** — depende de rede/credenciais; se falhar, commit permanece local e o estado real é reportado.

## 10. Handoff explícito para a Iteração 03

**Ao orquestrador (opencode):** a Iteração 02 está `CONCLUDED` (validação do executor concluída; review gate 3x a disparar). Disparar o próximo agente executor `deepseek-max` para a **Iteração 03 — Causa raiz, coortes e onboarding economics**, com:

1. **Entradas:** `solution/docs/analytical-contract.md` (contrato congelado — lentes por pergunta, grão account-month, regras temporais/anti-leakage), `solution/data/processed/account_month.csv` (base-mestre; schema no `data/processed/README.md`), `solution/evidence/02_consistency_report.md` (números de reconciliação), `solution/evidence/01_audit_report.md`, CSVs raw.
2. **Regras obrigatórias do contrato:** lente de eventos para diagnóstico (primeiro evento por conta, censura no corte 2024-12); lente de assinaturas para exposição bruta (R1 — gross ending MRR; NÃO rotular como perda sem declarar a lente) e estado/winner para perda líquida (R2 — churn-to-inactive + active contraction; proibido como churn contratual isolado — contrato §5/§6, decisão D9); features de risco apenas com dados ≤ data índice (alvo vs feature no mesmo mês proibido — contrato §8, incl. `mrr_ended_in_month`/`n_ended_in_month` como desfechos); uso/tickets com variante bruta vs alinhada declarada (contrato §9); CSAT/resolução apenas com tickets fechados, `closed_at` nulo excluído com denominador explícito, nunca imputar fechamento futuro (contrato §7/§10, decisão D10); CSAT/reason/feedback apenas sugestivos (contrato §10); nenhuma comparação entre lentes (contrato §4).
3. **Atenções para It03:** 352 contas com evento (175 multi-evento; 61 reativações em 55 contas); 2 contas com ciclo ativo→inativo→(re)ativo pela lente de assinatura (A-0baac2, A-180abf); 0 contas inativas no corte por assinatura; 76,6% de uso fora da janela; hipóteses devem ser registradas ANTES da análise.
4. **Restrições:** nada fora de `submissions/jose-nascimento/`; sem conclusão causal sem rótulo; pipeline offline; números re-executados (nada de pesquisa interna).
5. **Critérios de aceitação objetivos (execution-plan §Iteração 03):** hipóteses versionadas antes da execução; veredito com número por hipótese; análises com censoring e alinhamento temporal; premissas do onboarding economics nomeadas e em faixa; correlação vs causalidade rotulada.
6. **Retorno ao orquestrador:** report estruturado com Status PASS/BLOCKED, commit hash, validações, riscos — sem conclusão simulada se algo bloquear.

---

*Prompt integral desta iteração em [`process-log/prompts/iteration-02-prompt.md`](../prompts/iteration-02-prompt.md); decisões em [`process-log/decisions/iteration-02-analytical-contract-decisions.md`](../decisions/iteration-02-analytical-contract-decisions.md).*

---

## 11. Adendo — review gate 3x e correções (2026-08-28)

O review gate 3x (3 revisores `deepseek-max` read-only) retornou **2 veredictos `PASS`** e **1 `PASS_WITH_FIXES`** (findings materiais M1/M2). Correção aplicada por agente sequencial (commit `fix: strengthen revenue churn contract`); registro completo em `process-log/reviews/iteration-02-review-summary.md` e detalhe em `process-log/reports/iteration-02-review-fix-report.md`. Resumo:

1. **M1 — lente de revenue churn degenerada (corrigida, decisão D9):** o contrato §5 agora define **duas lentes nomeadas** — R1 *gross subscription ending MRR* (exposição bruta; 1.179.139 / 486 na janela; NÃO rotulada como perda automática) e R2 *net account-state MRR loss* (churn-to-inactive 18.507/2 transições + active contraction 150.817/36 transições; total 169.324); saídas ocultas não-dominantes quantificadas (274 assinaturas / 422.691; episódios conta-mês 254; 226 inalterados/0 reduzidos; ex. A-5a215a 2024-12 com 34.626 encerrados e winner inalterado em 17.313); uso isolado do winner como churn contratual **proibido** (report §7, contrato §5/§6).
2. **M2 — números de qualidade hardcoded (corrigidos):** 19.142/25.000/76,6%, 290, 5.568/22,3%, 13.198, 1.077, 53, 90, 143, 825/41,2%, 95, 148 agora são derivados em runtime (`quality_metrics`) e injetados no render do report §8 e contrato §9/§10; varredura adicional eliminou 110/312/352 e 35/277/125 do render (parametrizados).
3. **`closed_at` (decisão D10):** política explícita no contrato §7/§10 (tickets por `submitted_at`; resolução/CSAT só com tickets fechados; nulos excluídos com denominador explícito; nunca imputar fechamento futuro); `closed_at` promovida a coluna mínima (REQUIRED) com D01 parseável e gate G15.
4. **Base account-month:** novas colunas auditáveis `mrr_ended_in_month` e `n_ended_in_month` (lente R1 por conta×mês; trials encerrados têm MRR 0 — contagem separada), rotuladas como desfechos (contrato §8) e reconciliadas à fonte pelo invariante **G14** (1.179.139 / 486 / 427 conta×mês). Invariantes agora G1–G15 (31 PASS / 1 WARN / 0 FAIL).
5. **LOWs baratos:** nota de arredondamento dos quantis e tie-break explícito do matching (report §4); coluna "Acumulado" removida; código morto (G5 `cur`) removido; redação de grão diário vs mensal clarificada (report §8, contrato §9); wording do D4 precisado (fim em 12-15 → inativa em dezembro). LOWs não-materiais aceitos com justificativa no review summary (§5).
6. **Recálculo independente do corretor:** 46/46 checks OK (painel reconstruído do zero, célula-a-célula contra o CSV commitado — 0 divergências; lentes de receita; métricas de qualidade; MV-A/B/C com as novas colunas; partições). Diferença vs o reviewer em saídas ocultas (274/422.691 vs 255/398.462 reportados): variante de agregação do reviewer (script não commitado); as 226 saídas com winner_mrr inalterado coincidem exatamente na visão conta-mês; conclusão material idêntica (≈21–23×).
7. **Sandbox de falha estrutural re-executado:** 3 cenários (coluna `churn_date` renomeada; arquivo `churn_events` ausente; coluna `signup_date` renomeada) → exit 1, relatório regravado com "Falha estrutural", sem traceback, outputs de dados preservados (anti-stale), idempotente no caminho de FAIL.