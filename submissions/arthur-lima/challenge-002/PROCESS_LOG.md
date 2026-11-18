# Process Log — Diagnóstico Forense, Automação Seletiva 3-Tiers e Revisão Adversarial

**Candidato:** Arthur Lima<br>
**Desafio:** Challenge 002 — Redesign de Suporte (Operações & CX)

> **Fluxo de trabalho:** o desenvolvimento partiu da especificação e dossiê arquitetural no Antigravity, incorporou a crítica adversarial prévia (DeepSeek) sobre anomalias dos datasets e custos operacionais (TCO/retrabalho), e seguiu para implementação verificável e auditoria no Codex, com minha revisão e decisões em cada etapa.

<a id="papeis-ia"></a>

## 1. Ferramentas, papéis e participação humana

| Participante / ferramenta | Papel no fluxo | Participação de Arthur |
|---|---|---|
| **Antigravity** | Especificação, auditoria estatística dos CSVs e construção modular do protótipo (`src/`, `app.py`, `tests/`). | Direcionar a arquitetura para separar o diagnóstico forense do Dataset 1 do motor calibrado no Dataset 2. |
| **DeepSeek** | Revisão adversarial da especificação inicial (questionamento sobre dados corrompidos no Dataset 1, TCO oculto e riscos de automação cega). | Incorporar as críticas descartando conclusões espúrias no Dataset 1 e adicionando penalidade de retrabalho + guardrails. |
| **Codex** | Auditoria técnica independente do código, dos testes comportamentais e da conciliação entre números e documentação. | Revisar os 8 apontamentos da auditoria inicial, corrigir o pipeline de anti-leakage/overrides/PII/ROI e validar a versão final. |
| **Arthur Lima** | Orquestração ponta a ponta, arbitragem metodológica e revisão de código e produto. | Assumir responsabilidade integral pelas decisões de negócio, pelos limites declarados e pela entrega. |

<a id="decisoes-humanas"></a>

## 2. Mapa de decisões humanas H1–H5

| ID | Problema identificado | Decisão e intervenção de Arthur | Implementação e verificação |
|---|---|---|---|
| **H1 — Recusar falsos gargalos no Dataset 1** | O Dataset 1 (`customer_support_tickets.csv`) tem `100%` de `{product_purchased}` literal, `49,30%` de tempos negativos (`TTR < FRT`) e p-valores não-significativos ($p > 0{,}27$) em todas as dimensões avaliadas. | Não fabricar causas-raiz por canal/prioridade nem treinar NLP de produção no Dataset 1; publicar a auditoria de integridade, os intervalos de confiança de 95% e o baseline linear (~acaso). | [`audit_dataset1_forensics`](./solution/src/data_loader.py), [`evaluate_dataset1_null_predictability`](./solution/src/benchmark.py) e `test_dataset1_forensic_anomalies_and_uniform_noise`. |
| **H2 — Automação seletiva calibrada em 3 Tiers sem vazamento entre folds** | Automatizar `100%` do Dataset 2 (`N_test = 9.568`, `0,00%` duplicatas) geraria `14,05%` de erros de roteamento. | Adotar `CalibratedClassifierCV(Pipeline([TfidfVectorizer, LinearSVC]), cv=3)` com corte $\tau_{\text{Tier 1}} = 0{,}80$ (`60,85%` da fila com `97,30%` de precisão), Tier 2 Copilot (`26,17%` com `94,97%` Top-2) e Tier 3 humano (`12,98%`). | [`SupportTriageEngine`](./solution/src/triage_engine.py), [`fit_triage_engine_from_dataframe`](./solution/src/triage_engine.py) e [`benchmark_report.md`](./solution/artifacts/benchmark_report.md). |
| **H3 — Guardrails determinísticos, sanitização de precedentes e contenção de Domain Shift** | Sem proteção de domínio, `39,31%` (`3.329/8.469`) dos tickets de consumidor do Dataset 1 teriam confiança $\ge 0{,}80$ no classificador de TI corporativo; além disso, textos de treino poderiam conter PII. | Preceder o treino e a inferência com `mask_pii`, bloquear *Prompt Injection* e demandas de reembolso/jurídico, impor aprovação PAM para `Administrative rights` e impedir que overrides promovam tickets bloqueados por Guardrail ao Tier 1. | [`evaluate_guardrails`](./solution/src/guardrails.py), `test_pii_redaction_and_security_guardrails` e `test_domain_shift_containment_on_dataset1`. |
| **H4 — Simulador de ROI explícito separando triagem pura de assistência e sem truncar prejuízo** | Misturar tempo de triagem com tempo total de resolução superestimaria o ganho direto do protótipo, e truncar horas líquidas em zero esconderia prejuízo em cenários de alto erro. | Separar `manual_triage_min` (Cenário 1: `4,0 min/ticket`, escopo executado pelo protótipo) de `assisted_resolution_saved_min` (Cenários 2 e 3), aplicar penalidade uniforme de retrabalho de `2,0x` e permitir saldo líquido negativo. | [`simulate_operational_roi`](./solution/src/roi_calculator.py) e `test_roi_simulator_rework_penalty_monotonicity_and_negative_loss`. |
| **H5 — Intervenção humana funcional, paridade e teste de mutação no pipeline** | O analista precisa reclassificar/homologar/escalar com segurança, e o teste de anti-leakage precisa mutar a partição de teste na entrada do pipeline antes do `.fit()`. | Implementar `FeedbackStore` atômico com `reset_all`, testar o clique real de override/reset via `AppTest` e mutar as linhas de teste no DataFrame antes de `fit_triage_engine_from_dataframe`. | [`FeedbackStore`](./solution/src/feedback_store.py), [`test_support_engine.py`](./solution/tests/test_support_engine.py). |

