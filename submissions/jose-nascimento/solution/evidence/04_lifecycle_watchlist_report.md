# Relatório de Ciclos de Reativação, Jornada da Conta e Watchlist — Iteração 04 (RavenStack)

Gerado por `solution/src/04_lifecycle_watchlist.py` (execução offline e determinística; sem timestamp para garantir output byte-a-byte estável entre execuções).

## 1. Metodologia

- **Contrato analítico (It02):** `solution/docs/analytical-contract.md` — eventos ≠ subscriptions ≠ snapshot (lentes C/B/A); winner = estado/exposição (§6); gross ending MRR = exposição, não receita perdida (§5); anti-leakage: features <= data índice, targets nunca em features (§8); censura no corte 2024-12-31.
- **Regras pré-especificadas ANTES dos resultados:** `process-log/decisions/iteration-04-watchlist-decisions.md` (D4: regras do backtest com thresholds fixos; D6: composição da watchlist; D8: nomenclatura proporcional ao lift). Nenhum threshold foi ajustado após ver os números.
- **Escopo:** NENHUMA recomendação/ROI (It05), NENHUM modelo preditivo/ML, nenhum score somando pesos sem validação.
- **Saídas:** este relatório; tabelas em `solution/out/tables/` (9 arquivos); gráficos em `solution/out/charts/` (4 arquivos).

## 2. Recorrência de eventos (lente C — histórico, NÃO predição)

- Eventos totais: **600**; contas com >= 1 evento: **352** de 500.
- Distribuição por conta (0/1/2/3/4/5 eventos): 0 / 177 / 116 / 47 / 10 / 2 contas. Máximo: **5** eventos.
- **Recorrência:** 175 contas com >= 2 eventos; 59 com >= 3. Concentração: **423 de 600 eventos (70.5%)** vêm das contas com >= 2 eventos — 175 contas concentram 70,5% dos episódios.
- Gaps entre eventos consecutivos da mesma conta: n=248, mediana **58 dias**, média 102.06; 148 gaps (59.7%) <= 90d. Este é o espaçamento observado ENTRE eventos — não é uma predição do próximo evento (ver backtest, seção 6: a regra de recorrência NÃO tem lift).

## 3. Reativação marcada (`is_reactivation`) — sequência temporal com censura

- Flags: **61** em **55** contas (confirmado: 61 flags / 55 contas).
- **26** flags são o PRIMEIRO evento da conta (sem evento anterior na janela 2023-2024): a flag marca 'retorno' no dataset sem evento anterior observável — nuance estrutural, não silenciada.
- Episódios com evento anterior: 35 (gap mediano 45 dias).
- Próximo evento após a reativação: observado em 24 episódios (gap mediano 53 dias; média 88); **37 episódios sem próximo evento observado** — NÃO são 'sucesso de reativação': a maioria das reativações é recente (26 flags em out-dez/2024) e a janela termina no corte (censura).
- **Follow-up explícito (denominador declarado):**

| Janela | Episódios com follow-up >= janela | Próximo evento dentro da janela | Taxa |
|---|---|---|---|
| <= 30d | 50 | 6 | 12.0% |
| <= 90d | 35 | 10 | 28.6% |
| <= 180d | 20 | 7 | 35.0% |

- **Kaplan-Meier (tempo até o próximo evento após reativação; censura no corte):** sobrevivência em 90d = **0.653** (ou seja, ≈ 35% dos episódios têm próximo evento <= 90d); em 180d = 0.476; mediana = **187 dias** (alcançada na janela). A taxa observada (24/61 = 39,3%) SUBestima o retorno por censura — e nenhuma taxa aqui é 'receita recuperada': reativação é episódio de evento, sem ligação demonstrável com receita (contrato §5).

## 4. Ciclos reais de estado (painel account-month; lente B)

