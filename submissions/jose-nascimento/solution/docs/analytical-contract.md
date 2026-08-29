# Contrato Analítico — Challenge 001 (RavenStack)

Versão congelada na Iteração 02, gerada por `solution/src/02_reconcile_churn.py` (determinística; números derivados dos CSVs commitados). Todas as iterações seguintes (03–07) DEVEM seguir este contrato; qualquer mudança exige nova iteração de reconciliação e re-validação dos invariantes.

## 1. Propósito

As três fontes de "churn" da base divergem (ver `solution/evidence/02_consistency_report.md` §3): `accounts.churn_flag` (snapshot), `subscriptions.churn_flag/end_date` (histórico de assinaturas) e `churn_events` (registro de eventos). Nenhuma fonte sozinha responde todas as perguntas do challenge; este contrato define **qual lente responde cada pergunta**, o grão-mestre account-month e as regras temporais/anti-leakage que impedem misturar métricas incompatíveis.

## 2. Snapshot, data-limite e janela observacional

- **Data-limite (corte):** 2024-12-31. Nenhuma observação posterior existe na base.
- **Janela observacional:** 2023-01-01..2024-12-31 (24 meses), idêntica à janela global da auditoria (Iteração 01).
- **Painel account-month:** para cada conta, meses do **mês do signup** até 2024-12 inclusive. Meses anteriores ao signup não existem para a conta (não entram em coortes nem em denominadores).
- **Semântica do mês:** o estado de um mês `m` é o estado no **fim** de `m` (último dia, granularidade de data). Eventos/uso com data em `m` pertencem a `m`.

## 3. Grão de cada métrica

| Métrica | Grão | Fonte primária | Notas |
|---|---|---|---|
| Eventos de churn (diagnóstico) | event | `churn_events` | carrega reason_code/refund/feedback; 1 linha por evento |
| Conta com evento | account | `churn_events` (distinct) | primeira ocorrência = primeiro churn por eventos |
| Churn de assinatura | subscription | `subscriptions.end_date`/`churn_flag` | receita em risco por assinatura |
| Conta com assinatura encerrada | account | `subscriptions` (distinct) | 312 contas na base |
| Status de conta (snapshot) | account | `accounts.churn_flag` | SOMENTE estado no corte; não é série temporal |
| Base-mestre | account × mês | `solution/data/processed/account_month.csv` | 1 linha por account×mês (5.807 linhas) |

## 4. Definições primárias por pergunta de negócio

| Pergunta | Definição primária | Lente |
|---|---|---|
| Diagnóstico/causa raiz (por que os clientes saem?) | eventos de `churn_events` (reason/feedback); primeiro evento por conta para tempo-ao-churn | C (eventos) |
| Churn de assinatura/receita (quanto MRR se perde?) | duas lentes nomeadas (§5): R1 — gross subscription ending MRR (exposição contratual bruta; `end_date`) e R2 — net account-state MRR loss (churn-to-inactive + active contraction no estado/winner do painel) | B (assinaturas) / painel |
| Status atual da conta (quem está churnado hoje?) | `accounts.churn_flag` no corte (110 contas) — apenas rótulo final | A (snapshot) |
| Risco (quem está em risco?) | features do painel disponíveis ANTES da data índice (winner MRR, uso alinhado, tickets, eventos anteriores); ver §8 | painel account-month |

**Quando NÃO comparar:** as contagens 110 (flag) / 312 (assinatura) / 352 (eventos) não são três medições do mesmo fenômeno e não podem ser somadas, subtraídas ou usadas como alvo alternativo entre si (ex.: "taxa de churn" calculada com eventos não é comparável a uma calculada com `end_date`; a diferença 35/277/125 é estrutura da base, não imprecisão de uma fonte). Cada análise escolhe UMA lente e declara qual.

## 5. Fórmulas e denominadores

