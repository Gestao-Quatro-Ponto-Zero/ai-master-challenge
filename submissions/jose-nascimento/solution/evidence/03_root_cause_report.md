# Relatório de Causa Raiz, Coortes e Onboarding — Iteração 03 (RavenStack)

Gerado por `solution/src/03_root_cause.py` (execução offline e determinística; sem timestamp para garantir output byte-a-byte estável entre execuções).

## 1. Metodologia

- **Hipóteses pré-registradas ANTES da análise:** `process-log/hypotheses/iteration-03-root-cause-hypotheses.md` (H1–H10, com thresholds fixados antes de ver os resultados; vereditos aplicados mecanicamente na seção 10).
- **Contrato analítico (Iteração 02):** `solution/docs/analytical-contract.md` — lente de eventos (C) para diagnóstico; lente de assinaturas para receita (R1 gross ending MRR = exposição; R2 net account-state MRR loss); painel account-month (`data/processed/account_month.csv`) como estado/risco; anti-leakage (features <= data índice; CSAT/resolução só com tickets fechados); variantes bruta vs alinhada de uso; censura no corte 2024-12-31.
- **Escopo:** NENHUMA recomendação (Iteração 05), NENHUMA watchlist (Iteração 04), NENHUM modelo preditivo/ML.
- **Saídas:** este relatório; tabelas em `solution/out/tables/` (13 arquivos); gráficos em `solution/out/charts/` (4 arquivos).

## 2. Série mensal 2023-2024 e decomposição do pico

- **Eventos totais:** 600 (fonte `churn_events`); **primeiros eventos:** 352 (contas únicas com evento: 352 de 500).
- **Período elevado (regra pré-registrada: first_events >= 1,5 x mediana 12/mês = 17.2):** 2024-03, 2024-05, 2024-06, 2024-07, 2024-08, 2024-09, 2024-10, 2024-11, 2024-12 (9 meses); vale em 2024-04 (abaixo da regra) — o 'churn subiu nos últimos meses' aparece como NÍVEL elevado sustentado (com pico em 2024-12), não um mês isolado.
- **Pico (mês de maior contagem):** **2024-12** com 43 primeiros eventos (taxa por conta elegível 22.51%; mês de maior taxa: 2024-12).
- **Receita (declarando a lente):** R1 gross ending MRR por mês (tabela t01) soma 1179139 (486 assinaturas) — exposição, NÃO perda (contrato §5). Concentração no fim de 2024: set-dez responde por 80.5% do R1 da janela e dezembro isolado por 48.7% (descritivo; pode ser artefato de geração da base — não interpretado como causa). R2 net account-state MRR loss soma 18507 (churn-to-inactive, 2 transições) + 150817 (active contraction) = 169324.
- **Decomposição do pico 2024-12** (baseline: 6 meses anteriores):
  - Por bucket de tenure (meses desde o signup): 0-3m: 36 (83.7% do pico; baseline 15.17; razão 2.37); 13-24m: 3 (7.0% do pico; baseline 3.83; razão 0.78); 4-6m: 2 (4.7% do pico; baseline 4.17; razão 0.48); 7-12m: 2 (4.7% do pico; baseline 5.33; razão 0.38).
  - Por coorte de signup (trimestre): 2023Q1: 0 (0.0%; razão 0.0); 2023Q2: 1 (2.3%; razão 0.46); 2023Q3: 2 (4.7%; razão 0.86); 2023Q4: 0 (0.0%; razão 0.0); 2024Q1: 1 (2.3%; razão 0.35); 2024Q2: 2 (4.7%; razão 0.32); 2024Q3: 4 (9.3%; razão 0.53); 2024Q4: 33 (76.7%; razão 9.43).
  - **Mecanismo do pico (regra H9):** bucket 0-3m (share 83.7%, ratio 2.37).
  - **Controle de composição de tenure (sensibilidade H2):** esperado 24.82 eventos pelo mix de tenure dos elegíveis x baseline dos buckets; observado 43 (ratio 1.73).

## 3. Coortes e tempo-ao-churn (Kaplan-Meier descritivo com censura)

