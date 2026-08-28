# Plano de Ações e Impacto — Iteração 05 (RavenStack)

Gerado por `solution/src/05_actions_impact.py` (execução offline e
determinística; sem timestamp para garantir output byte-a-byte estável).
Premissas fixadas ANTES do cálculo em
`process-log/decisions/iteration-05-action-impact-assumptions.md`.

## 1. Resposta primeiro

Quatro ações: três para agora (uma como pré-requisito), uma para depois:

| Ação | Decisão | Por quê |
|---|---|---|
| **ACT-03** Instrumentação de dados (milestone de ativação, reason estruturado, timestamps, CSAT, lens unificada) | **Now** | pré-requisito da medição E do rollout do ACT-01; SLA ≤ 30d para o milestone de ativação em produção; metas de qualidade nomeadas (sem US$) |
| **ACT-01** Programa de ativação/onboarding 0-90d com milestones instrumentados e rollout gradual (experimento com holdout) | **Now** | única ação ancorada em sinal com validação temporal (lift 1,57/1,56/1,83 nos 3 cutoffs 90d; N≥25); rollout inicia somente após instrumentation readiness (ACT-03). Impacto PLANEJADO (não medido): **2,7–13,0 eventos/90d** e **21.104–101.078 US$ de expected MRR-equivalent exposure affected/90d** (base: 6,9 eventos; 53.497 US$). O lift descreve associação observada — **não é efeito do programa**; o efeito será medido pelo experimento |
| **ACT-02** Triage semanal da watchlist top-20 (8 onboarding validados vs 12 exposure-only) | **Now** | esforço baixo (S), usa watchlist existente, independe de instrumentação; exposição coberta **392.030 US$/mês (10,7% do total)**. Os 12 exposure-only NÃO são rotulados como alto risco |
| **ACT-04** Piloto observacional de reativação/recorrência | **Later** | baixa confiança (sem lift; associação descritiva com censura); sem claim de ROI |

## 2. Evidência que sustenta (curto)

- **Onboarding ≤ 90d é o único sinal validado** temporalmente (backtest
  point-in-time It04; regra D: 1,57/1,56/1,83; sensibilidade 180d 1,26/1,51).
  Coerente com a causa raiz It03 (53,4% dos primeiros eventos ≤ 90d do signup;
  R1 ≤ 90d = 68,4% da janela — exposição, não perda).
- **Recorrência, reativação e alto MRR NÃO validam** (0,44/0,41/0,89 ·
  0,52/0,41/1,29 · 0,56/0,85/0,71) → watchlist é **operational
  priority/exposure**, nunca score.
- **Segmentos amplos, uso e suporte não discriminam** (It03 H3–H6) →
  nenhuma ação é desenhada sobre eles.
- **All-active no corte** (500/500 por estado) → impacto medido por eventos
  (lente C) e exposição (lentes R1/winner separadas), nunca por "perda real
  de estado" no presente.

## 3. Ações priorizadas (detalhe em `t18_actions_prioritized.csv`)

| ID | Ação | Decisão | Evidência | Impacto (faixa) | Esforço | 1º sinal | Owner |
|---|---|---|---|---|---|---|---|
| ACT-03 | Instrumentação de dados: milestone de ativação, reason estruturado, timestamps alinhados, CSAT com cobertura, lens unificada | Now | ALTA como habilitadora | CSAT com nota: 58,8% hoje -> >= 90%; reason 'unknown' 15,8% -> < 5%; uso em janela 22,3% -> >= 90%; milestone de ativação 0% -> 100% dos novos signups | M | <= 30d (SLA do milestone de ativação em produção) | Data/Product Eng |
| ACT-01 | Programa de ativação/onboarding 0-90d: milestones instrumentados, intervenção por estágio e rollout gradual com holdout (desenho experimental) | Now | ALTA | 2,7–13,0 eventos/90d; exposição 21.104–101.078 US$/90d (cenários conservador–ambicioso) | M | 90d (1ª coorte completa do rollout; rollout inicia somente após instrumentação ACT-03 — SLA <= 30d) | PM Onboarding (desenho) + CS (execução) |
| ACT-02 | Triage operacional semanal da watchlist top-20: 8 onboarding validados vs 12 exposure-only | Now | MÉDIA | 20 contas/semana; exposição coberta 392.030 US$/mês (10,7% da exposição total); sem estimativa de US$ de efeito | S | 1 semana | CS Lead + agente CS |
| ACT-04 | Piloto OBSERVACIONAL de reativação/recorrência com dados instrumentados (sem claim de ROI) | Later | BAIXA | sem estimativa financeira (proibido ROI de winback/reativação mais barata) | S | 1 trimestre (primeiras reativações com follow-up) | CS + Data |