- **Logo churn (eventos):** contas com ≥1 evento no mês `m` (primeiro evento para coortes); denominador = contas em risco no início de `m` (signup ≤ m, sem primeiro evento anterior, não censuradas). Censura no corte para contas sem evento.
- **R1 — gross subscription ending MRR (exposição contratual bruta):** soma do MRR das assinaturas com `end_date` no período (na janela inteira: 1179139 de 486 assinaturas; no painel, por conta×mês nas colunas `mrr_ended_in_month`/`n_ended_in_month`, reconciliadas à fonte pelo invariante G14). NÃO rotular como "receita perdida" automaticamente: a saída pode ser troca/replacement/sobreposição (89,2% das linhas do painel têm >1 assinatura ativa) — é o **teto** da receita em risco no período, não a perda.
- **R2 — net account-state MRR loss (perda líquida do estado/winner):** variação de `winner_mrr` entre snapshots de fim de mês, decomposta em: (a) **churn-to-inactive** = Σ winner_mrr(m−1) das contas ativas em m−1 e inativas em `m` (na janela: 18507 em 2 transições: 2023-10->2023-11 (12736); 2024-08->2024-09 (5771)); (b) **active contraction** = Σ [winner_mrr(m−1) − winner_mrr(m)] das contas ativas em m−1 e `m` com winner_mrr decrescente (na janela: 150817 em 36 transições). Total líquido na janela: 169324. Cobertura/trade-off: a lente de estado só observa a assinatura dominante; saídas não-dominantes são invisíveis (274 assinaturas / 422691 na janela — razão 22.8× vs churn-to-inactive; episódios conta-mês: 254 / 422691), e expansões ativas na mesma conta (+2287279 na janela) compensam perdas — o estado é líquido, não contratual.
- **PROIBIDO (decisão D9):** usar a saída da lente winner/estado **isoladamente** como total de churn contratual/receita perdida; apresentar R1 como perda sem declarar a lente; ou misturar R1/R2 na mesma fórmula. Análises de receita (It03+) DEVEM declarar a lente (R1 = exposição; R2 = estado líquido) e reportar o gap entre elas.
- **Activity signal:** uso ALINHADO = linhas de `feature_usage` com `usage_date` dentro de [start_date, end_date] da assinatura (inclusive). Sinais por mês: `usage_rows_month` (bruto) e `usage_rows_in_window_month` (alinhado); a política §9 exige reportar ambos.
- **Status de conta:** `active` se ≥1 assinatura ativa no fim do mês; `inactive` caso contrário (lente B). Não usar `accounts.churn_flag` como série.

## 6. Múltiplas assinaturas e regra do winner (determinística)

A base tem 2–19 assinaturas por conta (mediana 10) com sobreposição massiva no tempo (4686 de 5254 linhas account-mês com >1 ativa). Somar MRR de assinaturas sobrepostas produz double-counting (62216507 vs 28766224 na janela — razão 2.16×). Regra adotada — **winner**: entre as ativas no fim do mês, escolhe (1) não-trial; (2) maior `mrr_amount`; (3) `start_date` mais recente; (4) `subscription_id` lexicográfico. O estado da conta (active/inactive) e o MRR do mês usam o winner. `mrr_sum_naive` é preservado para auditoria e comparação, nunca como métrica de receita. Alternativas rejeitadas: soma ingênua (double-counting); winner por start mais recente (menos estável em upgrades; usado apenas como sensibilidade).

**Escopo do winner:** o winner é **estado/risco da conta** (status e nível de MRR dominante). Ele NÃO é, isoladamente, uma métrica de churn contratual de receita: saídas de assinaturas não-dominantes com a conta ativa são invisíveis à série do winner (274 assinaturas / 422691 na janela; ex.: A-5a215a em 2024-12 com 34626 de MRR de assinaturas encerradas e winner inalterado em 17313). Para receita, usar R1/R2 do §5; o winner serve para features de risco e estado (ver também D9).

## 7. Semântica de intervalos, cancelamento, reativação e sobreposição

- Intervalo de assinatura: **[start_date, end_date] inclusive** (uma assinatura que termina em `d` é ativa no fim de qualquer mês cujo último dia ≤ d).
- Assinatura ativa no mês `m` ⟺ start_date ≤ último dia de `m` E (end_date nulo OU end_date ≥ último dia de `m`). `end_date` nulo = ativa no corte.
- Cancelamento: assinatura com `end_date` presente e `churn_flag=True` (0 violações na base — D04 da Iteração 01).
- Reativação: evento com `is_reactivation=True` registra retorno; no painel, a conta volta a `active` quando uma assinatura ativa existe no fim do mês. Reativação é um episódio da lente de eventos, não um estado de assinatura.
- Sobreposição: assinaturas simultâneas da mesma conta são resolvidas pela regra do winner (§6); nunca somadas para métricas de receita.
- Eventos múltiplos no mesmo mês: `n_events_in_month` conta todos; `churn_event_in_month` é binário (≥1). Nenhum episódio vira conta perdida sozinho — status vem da lente de assinatura.
- Tickets: existem por `submitted_at` (abertura); `closed_at` documenta o fechamento. Métricas de resolução e CSAT usam APENAS tickets fechados com informação observável até a data índice; `closed_at` nulo exclui o ticket com denominador explícito; **nunca imputar fechamento futuro** (política detalhada no §10).

