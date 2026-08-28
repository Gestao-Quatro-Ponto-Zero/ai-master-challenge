# Prompt — Iteração 05 · Ações priorizadas, impacto e plano de medição

Transcrição fiel do prompt recebido pelo agente executor desta iteração (arquivado por evidência de processo, conforme regra de governança).

---

Você é o AGENTE EXECUTOR ÚNICO da ITERAÇÃO 05 — ações priorizadas, impacto e plano de medição — do G4 AI Master Challenge. Converta evidência validada em decisões executivas, sem inventar causalidade, receita ou custos. NÃO escreva ainda o relatório executivo final (It07), automação final (It06) ou PR.

REPO/ESCOPO
- `/tmp/opencode/ai-master-challenge-work`, branch `submission/jose-nascimento`, pasta única `submissions/jose-nascimento/`, HEAD esperado `617e4ac252043475492d2b2e4c92e2eea1a3f385`.
- Leia instruções oficiais, plano/checklist, contrato, evidence/reviews/fixes It01–04, tabelas/watchlist e arquitetura de orquestração. Não use pesquisa externa/concorrentes como fonte.
- Fatos congelados: onboarding ≤90d é a única regra com lift consistente 1,57/1,56/1,83; segmentos amplos, uso e suporte não discriminam; watchlist é operational priority/exposure, não score; R1 é exposição contratual bruta, não perda; all-active no corte; CAC/winback/custos não existem.

FASE A — ASSUMPTIONS/DECISIONS ANTES DO CÓDIGO
1. Antes de calcular impactos, crie `process-log/decisions/iteration-05-action-impact-assumptions.md`, com timestamp e:
   - 3–5 ações candidatas, racional, owner, horizonte, mecanismo esperado;
   - fórmula de impacto e nomes honestos das métricas;
   - cenários pré-definidos conservador/base/ambicioso (ex.: redução relativa de evento, NÃO ponto mágico), ranges e origem;
   - esforço qualitativo/recursos, nunca custo monetário inventado;
   - stop/go criteria e métricas leading/lagging;
   - claims proibidos: revenue saved, CAC queimado factual, causalidade provada, score preditivo, reativação mais barata.
2. Arquive este prompt em `process-log/prompts/iteration-05-prompt.md`; faça commit/push separado ANTES do script: `docs: define action and impact assumptions`. Não reescreva retroativamente; adendos datados.

FASE B — CÁLCULO/PLANO
3. Implemente `solution/src/05_actions_impact.py`, offline, paths relativos, determinístico, usando outputs das It02–04 e/ou raw. Gere:
   - `solution/evidence/05_action_plan.md` (CEO-readable, conciso);
   - `solution/out/tables/t18_actions_prioritized.csv`;
   - `solution/out/tables/t19_impact_sensitivity.csv`;
   - `solution/out/tables/t20_measurement_plan.csv`;
   - no máximo uma tabela extra se indispensável. **Não crie novo PNG**: o keep-set visual já está fechado em 6.
4. Ações esperadas como famílias (valide/ajuste com evidência; não copie fraseado):
   A. onboarding/time-to-value de 0–90d com milestones instrumentados e intervenção por estágio;
   B. uso operacional da top-20 watchlist com triagem humana e tratamento diferente para onboarding validado vs exposure-only;
   C. contrato/instrumentação de dados (unificar lens, consertar timestamps/CSAT/reasons, capturar activation milestone e motivo estruturado);
   D. experimento controlado/phased rollout de onboarding para identificar causalidade;
   E. piloto de reactivation/recurrence apenas se classificado baixa confiança, sem claim de ROI.
   Consolide para 3–5 ações; evite duplicação A/D se um programa com desenho experimental resolver.
5. Impacto:
   - derive base elegível atual (N/MRR winner) e historical 90d outcomes dos backtests;
   - use `expected exposure affected`/`MRR-equivalent exposure`, não "receita salva";
   - cenários = população elegível × incidence histórica observada × redução relativa assumida, com lower/base/upper e sensitivity. Declare que eventos não equivalem a logo/revenue churn e que R1 não é perda;
   - se anualizar, chame explicitamente `annualized MRR-equivalent exposure` e não forecast; melhor evitar se confuso;
   - não aplique lift como causal effect do programa;
   - para ações sem estimativa financeira defensável, use impacto operacional mensurável (coverage, data quality, time-to-value instrumentation), não force US$.
6. Priorização: matriz/tabela transparente com evidence strength, impact range, effort, time-to-first-signal, reversibility, owner, dependencies e decisão Now/Next/Later. Sem score numérico arbitrário; se usar, fórmula/pesos pré-definidos e sensibilidade.
7. Measurement plan:
   - métricas leading (milestone/time-to-value, onboarding completion, coverage), lagging (first-event 90d, R1 gross exposure, state MRR lens separada), guardrails;
   - denominador/coorte/janela/fonte/owner/cadência/stop-go por ação;
   - desenho A/B ou staggered rollout com holdout, power limitations/N aproximado e regra de decisão; sem prometer significância impossível.
8. Watchlist: separar os 8 onboarding validados dos 12 exposure-only; ação/owner/cadência e não rotular os últimos como alto risco. Não publicar dados futuros.
9. Inclua seção "não fazer agora": ML/score, desconto generalizado, automação de churn, decisão por reason/CSAT, ROI pontual.
10. Verifique pelo menos 3 cálculos manualmente: base onboarding atual; um cenário de impacto; cobertura/$ top20 por tier. Recalcule com implementação independente.
11. Evidência: `process-log/reports/iteration-05-actions-impact-report.md` com timeline dos dois commits, assumptions→cálculo→decisão, erros reais/correções, validações, limitações, handoff It06; adendo decisions se necessário. Atualize plano/checklist: It05 CONCLUDED após validação, gate 3x PENDING, futuras PENDING.
12. Valide 2x/idempotência/CWD; FAIL estrutural sem stale/traceback; tables/report consistency; nenhuma constante de dado hardcoded; no new PNG/pruned; syntax/import; Markdown/links; paths/segredos; diff-check/escopo.

CONTENÇÃO
- Sem web, ML, app, dashboard, PDF, gráfico novo ou ROI elaborado. Textos/tabelas curtos. Uma recomendação por problema, não 20 ideias.

GIT FASE B
- Commit `feat: prioritize churn interventions and impact scenarios`; push; local==remote/tree limpo; sem amend/force/config/destrutivo.

ACEITAÇÃO
- 3–5 ações acionáveis, priorizadas, owners/prazos/métricas; impacto em faixa com premissas; causalidade/honestidade; top20 usada corretamente; measurement/experiment plan; não-fazer; 3 checks; outputs/process/git completos.

REPORT FINAL
PASS/BLOCKED; dois hashes/timeline; ações Now/Next/Later; fórmula/cenários e números; experimento/medição; 3 checks; erros; validações/riscos; handoff It06. BLOCKED se chamar exposição de receita ou tratar lift como efeito causal.