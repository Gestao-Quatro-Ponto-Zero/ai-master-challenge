# Data Dictionary — RavenStack Synthetic SaaS Dataset

**Fonte:** submissions/lucas-reis/solution/data/README.md
**Autor do dataset:** River @ Rivalytics
**Licença:** MIT-like (sintético, sem PII)
**Extraído por:** Lucas Reis em 2026-03-20

---

## Relacionamentos entre tabelas

```
accounts (PK: account_id)
│
├── subscriptions (FK → accounts.account_id)          [1:N]
│   └── feature_usage (FK → subscriptions.subscription_id)  [1:N]
│
├── support_tickets (FK → accounts.account_id)        [1:N]
└── churn_events (FK → accounts.account_id)           [1:N — reativações criam múltiplos registros]
```

**Joins possíveis:**

| Join | Condição | Cardinalidade |
|------|----------|--------------|
| accounts → subscriptions | `accounts.account_id = subscriptions.account_id` | 1:N (média 10 subs/conta) |
| subscriptions → feature_usage | `subscriptions.subscription_id = feature_usage.subscription_id` | 1:N |
| accounts → support_tickets | `accounts.account_id = support_tickets.account_id` | 1:N |
| accounts → churn_events | `accounts.account_id = churn_events.account_id` | 1:N (⚠️ reativações duplicam) |
| accounts → feature_usage | via subscriptions (two-hop join) | — |

---

## accounts.csv — 500 registros

| Coluna | Tipo | Descrição | Observações |
|--------|------|-----------|-------------|
| account_id | ID (PK) | Identificador único do cliente | Chave primária de todo o modelo |
| account_name | string | Nome fictício da empresa | Sem valor analítico direto |
| industry | categorical | Vertical SaaS (ex: DevTools, EdTech) | Segmentação de churn por setor |
| country | string | Código ISO-2 do país | Pode revelar padrões regionais |
| signup_date | date | Data de criação da conta | Base para cohort analysis (tenure) |
| referral_source | categorical | organic, ads, event, partner, other | Canal de aquisição → qualidade do cliente |
| plan_tier | categorical | Plano inicial (Basic, Pro, Enterprise) | Plano no momento do signup — pode diferir do plano atual em subscriptions |
| seats | integer | Número de licenças do usuário | Proxy de tamanho da empresa |
| is_trial | boolean | Conta está em trial atualmente | ⚠️ Snapshot atual, não histórico |
| churn_flag | boolean | Churnou em algum momento | **Target principal para o modelo** — já está calculado |

---

## subscriptions.csv — 5.000 registros

| Coluna | Tipo | Descrição | Observações |
|--------|------|-----------|-------------|
| subscription_id | ID (PK) | Identificador único da subscrição | |
| account_id | ID (FK) | Referência a accounts.account_id | |
| start_date | date | Início da subscrição | |
| end_date | date | Fim da subscrição | **Nullable** para planos ativos |
| plan_tier | categorical | Plano no momento do billing | Pode diferir de accounts.plan_tier (mudanças de plano) |
| seats | integer | Assentos licenciados | |
| mrr_amount | currency | Receita mensal | Proxy de contract_value — usar no lugar de contract_value |
| arr_amount | currency | Receita anual | `arr_amount ≈ mrr_amount × 12` para billing mensal |
| is_trial | boolean | Status de trial desta subscrição | |
| upgrade_flag | boolean | Plano foi upgraded no meio do ciclo | Sinal de engajamento positivo |
| downgrade_flag | boolean | Plano foi downgraded no meio do ciclo | ⚠️ Forte sinal de pré-churn |
| churn_flag | boolean | True se subscrição encerrou | Nível de subscrição (não conta) |
| billing_frequency | categorical | monthly ou annual | Annual = menor propensão a churn |
| auto_renew_flag | boolean | Renovação automática ativa | 80% true → os 20% false são sinal de alerta |

---

## feature_usage.csv — 25.000 registros

| Coluna | Tipo | Descrição | Observações |
|--------|------|-----------|-------------|
| usage_id | ID (PK) | Evento único de uso | |
| subscription_id | ID (FK) | Referência a subscriptions.subscription_id | Join two-hop para chegar em account_id |
| usage_date | date | Data do uso | Permite análise de tendência temporal |
| feature_name | categorical | Pool de 40 features SaaS | Alta cardinalidade — avaliar one-hot vs embedding |
| usage_count | integer | Frequência do evento | |
| usage_duration_secs | integer | Tempo gasto **em segundos** | ⚠️ **SEGUNDOS, não minutos** — converter ao agregar |
| error_count | integer | Erros registrados durante o uso | Sinal de má experiência → correlação com churn |
| is_beta_feature | boolean | 10% das features são beta | Beta features podem ter mais erros — controlar |

---

## support_tickets.csv — 2.000 registros

| Coluna | Tipo | Descrição | Observações |
|--------|------|-----------|-------------|
| ticket_id | ID (PK) | Identificador único do ticket | |
| account_id | ID (FK) | Referência a accounts.account_id | Join direto com accounts |
| submitted_at | datetime | Timestamp de abertura | |
| closed_at | datetime | Timestamp de resolução | Nullable se ticket em aberto |
| resolution_time_hours | float | Duração até resolução | |
| priority | categorical | **low, medium, high, urgent** | ⚠️ 4 níveis — "urgent" existe além de "high" |
| first_response_time_minutes | integer | Minutos até primeira resposta | SLA metric crítico |
| satisfaction_score | integer | 1–5 | **Nullable** (null = sem resposta) — null em si é sinal |
| escalation_flag | boolean | True se ticket foi escalado | Forte sinal de problema sério |