Sem score numérico: decisão por evidência + impacto + esforço, com
reversibilidade, dependências e stop/go declarados por linha.

## 4. Impacto em faixa — fórmula, cenários e honestidade

**Fórmula (só ACT-01 tem estimativa de exposição defensável):**

```
expected_events_90d   = N_elegível × incidence_90d              (histórico descritivo)
events_affected_90d   = N_elegível × incidence_90d × redução_relativa
exposure_affected     = Σ winner_mrr(elegíveis) × incidence_90d × redução_relativa
```

- `N_elegível` = 80 contas onboarding no corte (tenure ≤ 90d);
  Σ winner MRR = **621.981 US$** (lente estado/exposição).
- `incidence_90d` = precision pooled da regra D nos cutoffs 90d =
  **83/193 = 0.4301**
  — faixa observada entre cutoffs (min-max de 3 coortes disjuntas):
  0.3393–0.5417. **A faixa NÃO é intervalo de confiança**;
  CI de Wilson 95% do pooled ≈ 0.362–0.501
  (derivado separadamente e rotulado como CI). Independência do pooling:
  overlap = 0 verificado entre as janelas de elegibilidade dos cutoffs
  (gate G13-disjoint; 193 contas únicas em t14b).
- `redução_relativa` = **premissa de planejamento** 10%/20%/30%
  (conservador/base/ambicioso) — NÃO derivada do lift; será testada pelo
  experimento ACT-01. Componentes exibidos arredondados (incidência a 4
  casas); re-cálculo a partir dos valores exibidos pode divergir ≤ 0,01%
  (~25 US$) do valor exibido (tolerância documentada).

| Ação | Cenário | Incidência 90d | N elegível | Eventos esp. 90d | Redução rel. | Eventos afetados | Exposição base (US$) | Exposição afetada (US$) | Nota |
|---|---|---|---|---|---|---|---|---|---|
| ACT-01 | conservador | 0.3393 | 80 | 27.10 | 10.0% | 2.70 | 621.981 | 21.104 | premissa de planejamento (10% de redução relativa); NÃO derivada do lift; a ser testada pelo experimento ACT-01 |
| ACT-01 | base | 0.4301 | 80 | 34.40 | 20.0% | 6.90 | 621.981 | 53.497 | premissa de planejamento (20% de redução relativa); NÃO derivada do lift; a ser testada pelo experimento ACT-01 |
| ACT-01 | ambicioso | 0.5417 | 80 | 43.30 | 30.0% | 13 | 621.981 | 101.078 | premissa de planejamento (30% de redução relativa); NÃO derivada do lift; a ser testada pelo experimento ACT-01; incidência = precisão do cutoff 2024-09-30 (janela do pico sintético — cautela It04) |
| ACT-01 | sens-inc-lo | 0.3393 | 80 | 27.10 | 20.0% | 5.40 | 621.981 | 42.208 | sensibilidade de incidência (precision regra D 90d por cutoff; faixa observada entre cutoffs — NÃO é intervalo de confiança) |
| ACT-01 | sens-inc-base | 0.4301 | 80 | 34.40 | 20.0% | 6.90 | 621.981 | 53.497 | sensibilidade de incidência (precision regra D 90d por cutoff; faixa observada entre cutoffs — NÃO é intervalo de confiança) |
| ACT-01 | sens-inc-hi | 0.5417 | 80 | 43.30 | 20.0% | 8.70 | 621.981 | 67.385 | sensibilidade de incidência (precision regra D 90d por cutoff; faixa observada entre cutoffs — NÃO é intervalo de confiança) |
| ACT-01 | sens-pop-flow | 0.4301 | 68.25 | 29.40 | 20.0% | 5.90 | 530.628 | 45.639 | sensibilidade de população: fluxo médio trimestral 2024 de signups |

