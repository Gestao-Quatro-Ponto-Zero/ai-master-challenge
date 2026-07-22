# Dicionário de Dados

Os campos abaixo foram identificados nos CSVs e no SQLite atual. O banco foi criado pelo pandas, então os tipos refletem os tipos SQLite observados.

## `accounts` / `ravenstack_accounts.csv`

| Campo | Tipo | Obrigatório | Descrição | Exemplo | Regra |
| --- | --- | ---: | --- | --- | --- |
| `account_id` | TEXT | Sim lógico | Identificador da conta. | `A-2e4581` | Relaciona contas, assinaturas, tickets e churn. |
| `account_name` | TEXT | Sim lógico | Nome da empresa/conta. | `Company_0` | Usado em busca e exibição. |
| `industry` | TEXT | Não físico | Segmento da conta. | `EdTech` | Filtro e segmentação de churn. |
| `country` | TEXT | Não físico | País da conta. | `US` | Filtro e segmentação. |
| `signup_date` | TEXT | Não físico | Data de cadastro. | `2024-10-16` | Usada em filtros `start_date`/`end_date`. |
| `referral_source` | TEXT | Não físico | Canal de origem. | `partner` | Filtro global. |
| `plan_tier` | TEXT | Não físico | Plano no cadastro. | `Basic` | Fallback quando assinatura não possui plano. |
| `seats` | INTEGER | Não físico | Assentos contratados ou cadastrados. | `9` | Fallback quando assinatura não possui assentos. |
| `is_trial` | INTEGER | Não físico | Indica trial. | `0` | Esperado como 0/1. |
| `churn_flag` | INTEGER | Não físico | Flag cadastral de churn. | `0` | Usada como fallback se não houver reativação recente. |

## `subscriptions` / `ravenstack_subscriptions.csv`

| Campo | Tipo | Obrigatório | Descrição | Exemplo | Regra |
| --- | --- | ---: | --- | --- | --- |
| `subscription_id` | TEXT | Sim lógico | Identificador da assinatura. | `S-0f6f44` | Relaciona uso de funcionalidades. |
| `account_id` | TEXT | Sim lógico | Conta proprietária. | `A-9b9fe9` | Relaciona com `accounts`. |
| `start_date` | TEXT | Não físico | Início da assinatura. | `2024-06-11` | Usado para escolher assinatura mais recente. |
| `end_date` | TEXT | Não físico | Fim da assinatura. | `2024-04-12` | Assinatura sem `end_date` tem prioridade. |
| `plan_tier` | TEXT | Não físico | Plano da assinatura. | `Pro` | Usado em filtros e receita por plano. |
| `seats` | INTEGER | Não físico | Assentos da assinatura. | `17` | Exibido no detalhe da conta. |
| `mrr_amount` | INTEGER | Não físico | Receita recorrente mensal. | `833` | Base para MRR ativo/perdido e valor. |
| `arr_amount` | INTEGER | Não físico | Receita recorrente anual. | `9996` | Base para ARR ativo/perdido. |
| `is_trial` | INTEGER | Não físico | Flag de trial da assinatura. | `0` | Pode sobrescrever valor da conta na base consolidada. |
| `upgrade_flag` | INTEGER | Não físico | Indica upgrade. | `0` | Usado na linha do tempo. |
| `downgrade_flag` | INTEGER | Não físico | Indica downgrade. | `0` | Sinal de risco quando verdadeiro. |
| `churn_flag` | INTEGER | Não físico | Flag de churn na assinatura. | `0` | Não é usada diretamente na regra consolidada atual. |
| `billing_frequency` | TEXT | Não físico | Frequência de cobrança. | `monthly` | Filtro e sinal de risco quando mensal. |
| `auto_renew_flag` | INTEGER | Não físico | Renovação automática ativa. | `1` | Sinal de risco quando falso. |

## `feature_usage` / `ravenstack_feature_usage.csv`

| Campo | Tipo | Obrigatório | Descrição | Exemplo | Regra |
| --- | --- | ---: | --- | --- | --- |
| `usage_id` | TEXT | Sim lógico | Identificador do evento de uso. | `U-1c6c24` | Chave lógica do registro. |
| `subscription_id` | TEXT | Sim lógico | Assinatura relacionada. | `S-0fcf7d` | Relaciona com `subscriptions`. |
| `usage_date` | TEXT | Não físico | Data de uso. | `2023-07-27` | Usada em timeline e cálculo de uso recente. |
| `feature_name` | TEXT | Não físico | Nome da funcionalidade. | `feature_20` | Agrupamento de uso por feature. |
| `usage_count` | INTEGER | Não físico | Volume de uso. | `9` | Soma nos gráficos e score. |
| `usage_duration_secs` | INTEGER | Não físico | Duração em segundos. | `5004` | Média por funcionalidade. |
| `error_count` | INTEGER | Não físico | Quantidade de erros. | `0` | Sinal de risco e análise beta/geral. |
| `is_beta_feature` | INTEGER | Não físico | Indica feature beta. | `0` | Segmenta uso beta versus geral. |

