# Submissão — Jose Nascimento — Challenge 001

## Sobre mim

- **Nome:** Jose Nascimento
- **LinkedIn:** não informado
- **Challenge escolhido:** 001 — Diagnóstico de Churn

---

## Executive Summary

O churn da RavenStack subiu porque clientes recém-adquiridos saem nos primeiros
90 dias de vida (churn precoce de onboarding): em dezembro/2024 foram 43
primeiros eventos (22,51% dos 191 elegíveis) contra mediana de 13,01% nos seis
meses anteriores, e 53,4% de todos os primeiros eventos da janela acontecem até
90 dias do signup (68,4% da exposição contratual R1 está em assinaturas com até
90 dias). Uso, suporte e segmentos não explicam o movimento (uso total +225,3%
com intensidade mediana 0,0%; CSAT/suporte sem diferença material). O padrão é
**hipótese causal plausível — não prova** — e o único sinal com validação
temporal é o onboarding (backtest: lift 1,57/1,56/1,83). **Decisão pedida:**
aprovar ACT-03 (instrumentação de dados, SLA ≤ 30d) e ACT-01 (programa de
ativação 0–90d com experimento e holdout), com ACT-02 (triage semanal da
watchlist top-20) em paralelo; não escalar nada sem IC95 excluindo 0. Impacto
planejado em faixa: 2,7–13,0 eventos e 21.104–101.078 US$ de exposição
MRR-equivalent afetada em 90 dias (premissas nomeadas; exposição, não receita
salva).

---

## Solução

Análise reproduzível do zero com um comando (`./run.sh` ou `make all`, offline,
determinístico) — gera todos os artefatos das Iterações 01–07, incluindo o
[relatório executivo](solution/report-executivo.md) com os 6 gráficos embutidos.

### Abordagem

Pipeline em 7 estágios + verificador: auditoria dos 5 datasets (It01),
reconciliação das lentes de churn e contrato analítico (It02), causa raiz com
hipóteses pré-registradas (It03), jornada da conta/watchlist com backtest
point-in-time (It04), ações/impacto em faixa com premissas nomeadas (It05),
pipeline de 1 comando (It06) e relatório executivo (It07). Cada número do
relatório é derivado em runtime das tabelas, com gates (G1–G9 no gerador;
F1–F8 no verificador; e G1–G11 = seção G do verificador para o process log da
It08 — escopos distintos, prefixos documentados por seção).

### Resultados / Findings

- **Causa raiz (hipótese causal plausível):** churn precoce de onboarding —
  pico de dez/24 composto 83,7% por contas de 0–3 meses; coortes recentes
  churnam mais cedo (KM t6: 58,9% em 2024Q1, 69,2% em 2024Q2); 53,4% dos
  primeiros eventos ≤ 90d do signup.
- **O que não explica:** uso cresce em volume (+225,3%) mas não por conta
  (intensidade mediana 0,0%); suporte/CSAT sem discriminação; segmentos amplos
  sem heterogeneidade; reasons/CSAT não confiáveis como causa.
- **Segmentos/contas:** estados de jornada (não indústria); 80 contas em
  onboarding = 621.981 US$/mês; watchlist top-20 = 392.030 US$/mês (10,7% da
  exposição atual), 8 onboarding validadas + 12 exposure-only — contas
  específicas com MRR/evidência/limitação no relatório §5 e no
  [CSV da watchlist](solution/out/tables/t16_watchlist_top20.csv).
- **Ações:** ACT-03 instrumentação (Now, SLA ≤ 30d) → ACT-01 programa de
  ativação com experimento (Now), ACT-02 triage semanal (Now), ACT-04 piloto
  observacional (Later); impacto em faixa com premissas e CI nomeados; regra
  de decisão em 3 estados (GO exige IC95 excluindo 0).
- **Não fazer:** ML/score sem validação, descontos amplos, decisão por
  reason/CSAT, automação sem holdout, claims de receita salva.

### Recomendações

Ver [relatório executivo](solution/report-executivo.md) §§6–7 e o
[plano de ações](solution/evidence/05_action_plan.md) (tabelas `t18–t21`).

### Limitações

Base sintética; lentes de churn decopladas (21,0% dos eventos têm assinatura
encerrada ±30d; 79,0% não têm); all-active no corte (estado por assinatura vs snapshot);
proxies (winner MRR ≠ receita contábil); poder estatístico baixo (MDE 68/51/37%
em 1/2/4 trimestres) — tudo declarado no relatório §9 e no
[contrato analítico](solution/docs/analytical-contract.md).

