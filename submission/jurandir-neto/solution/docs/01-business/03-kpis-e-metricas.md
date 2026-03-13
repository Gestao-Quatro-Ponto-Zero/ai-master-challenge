# KPIs e Métricas de Sucesso

## Métricas de negócio (contexto RavenStack)

| Métrica | Descrição | Fonte de dados |
|---------|-----------|----------------|
| Churn rate | % de contas canceladas no período | `ravenstack_churn_events.csv` |
| MRR perdido por churn | Receita mensal recorrente das contas que cancelaram | `ravenstack_subscriptions.csv` + `ravenstack_churn_events.csv` |
| ARR em risco | Receita anual de contas com sinais de churn | `ravenstack_subscriptions.csv` |
| Feature adoption rate | % de features ativas por conta | `ravenstack_feature_usage.csv` |
| Support ticket resolution time | Tempo médio de resolução de tickets | `ravenstack_support_tickets.csv` |
| First response time | Tempo até primeira resposta ao ticket | `ravenstack_support_tickets.csv` |
| CSAT | Satisfação pós-atendimento | `ravenstack_support_tickets.csv` |
| Escalation rate | % de tickets escalados | `ravenstack_support_tickets.csv` |

## Métricas de sucesso da análise

O diagnóstico será bem-sucedido se:

1. **Causa raiz identificada** — não apenas "uso caiu", mas por que e em quais segmentos
2. **Segmentos de risco quantificados** — contas ou grupos identificados com evidência nos dados
3. **Impacto financeiro estimado** — churn ponderado por MRR/ARR
4. **Recomendações priorizadas** — ações com impacto estimado, não genéricas
5. **Narrativa compreensível para o CEO** — sem jargão técnico desnecessário

## Segmentações a explorar

- Por indústria (`ravenstack_accounts.csv`)
- Por país (`ravenstack_accounts.csv`)
- Por canal de aquisição (`ravenstack_accounts.csv`)
- Por plano e billing frequency (`ravenstack_subscriptions.csv`)
- Por contas em trial vs. pagas (`ravenstack_accounts.csv`)
- Por faixa de MRR (pequenas, médias, grandes contas)