- Transições `active→inactive` no painel: **2** (contrato R2: churn-to-inactive = 18.507 em exatamente essas 2 transições).
- Transições `inactive→active`: **281**, das quais **279** são o gap inicial signup→primeira assinatura ativa (ex.: A-019782 signup 2023-04, primeira assinatura ativa 2023-06) e **2** são retornos reais após inatividade.
- **Ciclos completos active→inactive→active: 2 contas** (A-0baac2, A-180abf). Detalhe: A-180abf (inativa nov/2023, ativa desde jan/2024; 5 eventos, nenhum flag de reativação) e A-0baac2 (inativa set/2024 — sub encerrada 2024-09-13 —, ativa desde out/2024; 4 eventos, nenhum flag de reativação).
- **Comparação honesta das lentes:** 175 contas com >= 2 eventos (recorrência) ≠ 55 contas com flag de reativação (evento) ≠ 2 contas com ciclo real de estado (assinatura). Nenhuma dessas contagens é intercambiável: 175 multi-evento NÃO são 175 contas que morreram/reviveram — o estado de assinatura mudou de ativo→inativo apenas 2 vezes em toda a janela.
- Contratualmente: 312 contas têm assinatura encerrada; 291 contas têm assinatura encerrada SEGUIDA de nova assinatura (440 assinaturas) — re-assinatura contratual, outra lente ainda (não confundir com reativação de evento nem com ciclo de estado do painel).

## 5. Jornada/valor: `lifecycle_value_proxy` e exposição atual

- **Definição (D2):** `lifecycle_value_proxy` = soma do `winner_mrr` mensal do painel account-month até o cutoff (1 valor por account×mês; sem dupla contagem de assinaturas sobrepostas). **PROXY operacional, não receita GAAP** e não receita recuperada.
- Totais: Σ proxy (janela) = **28.766.224** (= Σ winner do painel, contrato It02); current winner MRR no corte (2024-12) = **3.668.852** (500 contas ativas por estado — ver limitações, seção 10).
- **Top-20 por current MRR vs top-20 por lifecycle proxy:** overlap = **7 contas** (Jaccard 0.21); correlação de Spearman entre as dimensões = **0.575**. Rank shifts >= 3 posições entre as duas listas (contas compartilhadas):

| Conta | Rank current | Rank lifecycle | Shift |
|---|---|---|---|
| A-1f0636 | 8 | 17 | -9 |
| A-68f37c | 5 | 1 | +4 |
| A-80eeb6 | 16 | 5 | +11 |
| A-977ca0 | 15 | 2 | +13 |
| A-aa9511 | 9 | 6 | +3 |

- **Viés declarado:** o proxy acumula ao longo do tenure → favorece contas antigas (ex.: A-a8d89d, 15.522/mês atuais, 201.786 de jornada, tenure 389d — top-20 da jornada, fora do top-20 atual); o MRR atual favorece contas novas de alto valor (ex.: A-c70870, 33.830/mês, jornada 34.419, tenure 70d). **As duas dimensões se complementam; nenhuma substitui a outra.**

## 6. Backtest point-in-time (sem ML; regras pré-especificadas em D4)

- **Desenho:** cutoffs 2024-03-31, 2024-06-30, 2024-09-30 com horizonte de 90 dias (totalmente observável; o mais tardio termina em 2024-12-29 <= corte); sensibilidade com horizonte de 180 dias nos dois primeiros cutoffs. Elegíveis = contas com signup <= cutoff. Outcome = primeiro/próximo evento em (cutoff, cutoff+horizonte] — binário por conta; múltiplos eventos NÃO duplicam logos.
- **Features (somente dados <= cutoff):** tenure_days; n_events_pre; n_react_pre; last_event_days; recent_ended_mrr_90d (R1); winner_mrr_at; lifecycle_proxy_pre. **Proibidos e não usados:** `accounts.churn_flag` (snapshot) e qualquer evento/assinatura com data > cutoff (auditoria coluna a coluna na seção 9).
- **Regras (thresholds fixos, sem tunagem):**

| Regra | Definição |
|---|---|
| R_A recorrencia>=2 | n_events_pre >= 2 |
| R_B reativacao>=1 | n_react_pre >= 1 |
| R_C evento<=90d | last_event_days <= 90 |
| R_D onboarding<=90d | tenure_days <= 90 |
| R_E winner>=P75 | winner_mrr_at >= P75 do cutoff |
| R_F A e C | recorrencia>=2 E evento<=90d |
| R_G B e C | reativacao>=1 E evento<=90d |
| R_H D e C | onboarding<=90d E evento<=90d |
| R_I E e (A|B|C) | winner>=P75 E (recorrencia|reativacao|evento<=90d) |