**Honestidade (obrigatória):** eventos ≠ logos ≠ revenue churn (lentes C/B/A
não intercambiáveis, contrato §4); R1 é exposição contratual, **não é perda**
(§5); **nenhuma linha anualizada é apresentada** (removida no pós-gate do
review 3x: "melhor evitar se confuso", prompt It05);
nenhum custo monetário é afirmado (CAC/winback não existem na base); ACT-02/03/04
não têm linha de US$ porque não há estimativa financeira defensável — impacto
operacional mensurável (coverage, quality, instrumentation) no lugar.

## 5. Experimento do programa de ativação (ACT-01)

- **Desenho:** rollout gradual por semana de signup, 50/50 tratado/holdout,
  por 4 trimestres; outcome = primeiro evento de churn
  (lente C) em 90d; features pré-registradas (mesmas do backtest It04, sem
  leakage). O rollout inicia somente após instrumentation readiness (ACT-03,
  SLA ≤ 30d); o outcome primário (lente C, churn_events) independe de ACT-03,
  as leading metrics de milestone dependem.
- **Poder (aproximação normal de 2 proporções; sem dependência extra):**
  N por braço ≈ 34/68/136 (1/2/4 trimestres) →
  menor efeito detectável a 80% power ≈
  **68% / 51% / 37%** de redução
  relativa. Com o fluxo de ~68 signups/trimestre, efeitos
  abaixo de ~37% **não são detectáveis** em 4 trimestres:
  resultados inconclusivos NÃO são evidência de ausência de efeito.
- **Poder por cenário (N=136/braço, derivado em runtime):** redução de 10% →
  ~11%; 20% → ~31%; 30% →
  ~61%. Um efeito real de 10–30% é, portanto,
  **frequentemente inconclusivo** com o fluxo atual (MDE ≈ 37%).
- **P(falso GO por ponto ≥ 10% sob efeito nulo) ≈ 24%**
  (derivado em runtime): o piso de 10% por si dispararia GO por ruído em ~1
  de 4 experimentos nulos — por isso a regra abaixo exige evidência
  estatística para escala.
- **Regra de decisão pré-registrada (3 estados; 1ª decisão [STOP/reescopo] em
  2 trimestres; decisão de escala em 4 trimestres de
  rollout + 90d de follow-up):**
  1. **SCALE/GO (eficácia):** redução relativa estimada ≥ 10% (piso
     operacional preservado) **E** IC95 do efeito exclui 0 na direção
     favorável, sem guardrail violado → escala total.
  2. **CONTINUE/LEARN:** ponto estimado favorável e/ou leading metrics
     melhoram, mas IC95 cruza 0 → NÃO alegar eficácia; estender
     holdout/ampliar amostra ou janela.
  3. **STOP/HARM:** efeito adverso com IC95 excluindo 0, ou guardrail
     crítico falhado (CSAT/escalação) → encerrar/reduzir.
  O piso de 10% permanece o mínimo operacional de planejamento; a evidência
  estatística (IC95 excluindo 0) é o que autoriza escala — sem isso, o
  desfecho honesto é inconclusivo, não ausência de efeito (gates
  G13-power-scenarios / G13-false-go / G13-decision-rule).

## 6. Plano de medição (detalhe em `t20_measurement_plan.csv`)

