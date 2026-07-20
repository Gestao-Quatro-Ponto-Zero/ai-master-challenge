# Regras temporais canônicas — Fase 2

## Relógio canônico

- tipo: `datetime64[ns]`;
- timezone: `NAIVE_SOURCE_TIME`;
- datas sem hora: meia-noite como representação técnica;
- granularidade de datas: diária;
- nenhuma sequência intradiária é inferida para datas sem hora.

## Ordenação no mesmo dia

A ordem técnica é: ACCOUNT_CREATED, SUBSCRIPTION_STARTED, FEATURE_USED, SUPPORT_TICKET_OPENED, SUPPORT_TICKET_CLOSED, CHURN_RECORDED, REACTIVATION_RECORDED e SUBSCRIPTION_ENDED. O valor está em `event_order_on_same_day`, não representa causalidade e recebe `SAME_DAY_ORDER_ASSIGNED` quando há colisão de conta/data.

## Regras por fonte

- accounts: `signup_date` gera no máximo um `ACCOUNT_CREATED` por registro não duplicado;
- subscriptions: `start_date` gera `SUBSCRIPTION_STARTED`; `end_date` não nulo gera `SUBSCRIPTION_ENDED`;
- feature_usage: `usage_date` gera `FEATURE_USED` e resolve conta exclusivamente pela FK validada de assinatura;
- support_tickets: `submitted_at` gera abertura e `closed_at` não nulo gera fechamento;
- churn_events: `is_reactivation=false` gera churn e `true` gera reativação explícita.

Não são gerados upgrade, downgrade, satisfação separada ou eventos comportamentais derivados por ausência de timestamp inequívoco.

## Quarentena

IDs obrigatórios ausentes, timestamp inválido, evento pré-conta, uso pré/pós-assinatura, fim anterior ao início, fechamento anterior à abertura e reativação sem churn anterior utilizável são fatais. Churn anterior à primeira assinatura também fica em quarentena por política conservadora.

## Warnings

IDs/chaves candidatas de uso repetidos, múltiplas assinaturas ativas, churn sem assinatura ativa, atribuição ambígua, ticket pós-churn, assinatura aberta após churn e desempate no mesmo dia permanecem visíveis como `VALID_WITH_WARNING` quando não coexistem com erro fatal.

## Deduplicação

Somente duplicatas integrais secundárias podem ser removidas. Duplicatas distintas de `usage_id` ou da chave candidata são preservadas, recebem IDs determinísticos diferentes por `source_row_number` e não são agregadas.

## Churn recorrente e reativação

Churn é evento recorrente de conta com sequência, anterior, próximo e dias desde o anterior. Reativação é explícita, separada e não apaga churn. Ausência de churn futuro não implica retenção.

## Atribuição a assinatura

Somente uma assinatura ativa produz `EXACT_ACTIVE_MATCH` e `candidate_subscription_id`. Múltiplas ativas, ausência de ativa e casos ambíguos permanecem sem vínculo inventado.

## Leakage

Não entram no event log `account_name`, `feedback_text`, `reason_code`, refund, churn flags, upgrade/downgrade flags ou status snapshot sem timestamp. Métricas de fechamento só aparecem no evento de fechamento.

## Flags observadas

- `AMBIGUOUS_CHURN_SUBSCRIPTION`: 478;
- `CHURN_BEFORE_FIRST_SUBSCRIPTION`: 53;
- `CHURN_WITHOUT_ACTIVE_SUBSCRIPTION`: 55;
- `DUPLICATE_CANDIDATE_KEY`: 6;
- `DUPLICATE_SOURCE_ID`: 42;
- `MULTIPLE_ACTIVE_SUBSCRIPTIONS`: 478;
- `POST_CHURN_EVENT`: 619;
- `POST_SUBSCRIPTION_USAGE`: 290;
- `PRE_ACCOUNT_EVENT`: 15347;
- `PRE_SUBSCRIPTION_USAGE`: 19142;
- `REACTIVATION_WITHOUT_PRIOR_CHURN`: 31;
- `SAME_DAY_ORDER_ASSIGNED`: 5011;

## Limitações

O snapshot contém conflitos temporais materiais, não declara timezone e não prova a disponibilidade histórica de campos mutáveis. A ordenação técnica deve ser tratada como desempate, nunca como evidência causal.