- **Resultados (horizonte 90d):** tabela completa em `out/tables/t14_backtest_temporal.csv` (baseline, precision, recall, lift, intervalo de Wilson 95% por regra × cutoff). Resumo dos lifts:

| Regra | lift 2024-03-31 | lift 2024-06-30 | lift 2024-09-30 | N por cutoff | Validada* |
|---|---|---|---|---|---|
| R_A recorrencia>=2 | 0.44 | 0.41 | 0.89 | 21; 49; 88 | NAO |
| R_B reativacao>=1 | 0.52 | 0.41 | 1.29 | 9; 20; 34 | NAO |
| R_C evento<=90d | 0.74 | 0.63 | 1.01 | 50; 77; 107 | NAO |
| R_D onboarding<=90d | 1.57 | 1.56 | 1.83 | 56; 65; 72 | SIM |
| R_E winner>=P75 | 0.56 | 0.85 | 0.71 | 74; 90; 105 | NAO |
| R_F A e C | 0.66 | 0.41 | 0.92 | 14; 30; 44 | NAO |
| R_G B e C | 0.00 | 0.67 | 1.27 | 3; 12; 16 | NAO |
| R_H D e C | 0.58 | 0.76 | 1.77 | 8; 16; 21 | NAO |
| R_I E e (A|B|C) | 0.31 | 0.72 | 0.62 | 15; 28; 38 | NAO |

*Critério pré-registrado (D4): lift > 1,15 nos TRÊS cutoffs de 90d com N >= 25.
- **Leitura:** a única regra com lift consistente é **R_D (onboarding, tenure <= 90d)**: 1,57 / 1,56 / 1,83 (precision 0,34–0,54; a base inteira tem taxa de evento em 90d de 0,22–0,30). **Recorrência (R_A: 0,44/0,41/0,89), reativação (R_B: 0,52/0,41/1,29 — lift apenas no período do spike, inconsistente) e alto MRR (R_E: 0,56/0,85/0,71) NÃO validam**; evento recente (R_C: 0,74/0,63/1,01) também não. A sensibilidade de 180d confirma: somente R_D tem lift (1,26/1,51); as demais ficam <= 1,05.
- **Consequência (D8):** NÃO existe score de risco de churn com validação temporal nesta base. A watchlist abaixo é nomeada **operational priority/exposure**: ordenação por exposição (winner MRR) + evidência (onboarding validado; recência para ação de CS), com cada linha rotulada pelo seu sinal. Recorrência e reativação permanecem como associações históricas descritas nas seções 2–3, nunca como preditores.

## 7. Segmentos de atenção (estados/jornadas; N e US$)

| Segmento | N | Current MRR (US$) | Lifecycle proxy (US$) | Taxa evento (hist.) | Taxa evento recente | Evidência de backtest | Incerteza | Rationale |
|---|---|---|---|---|---|---|---|---|
| S1 Onboarding (tenure<=90d) | 80 | 621981 | 1026824 | 0.675 | 0.675 | sinal VALIDADO no backtest (regra D: lift 1,57/1,56/1,83 nos cutoffs 90d) | intervalos largos (N pequeno); censura no corte | estado de jornada; mecanismo It03 H1/H8 (churn precoce de coortes novas) |
| S2 Repeat-event (>=2 eventos) | 175 | 1245634 | 9821516 | 1.000 | 0.629 | regra A: lift 0,44/0,41/0,89 — SEM lift consistente; associação histórica | intervalos largos (N pequeno); censura no corte | concentração de eventos (70,5% dos eventos vêm de 175 contas); recorrência descreve histórico, não prediz próximo evento |
| S3 Reativacao recente (flag out-dez/2024) | 25 | 179256 | 1321045 | 1.000 | 1.000 | regras B/G: lift 0,52/0,40/1,30 — inconsistente; KM 90d = 0,653 (35% dos episódios com próximo evento <=90d), mediana 187d, censura declarada | intervalos largos (N pequeno); censura no corte; 26 das 61 flags são o 1º evento da conta | episódio de evento marcado is_reactivation; NÃO é ciclo de estado; subconjunto de S4 (declarado) |
| S4 Evento recente (ultimo evento<=90d) | 178 | 1299245 | 7524526 | 1.000 | 1.000 | regra C: lift 0,74/0,63/1,01 — SEM lift; janela acionável de CS | intervalos largos (N pequeno); censura no corte | último episódio de churn em out-dez/2024; acionabilidade operacional, não predição |
| S5 Alto valor (winner>=P75) | 130 | 1780851 | 13105611 | 0.692 | 0.346 | regra E: lift 0,56/0,85/0,71 — SEM lift; segmento de exposição, não risco | intervalos largos (N pequeno); censura no corte | exposição atual (winner MRR >= P75); proteção de receita; 130 contas (empates no quantil; 125 esperadas) |