| Ação | Tipo | Métrica | Definição (resumo) | Denominador | Coorte | Janela | Fonte | Owner | Cadência |
|---|---|---|---|---|---|---|---|---|---|
| ACT-01 | leading | milestone_completion_rate | proporção de novos signups que completam o milestone de ativação dentro de 7/14/30 dias do signup | novos signups com milestone capturado (ACT-03) | coorte de signup (semanal) | 7/14/30d do signup | instrumentação ACT-03 (novo campo) | PM Onboarding | semanal |
| ACT-01 | leading | time_to_first_key_action | dias do signup até a primeira ação-chave (integração/uso alinhado) | novos signups | coorte de signup (semanal) | 90d | feature_usage alinhado (contrato §9) | PM Onboarding | semanal |
| ACT-01 | leading | onboarding_completion_rate | proporção de contas onboarding com todas as etapas do programa concluídas em 90d | coorte de signup | coorte de signup | 90d | instrumentação ACT-03 | CS | semanal |
| ACT-01 | lagging | first_event_90d_rate | taxa de primeiro evento de churn (lente C) em 90d por coorte | contas elegíveis da coorte (signup <= início) | coorte de signup | 90d após signup | churn_events (contrato §4/§8) | CS + Data | mensal |
| ACT-01 | lagging | r1_gross_exposure_short_lived | R1 gross ending MRR de assinaturas com <= 90d de vida (lente R1 separada; exposição, NÃO perda) | assinaturas encerradas | trimestre | 90d de vida da assinatura | subscriptions (contrato §5) | Data | trimestral |
| ACT-01 | lagging | state_mrr_lens | winner MRR (estado) e R2 net loss (churn-to-inactive + contraction) por lente separada | contas ativas | trimestre | trimestre | account_month (contrato §5) | Data | trimestral |
| ACT-01 | guardrail | csat_and_escalation | CSAT médio e taxa de escalação do suporte nas contas do programa | tickets fechados com nota (contrato §10) | contas do rollout | 90d | support_tickets | CS | semanal |
| ACT-02 | leading | triage_coverage_weekly | proporção do top-20 com triage registrado na semana | top-20 (t16) | top-20 fixo na semana | semana | t16_watchlist_top20.csv + registro de triage (novo) | CS Lead | semanal |
| ACT-02 | leading | action_documented_rate | proporção de contas triaged com ação registrada (contato de ativação/renovação/revisão) | top-20 triaged | semana | semana | registro de triage (novo) | CS Lead | semanal |
| ACT-02 | lagging | contact_outcome_90d | desfecho documentado dos contatos em 90d (ativação concluída, renovação, upgrade, re-evento) | contas com contato | coorte de contato | 90d | registro de triage + churn_events | CS Lead | trimestral |
| ACT-02 | guardrail | no_risk_labeling | comunicação sem rótulo de risco para os 12 exposure-only | top-20 | semana | semana | registro de triage | CS Lead | semanal |
| ACT-03 | leading | field_coverage | cobertura de campos instrumentados (CSAT, reason estruturado, milestone de ativação) | tickets/eventos/signups | mês corrente | mês | tickets/events/novo campo milestone | Data Eng | semanal |
| ACT-03 | leading | usage_in_window_share | proporção de linhas de uso dentro da janela da assinatura | feature_usage | mês corrente | mês | feature_usage + subscriptions (contrato §9) | Data Eng | mensal |
| ACT-03 | lagging | event_sub_linkage | proporção de eventos com assinatura encerrada ±30d na mesma conta | churn_events | trimestre | trimestre | churn_events + subscriptions | Data Eng | trimestral |
| ACT-03 | guardrail | no_imputation | nenhuma imputação de fechamento futuro/CSAT (política closed_at) | tickets | mês | mês | support_tickets | Data Eng | mensal |
| ACT-04 | leading | reactivation_followup | nº de reativações marcadas com follow-up explícito (janela observável) | episódios is_reactivation | mês corrente | mês | churn_events (It04 §3) | CS + Data | mensal |
| ACT-04 | lagging | next_event_rate_90d_180d | taxa de próximo evento <= 90d/180d pós-reativação (KM com censura no corte) | episódios de reativação | coorte de reativação | 90d/180d | churn_events (It04 §3) | Data | trimestral |
| ACT-04 | guardrail | no_roi_claim | nenhum valor em US$ atribuído a reativação (sem ligação com receita) | n/a | n/a | n/a | n/a | CS + Data | n/a |

## 7. Watchlist: 8 onboarding validados vs 12 exposure-only

A watchlist (It04) é **operational priority/exposure**. O Tier A (8 contas,
onboarding ≤ 90d — único sinal validado) recebe contato de ativação; os
Tiers B/C (12 contas: evento recente + proteção de receita) recebem revisão
de conta/renovação e **não são rotulados como alto risco de churn**.