- **Censura no corte 2024-12-31:** contas sem primeiro evento são observadas até o último mês do painel (at-risk) e censuradas — a taxa observada (eventos/n) SUBestima o churn de coortes recentes; a estimativa KM corrige isso. Tabela completa por trimestre e por mês: `t02_cohort_km.csv`; at-risk por trimestre: `t02b_cohort_km_at_risk.csv`.
- **IMPORTANTE (censura):** coortes de Q4-2024 têm <= 3 meses observáveis; NÃO comparar Q4 com janela completa. `km_surv_t6/t12/t18` vazio = horizonte NÃO observável (follow-up < horizonte, censura no corte). Quando observável, o valor é o da FUNÇÃO DEGRAU no maior tempo <= horizonte (carry-forward — não exige evento/censura exatamente em t = horizonte).

| Coorte (trimestre) | N contas | Eventos | Censuradas | Taxa observada | Sobrev. KM t=6 | Churn KM t=6 |
|---|---|---|---|---|---|---|
| 2023Q1 | 55 | 40 | 15 | 72.7% | 0.6364 | 36.4 |
| 2023Q2 | 54 | 31 | 23 | 57.4% | 0.7963 | 20.4 |
| 2023Q3 | 53 | 40 | 13 | 75.5% | 0.6415 | 35.9 |
| 2023Q4 | 65 | 52 | 13 | 80.0% | 0.4769 | 52.3 |
| 2024Q1 | 56 | 39 | 17 | 69.6% | 0.4107 | 58.9 |
| 2024Q2 | 65 | 47 | 18 | 72.3% | 0.3077 | 69.2 |
| 2024Q3 | 72 | 49 | 23 | 68.1% | não observado | — |
| 2024Q4 | 80 | 54 | 26 | 67.5% | não observado | — |

## 4. Onboarding economics (exposição bruta precoce; cenários CAC-equivalent)

- **R1 total (janela):** 1179139 em assinaturas encerradas.
- **Exposição por duração da assinatura** (tabela `t03_onboarding_buckets.csv`): 0d: 13 assinaturas, 46324 (3.9% do R1); 1-30d: 195 assinaturas, 467262 (39.6% do R1); 31-60d: 79 assinaturas, 188974 (16.0% do R1); 61-90d: 43 assinaturas, 103859 (8.8% do R1); 91-180d: 77 assinaturas, 177390 (15.0% do R1); 181-365d: 58 assinaturas, 171732 (14.6% do R1); >365d: 21 assinaturas, 23598 (2.0% do R1). O bucket `0d` = assinaturas com start = end (mesma data; 13 na base) — exposição instantânea, incluída para o share fechar 100%.
- **Exposição acumulada por duração (incluindo same-day `0d`;** tabela `t03c_cac_equivalent.csv`): <= 30d: 513586 (43.6% do R1; o bucket 1-30d isolado é 467262 = 39.6% do R1); <= 60d: 702560 (59.6% do R1); <= 90d: 806419 (68.4% do R1).
- **Primeiro evento por conta** (tabela `t03b_onboarding_accounts.csv`): <= 30d: 91 contas (25.9% das contas com evento); <= 60d: 150 contas (42.6% das contas com evento); <= 90d: 188 contas (53.4% das contas com evento).
- **Cenários CAC-equivalent exposure** (tabela `t03c_cac_equivalent.csv`): o dataset NÃO contém custo de aquisição; os cenários são múltiplos de MRR (1x, 3x, 6x, 12x) sobre a exposição bruta precoce, explicitamente nomeados — nunca 'CAC queimado' nem 'receita perdida' (R1 é exposição contratual, contrato §5).

## 5. Uso: 'o uso cresceu' — volume vs intensidade por conta

