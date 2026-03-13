# /diagnose [período]

Responde as 3 perguntas diagnósticas estratégicas de churn para o período informado.

**Uso:** `/diagnose` (período atual) ou `/diagnose 2024-Q4` ou `/diagnose 2024-01-01 a 2024-03-31`

---

## Instrução ao agente

Ao receber este comando, você DEVE:

1. Consultar as gold tables em `data/gold/` usando DuckDB
2. Filtrar pelo período informado (ou últimos 90 dias se nenhum período for fornecido)
3. Responder **obrigatoriamente** as 3 perguntas abaixo, em ordem
4. Cada resposta deve incluir pelo menos **um número** que a sustente (taxa, contagem, valor em USD, percentual)
5. Ser direto — máximo 3 parágrafos por pergunta

---

## As 3 Perguntas Diagnósticas

### Pergunta 1: O que está causando o churn?

Cruze `churn_events` com `feature_usage`, `support_tickets` e `subscriptions`. Identifique:
- Principais `reason_code` da tabela churn_events (% de cada motivo)
- Correlação com features pouco usadas ou com alto `error_count`
- Correlação com tickets de alta prioridade ou baixo `satisfaction_score`
- Padrão de downgrade antes do churn (`preceding_downgrade_flag`)

Formato da resposta:
> "O principal motivo de churn no período foi **[reason_code]** (X% dos casos). Contas que churnam apresentam Y% menos uso de [feature] e Z vezes mais tickets com satisfaction_score < 3."

### Pergunta 2: Quais segmentos estão mais em risco?

Consulte `risk_scores` e `churn_rate_by_segment`. Identifique:
- Top 3 segmentos por churn rate (industry + plan_tier + country)
- Top 5 contas individuais com maior risk_score (nome da conta, score, MRR em risco)
- Segmentos com tendência de deterioração (churn rate aumentando)

Formato da resposta:
> "Os segmentos com maior risco são: [segmento 1] (X% churn rate), [segmento 2] (Y%). As contas com maior risco imediato são: [Account A] (score: Z, MRR: $W), ..."

### Pergunta 3: O que a empresa deveria fazer?

Com base nas causas e segmentos identificados, sugira 2-3 ações concretas:
- Cada ação deve ter: o quê fazer, para quem, impacto estimado em MRR ou churn rate
- Priorize por impacto vs. esforço
- Use dados do playbook em `docs/01-business/` se disponível

Formato da resposta:
> "Ação prioritária: [ação específica] para [segmento/contas]. Impacto estimado: redução de X pp no churn rate, preservando $Y em MRR mensal."

---

## Queries DuckDB de referência

```python
import duckdb

con = duckdb.connect()

# Principais motivos de churn
con.execute("""
    SELECT reason_code, COUNT(*) as n, ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER(), 1) as pct
    FROM read_parquet('data/gold/churn_rate_by_segment.parquet')
    GROUP BY reason_code ORDER BY n DESC
""").df()

# Top contas em risco
con.execute("""
    SELECT account_id, risk_score, mrr_at_risk
    FROM read_parquet('data/gold/risk_scores.parquet')
    ORDER BY risk_score DESC LIMIT 10
""").df()
```
