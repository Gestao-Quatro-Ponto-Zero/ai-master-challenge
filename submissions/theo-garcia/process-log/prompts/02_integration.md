# Fase 2 — Integração Cross-Table

## O que pedi para a IA
- Merge das 5 tabelas por account_id
- Feature engineering: criar variáveis derivadas que capturem comportamento

## Decisões que tomei (não a IA)

### Correção 1 — Agregação de subscrições
A IA sugeriu usar apenas a última subscrição de cada conta. Rejeitei.
Se um cliente fez upgrade → downgrade → churn, perder esse histórico é perder o sinal mais importante. Agreguei TODAS as subscrições com médias, totais, contagens de up/downgrade, e criei net_plan_movement.

### Correção 2 — Imputação de satisfaction_score
41.6% dos scores são null. A IA sugeriu imputar com a média. Rejeitei por non-response bias — clientes insatisfeitos tendem a não responder pesquisas. Imputar com a média seria dizer "quem não respondeu está na média", o que provavelmente é falso.

## Resultado
Master table: 500 rows × 55 colunas. Cada linha é uma conta, cada coluna é uma variável cross-table.

Features criadas: sub_churn_rate, net_plan_movement, pct_annual, pct_auto_renew, error_rate, unique_features_used, pct_beta_usage, escalation_rate, avg_resolution_hours, avg_first_response_min.
