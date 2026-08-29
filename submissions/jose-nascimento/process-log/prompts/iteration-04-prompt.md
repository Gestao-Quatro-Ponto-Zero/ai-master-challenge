# Prompt — Iteração 04 · Ciclos de reativação, jornada da conta e watchlist operacional

Transcrição fiel do prompt recebido pelo agente executor desta iteração (arquivado por evidência de processo, conforme regra de governança).

---

Você é o AGENTE EXECUTOR ÚNICO da ITERAÇÃO 04 — ciclos de reativação, jornada da conta e watchlist operacional — do G4 AI Master Challenge. Execute somente esta etapa, com regras point-in-time, backtest honesto, evidência e git. NÃO escreva recomendações/ROI finais (It05) nem relatório executivo final (It07).

REPO/CONTEXTO
- Repo `/tmp/opencode/ai-master-challenge-work`; branch `submission/jose-nascimento`; pasta única permitida `submissions/jose-nascimento/`; HEAD esperado `12ff47c9bcc29f1dbd81aba186985c1191a8f10b`.
- Leia instruções oficiais, plano/checklist, contrato It02 corrigido, evidence/outputs It01–It03 e review summaries. Use apenas dados/scripts da submissão; não leia pesquisas externas internas.
- Fatos do contrato que devem ser respeitados: eventos ≠ subscriptions ≠ snapshot; winner serve para estado/exposição, não churn contratual isolado; `gross ending MRR` não é receita automaticamente perdida; todos os targets/outcomes devem ser excluídos de features point-in-time.

OBJETIVO
Entregar segmentos de risco/atenção com denominadores e contas específicas, sem inventar poder preditivo. Distinguir:
- recorrência de eventos (múltiplos `churn_events`);
- reativação marcada no dataset;
- ciclos reais active→inactive→active no painel de assinatura;
- exposição atual (winner MRR);
- valor de jornada como proxy acumulada sem dupla contagem.
Criar watchlist atual auditável e validá-la por backtests temporais anteriores; se regras não derem lift, chamá-la `operational priority/exposure`, não `churn risk score`.

TAREFAS
1. Inspecione git/status/log. It04 logicamente OPEN durante execução e CONCLUDED após validação; gate 3x PENDING; futuras PENDING.
2. Implemente `solution/src/04_lifecycle_watchlist.py`, offline, paths relativos, determinístico, gerando:
   - `solution/evidence/04_lifecycle_watchlist_report.md`;
   - tabelas pequenas e auditáveis em `solution/out/tables/`: account lifecycle, reactivation/recurrence, temporal backtest, priority segments e top-20 watchlist;
   - 3–4 gráficos úteis em `solution/out/charts/` (prefixo It04), sem repetir gráficos It03.
3. Reativação/recorrência:
   - recalcule events por conta (2+,3+,máx), 61 flags/55 contas se confirmado;
   - defina sequência temporal e estime próximo evento após reativação, taxa, tempo mediano e censura; não chame ausência observada de sucesso sem follow-up;
   - quantifique concentração de eventos e gross ending MRR/exposição dessas contas com lentes separadas;
   - não afirme que reativar custa menos (CAC/winback inexistentes); não trate `is_reactivation` como dinheiro recuperado sem ligação demonstrável.
4. Ciclos reais: derive active→inactive→active do account-month e compare com múltiplos eventos/subscriptions encerradas. Mostre quando "ciclo" é episódio de evento vs mudança real de estado. Não use 175 multi-evento como 175 contas que morreram/reviveram.
5. Jornada/valor:
   - compute `lifecycle_value_proxy` por conta a partir de winner MRR account-month (somatório mensal até cutoff; declare proxy, não receita GAAP);
   - current winner MRR, tenure, nº subs/events/reactivations, datas recentes, gross ending MRR recente, status/ciclos;
   - compare top-20 por current MRR vs top-20 por lifecycle proxy: overlap e rank shifts; explique viés contra contas novas e use as duas dimensões, não substitua uma pela outra.