- **Overlap declarado (nunca oculto):**

| Par | Overlap (contas) |
|---|---|
| S1 ∩ S2 | 26 |
| S1 ∩ S4 | 54 |
| S2 ∩ S4 | 110 |
| S3 ∩ S4 | 25 |
| S2 ∩ S3 | 19 |

- Notas: S3 (reativação recente) ⊆ S4 (evento recente) por construção (o flag é um evento). S5 é segmento de exposição, NÃO de risco (regra E sem lift). Os segmentos são jornadas, não firmografia — It03 (H6) não encontrou heterogeneidade material por industry/channel/tier.

## 8. Watchlist atual (cutoff 2024-12-31) — operational priority/exposure

- **Regra de composição (D6, pré-especificada):** tiers com caps declarados, NUNCA score: **Tier A** (8) = onboarding (tenure <= 90d — único sinal validado no backtest); **Tier B** (8) = evento recente (último evento <= 90d, fora do A — janela acionável de CS, sem lift validado); **Tier C** (4) = recorrência/reativação sem evento recente com winner >= P50 (proteção de receita). Dentro de cada tier: `winner_mrr` desc (exposição), desempate por account_id. A composição 8/8/4 é uma escolha de governança declarada e reproduzível, não um modelo de risco.
- **Top-20 (tabela completa: `out/tables/t16_watchlist_top20.csv`):**

| Rank | Conta | Tier | Winner MRR | Lifecycle proxy | Tenure (d) | Eventos | Reativ. | Último evento | Dias desde | R1 recente 90d | Flag snapshot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | A-c70870 | A | 33830 | 34419 | 70 | 1 | 0 | 2024-12-13 | 18 | 0 | 0 |
| 2 | A-18793f | A | 29452 | 29452 | 13 | 1 | 0 | 2024-12-30 | 1 | 2812 | 0 |
| 3 | A-d4e0d4 | A | 23283 | 69849 | 74 | 0 | 0 | — | — | 23283 | 0 |
| 4 | A-ce550d | A | 21691 | 39402 | 65 | 1 | 0 | 2024-12-28 | 3 | 23406 | 1 |
| 5 | A-66224b | A | 18308 | 54924 | 74 | 0 | 0 | — | — | 18308 | 0 |
| 6 | A-b48f73 | A | 15920 | 19840 | 48 | 0 | 0 | — | — | 0 | 0 |
| 7 | A-76fa4d | A | 13731 | 27462 | 37 | 2 | 0 | 2024-12-03 | 28 | 13731 | 0 |
| 8 | A-82d8a6 | A | 13532 | 13532 | 33 | 1 | 0 | 2024-12-29 | 2 | 340 | 0 |
| 9 | A-68f37c | B | 24079 | 433422 | 535 | 4 | 2 | 2024-12-18 | 13 | 0 | 0 |
| 10 | A-d77f4c | B | 18706 | 172572 | 463 | 3 | 0 | 2024-12-03 | 28 | 196 | 0 |
| 11 | A-05f0e5 | B | 18308 | 204572 | 607 | 2 | 0 | 2024-11-25 | 36 | 0 | 0 |
| 12 | A-4814a3 | B | 17313 | 56202 | 105 | 1 | 0 | 2024-11-25 | 36 | 17313 | 1 |
| 13 | A-65c341 | B | 16716 | 173329 | 371 | 2 | 0 | 2024-12-16 | 15 | 1911 | 0 |
| 14 | A-58b9ff | B | 15124 | 61586 | 214 | 1 | 0 | 2024-10-10 | 82 | 0 | 0 |
| 15 | A-4e44e8 | B | 14925 | 32016 | 133 | 2 | 1 | 2024-10-11 | 81 | 392 | 1 |
| 16 | A-712f1c | B | 14925 | 161389 | 381 | 1 | 0 | 2024-10-24 | 68 | 0 | 1 |
| 17 | A-56962b | C | 32437 | 59495 | 266 | 2 | 0 | 2024-08-26 | 127 | 0 | 0 |
| 18 | A-80eeb6 | C | 17711 | 264122 | 602 | 2 | 0 | 2024-02-09 | 326 | 5024 | 0 |
| 19 | A-e51ec7 | C | 16517 | 104276 | 465 | 3 | 0 | 2024-04-07 | 268 | 0 | 0 |
| 20 | A-a8d89d | C | 15522 | 201786 | 389 | 2 | 0 | 2024-08-26 | 127 | 0 | 0 |