## 8. Política anti-leakage

- **Data índice:** para análises de risco/coortes, a data índice é o fim do mês de referência. Features do mês `m` usam apenas informação disponível até o fim de `m`.
- **Alvo vs feature no mesmo mês:** quando o desfecho é "churn no mês `m`" (evento ou inatividade), as features DEVEM vir de linhas do painel com mês ≤ m−1 (ou de informação com data < início de `m`); `churn_event_in_month(m)`, `n_events_in_month(m)` e `status(m)` são o desfecho, nunca features do próprio mês.
- **Colunas variantes no tempo** do painel (`status`, `winner_mrr`, `n_active_subs`, `churn_event_in_month`, `n_events_in_month`, `mrr_ended_in_month`, `n_ended_in_month`, uso, tickets, CSAT) são derivadas somente de linhas-fonte com data ≤ fim de `m` (invariante G10).
- **Colunas de desfecho rotuladas (nunca features do próprio mês):** `churn_event_in_month(m)`, `n_events_in_month(m)`, `status(m)`, `mrr_ended_in_month(m)` e `n_ended_in_month(m)` (assinaturas com `end_date` em `m` — lente R1) são eventos/estado do mês `m`: quando o desfecho é "churn/receita em `m`", features DEVEM vir de linhas com mês ≤ m−1.
- **Proibido em features de risco:** `churn_flag_snapshot_2024_12_31` (rótulo do corte, não série temporal); eventos/uso/tickets posteriores à data índice; `accounts.churn_flag` como variável explicativa de meses anteriores ao corte.
- **Alvo:** definido por pergunta (§4) — nunca misturar lentes na mesma fórmula.

## 9. Registros temporalmente inválidos (política e sensibilidade)

A auditoria (Iteração 01) encontrou anomalias temporais estruturais da base sintética. Política: **nada é descartado silenciosamente** — cada conjunto é quantificado, reportado e usado onde tem significado:

| Registro | Quantidade | Uso permitido |
|---|---|---|
| Uso antes do `start_date` (76.6% das linhas) | 19142 | fora de janelas alinhadas; contagem separada (`usage_rows_month`) |
| Uso depois do `end_date` | 290 | idem |
| Uso dentro da janela (22.3%) | 5568 | sinais de atividade alinhados (`usage_rows_in_window_month`) |
| Uso/tickets anteriores ao signup (grão de linha) | 13198 / 1077 | fora da janela observacional da conta; no painel mensal entram apenas linhas do mês de signup posteriores à data de signup |
| Eventos fora da vida de assinaturas (53 antes da 1ª assinatura; 90 após a última `end_date`) | 143 | mantidos na lente de eventos; alinhamento documentado (§4 do report) |

Sensibilidade: análises que usam atividade DEVEM declarar a variante (bruta vs alinhada) e reportar a diferença; análises de coorte temporal DEVEM usar apenas linhas alinhadas ou declarar o viés. CSAT (825 nulos, 41.2%) e reason/feedback (95 'unknown'; 148 nulos de feedback) são tratados conforme §10.

## 10. CSAT, reason codes, feedback e política de `closed_at`

`satisfaction_score` (domínio {3, 4, 5}, 825 nulos (41.2%)), `reason_code` (95 'unknown') e `feedback_text` (148 nulos) são evidência **sugestiva** de qualidade da experiência — não prova causal de churn. Relações entre essas variáveis e churn, quando observadas, são correlações e serão rotuladas como tal nas Iterações 03–05.

**Política de `closed_at` (decisão D10):** os tickets existem por `submitted_at` (abertura); `closed_at` documenta o fechamento. (1) Métricas de resolução (ex.: tempo até `closed_at`) e de CSAT usam APENAS tickets fechados — na base atual, 2000 de 2000 tickets têm `closed_at` (0 nulos; verificado pelo gate G15); (2) tickets com `satisfaction_score` nulo são excluídos da média com **denominador explícito** (1175 tickets com nota na base); (3) **nunca imputar fechamento futuro**: se um ticket está aberto na data índice, nenhuma métrica de resolução/CSAT do período o inclui como fechado; (4) `csat_mean_month` do painel agrega por mês de `submitted_at` — a política (1)–(3) aplica-se a qualquer uso posterior.

