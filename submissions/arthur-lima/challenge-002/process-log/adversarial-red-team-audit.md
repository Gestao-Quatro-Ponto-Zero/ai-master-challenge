# Registro de Revisão Adversarial e Auditoria — Challenge 002 (Redesign de Suporte)

## 1. Síntese do Fluxo

O desenvolvimento seguiu três etapas sob direção e revisão de Arthur Lima:
1. **Dossiê e especificação inicial (Antigravity + crítica adversarial DeepSeek):** identificação das anomalias determinísticas no Dataset 1 (`{product_purchased}` não interpolado em `100%` das linhas e `49,30%` de durações negativas nos fechados) e definição da arquitetura em 3 Tiers com TCO explícito.
2. **Implementação modular e verificável (Antigravity):** construção de `src/data_loader.py`, `src/guardrails.py`, `src/triage_engine.py`, `src/roi_calculator.py`, `src/feedback_store.py`, `src/benchmark.py`, `app.py` e suíte `tests/test_support_engine.py`.
3. **Auditoria técnica independente (Codex):** primeira rodada de auditoria adversarial identificou 8 pontos de melhoria (`1 P1`, `6 P2`, `1 P3`), todos corrigidos no código, nos testes e na documentação antes da re-auditoria de fechamento.

## 2. Principais Achados Incorporados na Arquitetura e na Rodada de Auditoria Codex

| Eixo Auditado | Problema Evitado / Corrigido | Evidência no Repositório |
|---|---|---|
| **Anti-Leakage de Pipeline e Calibração (`[P1]`)** | Encapsulamento do `TfidfVectorizer` + `LinearSVC` em `Pipeline` dentro do `CalibratedClassifierCV(cv=3)` (evitando vazamento de IDF entre folds) e criação de `fit_triage_engine_from_dataframe`, testado corrompendo as linhas da partição de teste no DataFrame de entrada antes do `.fit()`. | `src/triage_engine.py` e `test_mutating_test_split_never_changes_engine_predictions`. |
| **Precisão Estatística no Dataset 1 (`[P2]`)** | Distinção rigorosa entre evidências determinísticas de corrupção (`100%` `{product_purchased}` e `49,30%` durações negativas) e testes de hipótese (ANOVA, Kruskal-Wallis e Permutação com $p > 0{,}27$), incluindo IC 95% nas tabelas e asserção explícita de `csat_perm_p > 0.20`. | `src/data_loader.py` e `test_dataset1_forensic_anomalies_and_uniform_noise`. |
| **Decomposição Honesta do ROI e Prejuízo Não-Truncado (`[P2]` / `[P3]`)** | Separação explícita entre o **Cenário 1 — Triagem e Roteamento Puro (`4,0 min/ticket`, `0,0 min` resolução)** (escopo real executado pelo protótipo) e os cenários de assistência/integração, com penalidade uniforme de retrabalho de `2,0x` e remoção do truncamento `max(0.0, ...)` para expor prejuízo líquido quando a taxa de erro é alta. | `src/roi_calculator.py` e `test_roi_simulator_rework_penalty_monotonicity_and_negative_loss`. |
| **Imutabilidade de Guardrails sob Override (`[P2]`)** | Bloqueio de promoção `approve_tier1` em chamados com `force_human_tier3=True` e preservação obrigatória do runbook `Human_Escalation_Guardrail` em bloqueios de segurança e escalações `escalate_tier3`. | `src/triage_engine.py` e `test_analyst_overrides_preserve_statistical_scores_and_respect_guardrails`. |
| **Sanitização de PII nos Precedentes e Cobertura Acima de 2.500 Linhas (`[P2]`)** | Aplicação de `mask_pii` sobre todo o corpus de treino dentro de `fit()` antes de construir `precedent_texts_` e remoção do corte silencioso de `2.500` linhas quando `include_precedents=True`. | `src/triage_engine.py` e `test_pii_redaction_and_security_guardrails`. |
| **Execução Direta do Benchmark e Auditoria de Duplicatas (`[P2]`)** | Suporte tanto a `python -m src.benchmark` quanto a `python src/benchmark.py` e verificação empírica de `0,00%` (`0/9.568`) de textos normalizados duplicados entre treino e teste no Dataset 2. | `src/benchmark.py` e `artifacts/benchmark_report.md`. |

## 3. Fechamento independente no Codex

Após o handover das correções implementadas no Antigravity, o Codex executou a suíte completa do Challenge 002 (**9 testes aprovados**) e a regressão do Challenge 003 (**19 testes aprovados**), sob a orientação de Arthur para concluir a entrega. O benchmark foi recalculado pelo comando direto documentado, com **nenhuma diferença no JSON** em relação ao relatório regenerado pela implementação.

A revisão de fechamento corrigiu uma lacuna adicional na expressão de guardrail: a frase isolada `Ignore all previous instructions` agora é detectada, com verificação independente dos gatilhos auxiliares presentes no exemplo anterior. Também simplificou o resumo executivo, delimitou a interpretação do diagnóstico e atualizou as quatro capturas da aplicação.

Os resultados finais do motor de TI são **60,85% de cobertura Tier 1, com 97,30% de acurácia**, no split de 9.568 tickets. A evidência de mutação cobre os textos da partição reservada; não é uma prova universal de ausência de qualquer forma de leakage. Guardrails por expressão regular são heurísticas, e o ROI permanece paramétrico. A aprovação é para a entrega como protótipo avaliável, não para operação autônoma em produção.