- **Volume total (primário, sem pré-signup):** 2775 -> 9027 linhas (225.3%); alinhado [start,end]: 883.3%.
- **Intensidade (mediana de linhas por conta-mês):** 2.0 -> 2.0 brutas (0.0%); alinhadas: 1.0 -> 1.0 (0.0%).
- **Definição da mediana:** mediana das medianas mensais sobre conta-meses com >= 1 linha de uso (não pareada por conta; mesmo desenho das iter. anteriores). Variante pooled (mediana sobre TODOS os account-months do ano, sem agregar por mês): alinhado 1.0 -> 2.0 (100.0%) — mais sensível à composição; o veredito H3 é dirigido pela variante raw (2.0 -> 2.0), robusta em ambas as definições.
- **Sensibilidade com pré-signup incluído:** total bruto 1.1% (tabela `t05_usage_monthly.csv` tem as duas variantes mês a mês).

## 6. Suporte pré-evento (desenho honesto; anti-leakage)

- **Desenho:** para cada mês m (2023-04..2024-12), grupo-churn = contas com primeiro evento em m; controle = contas elegíveis no início de m sem evento em m; janela W(m) = [dia 1 de m - 90d, dia 1 de m); tickets pré-signup excluídos; CSAT/resolução apenas de tickets fechados (contrato §10). Tabela mensal: `t06_support_monthly.csv`.
- **Pooled (média por conta-mês):** tickets/conta churn 0.309 vs controle 0.349; escalação 2.8% vs 5.1%; CSAT 4.0 vs 3.97 (denominador: tickets fechados com nota); FRT mediana 89.0 vs 93.5 min; resolução mediana 37.0 vs 35.0 h. Controle restrito a nunca-churn: tickets/conta 0.378.
- **Estratificado por tenure (sensibilidade):** 0-6m: churn 0.255 vs controle 0.263 tickets/conta; 7-12m: 0.567 vs 0.493; 13+m: 0.259 vs 0.478.

## 7. Segmentos (industry / canal / plano / trial)

- **Taxa global de primeiro evento:** 70.4% das contas (352 de 500); sobrevivência KM global no mês 6: 0.4428.
- Tabela completa: `t07_segments.csv`. Flags: `N_BAIXO` (N < 25, sem ranking), `RATE_FLAG` (taxa >= 1,5x global com N >= 25), `SURV_FLAG` (sobrevivência KM t=6 >= 10 p.p. abaixo da global, N >= 25), `MRR_FLAG` (share de R1 > 10%).

| Segmento | Valor | N | 1º evento | Taxa | Sobrev. KM t=6 | R1 (US$) | Share R1 | Flags |
|---|---|---|---|---|---|---|---|---|
| industry | Cybersecurity | 100 | 72 | 72.0% | 0.4079 | 279062 | 23.7% | MRR_FLAG |
| industry | DevTools | 113 | 83 | 73.5% | 0.4242 | 238611 | 20.2% | MRR_FLAG |
| industry | EdTech | 79 | 57 | 72.2% | 0.3834 | 198743 | 16.9% | MRR_FLAG |
| industry | FinTech | 112 | 76 | 67.9% | 0.48 | 253446 | 21.5% | MRR_FLAG |
| industry | HealthTech | 96 | 64 | 66.7% | 0.5073 | 209277 | 17.7% | MRR_FLAG |
| referral_source | ads | 98 | 59 | 60.2% | 0.5453 | 194077 | 16.5% | MRR_FLAG |
| referral_source | event | 96 | 68 | 70.8% | 0.4209 | 260954 | 22.1% | MRR_FLAG |
| referral_source | organic | 114 | 85 | 74.6% | 0.3734 | 265637 | 22.5% | MRR_FLAG |
| referral_source | other | 103 | 73 | 70.9% | 0.4447 | 273644 | 23.2% | MRR_FLAG |
| referral_source | partner | 89 | 67 | 75.3% | 0.4396 | 184827 | 15.7% | MRR_FLAG |
| plan_tier | Basic | 168 | 115 | 68.5% | 0.4441 | 328588 | 27.9% | MRR_FLAG |
| plan_tier | Enterprise | 154 | 108 | 70.1% | 0.4512 | 427710 | 36.3% | MRR_FLAG |
| plan_tier | Pro | 178 | 129 | 72.5% | 0.434 | 422841 | 35.9% | MRR_FLAG |
| is_trial_s | False | 403 | 285 | 70.7% | 0.4253 | 986195 | 83.6% | MRR_FLAG |
| is_trial_s | True | 97 | 67 | 69.1% | 0.5152 | 192944 | 16.4% | MRR_FLAG |