6. Segmentos de atenção devem ser estados/jornadas sustentados pelos dados (ex.: onboarding <90d; repeat-event/reativação recente; alto valor com sinal recente), pois It03 não encontrou heterogeneidade forte por industry/channel/tier. Para cada segmento: N, current MRR, lifecycle proxy, historical event rate ou backtest outcome, incerteza e rationale. Evite overlap oculto entre segmentos.
7. Backtest point-in-time SEM ML:
   - escolha no mínimo 2 cutoffs históricos com horizonte observável (preferencialmente 2024-06-30 e 2024-09-30, 90 dias; adicione outro se necessário);
   - construa features usando somente dados ≤cutoff: tenure, eventos anteriores, reactivation anterior, recent ending MRR, current winner MRR/lifecycle proxy até cutoff; proíba `accounts.churn_flag` snapshot e qualquer evento/outcome futuro;
   - outcome = primeiro/próximo evento no horizonte, com definição clara para contas elegíveis; múltiplos eventos não viram logos duplicados;
   - reporte baseline, precision/recall/lift por regra e combinação; use intervals/N. Não ajuste thresholds no mesmo período sem disclosure; se explorar, separe desenvolvimento/validação temporal.
   - se não houver lift consistente, não crie score pseudo-científico; ordene por exposição + evidência e rotule corretamente.
8. Watchlist atual (cutoff 2024-12-31): top 20 contas específicas com account_id e campos estritamente observáveis até cutoff; regra de inclusão, prioridade, evidência, current MRR, lifecycle proxy, tenure, eventos prévios, última data, flags de qualidade/limitações. Não inclua target futuro inexistente; não declare churn futuro. Inclua guia de interpretação.
9. Valide manualmente ao menos 3 contas: uma reativada com/sem próximo evento; uma com rank shift current vs lifecycle; uma conta onboarding/watchlist. Recalcule independentemente métricas principais.
10. Causalidade/limitações: recurrence é associação; all-active at cutoff limita validação direta; valores são proxies; sinteticidade/timestamps; censura. Explique o que CS poderia fazer com a lista sem afirmar certeza.
11. Evidência:
   - prompt integral `process-log/prompts/iteration-04-prompt.md`;
   - decisão `process-log/decisions/iteration-04-watchlist-decisions.md` com opções/evidência/trade-offs;
   - report `process-log/reports/iteration-04-lifecycle-watchlist-report.md` com workflow, erros reais, hipótese/regra→backtest→decisão, validações, riscos/handoff It05.
12. Validações: baseline 2x/idempotência/checksums; CWD diferente; FAIL estrutural sem stale/traceback; outputs report↔CSV; PNGs abrem/labels; no leakage audit coluna a coluna; 3 MVs; git diff-check/escopo/paths/segredos/Markdown.

CONTENÇÃO
- Sem ML, dashboard, app, PDF, recomendações finais ou ROI. Sem score arbitrário somando pesos sem validação.
- Use pandas/matplotlib já existentes; não adicione dependência.

GIT
- Preserve histórico; só pasta permitida; `git add -f` paths pretendidos.
- Commit `feat: prioritize accounts by lifecycle and validated risk signals`.
- Sem amend/force/config/destrutivo; push; valide local==remote/tree limpo.

CRITÉRIOS DE ACEITAÇÃO
- Recorrência, reativação e ciclo de estado não confundidos.
- Lifecycle proxy sem overlap, current exposure preservada.
- Backtest point-in-time reproduzível e sem leakage; nomenclatura proporcional ao lift.
- Top-20 com contas específicas e explicação; segmentos com N/$; 3 checks; outputs/gates/process/git completos.

REPORT FINAL
PASS/BLOCKED; hash/push; métricas de recorrência/reativação; ciclos reais; rank overlap; backtest por cutoff (baseline/precision/recall/lift); regra final e nome honesto da watchlist; segmentos; top contas (resumo); MVs/erros/testes; riscos e handoff It05. BLOCKED se houver leakage ou score sem validação.