---

## churn_events.csv — 600 registros

| Coluna | Tipo | Descrição | Observações |
|--------|------|-----------|-------------|
| churn_event_id | ID (PK) | Instância única de churn | |
| account_id | ID (FK) | Referência a accounts.account_id | ⚠️ Não é 1:1 — reativações criam múltiplos eventos por conta |
| churn_date | date | Data em que a conta saiu | |
| reason_code | categorical | pricing, support, features, etc. | Categorias exatas a descobrir na EDA |
| refund_amount_usd | currency | Valor reembolsado | $0 padrão, 25% têm crédito/reembolso |
| preceding_upgrade_flag | boolean | Tinha upgrade nos últimos 90 dias | ⚠️ Churnou após upgrade = "buyer's remorse" ou expectativa não atendida |
| preceding_downgrade_flag | boolean | Tinha downgrade nos últimos 90 dias | Forte sinal: downgrade → churn (sequência clássica) |
| is_reactivation | boolean | 10% eram clientes que já churned | Conta pode aparecer múltiplas vezes — DEDUPLICAR ao fazer JOIN |
| feedback_text | string | Comentário opcional do cliente | Nullable — oportunidade de NLP para categorizar causas |

---

## Colunas mais relevantes para análise de churn

### Features de alta importância esperada

| Coluna | Tabela | Motivo |
|--------|--------|--------|
| `downgrade_flag` | subscriptions | Sequência downgrade→churn é padrão clássico |
| `auto_renew_flag = False` | subscriptions | Sinal explícito de intenção de sair |
| `preceding_downgrade_flag` | churn_events | Confirma a sequência downgrade→churn |
| `escalation_flag` | support_tickets | Problemas sérios não resolvidos |
| `satisfaction_score` (baixo ou null) | support_tickets | Null = cliente desengajado |
| `error_count` (agregado) | feature_usage | Má experiência de produto |
| `distinct features used` (agregado) | feature_usage | Baixo uso → não encontrou valor |
| `billing_frequency = monthly` | subscriptions | Anual tem lock-in, mensal tem saída fácil |
| `is_trial` (accounts) | accounts | Trial users têm maior churn |
| `priority = urgent` (contagem) | support_tickets | Urgência correlaciona com risco de saída |

### Features para segmentação

| Coluna | Tabela | Uso |
|--------|--------|-----|
| `plan_tier` | accounts/subscriptions | Churn rate por plano |
| `industry` | accounts | Churn por setor |
| `referral_source` | accounts | Qualidade do canal de aquisição |
| `country` | accounts | Padrões regionais |
| `seats` | accounts | Proxy de tamanho da empresa |
| `mrr_amount` | subscriptions | Revenue at risk |
| `reason_code` | churn_events | Causa raiz declarada |

---

## O que não é óbvio no README e pode mudar a análise

### 1. `usage_duration_secs` — em SEGUNDOS, não minutos
O README especifica `usage_duration_secs`. O código inicial foi gerado assumindo `usage_duration_min`. **Todos os agents precisam ser corrigidos** para converter: `duration_min = usage_duration_secs / 60`.

### 2. `churn_events` não é 1:1 com accounts
`is_reactivation = True` em 10% dos casos significa que uma conta pode ter **múltiplos registros em churn_events**. Um LEFT JOIN direto pode inflar a contagem de churns. A query no Agent 02 precisa de `GROUP BY account_id` ou `QUALIFY ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY churn_date DESC) = 1` para pegar apenas o churn mais recente.

### 3. `satisfaction_score = NULL` é um sinal, não ruído
Null não significa "dado faltante por acidente" — significa que o cliente não respondeu à pesquisa de satisfação. Clientes desengajados não respondem. Tratar null como categoria própria (`-1` ou `0`) em vez de imputar a média.

### 4. Não existe `company_size` nem `contract_value` no schema real
O código dos agents 02–04 referencia essas colunas que não existem. Substituir:
- `company_size` → usar `seats` como proxy de tamanho
- `contract_value` → usar `mrr_amount` ou `arr_amount` de subscriptions

### 5. `priority` tem 4 níveis: low, medium, high, **urgent**
O código do Agent 02 filtra apenas `priority = 'high'`. Precisa incluir `urgent` que é o nível mais grave.

### 6. `preceding_upgrade_flag` em churn_events é contra-intuitivo
Clientes que fizeram upgrade nos 90 dias antes do churn representam um padrão de "buyer's remorse" — pagaram mais, não encontraram valor, saíram. Este sinal deve ser analisado separadamente dos que downgraded.

### 7. `feedback_text` é oportunidade de NLP
Campo de texto livre e opcional nas churn_events. Mesmo com alta taxa de null, os registros preenchidos podem revelar padrões qualitativos que `reason_code` não captura.

### 8. `plan_tier` existe em dois lugares com semântica diferente
- `accounts.plan_tier`: plano no momento do signup (histórico)
- `subscriptions.plan_tier`: plano no momento do billing (pode ter mudado)
Usar `subscriptions.plan_tier` para análise de comportamento atual. Comparar os dois para detectar upgrades/downgrades históricos.

### 9. Dataset foi gerado com edge cases intencionais
O README menciona explicitamente: "mid-cycle plan changes, null fields, reactivations, duplicate referrals, beta feature spikes". Esses não são erros — são padrões realistas que precisam ser tratados, não removidos.

### 10. `is_beta_feature` pode distorcer métricas de uso
10% das features são beta. Features beta tendem a ter mais `error_count` por serem instáveis. Controlar este efeito ao calcular erro médio por conta — ou criar métricas separadas: `beta_error_rate` vs `stable_error_rate`.