<a id="registro-decisoes"></a>

## 3. Falhas evitadas, correções da auditoria e verificação

| Risco ou apontamento de auditoria | Como foi tratado na solução | Como verificar |
|---|---|---|
| Apontar "gargalos por canal" ou extrapolar conclusões de testes de hipótese no Dataset 1. | Demonstração determinística de `100%` `{product_purchased}` e `49,30%` de durações negativas, combinada com ANOVA, Kruskal-Wallis e Permutação ($p > 0{,}27$) e IC 95% por grupo. | Aba 1 do painel, seção 1 de `benchmark_report.md` e `test_dataset1_forensic_anomalies_and_uniform_noise`. |
| Vazamento de vocabulário/IDF nos folds de calibração ou teste de mutação inócuo. | `Pipeline([TfidfVectorizer, LinearSVC])` dentro do `CalibratedClassifierCV(cv=3)` + teste que corrompe as linhas de teste no DataFrame de entrada antes de `fit_triage_engine_from_dataframe`. | `test_mutating_test_split_never_changes_engine_predictions` em `tests/test_support_engine.py`. |
| Aplicar classificador de TI (Dataset 2) diretamente em tickets de consumidor (Dataset 1). | Teste de estresse mostra `39,31%` de falso Tier 1 sem guardrail vs. `100,00%` de contenção no Dataset 1 bruto (`93,43%` mesmo interpolando `{product_purchased}`). | `test_domain_shift_containment_on_dataset1` e seção 3 de `benchmark_report.md`. |
| Override humano acidental promovendo ticket com *Prompt Injection*/Guardrail para Tier 1 ou removendo runbook de escalação. | `triage_dataframe` bloqueia `approve_tier1` quando `guard.force_human_tier3=True` e preserva `Human_Escalation_Guardrail` em todo `escalate_tier3`. | `test_analyst_overrides_preserve_statistical_scores_and_respect_guardrails`. |
| Vazamento de PII no banco de precedentes recuperados. | `SupportTriageEngine.fit()` sanitiza todos os textos de treino com `mask_pii` antes de indexar `precedent_texts_` e o vocabulário TF-IDF. | `test_pii_redaction_and_security_guardrails`. |

## 4. Revisão final após o handover

Solicitei ao Codex que assumisse o fechamento após a conclusão das correções no Antigravity. A revisão executou os dois conjuntos de testes (9 de suporte e 19 do Lead Scorer), reproduziu o benchmark, corrigiu uma variante isolada de detecção por expressão regular, ajustou a apresentação comercial e renovou as evidências visuais. Minha participação foi dirigir essa passagem entre implementação e revisão, exigir coerência com o comportamento executado e manter explícitos os limites do protótipo.