| Rank | Conta | Tier | Grupo | Winner MRR | Ação de triage | Owner | Cadência |
|---|---|---|---|---|---|---|---|
| 1 | A-c70870 | A | validated_onboarding | 33.830 | Contato de ativação/onboarding com milestone (sinal validado: lift 1,57/1,56/1,83) | CS Lead + agente CS | semanal |
| 2 | A-18793f | A | validated_onboarding | 29.452 | Contato de ativação/onboarding com milestone (sinal validado: lift 1,57/1,56/1,83) | CS Lead + agente CS | semanal |
| 3 | A-d4e0d4 | A | validated_onboarding | 23.283 | Contato de ativação/onboarding com milestone (sinal validado: lift 1,57/1,56/1,83) | CS Lead + agente CS | semanal |
| 4 | A-ce550d | A | validated_onboarding | 21.691 | Contato de ativação/onboarding com milestone (sinal validado: lift 1,57/1,56/1,83) | CS Lead + agente CS | semanal |
| 5 | A-66224b | A | validated_onboarding | 18.308 | Contato de ativação/onboarding com milestone (sinal validado: lift 1,57/1,56/1,83) | CS Lead + agente CS | semanal |
| 6 | A-b48f73 | A | validated_onboarding | 15.920 | Contato de ativação/onboarding com milestone (sinal validado: lift 1,57/1,56/1,83) | CS Lead + agente CS | semanal |
| 7 | A-76fa4d | A | validated_onboarding | 13.731 | Contato de ativação/onboarding com milestone (sinal validado: lift 1,57/1,56/1,83) | CS Lead + agente CS | semanal |
| 8 | A-82d8a6 | A | validated_onboarding | 13.532 | Contato de ativação/onboarding com milestone (sinal validado: lift 1,57/1,56/1,83) | CS Lead + agente CS | semanal |
| 9 | A-68f37c | B | exposure_only | 24.079 | Revisão de conta/renovação com contexto do episódio (sem sinal validado — NÃO rotular alto risco) | CS Lead + agente CS | semanal |
| 10 | A-d77f4c | B | exposure_only | 18.706 | Revisão de conta/renovação com contexto do episódio (sem sinal validado — NÃO rotular alto risco) | CS Lead + agente CS | semanal |
| 11 | A-05f0e5 | B | exposure_only | 18.308 | Revisão de conta/renovação com contexto do episódio (sem sinal validado — NÃO rotular alto risco) | CS Lead + agente CS | semanal |
| 12 | A-4814a3 | B | exposure_only | 17.313 | Revisão de conta/renovação com contexto do episódio (sem sinal validado — NÃO rotular alto risco) | CS Lead + agente CS | semanal |
| 13 | A-65c341 | B | exposure_only | 16.716 | Revisão de conta/renovação com contexto do episódio (sem sinal validado — NÃO rotular alto risco) | CS Lead + agente CS | semanal |
| 14 | A-58b9ff | B | exposure_only | 15.124 | Revisão de conta/renovação com contexto do episódio (sem sinal validado — NÃO rotular alto risco) | CS Lead + agente CS | semanal |
| 15 | A-4e44e8 | B | exposure_only | 14.925 | Revisão de conta/renovação com contexto do episódio (sem sinal validado — NÃO rotular alto risco) | CS Lead + agente CS | semanal |
| 16 | A-712f1c | B | exposure_only | 14.925 | Revisão de conta/renovação com contexto do episódio (sem sinal validado — NÃO rotular alto risco) | CS Lead + agente CS | semanal |
| 17 | A-56962b | C | exposure_only | 32.437 | Revisão de conta/renovação com contexto do episódio (sem sinal validado — NÃO rotular alto risco) | CS Lead + agente CS | semanal |
| 18 | A-80eeb6 | C | exposure_only | 17.711 | Revisão de conta/renovação com contexto do episódio (sem sinal validado — NÃO rotular alto risco) | CS Lead + agente CS | semanal |
| 19 | A-e51ec7 | C | exposure_only | 16.517 | Revisão de conta/renovação com contexto do episódio (sem sinal validado — NÃO rotular alto risco) | CS Lead + agente CS | semanal |
| 20 | A-a8d89d | C | exposure_only | 15.522 | Revisão de conta/renovação com contexto do episódio (sem sinal validado — NÃO rotular alto risco) | CS Lead + agente CS | semanal |

## 8. Não fazer agora

1. **ML/score preditivo de churn** — nenhuma regra além de onboarding valida
   temporalmente (It04 D8); score sem validação é claim falso.
2. **Desconto generalizado** — sem custos na base, seria preço inventado;
   nenhuma evidência de que preço dirige o churn precoce.
3. **Automação de churn (mensagens/desconto automáticos)** — sem validação
   causal; começaria pela experimentação (ACT-01).
4. **Decisão por reason_code/CSAT** — evidência sugestiva com missingness alta
   (CSAT 41,2% nulos; reason 'unknown' 15,8%; contrato §10).
5. **ROI pontual / revenue saved / reativação mais barata** — proibido nesta
   base (sem CAC/winback; R1 é exposição; reativação sem ligação com receita).

## 9. Limitações e handoff para a Iteração 06

- Impacto é **planejado, não medido**: cenários são premissas nomeadas com
  componentes expostos; o experimento ACT-01 é o caminho para efeito medido.