## `support_tickets` / `ravenstack_support_tickets.csv`

| Campo | Tipo | Obrigatório | Descrição | Exemplo | Regra |
| --- | --- | ---: | --- | --- | --- |
| `ticket_id` | TEXT | Sim lógico | Identificador do ticket. | `T-0024de` | Chave lógica do registro. |
| `account_id` | TEXT | Sim lógico | Conta que abriu o ticket. | `A-712f1c` | Relaciona com `accounts`. |
| `submitted_at` | TEXT | Não físico | Data de abertura. | `2023-07-27` | Usada no detalhe e linha do tempo. |
| `closed_at` | TEXT | Não físico | Data/hora de fechamento. | `2023-07-28 03:00:00` | Exibida no detalhe. |
| `resolution_time_hours` | REAL | Não físico | Tempo de resolução. | `27.0` | Média e sinal de resolução lenta. |
| `priority` | TEXT | Não físico | Prioridade do ticket. | `urgent` | Gráfico e sinal de ticket urgente. |
| `first_response_time_minutes` | INTEGER | Não físico | Tempo até primeira resposta. | `144` | Média e sinal de resposta lenta. |
| `satisfaction_score` | REAL | Não físico | Nota de satisfação. | `4.0` | Média e sinal de baixa satisfação. |
| `escalation_flag` | INTEGER | Não físico | Indica escalonamento. | `0` | Sinal de risco. |

## `churn_events` / `ravenstack_churn_events.csv`

| Campo | Tipo | Obrigatório | Descrição | Exemplo | Regra |
| --- | --- | ---: | --- | --- | --- |
| `churn_event_id` | TEXT | Sim lógico | Identificador do evento. | `C-816288` | Chave lógica do registro. |
| `account_id` | TEXT | Sim lógico | Conta relacionada. | `A-c37cab` | Relaciona com `accounts`. |
| `churn_date` | TEXT | Não físico | Data do churn ou reativação. | `2024-10-27` | Usada para último evento e timeline. |
| `reason_code` | TEXT | Não físico | Motivo do churn. | `pricing` | Filtro e gráfico de motivos. |
| `refund_amount_usd` | REAL | Não físico | Reembolso em USD. | `4.03` | Somado na análise de motivos. |
| `preceding_upgrade_flag` | INTEGER | Não físico | Upgrade antes do evento. | `0` | Exibido no detalhe. |
| `preceding_downgrade_flag` | INTEGER | Não físico | Downgrade antes do evento. | `0` | Exibido no detalhe. |
| `is_reactivation` | INTEGER | Não físico | Indica reativação. | `0` | Reativação recente torna conta ativa. |
| `feedback_text` | TEXT | Não físico | Feedback textual. | `switched to competitor` | Exibido no detalhe. |

## Valores Observados para Filtros

| Campo | Valores observados |
| --- | --- |
| `plan_tier` | `Basic`, `Pro`, `Enterprise` |
| `industry` | `Cybersecurity`, `DevTools`, `EdTech`, `FinTech`, `HealthTech` |
| `country` | `AU`, `CA`, `DE`, `FR`, `IN`, `UK`, `US` |
| `referral_source` | `ads`, `event`, `organic`, `other`, `partner` |
| `billing_frequency` | `annual`, `monthly` |
| `priority` | `low`, `medium`, `high`, `urgent` |
| `reason_code` | `budget`, `competitor`, `features`, `pricing`, `support`, `unknown` |

## Intervalos de Datas Observados

| Fonte | Menor data | Maior data |
| --- | --- | --- |
| Contas | `2023-01-02` | `2024-12-31` |
| Assinaturas, início | `2023-01-09` | `2024-12-31` |
| Assinaturas, fim | `2023-04-05` | `2024-12-31` |
| Uso | `2023-01-01` | `2024-12-31` |
| Tickets | `2023-01-02` | `2024-12-31` |
| Churn/reativação | `2023-01-25` | `2024-12-31` |