---

## Process Log — Como usei IA

> **Este bloco é obrigatório.** Sem ele, a submissão é desclassificada.

Consolidação final (Iteração 08; QA final integral na Iteração 09; remediação da auditoria crítica final antes da It10) com evidência versionada, navegável pelos 4 artefatos-base e pelo registro de remediação:
[`process-log/README.md`](process-log/README.md) (entrada principal: escopo, ferramentas, pipeline, decomposição It00–09, contagens) · [`process-log/errors/ai-errors-and-corrections.md`](process-log/errors/ai-errors-and-corrections.md) (8 erros reais da IA com causa raiz e correção) · [`process-log/decisions/decision-ledger.md`](process-log/decisions/decision-ledger.md) (quem decidiu o quê — candidato vs orquestrador vs executor vs revisores) · [`process-log/evidence-index.md`](process-log/evidence-index.md) (índice completo de paths versionados).

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| OpenCode (harness compartilhado) | Harness único para orquestrador e subagentes: gestão de sessões e agentes, permissões, contexto isolado por subagente, git e geração de evidências |
| GPT 5.6 Sol (`openai/gpt-5.6-sol`, orquestrador — perfil de máxima capacidade da sessão, "GPT 5.6 Sol Max") | Manter o contexto global/estado do projeto; decompor etapas; escrever prompts e contratos; arbitrar divergências dos revisores; decidir rework; controlar gates e risco. Não executa scripts nem edita a solução — delega a subagentes |
| DeepSeek V4 Flash (`deepseek-max`, executor — via OpenCode Go, max reasoning) | Executar cada etapa da análise: exatamente um executor por iteração, com contexto novo/limpo e escopo fechado; implementa, testa, documenta e faz commit/push |
| DeepSeek V4 Flash (`deepseek-max`, 3 revisores independentes — via OpenCode Go) | Revisar cada etapa em paralelo e em modo read-only (mesmo prompt, contextos separados), produzindo reports externos únicos com veredicto e findings |
| DeepSeek V4 Flash (`deepseek-max`, corretor sequencial — via OpenCode Go) | Ler os 3 reports de revisão, resolver findings materiais, testar, registrar o review summary e fazer commit/push |

> A descrição inicial desta tabela era curta e incompleta. A arquitetura completa (papéis, modelos, contexto, permissões, rationale, limitações e fontes) está em [`process-log/management/orchestration-architecture.md`](process-log/management/orchestration-architecture.md), adendo que é a fonte atual de verdade de ferramenta/processo.

### Workflow

1. **Iteração 00** — planejamento e governança (plano, checklist, prompt arquivado): [`process-log/reports/iteration-00-planning-report.md`](process-log/reports/iteration-00-planning-report.md).
2. **Iterações 01–05** — uma etapa por agente executor (auditoria → contrato → causa raiz → jornada/watchlist → ações/impacto), cada uma com revisão 3x read-only e correção sequencial; prompts literais em [`process-log/prompts/`](process-log/prompts/).
3. **Iteração 06** — pipeline de 1 comando (`run.sh`/`Makefile`) + verificador: [`solution/README.md`](solution/README.md).
4. **Iteração 07** — narrativa pré-registrada ([outline](process-log/decisions/iteration-07-executive-report-outline.md)) antes do gerador do relatório executivo; gates G1–G9 no gerador e F1–F8 no verificador.
5. **Iteração 08** — process log final e evidências (4 artefatos acima) + verificador ampliado com gates de processo G1–G11.
6. **Iteração 09** — QA final integral (`CONCLUDED`; auditoria git/escopo, re-execução em clone fresco 88 PASS/0 FAIL, re-derivação numérica independente 59/59, originalidade, links/markdown, readiness checklist; gate 3x `CONCLUDED`): [`process-log/reports/iteration-09-final-qa-report.md`](process-log/reports/iteration-09-final-qa-report.md) · [`process-log/management/submission-readiness-checklist.md`](process-log/management/submission-readiness-checklist.md).
7. **Remediação da auditoria crítica final** — HIGH-001/HIGH-002 corrigidos com gates e regeneração dos consumidores; registro separado preserva It00–09 e E1–E8: [`process-log/reviews/final-critical-audit-summary.md`](process-log/reviews/final-critical-audit-summary.md).
8. **Iteração 10** — data final, commit final de submissão e PR (pendente).

### Onde a IA errou e como corrigi

**8 erros materiais reais**, cada um com etapa, output errado, porquê/perigo, quem detectou, causa raiz, correção, validação e commit — ledger completo em [`process-log/errors/ai-errors-and-corrections.md`](process-log/errors/ai-errors-and-corrections.md). Síntese:

- **It01** — schema ausente/renomeado causava `KeyError` e relatório de auditoria stale (corrigido com guards de coluna; detectado 3/3 pelos revisores).
- **It02** — lente de revenue churn por winner escondia encerramentos não dominantes (18.507 capturados vs 422.691 ocultos; razão ≈22,8×) → duas lentes nomeadas R1/R2 e winner proibido como total contratual.
- **It03** — meses pré-signup contados como zero (H4; Δ 13,7 p.p. era artefato → recalculado 9,0 p.p.); KM por tempo exato com células vazias e gráfico B cortado → função degrau + ylim 0–1.
- **It04** — mapeamento visual R_D↔R_F invertido no gráfico de backtest (26/27 pares divergiam de t14), detectado pela **inspeção ocular do orquestrador** apesar de os validadores programáticos passarem → mapping keyed + gate embutido.
- **It05** — regra GO ≥10% por ponto sem considerar poder/IC (falso-GO ≈24%; poder 11/31/61%) → regra de decisão em 3 estados com poder/falso-GO derivados em runtime; faixa rotulada ≠ CI; `annualized` removido.
- **It06** — valor categórico inválido crashava com `KeyError` + stale; invocação direta do verificador gerava `__pycache__` que quebrava o próprio check D1 → guard de valor booleano + `sys.dont_write_bytecode`.
- **It07** — drift de contagens nos docs, células de tabela truncadas no meio da palavra e word count no teto → contagens derivadas em runtime, tabela com '…' explícito + gate G3b, margem restaurada.

Nenhuma iteração relatou "não houve erros". Detecção (derivada dos summaries/gates): 7/8 pelos revisores — E1 3/3; E2 1/3 material (revisor R3, review-8b41e9c2, com os 3 concordando na correção); E3 1/3 material (review-4c090c69, confirmado no recálculo); E4 parcial (KM por tempo exato 3/3 — L5/INFO-1/#6; gráfico B 1/3 — #5); E6 3/3; E7 2/3 (review-18199ddc + review-f1fa7caa); E8 3/3 (LOWs convergentes) — e 1/8 pela inspeção ocular do orquestrador (E5).

### O que eu adicionei que a IA sozinha não faria

Síntese; ledger completo com atribuição por decisão em [`process-log/decisions/decision-ledger.md`](process-log/decisions/decision-ledger.md):

- **Decisões humanas do candidato:** escolha do Challenge 001 e da ferramenta; exigência de 1 executor serial + revisão 3x read-only por etapa; originalidade (zero fontes concorrentes como solução); ângulos (lente por pergunta e regra do winner, sem misturar 110/312/352/600); exigência de inspeção visual e auditoria final. O candidato **não** escreveu nem rodou o código manualmente — a execução foi dos subagentes.
- **O que o processo adicionou além de um prompt único:** pré-registro de hipóteses (It03), premissas (It05) e narrativa (It07) commitados antes do código; contrato analítico congelado com invariantes G1–G15; gates de honestidade (faixa ≠ CI; exposição ≠ perda; hipótese ≠ prova); watchlist nomeada "operational priority" em vez de score; regra de decisão em 3 estados; correções de gate com recálculo independente; contenção de tempo conforme [`process-log/management/execution-plan.md`](process-log/management/execution-plan.md).

---

## Evidências

- [x] Git history (histórico git incremental e semântico na branch `submission/jose-nascimento`, autor do candidato — confira com `git log --author="Jose Nascimento"`)
- [ ] Chat exports (não produzidos: nenhum export de chat da ferramenta foi salvo; os prompts literais de todas as iterações estão arquivados em [`process-log/prompts/`](process-log/prompts/) — são transcrições de prompts, não exports de chat)
- [x] Outro: prompts literais, reports de iteração/correção, decisões, hipóteses, review summaries dos gates 3x — process log completo em [`process-log/`](process-log/README.md) (4 artefatos navegáveis)
- [x] Outro: 5 reports de evidence + 26 tabelas CSV + 6 gráficos PNG regeneráveis com 1 comando ([`solution/evidence/`](solution/evidence/), [`solution/out/`](solution/out/))
- [ ] Screenshots das conversas com IA (não produzidos; fluxo integral documentado em texto no process log)
- [ ] Screen recording do workflow (não produzido; pipeline reproduzível cobre a verificação)

---

_Submissão enviada em: **pendente** (data preenchida na Iteração 10, quando o PR for aberto)_