- All-active no corte, sinteticidade da base e N pequenos (intervalos largos)
  seguem limitando qualquer extrapolação (It04 §10).
- It06 (automação): recebe este script como 5º estágio do pipeline
  (`01..05`), determinístico, offline, sem novas dependências; `run.sh` deve
  re-gerar `05_action_plan.md` + `t18..t21` idênticos (byte-a-byte).

## 10. Gates e validações

| ID | Escopo | Check | Veredito | Detalhe |
|---|---|---|---|---|
| F01 | ravenstack_accounts.csv | arquivo presente e carregável | PASS | ravenstack_accounts.csv: CSV parseado (500 registros) |
| SC-F01 | ravenstack_accounts.csv | colunas mínimas presentes | PASS | ravenstack_accounts.csv: 2 colunas exigidas presentes |
| F02 | ravenstack_subscriptions.csv | arquivo presente e carregável | PASS | ravenstack_subscriptions.csv: CSV parseado (5000 registros) |
| SC-F02 | ravenstack_subscriptions.csv | colunas mínimas presentes | PASS | ravenstack_subscriptions.csv: 4 colunas exigidas presentes |
| F03 | ravenstack_churn_events.csv | arquivo presente e carregável | PASS | ravenstack_churn_events.csv: CSV parseado (600 registros) |
| SC-F03 | ravenstack_churn_events.csv | colunas mínimas presentes | PASS | ravenstack_churn_events.csv: 4 colunas exigidas presentes |
| F04 | ravenstack_feature_usage.csv | arquivo presente e carregável | PASS | ravenstack_feature_usage.csv: CSV parseado (25000 registros) |
| SC-F04 | ravenstack_feature_usage.csv | colunas mínimas presentes | PASS | ravenstack_feature_usage.csv: 3 colunas exigidas presentes |
| F05 | ravenstack_support_tickets.csv | arquivo presente e carregável | PASS | ravenstack_support_tickets.csv: CSV parseado (2000 registros) |
| SC-F05 | ravenstack_support_tickets.csv | colunas mínimas presentes | PASS | ravenstack_support_tickets.csv: 2 colunas exigidas presentes |
| F06 | account_month.csv | arquivo presente e carregável | PASS | account_month.csv: CSV parseado (5807 registros) |
| SC-F06 | account_month.csv | colunas mínimas presentes | PASS | account_month.csv: 3 colunas exigidas presentes |
| F07 | t11_account_lifecycle.csv | arquivo presente e carregável | PASS | t11_account_lifecycle.csv: CSV parseado (500 registros) |
| SC-F07 | t11_account_lifecycle.csv | colunas mínimas presentes | PASS | t11_account_lifecycle.csv: 3 colunas exigidas presentes |
| F08 | t14_backtest_temporal.csv | arquivo presente e carregável | PASS | t14_backtest_temporal.csv: CSV parseado (45 registros) |
| SC-F08 | t14_backtest_temporal.csv | colunas mínimas presentes | PASS | t14_backtest_temporal.csv: 7 colunas exigidas presentes |
| F09 | t15_priority_segments.csv | arquivo presente e carregável | PASS | t15_priority_segments.csv: CSV parseado (5 registros) |
| SC-F09 | t15_priority_segments.csv | colunas mínimas presentes | PASS | t15_priority_segments.csv: 3 colunas exigidas presentes |
| F10 | t16_watchlist_top20.csv | arquivo presente e carregável | PASS | t16_watchlist_top20.csv: CSV parseado (20 registros) |
| SC-F10 | t16_watchlist_top20.csv | colunas mínimas presentes | PASS | t16_watchlist_top20.csv: 3 colunas exigidas presentes |
| F11 | t14b_backtest_detail.csv | arquivo presente e carregável | PASS | t14b_backtest_detail.csv: CSV parseado (1682 registros) |
| SC-F11 | t14b_backtest_detail.csv | colunas mínimas presentes | PASS | t14b_backtest_detail.csv: 4 colunas exigidas presentes |
| F12 | t12_reactivation_recurrence.csv | arquivo presente e carregável | PASS | t12_reactivation_recurrence.csv: CSV parseado (31 registros) |
| SC-F12 | t12_reactivation_recurrence.csv | colunas mínimas presentes | PASS | t12_reactivation_recurrence.csv: 3 colunas exigidas presentes |
| G2-onboarding-base | base elegível | base onboarding (t11) consistente com segmento S1 (t15) | PASS | t11: n=80, MRR=621981; t15 S1: n=80, MRR=621981 |
| G3-incidence | incidência | precision pooled/min/max da regra D (90d) consistentes | PASS | pooled=0.4301 (2 vias), lo=0.3393, hi=0.5417 |
| G4-scenarios | cenários | aritmética dos cenários re-calculada de forma independente | PASS | 0 linhas com divergência > 0,1 |
| G5-top20 | watchlist | split 8/12 e exposição coberta consistentes | PASS | Tier A: 8 contas / 169747; B+C: 12 / 222283; total 20 / 392030 (10.7% da exposição 3668852) |
| G6-inflow | população | fluxo trimestral 2024 consistente | PASS | trimestres=[56, 65, 72, 80], total=273, média=68.25 |
| G7-power | experimento | MDE monotônico decrescente com N por braço | PASS | N/braço=[34, 68, 136] -> MDE(80% power)=['68%', '51%', '37%'] |
| G8-measurement | medição | plano de medição com leading/lagging/guardrail por ação | PASS | faltam: nenhum |
| G9-outputs | outputs | exatamente 4 tabelas (sem extra); charts intocados (sem PNG novo) | PASS | tabelas=4 (extra=nenhuma, ausentes=nenhuma); charts antes/depois iguais |
| G10-no-hardcoded | higiene | valores derivados ausentes como literais no script | PASS | literais derivados encontrados=nenhum |
| G11-data-quality | dados | baseline de qualidade derivado em runtime (sem literais) | PASS | CSAT=58.8%, unknown=15.83%, uso em janela=22.3%, vínculo evento-sub=21.0%, campo de ativação presente=False |
| G12-consistency | consistência | tabelas escritas re-lidas e consistentes com o cálculo | PASS | t19 base rows=1, t21 soma=392030 (esperado 392030), t18 ações=4, t21 linhas=20 |
| G13-power-scenarios | experimento | poder por cenário (10/20/30%) derivado em runtime (N=136/braço) | PASS | poder=['11%', '31%', '61%'] (monotônico=True) |
| G13-false-go | experimento | P(falso GO por ponto >= 10% sob efeito nulo) derivada em runtime | PASS | P(ponto >= 10% | nulo)=23.7% (N/braço=136) |
| G13-wilson | incidência | CI de Wilson 95% do pooled derivado e coerente (não é a faixa observada entre cutoffs) | PASS | Wilson 95%: 0.362–0.501 (pooled 0.4301; faixa observada 0.3393–0.5417) |
| G13-disjoint | incidência | coortes da regra D (90d) disjuntas entre cutoffs (overlap = 0) | PASS | contas únicas=193 vs Σ n_rule=193 (por cutoff: {'2024-03-31': 56, '2024-06-30': 65, '2024-09-30': 72}; contas em >1 cutoff=0) |
| G13-sequencing | ações | sequenciamento: ACT-03 Now/pré-requisito com SLA <= 30d; ACT-01 após instrumentation readiness; ACT-04 Later | PASS | ACT-03=Now; ACT-01 deps SLA/30d/readiness=True; ACT-04=Later |
| G13-annualized-absent | cenários | sem linha annualized na t19 (removida no pós-gate) | PASS | linhas annualized=0 |
| G13-wording | honestidade | impacto do ACT-01 nomeado como afetados no cenário (não evitados) | PASS | impact_metric ACT-01 contém 'afetad'=True, 'evitad'=False |
| G11b-forbidden-claims | honestidade | texto do relatório sem claims proibidos (afirmativos) | PASS | hits=nenhum |
| G13-decision-rule | experimento | regra de decisão ACT-01 em 3 estados (SCALE/GO exige IC95 excluindo 0; sem GO por ponto isolado) | PASS | 3 estados=sim (GO por ponto isolado ausente) |
| G13-wording-md | honestidade | seções 1-7 sem 'eventos evitados' (afetados no cenário apenas) | PASS | hits=nenhum |

## 11. Arquivos gerados

- Tabelas: t18_actions_prioritized.csv, t19_impact_sensitivity.csv, t20_measurement_plan.csv, t21_watchlist_split_actions.csv.
- Relatório: este arquivo (`05_action_plan.md`). Nenhum PNG gerado (keep-set
  visual fechado em 6; charts intocados — gate G9).