## 8. Reasons / CSAT / feedback (evidência sugestiva, nunca causa)

- **Missingness:** CSAT 41.2% nulos; reason 'unknown' 15.8%; feedback nulos 24.7%.
- **Decoplamento estrutural:** apenas 21.0% dos eventos têm assinatura encerrada ±30 dias na mesma conta — reason_code não se ancora em perda contratual (contrato §4/§10).
- **CSAT (tickets fechados com nota, todo o período):** contas com evento 3.98 vs sem evento 3.98 — comparação sugestiva, não causal.
- Distribuição por reason e associações com refund/upgrade/downgrade: tabela `t08_reasons.csv`.

## 9. Correlação vs causalidade

| Achado | Associação observada | Confundidores/alternativas | Status | Dado adicional |
|---|---|---|---|---|
| Tenure curto e churn (H1) | SUSTENTADA | mix de coortes (mais signups 2024); censura; eventos múltiplos | **hipótese causal plausível** | dados de onboarding real (ativação, integrações), não disponíveis na base |
| Spike mensal e coortes (H2/H9) | pico 2024-12: SUSTENTADA (aumento real de taxa); mecanismo: bucket 0-3m (share 83.7%, ratio 2.37) | sazonalidade; censura no corte; definição de pico; composição de tenure dos elegíveis (controlada no H2) | **hipótese causal plausível** | datas de ativação/uso pós-signup; campanhas de marketing |
| Uso cresceu em volume, não por conta (H3) | SUSTENTADA | 76,6% de uso fora da janela; pré-signup; mais contas em 2024 | **descritivo** | telemetria real de produto por conta |
| Uso pré-evento não precede churn (H4) | REFUTADA | uso pré-signup; janelas curtas; base sintética com uso independente do ciclo de vida | **não identificável** | série de uso real dentro do ciclo de assinatura |
| Sinais de suporte pré-evento (H5) | REFUTADA | tickets pré-signup; mix de tenure; nulos de CSAT | **não identificável** | conteúdo de tickets; CSAT com cobertura maior |
| Segmentos em risco (H6) | REFUTADA | mix de tenure/coorte por segmento; winner do mês; trials | **descritivo** | firmografia/uso por segmento |
| Reasons/CSAT/feedback (H7) | SUSTENTADA | missingness; nulos não-aleatórios; decoplamento das lentes | **não identificável** | entrevistas de churn; reasons com cobertura completa |
| Economia do onboarding (H8) | SUSTENTADA | R1 é exposição, não perda (troca/sobreposição); trials MRR 0 | **descritivo (parametrizado em cenários CAC-equivalent)** | custo real de aquisição; caminho de ativação |
| Decoplamento evento vs assinatura (estrutural da base) | 21.0% dos eventos com assinatura encerrada ±30d | base sintética; lentes de churn independentes | **descritivo** | fonte de eventos com vínculo contratual |

## 10. Vereditos das hipóteses (thresholds pré-registrados)