- **Guia de interpretação (leia antes de usar):**
  1. Esta lista NÃO prevê churn futuro: NENHUM alvo futuro é incluído e nenhuma conta é 'declarada em risco de sair'. É uma priorização operacional de atenção (onboarding validado; episódios recentes; exposição).
  2. `churn_flag_snapshot_2024_12_31` é o rótulo snapshot do dataset (110 contas no corte) — contexto de qualidade, PROIBIDO como feature preditora (contrato §8); sua presença na tabela não altera a prioridade.
  3. `winner_mrr` = exposição atual (estado, contrato §6); `lifecycle_value_proxy` = jornada acumulada (proxy, D2).
  4. CS pode usar a lista para: contato de ativação/onboarding (Tier A), conversa de renovação/winback com contexto do episódio recente (Tier B) e revisão de conta de alto valor com histórico (Tier C) — sem afirmar que qualquer conta 'vai sair'.
  5. As 500 contas com todas as features estão em `out/tables/t11_account_lifecycle.csv` — qualquer re-fatia da regra é reproduzível.

## 9. Auditoria de leakage (coluna a coluna)

| Feature (backtest) | Fonte | Janela de dados usada | Verificação estrutural |
|---|---|---|---|
| tenure_days | ravenstack_accounts.signup_date | signup <= cutoff | data fixa de cadastro; sem componente futuro |
| n_events_pre | ravenstack_churn_events.churn_date | churn_date <= cutoff | max(churn_date) <= cutoff (check G6b) |
| n_react_pre | ravenstack_churn_events (is_reactivation) | churn_date <= cutoff | idem |
| last_event_days | ravenstack_churn_events.churn_date | max churn_date <= cutoff | idem |
| recent_ended_mrr_90d | ravenstack_subscriptions.end_date | end_date em (cutoff-90d, cutoff] | max(end_date) <= cutoff (check G6b) |
| winner_mrr_at | account_month (mês do cutoff) | month == mês do cutoff | painel derivado de subs com start <= fim do mês (contrato G10) |
| lifecycle_proxy_pre | account_month.winner_mrr | month <= mês do cutoff | idem |
| outcome | ravenstack_churn_events.churn_date | churn_date em (cutoff, cutoff+horizonte] | NUNCA usado em features (conjuntos disjuntos por construção) |
| accounts.churn_flag | ravenstack_accounts | — | PROIBIDO em features (snapshot); presente apenas como contexto na watchlist |

## 10. Limitações e causalidade

