# Dados Disponíveis

Cinco datasets públicos do Kaggle (licença MIT), conectados por `account_id` e `subscription_id`.

**Fonte:** [SaaS Subscription & Churn Analytics](https://www.kaggle.com/datasets/rivalytics/saas-subscription-and-churn-analytics-dataset)

---

## ravenstack_accounts.csv (~500 registros)

**Chave:** `account_id`

**O que representa:** Cada linha é uma conta corporativa (cliente B2B) da RavenStack.

| Campo | Significado |
|-------|-------------|
| `account_id` | Identificador único da conta |
| `industry` | Setor de atuação da empresa cliente |
| `country` | País de origem da conta |
| `acquisition_channel` | Como a conta foi adquirida (ex: organic, paid, referral) |
| `plan` | Plano contratado |
| `is_trial` | Flag indicando se a conta está em período de trial |

**Uso analítico:** Base de segmentação. Todo cruzamento começa aqui — permite estratificar churn por indústria, país, canal de aquisição e tipo de plano.

---

## ravenstack_subscriptions.csv (~5.000 registros)

**Chave:** `subscription_id` → `account_id`

**O que representa:** Cada linha é uma assinatura. Uma conta pode ter múltiplas assinaturas ao longo do tempo (upgrades, downgrades, renovações).

| Campo | Significado |
|-------|-------------|
| `subscription_id` | Identificador único da assinatura |
| `account_id` | Conta à qual a assinatura pertence |
| `mrr` | Monthly Recurring Revenue — receita mensal recorrente da assinatura |
| `arr` | Annual Recurring Revenue — receita anual recorrente |
| `plan` | Plano da assinatura |
| `billing_frequency` | Frequência de cobrança (mensal ou anual) |
| `has_upgrade` | Indica se houve upgrade nessa assinatura |
| `has_downgrade` | Indica se houve downgrade — sinal de insatisfação ou redução de uso |

**Uso analítico:** Dimensiona o impacto financeiro do churn. Downgrade antes do cancelamento é um sinal precursor relevante. MRR/ARR permite ponderar a importância de cada conta.

---

## ravenstack_feature_usage.csv (~25.000 registros)

**Chave:** `subscription_id`

**O que representa:** Cada linha é um registro de uso diário de uma feature por uma assinatura.

| Campo | Significado |
|-------|-------------|
| `subscription_id` | Assinatura que usou a feature |
| `feature_name` | Nome da feature utilizada |
| `usage_count` | Quantidade de vezes que a feature foi acionada no dia |
| `usage_duration` | Tempo total de uso da feature no dia |
| `error_count` | Número de erros ocorridos durante o uso |
| `is_beta` | Flag indicando se a feature é experimental (beta) |
| `date` | Data do registro |

**Uso analítico:** Revela engajamento real com o produto. Cruza com churn para identificar quais features estão associadas à retenção ou ao abandono. Alta taxa de erros pode indicar frustração técnica.

---

## ravenstack_support_tickets.csv (~2.000 registros)

**Chave:** `account_id`

**O que representa:** Cada linha é um ticket de suporte aberto por uma conta.

| Campo | Significado |
|-------|-------------|
| `account_id` | Conta que abriu o ticket |
| `ticket_id` | Identificador único do ticket |
| `resolution_time` | Tempo total até a resolução do ticket |
| `first_response_time` | Tempo até a primeira resposta do time de suporte |
| `satisfaction_score` | Nota de satisfação dada pelo cliente após o atendimento |
| `is_escalated` | Flag indicando se o ticket foi escalado para nível superior |

**Uso analítico:** Mede a experiência com o suporte. Contas que churnearam com histórico de tickets escalados, CSAT baixo ou alto tempo de resposta revelam um vetor de churn relacionado à experiência de atendimento.

---

## ravenstack_churn_events.csv (~600 registros)

**Chave:** `account_id`

**O que representa:** Cada linha é um evento de cancelamento de uma conta.

| Campo | Significado |
|-------|-------------|
| `account_id` | Conta que cancelou |
| `churn_date` | Data do cancelamento |
| `reason_code` | Categoria do motivo de cancelamento (estruturado) |
| `refund_value` | Valor de reembolso concedido, se houver |
| `feedback_text` | Feedback livre do cliente no momento do cancelamento |

**Uso analítico:** É a tabela âncora da análise. Os reason codes categorizam os motivos, mas o `feedback_text` pode revelar padrões qualitativos. O `refund_value` ajuda a estimar o impacto financeiro direto do churn.

---

## Modelo de relacionamento entre tabelas

```
ravenstack_accounts (account_id)
        │
        ├──── ravenstack_subscriptions (account_id → subscription_id)
        │              │
        │              └──── ravenstack_feature_usage (subscription_id)
        │
        ├──── ravenstack_support_tickets (account_id)
        │
        └──── ravenstack_churn_events (account_id)
```