| Hipótese | Veredito | Números | Nota |
|---|---|---|---|
| H1 | **SUSTENTADA** | primeiros eventos com tenure <= 6m: 75.3% (N=352); mediana = 3m; threshold: >=50% e mediana <=6 | ver threshold no arquivo de hipóteses |
| H2 | **SUSTENTADA (aumento real de taxa)** | pico 2024-12: taxa 22.51% vs mediana da janela 7.42% (razão 3.03); vs mediana 6m anteriores 13.01% (razão 1.73); controle de composição de tenure: esperado 24.82 eventos, observado 43 (ratio 1.73) — aumento persiste após controle de tenure | thresholds: composição se razão 0,75-1,25 vs mediana; taxa se >=1,5x 6m anteriores |
| H3 | **SUSTENTADA** | total bruto (sem pré-signup): 2775 -> 9027 (225.3%); mediana por conta: 2.0 -> 2.0 (0.0%); alinhado: 883.3% total, 0.0% mediana; sensibilidade tudo: 1.1% | threshold: total >= +20% E mediana por conta < +10% |
| H4 | **REFUTADA** | mediana linhas alinhadas/mês pré-evento: churn 0.0 vs controle 0.0 (razão NA); zero-uso: churn 61.7% vs controle 52.7% (Δ 9.0 p.p.) | threshold: razão < 0,5 OU Δ zero-uso >= 25 p.p.; janela restrita a meses pós-signup (contrato §2) — o Δ 13,7 p.p. reportado antes era artefato de exposição (meses pré-signup contados como zero) e foi corrigido |
| H5 | **REFUTADA** | tickets/conta 0.309 vs 0.349 (Δ -0.04); escalação 2.8% vs 5.1%; CSAT 4.0 vs 3.97; FRT 89.0 vs 93.5 min; resolução 37.0 vs 35.0 h | threshold: Δ tickets >= 1 OU escalação >= 1,5x OU CSAT <=3,5 vs >4,0 OU FRT/resolução >= 1,5x |
| H6 | **REFUTADA** | nenhum segmento com taxa >= 1,5x a global e N >= 25. NOTA: o limiar RATE_FLAG é estruturalmente inalcançável (1,5 x 70.4% = 105.6% > 100%) — teste de taxa não informativo por desenho (erro de threshold pré-registrado, documentado; não renegociado). Conclusão pelo critério alternativo pré-registrado SURV_FLAG (KM t=6 >= 10 p.p. abaixo da global 0.4428): nenhum segmento cruza (maior gap 6.9 p.p.); spread de taxas observado 60.2-75.3% | threshold: N >= 25 E taxa >= 1,5x global (inalcançável por desenho com taxa global > 66,7% — documentado); critério alternativo pré-registrado válido: SURV_FLAG (KM t=6 >= 10 p.p. abaixo da global); MRR_FLAG reportado à parte |
| H7 | **SUSTENTADA** | CSAT nulos 41.2%; reason 'unknown' 15.8%; feedback nulos 24.7%; associação refund por reason: presente; eventos com sub encerrada ±30d: 21.0% | threshold: missingness > 25% OU unknown > 10% OU sem associação com refund/upgrade/downgrade |
| H8 | **SUSTENTADA** | R1 de assinaturas com <=90d de vida: 68.4% do total; primeiros eventos <=90d do signup: 53.4% das contas com evento | threshold: R1 <=90d >= 25% OU eventos <=90d >= 30% |
| H9 | **SUSTENTADA** | pico 2024-12 (43 primeiros eventos): mecanismo = bucket 0-3m (share 83.7%, ratio 2.37) | threshold: bucket com maior share E ratio >= 1,5x a própria linha de base |
| H10 | **APLICADA** | tabela de causalidade com status por achado (descritivo | hipótese causal plausível | não identificável) e confundidores | compromisso de processo, não hipótese de negócio |

## 11. Gates e validações