## 11. Invariantes e gates (executáveis)

A cada execução do `02_reconcile_churn.py`, os invariantes G1–G15 (ver report §9) são verificados: unicidade account×mês; MRR ≥ 0; datas válidas; contas ativas ≤ 500; transições fecham (contagem e MRR, tolerância 0, inteiros); totais de cada lente reconciliam à fonte; cobertura de assinaturas; anti-leakage estrutural; gross ending MRR do painel reconciliado à fonte (G14); política de `closed_at` (G15). Qualquer violação é FAIL e o pipeline para (exit 1) com relatório atualizado.

## 12. Decisões registradas (problema → opções → evidência → decisão → trade-off)

Resumo executivo das decisões desta iteração; detalhe completo em `process-log/decisions/iteration-02-analytical-contract-decisions.md`.

| Decisão | Problema | Opções | Decisão | Trade-off |
|---|---|---|---|---|
| D1 — Lente primária por pergunta | 3 fontes de churn divergentes (110/312/352) | fonte única vs lente por pergunta | lente por pergunta (contrato §4) | exige disciplina: nunca misturar |
| D2 — Grão-mestre | contagens por grão diferentes | account / subscription / account×mês | account×mês (painel do signup ao corte) | painel maior; suporta coortes e séries |
| D3 — Regra do winner | sobreposição de assinaturas dobra MRR | soma ingênua vs winner (max MRR) vs winner (start recente) | winner não-trial, max MRR, start recente, id | MRR da conta = assinatura dominante; soma preservada p/ auditoria |
| D4 — Semântica temporal | bordas de mês/intervalo ambíguas | início vs fim do mês; exclusive vs inclusive | estado no FIM do mês; [start, end] inclusive | assinatura que termina em `d` deixa de contar no mês cujo último dia > d (ex.: fim em 12-15 → inativa em dezembro); regra determinística, sem look-ahead intra-mês |
| D5 — Registros inválidos | 76,6% do uso fora da janela | descartar vs reter com política | reter com política dupla (bruto/alinhado) e quantificação | análises precisam declarar variante |
| D6 — Rótulo snapshot no painel | flag do corte como série vazaria | omitir vs incluir com proibição | incluir como `churn_flag_snapshot_2024_12_31` proibido em features | conveniência vs risco de mau uso (G10 cobre) |
| D7 — CSAT/reason/feedback | qualidade e completude limitadas | tratar como prova vs sugestiva | evidência sugestiva rotulada | conclusões causais proibidas (It03–05) |
| D9 — Duas lentes de receita | fórmula única de revenue churn (winner) era degenerada (18.507 capturados vs 422.691/274 saídas ocultas; 1.179.139 de exposição) | uma fórmula vs duas lentes nomeadas | R1 gross ending MRR (exposição) + R2 net account-state MRR loss (churn-to-inactive + contraction); winner preservado como estado/risco, PROIBIDO como churn contratual isolado | análises de receita precisam declarar a lente e o gap (contrato §5; report §7) |
| D10 — Política de `closed_at` | semântica de tickets adiada da It01 (assimetria de nulos vs `end_date`) | imputar vs documentar | tickets existem por `submitted_at`; resolução/CSAT só com tickets fechados; nulos excluídos com denominador explícito; nunca imputar fechamento futuro | métricas de resolução dependem da completude de `closed_at` (0 nulos na base; gate G15) |

## 13. Errata da auditoria crítica final (2026-08-29)

A auditoria crítica final identificou dois defeitos nos consumidores da Iteração 04/07; esta errata não altera o grão, as lentes ou as definições deste contrato. O vínculo evento–assinatura é reportado com polaridade explícita: 21,0% dos eventos têm assinatura encerrada em ±30d e 79,0% não têm. Para o tempo até o próximo evento após reativação, a estimativa KM em horizonte h usa a função degrau `S(h) = S(max(t <= h))` quando há follow-up suficiente; horizonte não observável retorna vazio. Os valores corrigidos são S(90d) = 0,681461 e S(180d) = 0,515156, com mediana de 187 dias. Ver a remediação em `process-log/reviews/final-critical-audit-summary.md` e os gates independentes no `solution/src/06_verify_pipeline.py`.
