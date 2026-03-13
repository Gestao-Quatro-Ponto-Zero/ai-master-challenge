# Jornada do Cliente — RavenStack

## Ciclo de vida da conta

```
Aquisição → Trial → Ativação → Expansão → Renovação → [Churn]
```

### 1. Aquisição
- Canal: variável (campo disponível em `ravenstack_accounts.csv`)
- Hipótese: canais diferentes podem ter perfis de retenção distintos

### 2. Trial
- Contas com flag de trial em `ravenstack_accounts.csv`
- Hipótese: contas que converteram de trial podem ter padrões de uso diferentes

### 3. Ativação
- Primeiros usos das features principais (`ravenstack_feature_usage.csv`)
- Métricas: contagem de uso, duração, erros na fase inicial

### 4. Expansão
- Upgrades de plano registrados em `ravenstack_subscriptions.csv`
- Adoção de novas features, incluindo features beta

### 5. Renovação (ou não)
- Billing frequency: mensal vs. anual
- Downgrades como sinal precursor de churn
- Tickets de suporte como sinal de insatisfação

### 6. Churn
- Reason codes disponíveis em `ravenstack_churn_events.csv`
- Feedback em texto livre (análise qualitativa possível)
- Valor de refund como proxy de impacto

## Pontos de fricção a investigar

| Momento | Sinal de risco | Dataset |
|---------|---------------|---------|
| Pós-trial | Baixo uso inicial | `feature_usage` |
| Uso contínuo | Aumento de erros | `feature_usage` |
| Suporte | Alta de tickets, baixo CSAT, escalações | `support_tickets` |
| Financeiro | Downgrade antes do cancelamento | `subscriptions` |
| Cancelamento | Reason code + feedback | `churn_events` |
