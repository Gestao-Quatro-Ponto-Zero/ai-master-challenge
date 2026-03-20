# Histórico de Prompts — G4 AI Master Challenge 001

**Candidato:** Lucas Reis  
**Sessão:** Claude.ai (AI Master)  
**Objetivo:** Intermediar estratégia e criar prompts para execução no Claude Code

---

## PROMPT 001 — Setup e arquitetura do projeto
**Objetivo:** Criar estrutura de pastas, CLAUDE.md, .gitignore e process log inicial  
**Output:** 44 arquivos criados · CLAUDE.md · 6 agents esqueletizados · docs/architecture.md

---

## PROMPT 001b — Leitura do schema oficial
**Objetivo:** Ler README do Kaggle antes do EDA para entender colunas reais  
**Output:** docs/data_dictionary.md · 5 colunas mais relevantes identificadas

---

## PROMPT 001c — Correção dos agents antes do EDA
**Objetivo:** Corrigir 5 erros críticos encontrados na leitura do schema  
**Correções:**
- `usage_duration_min` → `usage_duration_secs/60`
- churn_events sem deduplicação → `ROW_NUMBER() OVER PARTITION BY account_id`
- `company_size` → `seats` · `contract_value` → `mrr_amount`
- `priority = 'high'` → `IN ('high','urgent')`
- `satisfaction_score NULL` → flag `satisfaction_no_response`

---

## PROMPT 002 — Agent EDA
**Objetivo:** Perfilar as 5 tabelas com DuckDB  
**Output:** 3 red flags · churn real 22% · buyer's remorse · SLA quebrado · entry_001

---

## PROMPT 003 — Agent Cross-table
**Objetivo:** Cruzar as 5 tabelas respondendo 6 perguntas de negócio  
**Correção aplicada:** target variable corrigida (70.4% → 22.0%)  
**Output:** 3 hipóteses refutadas · DevTools OR=2.36× · $710K MRR em risco

---

## PROMPT 004 — Agent Hipóteses
**Objetivo:** Validação estatística de 5 hipóteses com t-test e chi-square  
**Output:** p-values documentados · distinção poder estatístico vs relevância econômica · OR=2.5×

---

## PROMPT 005 — Agent Modelo Preditivo
**Objetivo:** LightGBM + SHAP · churn score das 500 contas  
**Output:** AUC=0.34 interpretado como diagnóstico · churn_scores.csv · 10 HIGH risk ativas

---

## PROMPT 006 — Agent Relatório Executivo
**Objetivo:** Gerar executive_report.md e executive_summary_1page.md  
**Output:** Relatório CEO · resumo 1 página · 3 ações priorizadas · "O que NÃO fazer"

---

## PROMPT 007 — README da submissão + estrutura final
**Objetivo:** Preencher template oficial da G4 com dados reais  
**Output:** README.md completo · workflow documentado · 8 erros da IA corrigidos listados

---

## PROMPT 008 — Auditoria completa do projeto
**Objetivo:** Diagnóstico honesto do estado antes do deploy  
**Output:** 4 gaps críticos identificados · nota 8/10 · feedback_text nunca analisado

---

## PROMPT 009 — Análise de feedback_text
**Objetivo:** Analisar 452 registros de texto livre dos churners  
**Descoberta crítica:** bug no 60.9% — número correto é 13.6%  
**Output:** Causa raiz corrigida para multicausal · executive_report.md atualizado

---

## PROMPT 009b — Correção dos agents após feedback_text
**Objetivo:** Corrigir target variable e narrativa em todos os arquivos  
**Output:** entry_000_corrections.md atualizado · relatório corrigido

---

## PROMPT 010 — Dashboard HTML + Notebook técnico
**Objetivo:** Gerar index.html com 4 abas interativas e churn_analysis.ipynb  
**Output:** Dashboard com Chart.js · 4 abas · CS automation · scatter 500 contas

---

## PROMPT 011 — Embutir data.json no HTML
**Objetivo:** Substituir PLACEHOLDER_JSON pelos dados reais sanitizados  
**Problema resolvido:** JSON malformado com caracteres especiais → sanitize() + ensure_ascii  
**Output:** index.html final · 208,886 chars · dados reais embutidos

---

## PROMPT 012 — Validação de consistência notebook vs dashboard
**Objetivo:** Garantir que os 20 números principais são idênticos nos dois entregáveis  
**Output:** 20/20 OK · 0 divergências · entry_008_consistency_validation.md

---

## Resumo de decisões estratégicas tomadas nesta sessão

| Decisão | Impacto |
|---------|---------|
| Ler schema antes do EDA | Evitou 5 erros que contaminariam toda a análise |
| Corrigir target variable (70.4% → 22.0%) | Evitou relatório com churn 3× errado |
| Interpretar AUC=0.34 como diagnóstico | Transformou "falha" em insight mais importante |
| Distinguir p-value de relevância econômica | OR=2.5× acionável mesmo com p=0.07 |
| Analisar feedback_text na auditoria | Corrigiu 60.9% → 13.6% antes do deploy |
| Dashboard + Notebook como entregáveis duplos | Cobre avaliador técnico e não-técnico |
| Validação de consistência 20/20 | Garante credibilidade dos dois entregáveis |

---