- **Associação, não causalidade:** recorrência e reativação são associações históricas descritas nas seções 2–3; o único padrão com validação temporal é onboarding (R_D), coerente com a causa raiz de It03 (churn precoce de coortes novas) — hipótese causal plausível, não prova.
- **All-active no corte:** todas as 500 contas estão ativas por estado em 2024-12 (enquanto o snapshot marca 110 como churnadas) — a validação direta de 'perda real de estado' no presente é limitada; o backtest usa eventos históricos como outcome.
- **Proxies:** lifecycle_value_proxy é soma de winner MRR mensal (não receita GAAP; não inclui MRR de assinaturas não-dominantes); winner é estado/exposição, não churn contratual isolado (contrato §6).
- **Sinteticidade/timestamps:** a base é sintética (It01 §5); o pico de eventos no fim de 2024 pode ser artefato de geração — os lifts do backtest em 2024-09-30+90d cobrem justamente esse período e são os mais altos para R_D, o que reforça a cautela de não extrapolar.
- **Censura:** episódios de reativação sem próximo evento observado são censurados no corte (KM, seção 3); coortes recentes têm follow-up curto.
- **N pequenos:** intervalos de Wilson largos (tabela t14); N >= 25 exigido para considerar uma regra (D4).

## 11. Gates e validações

