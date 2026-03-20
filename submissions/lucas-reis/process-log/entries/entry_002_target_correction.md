# Entry 002 — Correção crítica: target variable do modelo

**Data:** 2026-03-20
**Tipo:** Correção pré-execução
**Arquivo corrigido:** 02_cross_table_agent.py
**Detectado em:** entry_001_eda_analysis.md

## O erro

O Agent 02 usava `latest_churn.churned = 1` como target, resultando em:
- 352 contas marcadas como churned → **70.4% de churn rate**

O correto é `a.churn_flag` (accounts.csv):
- 110 contas churned → **22.0% de churn rate**

## Por que a discrepância existe

`churn_events` tem 600 linhas para 352 `account_id` únicos.
Mesmo após deduplicação (1 por account_id), os 352 incluem contas que
cancelaram subscrições individuais mas não saíram da plataforma.

`accounts.churn_flag` é o indicador de saída definitiva do cliente.

## Mudança aplicada no código

```python
# ANTES (errado):
COALESCE(c.churned, 0)  AS churned   -- c vem de latest_churn (churn_events)

# DEPOIS (correto):
CAST(a.churn_flag AS INTEGER)  AS churned   -- a = accounts.csv
```

O `latest_churn_info` (CTE de churn_events) foi renomeado para deixar claro
que é APENAS fonte de variáveis explicativas (reason_code, preceding_flags).

## Impacto se não corrigido

Um modelo treinado com churn_rate=70.4% produziria:
- Recall artificialmente alto (quase tudo é positivo)
- AUC inflado por distribuição de classes errada
- Recomendações de retenção para 352 contas quando só 110 precisam
- Estimativas de MRR em risco 3.2× maiores que a realidade