| ID | Escopo | Check | Veredito | Detalhe |
|---|---|---|---|---|
| F01-ravenstack_accounts.csv | ravenstack_accounts.csv | arquivo presente e carregável | **PASS** | 36148 bytes, CSV parseado (500 registros) |
| S01-ravenstack_accounts.csv | ravenstack_accounts.csv | colunas mínimas desta iteração presentes | **PASS** | 6 colunas exigidas presentes |
| F01-ravenstack_subscriptions.csv | ravenstack_subscriptions.csv | arquivo presente e carregável | **PASS** | 432565 bytes, CSV parseado (5000 registros) |
| S01-ravenstack_subscriptions.csv | ravenstack_subscriptions.csv | colunas mínimas desta iteração presentes | **PASS** | 5 colunas exigidas presentes |
| F01-ravenstack_churn_events.csv | ravenstack_churn_events.csv | arquivo presente e carregável | **PASS** | 44029 bytes, CSV parseado (600 registros) |
| S01-ravenstack_churn_events.csv | ravenstack_churn_events.csv | colunas mínimas desta iteração presentes | **PASS** | 7 colunas exigidas presentes |
| F01-ravenstack_feature_usage.csv | ravenstack_feature_usage.csv | arquivo presente e carregável | **PASS** | 1375897 bytes, CSV parseado (25000 registros) |
| S01-ravenstack_feature_usage.csv | ravenstack_feature_usage.csv | colunas mínimas desta iteração presentes | **PASS** | 2 colunas exigidas presentes |
| F01-ravenstack_support_tickets.csv | ravenstack_support_tickets.csv | arquivo presente e carregável | **PASS** | 143597 bytes, CSV parseado (2000 registros) |
| S01-ravenstack_support_tickets.csv | ravenstack_support_tickets.csv | colunas mínimas desta iteração presentes | **PASS** | 7 colunas exigidas presentes |
| S02-panel | account_month.csv | colunas mínimas do painel presentes | **PASS** | 13 colunas exigidas presentes (5807 linhas) |
| C01-charts | gráficos | número de gráficos gerado | **PASS** | 4 PNGs (manifesto: a_monthly_events_and_rate.png, b_km_by_signup_quarter.png, c_onboarding_exposure_by_duration.png, d_usage_volume_vs_intensity.png) |
| G1-events | série mensal | eventos totais/primeiros reconciliam a churn_events e ao painel | **PASS** | eventos=600 (fonte 600); primeiros=352 (contas com evento 352); painel=600 |
| G2-r1 | lente de receita bruta | R1 gross ending MRR e contagem reconciliam ao painel/contrato | **PASS** | R1=1179139 (contrato: 1.179.139); assinaturas=486 (contrato: 486) |
| G3-r2 | lente de estado (R2) | R2 churn-to-inactive + active contraction reconciliam ao contrato | **PASS** | churn-to-inactive=18507 (contrato 18.507); contraction=150817 (contrato 150.817); net=169324 (contrato 169.324) |
| G4-eligible | denominador elegível | cadeia elegível(m) = signups <= m - primeiros eventos anteriores | **PASS** | 0 meses com quebra de cadeia; último eligible=191 |
| G5-km | Kaplan-Meier | at_risk(0) = N da coorte; sobrevivência em [0,1] e monotônica | **PASS** | 0 violações em 8 coortes |
| G6-usage | uso | linhas totais reconciliam à fonte (25.000) e pré-signup separado | **PASS** | Σ linhas por mês (com pré-signup)=25000 (fonte 25.000); variante sensibilidade=25000 |
| G7-support | suporte | pool de suporte com N >= 30 conta-mês por lado; política closed_at respeitada | **PASS** | churn=346 contas-pool; controle=3162; CSAT só fechados com nota; pré-signup excluído no primário |
| G8-segments | segmentos | contagens de segmentos fecham (500 contas / 352 eventos / R1 1.179.139) | **PASS** | contas=500; eventos=352; R1=1179139 |
| G9-zerodiv | denominadores | sem NaN em taxas com denominador > 0 | **PASS** | 0 colunas com NaN indevido |
| G10-outputs | outputs | tabelas e gráficos gerados e não-vazios | **PASS** | tabelas ausentes/vazias=nenhuma; gráficos ausentes/vazios=nenhuma |
| G11-onboarding | onboarding economics | soma dos buckets de duração reconcilia ao R1 total (1.179.139) | **PASS** | Σ buckets=1179139 (R1 total 1.179.139); bucket 0d incluso |

## 12. Causa raiz (síntese) e limitações

- Síntese da causa raiz: ver `process-log/reports/iteration-03-root-cause-report.md` (seção de decisão do executor). Este relatório é a evidência numérica; a interpretação com status de certeza e o handoff para a Iteração 04 estão no report de processo.
- Limitações: base sintética (Iteração 01 §5); lentes de churn decopladas (contrato §4); 76,6% do uso fora da janela (contrato §9); CSAT/reasons sugestivos (contrato §10); nenhum custo de aquisição na base (CAC-equivalent são cenários nomeados).