| ID | Escopo | Check | Veredito | Detalhe |
|---|---|---|---|---|
| F01-ravenstack_accounts.csv | ravenstack_accounts.csv | arquivo presente e carregável | PASS | 36148 bytes, CSV parseado (500 registros) |
| S01-ravenstack_accounts.csv | ravenstack_accounts.csv | colunas mínimas presentes | PASS | ravenstack_accounts.csv: 3 colunas exigidas presentes |
| F01-ravenstack_subscriptions.csv | ravenstack_subscriptions.csv | arquivo presente e carregável | PASS | 432565 bytes, CSV parseado (5000 registros) |
| S01-ravenstack_subscriptions.csv | ravenstack_subscriptions.csv | colunas mínimas presentes | PASS | ravenstack_subscriptions.csv: 6 colunas exigidas presentes |
| F01-ravenstack_churn_events.csv | ravenstack_churn_events.csv | arquivo presente e carregável | PASS | 44029 bytes, CSV parseado (600 registros) |
| S01-ravenstack_churn_events.csv | ravenstack_churn_events.csv | colunas mínimas presentes | PASS | ravenstack_churn_events.csv: 4 colunas exigidas presentes |
| F01-account_month.csv | account_month.csv | arquivo presente e carregável | PASS | CSV parseado (5807 linhas) |
| S02-panel | account_month.csv | colunas mínimas presentes | PASS | account_month.csv: 5 colunas exigidas presentes |
| G6b-leak-2024-03-31-90 | anti-leakage | features do cutoff 2024-03-31 (horizonte 90d) usam apenas dados <= cutoff | PASS | máx churn_date em features=2024-03-31 00:00:00; máx end_date=2024-03-29 00:00:00; cutoff=2024-03-31 |
| G6b-leak-2024-06-30-90 | anti-leakage | features do cutoff 2024-06-30 (horizonte 90d) usam apenas dados <= cutoff | PASS | máx churn_date em features=2024-06-30 00:00:00; máx end_date=2024-06-29 00:00:00; cutoff=2024-06-30 |
| G6b-leak-2024-09-30-90 | anti-leakage | features do cutoff 2024-09-30 (horizonte 90d) usam apenas dados <= cutoff | PASS | máx churn_date em features=2024-09-30 00:00:00; máx end_date=2024-09-30 00:00:00; cutoff=2024-09-30 |
| G6b-leak-2024-03-31-180 | anti-leakage | features do cutoff 2024-03-31 (horizonte 180d) usam apenas dados <= cutoff | PASS | máx churn_date em features=2024-03-31 00:00:00; máx end_date=2024-03-29 00:00:00; cutoff=2024-03-31 |
| G6b-leak-2024-06-30-180 | anti-leakage | features do cutoff 2024-06-30 (horizonte 180d) usam apenas dados <= cutoff | PASS | máx churn_date em features=2024-06-30 00:00:00; máx end_date=2024-06-29 00:00:00; cutoff=2024-06-30 |
| C01-charts | gráficos | número de gráficos gerado | PASS | esperado 4, gerado 4 |
| G1-events | recorrência | totais de eventos e contas reconciliam com churn_events | PASS | eventos=600 (fonte 600); contas=352 (fonte 352) |
| G1b-events | recorrência | contagens 2+/3+/máx corretas | PASS | 2+=175 (esperado 175); 3+=59 (esperado 59); máx=5 (esperado 5) |
| G2-reactivation | reativação | flags e contas de reativação (61/55) confirmadas | PASS | flags=61 (esperado 61); contas=55 (esperado 55) |
| G2b-reactivation | reativação | episódios fecham (com/sem próximo evento + censura) | PASS | com próximo=24; censurados=37; total=61 |
| G3-cycles | ciclos de estado | transições do painel fecham (contrato R2: 2 churn-to-inactive) | PASS | dec=2 (esperado 2); inc=281 (esperado 281); gaps=279; retornos=2; ciclos=2 |
| G4-panel | painel | 500 contas; Σ winner da janela reconcilia com o contrato (28.766.224) | PASS | Σ proxy=28766224 (esperado 28.766.224) |
| G4b-panel | painel | current winner MRR do corte (3.668.852) e 500 contas ativas por estado | PASS | Σ winner 2024-12=3668852 (esperado 3.668.852); ativas por estado=500/500 |
| G5-proxy | lifecycle proxy | Σ proxy por conta == Σ winner_mrr do painel (sem dupla contagem) | PASS | proxy = soma mensal de winner_mrr (1 linha por account×mês) |
| G6-backtest | backtest | elegíveis e outcomes por cutoff reconciliam com as fontes | PASS | elegíveis={'2024-03-31': 283, '2024-06-30': 348, '2024-09-30': 420} (esperado {'2024-03-31': 283, '2024-06-30': 348, '2024-09-30': 420}); outcomes={'2024-03-31': 61, '2024-06-30': 86, '2024-09-30': 124} (esperado {'2024-03-31': 61, '2024-06-30': 86, '2024-09-30': 124}) |
| G7-rules | backtest | veredito de validação mecânico (lift > 1,15 nos 3 cutoffs, N >= 25) | PASS | regras validadas=['D'] (esperado {D}) — thresholds pré-especificados em D4, sem tunagem |
| G8-watchlist | watchlist | 20 contas únicas; composição 8/8/4 (tiers A/B/C) | PASS | linhas=20; únicas=20; tiers={'A': 8, 'B': 8, 'C': 4} |
| G9-segments | segmentos | segmentos com N>0 e overlap declarado | PASS | segmentos=5; pares de overlap=5 |
| G10-outputs | outputs | tabelas e gráficos desta iteração gerados e não-vazios | PASS | tabelas=9; gráficos=4 |
| G11-rank | rank comparison | overlap top-20 current vs lifecycle e Spearman (âncora de regressão) | PASS | overlap=7 (âncora 7); Spearman=0.575 (âncora 0,575) |
| G12-zerodiv | denominadores | sem NaN em precision com n_rule > 0 | PASS | linhas com NaN indevido=0 |

## 12. Arquivos gerados

- Tabelas: `t11_account_lifecycle.csv`, `t12_reactivation_recurrence.csv`, `t13_state_cycles.csv`, `t14_backtest_temporal.csv`, `t14b_backtest_detail.csv`, `t15_priority_segments.csv`, `t15b_segment_overlap.csv`, `t16_watchlist_top20.csv`, `t17_rank_comparison.csv`.
- Gráficos: `It04_a_recurrence_reactivation.png`, `It04_b_cycle_lenses.png`, `It04_c_lifecycle_vs_current_mrr.png`, `It04_d_backtest_lift.png`.

Leitura das tabelas: `t11_account_lifecycle.csv` (jornada completa de 500 contas), `t12_reactivation_recurrence.csv` (distribuições de eventos e episódios de reativação), `t13_state_cycles.csv` (ciclos reais vs lentes), `t14_backtest_temporal.csv` (regras × cutoffs) e `t14b_backtest_detail.csv` (flags por conta × cutoff para auditoria), `t15_priority_segments.csv` (segmentos N/US$) e `t15b_segment_overlap.csv` (overlap), `t16_watchlist_top20.csv` (watchlist), `t17_rank_comparison.csv` (top-20 current vs lifecycle).