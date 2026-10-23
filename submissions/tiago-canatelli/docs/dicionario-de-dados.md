# Dicionário de dados

Gerado por `scripts/gen_data_dictionary.py` a partir de `ops.catalog_tables` / `ops.catalog_columns` (descrições = `COMMENT ON` das migrations). Dados até 2024-12-31. Modelo e decisões: [`modelo-de-dados.md`](modelo-de-dados.md).

## Índice

- **Bronze — cópia fiel dos CSVs:** [`bronze.accounts`](#bronzeaccounts), [`bronze.churn_events`](#bronzechurnevents), [`bronze.feature_usage`](#bronzefeatureusage), [`bronze.subscriptions`](#bronzesubscriptions), [`bronze.support_tickets`](#bronzesupporttickets)
- **Silver — dados tipados e validados:** [`silver._rejects`](#silverrejects), [`silver.accounts`](#silveraccounts), [`silver.churn_events`](#silverchurnevents), [`silver.feature_usage`](#silverfeatureusage), [`silver.subscriptions`](#silversubscriptions), [`silver.support_tickets`](#silversupporttickets)
- **Gold — fatos, dimensões, KPIs e score de risco:** [`gold.account_360`](#goldaccount360), [`gold.churn_reason_vs_behavior`](#goldchurnreasonvsbehavior), [`gold.dim_account`](#golddimaccount), [`gold.dim_customer_persona`](#golddimcustomerpersona), [`gold.fct_account_month`](#goldfctaccountmonth), [`gold.fct_churn_event`](#goldfctchurnevent), [`gold.kpi_churn_by_segment`](#goldkpichurnbysegment), [`gold.kpi_churn_type`](#goldkpichurntype), [`gold.kpi_cohort`](#goldkpicohort), [`gold.kpi_feature_health`](#goldkpifeaturehealth), [`gold.kpi_loss_concentration`](#goldkpilossconcentration), [`gold.kpi_persona_summary`](#goldkpipersonasummary), [`gold.kpi_reactivation`](#goldkpireactivation), [`gold.kpi_revenue_monthly`](#goldkpirevenuemonthly), [`gold.kpi_silent_churn`](#goldkpisilentchurn), [`gold.kpi_support_health`](#goldkpisupporthealth), [`gold.kpi_tenure_hazard`](#goldkpitenurehazard), [`gold.kpi_usage_segment_monthly`](#goldkpiusagesegmentmonthly), [`gold.persona_catalog`](#goldpersonacatalog), [`gold.risk_scores`](#goldriskscores)
- **Ops — operação do lake (ingestão, qualidade, catálogo):** [`ops.catalog_columns`](#opscatalogcolumns), [`ops.catalog_tables`](#opscatalogtables), [`ops.dq_results`](#opsdqresults), [`ops.ingestion_runs`](#opsingestionruns), [`ops.ingestion_steps`](#opsingestionsteps)
- **App — prompts, perfis, usuários e auditoria da IA:** [`app.ai_runs`](#appairuns), [`app.analysis_profiles`](#appanalysisprofiles), [`app.prompt_templates`](#appprompttemplates), [`app.roles`](#approles), [`app.users`](#appusers)

## Bronze — cópia fiel dos CSVs

<a id="bronzeaccounts"></a>
### `bronze.accounts`

Cópia fiel de ravenstack_accounts.csv; uma linha por linha do arquivo.  
*500 linhas · 15 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `account_id` | text |  |  |  | Valor bruto (texto) da coluna account_id do CSV. |
| `account_name` | text |  |  |  | Valor bruto (texto) da coluna account_name do CSV. |
| `industry` | text |  |  |  | Valor bruto (texto) da coluna industry do CSV. |
| `country` | text |  |  |  | Valor bruto (texto) da coluna country do CSV. |
| `signup_date` | text |  |  |  | Valor bruto (texto) da coluna signup_date do CSV. |
| `referral_source` | text |  |  |  | Valor bruto (texto) da coluna referral_source do CSV. |
| `plan_tier` | text |  |  |  | Valor bruto (texto) da coluna plan_tier do CSV. |
| `seats` | text |  |  |  | Valor bruto (texto) da coluna seats do CSV. |
| `is_trial` | text |  |  |  | Valor bruto (texto) da coluna is_trial do CSV. |
| `churn_flag` | text |  |  |  | Valor bruto (texto) da coluna churn_flag do CSV. |
| `_run_id` | uuid |  |  |  | Execução que carregou a linha. |
| `_file_sha256` | text | 🔑 |  |  | Hash do arquivo de origem (versão do arquivo). |
| `_row_number` | integer | 🔑 |  |  | Número da linha no arquivo (1 = primeira linha de dados). |
| `_row_hash` | text |  |  |  | sha256 do conteúdo da linha. |
| `_ingested_at` | timestamp with time zone |  |  |  | Momento da carga. |

<a id="bronzechurnevents"></a>
### `bronze.churn_events`

Cópia fiel de ravenstack_churn_events.csv; uma linha por linha do arquivo.  
*600 linhas · 14 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `churn_event_id` | text |  |  |  | Valor bruto (texto) da coluna churn_event_id do CSV. |
| `account_id` | text |  |  |  | Valor bruto (texto) da coluna account_id do CSV. |
| `churn_date` | text |  |  |  | Valor bruto (texto) da coluna churn_date do CSV. |
| `reason_code` | text |  |  |  | Valor bruto (texto) da coluna reason_code do CSV. |
| `refund_amount_usd` | text |  |  |  | Valor bruto (texto) da coluna refund_amount_usd do CSV. |
| `preceding_upgrade_flag` | text |  |  |  | Valor bruto (texto) da coluna preceding_upgrade_flag do CSV. |
| `preceding_downgrade_flag` | text |  |  |  | Valor bruto (texto) da coluna preceding_downgrade_flag do CSV. |
| `is_reactivation` | text |  |  |  | Valor bruto (texto) da coluna is_reactivation do CSV. |
| `feedback_text` | text |  |  |  | Valor bruto (texto) da coluna feedback_text do CSV. |
| `_run_id` | uuid |  |  |  | Execução que carregou a linha. |
| `_file_sha256` | text | 🔑 |  |  | Hash do arquivo de origem (versão do arquivo). |
| `_row_number` | integer | 🔑 |  |  | Número da linha no arquivo (1 = primeira linha de dados). |
| `_row_hash` | text |  |  |  | sha256 do conteúdo da linha. |
| `_ingested_at` | timestamp with time zone |  |  |  | Momento da carga. |

<a id="bronzefeatureusage"></a>
### `bronze.feature_usage`

Cópia fiel de ravenstack_feature_usage.csv; uma linha por linha do arquivo.  
*25.000 linhas · 13 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `usage_id` | text |  |  |  | Valor bruto (texto) da coluna usage_id do CSV. |
| `subscription_id` | text |  |  |  | Valor bruto (texto) da coluna subscription_id do CSV. |
| `usage_date` | text |  |  |  | Valor bruto (texto) da coluna usage_date do CSV. |
| `feature_name` | text |  |  |  | Valor bruto (texto) da coluna feature_name do CSV. |
| `usage_count` | text |  |  |  | Valor bruto (texto) da coluna usage_count do CSV. |
| `usage_duration_secs` | text |  |  |  | Valor bruto (texto) da coluna usage_duration_secs do CSV. |
| `error_count` | text |  |  |  | Valor bruto (texto) da coluna error_count do CSV. |
| `is_beta_feature` | text |  |  |  | Valor bruto (texto) da coluna is_beta_feature do CSV. |
| `_run_id` | uuid |  |  |  | Execução que carregou a linha. |
| `_file_sha256` | text | 🔑 |  |  | Hash do arquivo de origem (versão do arquivo). |
| `_row_number` | integer | 🔑 |  |  | Número da linha no arquivo (1 = primeira linha de dados). |
| `_row_hash` | text |  |  |  | sha256 do conteúdo da linha. |
| `_ingested_at` | timestamp with time zone |  |  |  | Momento da carga. |

<a id="bronzesubscriptions"></a>
### `bronze.subscriptions`

Cópia fiel de ravenstack_subscriptions.csv; uma linha por linha do arquivo.  
*5.000 linhas · 19 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `subscription_id` | text |  |  |  | Valor bruto (texto) da coluna subscription_id do CSV. |
| `account_id` | text |  |  |  | Valor bruto (texto) da coluna account_id do CSV. |
| `start_date` | text |  |  |  | Valor bruto (texto) da coluna start_date do CSV. |
| `end_date` | text |  |  |  | Valor bruto (texto) da coluna end_date do CSV. |
| `plan_tier` | text |  |  |  | Valor bruto (texto) da coluna plan_tier do CSV. |
| `seats` | text |  |  |  | Valor bruto (texto) da coluna seats do CSV. |
| `mrr_amount` | text |  |  |  | Valor bruto (texto) da coluna mrr_amount do CSV. |
| `arr_amount` | text |  |  |  | Valor bruto (texto) da coluna arr_amount do CSV. |
| `is_trial` | text |  |  |  | Valor bruto (texto) da coluna is_trial do CSV. |
| `upgrade_flag` | text |  |  |  | Valor bruto (texto) da coluna upgrade_flag do CSV. |
| `downgrade_flag` | text |  |  |  | Valor bruto (texto) da coluna downgrade_flag do CSV. |
| `churn_flag` | text |  |  |  | Valor bruto (texto) da coluna churn_flag do CSV. |
| `billing_frequency` | text |  |  |  | Valor bruto (texto) da coluna billing_frequency do CSV. |
| `auto_renew_flag` | text |  |  |  | Valor bruto (texto) da coluna auto_renew_flag do CSV. |
| `_run_id` | uuid |  |  |  | Execução que carregou a linha. |
| `_file_sha256` | text | 🔑 |  |  | Hash do arquivo de origem (versão do arquivo). |
| `_row_number` | integer | 🔑 |  |  | Número da linha no arquivo (1 = primeira linha de dados). |
| `_row_hash` | text |  |  |  | sha256 do conteúdo da linha. |
| `_ingested_at` | timestamp with time zone |  |  |  | Momento da carga. |

<a id="bronzesupporttickets"></a>
### `bronze.support_tickets`

Cópia fiel de ravenstack_support_tickets.csv; uma linha por linha do arquivo.  
*2.000 linhas · 14 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `ticket_id` | text |  |  |  | Valor bruto (texto) da coluna ticket_id do CSV. |
| `account_id` | text |  |  |  | Valor bruto (texto) da coluna account_id do CSV. |
| `submitted_at` | text |  |  |  | Valor bruto (texto) da coluna submitted_at do CSV. |
| `closed_at` | text |  |  |  | Valor bruto (texto) da coluna closed_at do CSV. |
| `resolution_time_hours` | text |  |  |  | Valor bruto (texto) da coluna resolution_time_hours do CSV. |
| `priority` | text |  |  |  | Valor bruto (texto) da coluna priority do CSV. |
| `first_response_time_minutes` | text |  |  |  | Valor bruto (texto) da coluna first_response_time_minutes do CSV. |
| `satisfaction_score` | text |  |  |  | Valor bruto (texto) da coluna satisfaction_score do CSV. |
| `escalation_flag` | text |  |  |  | Valor bruto (texto) da coluna escalation_flag do CSV. |
| `_run_id` | uuid |  |  |  | Execução que carregou a linha. |
| `_file_sha256` | text | 🔑 |  |  | Hash do arquivo de origem (versão do arquivo). |
| `_row_number` | integer | 🔑 |  |  | Número da linha no arquivo (1 = primeira linha de dados). |
| `_row_hash` | text |  |  |  | sha256 do conteúdo da linha. |
| `_ingested_at` | timestamp with time zone |  |  |  | Momento da carga. |

## Silver — dados tipados e validados

<a id="silverrejects"></a>
### `silver._rejects`

Linhas que não entraram no silver, com o motivo e o conteúdo original.  
*0 linhas · 8 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `reject_id` | bigint | 🔑 |  |  | Identificador. |
| `run_id` | uuid |  |  |  | Execução que rejeitou. |
| `dataset` | text |  |  |  | Dataset de origem. |
| `file_sha256` | text |  |  |  | Arquivo de origem. |
| `row_number` | integer |  |  |  | Linha no arquivo. |
| `reason` | text |  |  |  | Motivo da rejeição. |
| `payload` | jsonb |  |  |  | Linha original (bronze). |
| `rejected_at` | timestamp with time zone |  |  |  | Quando foi rejeitada. |

<a id="silveraccounts"></a>
### `silver.accounts`

Contas (clientes) da RavenStack. Uma linha por conta.  
*500 linhas · 13 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `account_id` | text | 🔑 | 0.00 | 500 | Identificador da conta. |
| `account_name` | text |  | 0.00 | 500 | Nome fictício da empresa. |
| `industry` | text |  | 0.00 | 5 | Indústria (DevTools, FinTech, Cybersecurity, HealthTech, EdTech). |
| `country` | text |  | 0.00 | 7 | País (ISO-2). |
| `signup_date` | date |  | 0.00 | 370 | Data de cadastro da conta. |
| `referral_source` | text |  | 0.00 | 5 | Canal de aquisição (organic, ads, event, partner, other). |
| `plan_tier` | text |  | 0.00 | 3 | Plano INICIAL da conta (o atual vem de subscriptions). |
| `seats` | integer |  | 0.00 | 73 | Licenças contratadas no cadastro. |
| `is_trial` | boolean |  | 0.00 | 2 | Conta em trial no cadastro. |
| `churn_flag` | boolean |  | 0.00 | 2 | Flag de churn da origem — NÃO é a definição de churn (usar churn_events); conflita com os eventos. |
| `_file_sha256` | text |  | 0.00 | 1 | Arquivo de origem. |
| `_row_number` | integer |  | 0.00 | 500 | Linha no arquivo de origem. |
| `_refreshed_at` | timestamp with time zone |  | 0.00 | 1 | Momento do refresh do silver. |

<a id="silverchurnevents"></a>
### `silver.churn_events`

Eventos de churn — FONTE DE VERDADE do churn (decisão 2026-10-23). Uma conta pode churnar várias vezes.  
*600 linhas · 12 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `churn_event_id` | text | 🔑 | 0.00 | 600 | Identificador do evento. |
| `account_id` | text |  | 0.00 | 352 | Conta que churnou. |
| `churn_date` | date |  | 0.00 | 311 | Data do churn. |
| `reason_code` | text |  | 0.00 | 6 | Motivo declarado (pricing, support, features, budget, competitor, unknown). |
| `refund_amount_usd` | numeric(12,2) |  | 0.00 | 142 | Valor devolvido (US$). |
| `preceding_upgrade_flag` | boolean |  | 0.00 | 2 | Teve upgrade nos 90 dias anteriores. |
| `preceding_downgrade_flag` | boolean |  | 0.00 | 2 | Teve downgrade nos 90 dias anteriores. |
| `is_reactivation` | boolean |  | 0.00 | 2 | A conta já tinha churnado antes. |
| `feedback_text` | text |  | 24.67 | 3 | Comentário do cliente (só 4 textos distintos na origem). |
| `_file_sha256` | text |  | 0.00 | 1 | Arquivo de origem. |
| `_row_number` | integer |  | 0.00 | 600 | Linha no arquivo de origem. |
| `_refreshed_at` | timestamp with time zone |  | 0.00 | 1 | Momento do refresh do silver. |

<a id="silverfeatureusage"></a>
### `silver.feature_usage`

Uso diário por feature. 77% das linhas têm data fora do período da assinatura (ver is_within_subscription).  
*25.000 linhas · 15 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `usage_key` | text | 🔑 | 0.00 | 25000 | Chave única: usage_id, com sufixo #n quando o mesmo usage_id aparece em eventos diferentes. |
| `usage_id` | text |  | 0.00 | 24979 | Identificador de origem (21 ids colidem entre eventos diferentes). |
| `subscription_id` | text |  | 0.00 | 4967 | Assinatura do uso. |
| `account_id` | text |  | 0.00 | 500 | Conta do uso (derivada via subscriptions). |
| `usage_date` | date |  | 0.00 | 731 | Data do uso. |
| `feature_name` | text |  | 0.00 | 40 | Feature usada (40 features). |
| `usage_count` | integer |  | 0.00 | 27 | Quantidade de eventos de uso. |
| `usage_duration_secs` | integer |  | 0.00 | 4168 | Tempo de uso em segundos. |
| `error_count` | integer |  | 0.00 | 9 | Erros registrados. |
| `is_beta_feature` | boolean |  | 0.00 | 2 | Feature em beta. |
| `is_within_subscription` | boolean |  | 0.00 | 2 | usage_date dentro de [start_date, end_date] da assinatura. |
| `has_id_collision` | boolean |  | 0.00 | 2 | O usage_id de origem se repete em outro evento. |
| `_file_sha256` | text |  | 0.00 | 1 | Arquivo de origem. |
| `_row_number` | integer |  | 0.00 | 25000 | Linha no arquivo de origem. |
| `_refreshed_at` | timestamp with time zone |  | 0.00 | 1 | Momento do refresh do silver. |

<a id="silversubscriptions"></a>
### `silver.subscriptions`

Assinaturas. Uma conta tem várias, muitas sobrepostas (todas as contas têm 2+ abertas).  
*5.000 linhas · 17 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `subscription_id` | text | 🔑 | 0.00 | 5000 | Identificador da assinatura. |
| `account_id` | text |  | 0.00 | 500 | Conta dona da assinatura. |
| `start_date` | date |  | 0.00 | 625 | Início da assinatura. |
| `end_date` | date |  | 90.28 | 208 | Fim da assinatura; nulo = ativa. |
| `plan_tier` | text |  | 0.00 | 3 | Plano no faturamento (Basic, Pro, Enterprise). |
| `seats` | integer |  | 0.00 | 123 | Licenças da assinatura. |
| `mrr_amount` | numeric(12,2) |  | 0.00 | 306 | Receita mensal recorrente (US$). |
| `arr_amount` | numeric(14,2) |  | 0.00 | 306 | Receita anual recorrente (US$) = 12 × MRR. |
| `is_trial` | boolean |  | 0.00 | 2 | Assinatura em trial. |
| `upgrade_flag` | boolean |  | 0.00 | 2 | Teve upgrade no meio do ciclo. |
| `downgrade_flag` | boolean |  | 0.00 | 2 | Teve downgrade no meio do ciclo. |
| `churn_flag` | boolean |  | 0.00 | 2 | Assinatura encerrada (origem) — não usar como definição de churn. |
| `billing_frequency` | text |  | 0.00 | 2 | Cobrança: monthly ou annual. |
| `auto_renew_flag` | boolean |  | 0.00 | 2 | Renovação automática ligada. |
| `_file_sha256` | text |  | 0.00 | 1 | Arquivo de origem. |
| `_row_number` | integer |  | 0.00 | 5000 | Linha no arquivo de origem. |
| `_refreshed_at` | timestamp with time zone |  | 0.00 | 1 | Momento do refresh do silver. |

<a id="silversupporttickets"></a>
### `silver.support_tickets`

Tickets de suporte.  
*2.000 linhas · 12 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `ticket_id` | text | 🔑 | 0.00 | 2000 | Identificador do ticket. |
| `account_id` | text |  | 0.00 | 492 | Conta que abriu o ticket. |
| `submitted_at` | timestamp with time zone |  | 0.00 | 671 | Abertura (a origem só traz a data; hora = 00:00 UTC). |
| `closed_at` | timestamp with time zone |  | 0.00 | 1893 | Fechamento. |
| `resolution_time_hours` | numeric(10,2) |  | 0.00 | 72 | Tempo de resolução em horas. |
| `priority` | text |  | 0.00 | 4 | Prioridade: low, medium, high, urgent. |
| `first_response_time_minutes` | integer |  | 0.00 | 180 | Tempo até a primeira resposta, em minutos. |
| `satisfaction_score` | smallint |  | 41.25 | 3 | CSAT 1–5; nulo = cliente não respondeu. |
| `escalation_flag` | boolean |  | 0.00 | 2 | Ticket escalado. |
| `_file_sha256` | text |  | 0.00 | 1 | Arquivo de origem. |
| `_row_number` | integer |  | 0.00 | 2000 | Linha no arquivo de origem. |
| `_refreshed_at` | timestamp with time zone |  | 0.00 | 1 | Momento do refresh do silver. |

## Gold — fatos, dimensões, KPIs e score de risco

<a id="goldaccount360"></a>
### `gold.account_360`

Visão 360 por conta: cadastro, estado atual, persona, risco e drivers, suporte, uso e último motivo de churn.  
*500 linhas · 31 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `account_id` | text |  | 0.00 | 500 |  |
| `account_name` | text |  | 0.00 | 500 |  |
| `industry` | text |  | 0.00 | 5 |  |
| `country` | text |  | 0.00 | 7 |  |
| `referral_source` | text |  | 0.00 | 5 |  |
| `initial_plan` | text |  | 0.00 | 3 |  |
| `initial_trial` | boolean |  | 0.00 | 2 |  |
| `initial_seats` | integer |  | 0.00 | 73 |  |
| `signup_date` | date |  | 0.00 | 370 |  |
| `signup_cohort` | text |  | 0.00 | 8 |  |
| `tenure_months` | numeric(6,1) |  | 0.00 | 208 |  |
| `current_plan` | text |  | 0.00 | 3 |  |
| `current_billing` | text |  | 0.00 | 2 |  |
| `current_seats` | integer |  | 0.00 | 88 |  |
| `current_auto_renew` | boolean |  | 0.00 | 2 |  |
| `current_mrr` | numeric |  | 0.00 | 165 |  |
| `is_active` | boolean |  | 0.00 | 2 |  |
| `churn_count` | integer |  | 0.00 | 6 |  |
| `last_churn_date` | date |  | 29.60 | 208 |  |
| `persona` | text |  | 13.60 | 8 |  |
| `probability_90d` | numeric(6,4) |  | 13.60 | 8 |  |
| `mrr_at_risk_90d` | numeric(12,2) |  | 13.60 | 310 |  |
| `driver_1` | text |  | 22.20 | 26 |  |
| `driver_2` | text |  | 52.60 | 25 |  |
| `driver_3` | text |  | 81.00 | 12 |  |
| `suggested_action` | text |  | 13.60 | 8 |  |
| `tickets_total` | bigint |  | 0.00 | 12 |  |
| `tickets_90d` | bigint |  | 0.00 | 4 |  |
| `csat_avg` | numeric |  | 6.80 | 25 |  |
| `usage_90d` | bigint |  | 0.00 | 132 |  |
| `last_churn_reason` | text |  | 29.60 | 6 |  |

<a id="goldchurnreasonvsbehavior"></a>
### `gold.churn_reason_vs_behavior`

Cada churn com o motivo declarado e o comportamento real nos 90 dias anteriores (H4).  
*600 linhas · 13 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `churn_event_id` | text |  | 0.00 | 600 |  |
| `account_id` | text |  | 0.00 | 352 |  |
| `churn_date` | date |  | 0.00 | 311 |  |
| `reason_code` | text |  | 0.00 | 6 |  |
| `mrr_at_churn` | numeric |  | 8.83 | 172 |  |
| `plan_at_churn` | text |  | 8.83 | 3 |  |
| `refund_amount_usd` | numeric(12,2) |  | 0.00 | 142 |  |
| `preceding_downgrade_flag` | boolean |  | 0.00 | 2 |  |
| `churn_type` | text |  | 0.00 | 3 |  |
| `usage_90d` | bigint |  | 0.00 | 135 |  |
| `errors_90d` | bigint |  | 0.00 | 16 |  |
| `tickets_90d` | bigint |  | 0.00 | 5 |  |
| `csat_90d` | numeric |  | 72.83 | 5 |  |

<a id="golddimaccount"></a>
### `gold.dim_account`

Contas com atributos de cadastro e estado atual (plano, MRR vigente, ativa ou não) na data de referência.  
*500 linhas · 19 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `account_id` | text |  | 0.00 | 500 | Conta. |
| `account_name` | text |  | 0.00 | 500 | Nome fictício. |
| `industry` | text |  | 0.00 | 5 | Indústria. |
| `country` | text |  | 0.00 | 7 | País. |
| `referral_source` | text |  | 0.00 | 5 | Canal de aquisição. |
| `initial_plan` | text |  | 0.00 | 3 | Plano no cadastro. |
| `initial_trial` | boolean |  | 0.00 | 2 | Trial no cadastro. |
| `initial_seats` | integer |  | 0.00 | 73 | Licenças no cadastro. |
| `signup_date` | date |  | 0.00 | 370 | Data de cadastro. |
| `signup_cohort` | text |  | 0.00 | 8 | Coorte de cadastro (trimestre). |
| `tenure_months` | numeric(6,1) |  | 0.00 | 208 | Meses de casa na data de referência. |
| `current_plan` | text |  | 0.00 | 3 | Plano vigente. |
| `current_billing` | text |  | 0.00 | 2 | Cobrança vigente. |
| `current_seats` | integer |  | 0.00 | 88 | Licenças vigentes. |
| `current_auto_renew` | boolean |  | 0.00 | 2 | Renovação automática vigente. |
| `current_mrr` | numeric |  | 0.00 | 165 | MRR vigente (0 se churnada). |
| `is_active` | boolean |  | 0.00 | 2 | Ativa na data de referência. |
| `churn_count` | integer |  | 0.00 | 6 | Quantas vezes a conta churnou. |
| `last_churn_date` | date |  | 29.60 | 208 | Último churn. |

<a id="golddimcustomerpersona"></a>
### `gold.dim_customer_persona`

Persona de cliente das contas ativas, por regra explícita com precedência (reincidente → em retração → recém-chegado → em expansão → âncora Enterprise → grande sem compromisso → Pro anual → pequeno Basic).  
*432 linhas · 6 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `account_id` | text |  | 0.00 | 432 |  |
| `persona` | text |  | 0.00 | 8 |  |
| `downgrade_90d` | boolean |  | 0.00 | 2 |  |
| `upgrade_90d` | boolean |  | 0.00 | 2 |  |
| `current_trial` | boolean |  | 0.00 | 2 |  |
| `rule_version` | text |  | 0.00 | 1 |  |

<a id="goldfctaccountmonth"></a>
### `gold.fct_account_month`

Uma linha por conta × mês desde o cadastro: estado, MRR vigente no fim do mês e churns do mês.  
*5.807 linhas · 16 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `account_id` | text |  | 0.00 | 500 | Conta. |
| `month_start` | date |  | 0.00 | 24 | Primeiro dia do mês. |
| `month_end` | date |  | 0.00 | 24 | Último dia do mês. |
| `quarter` | text |  | 0.00 | 8 | Trimestre (AAAAQn). |
| `tenure_months` | integer |  | 0.00 | 24 | Meses completos desde o cadastro. |
| `tenure_bucket` | text |  | 0.00 | 4 | Faixa de tempo de casa: 0-3m, 3-6m, 6-12m, 12m+. |
| `active_at_start` | boolean |  | 0.00 | 2 | Conta ativa no início do mês (cadastrada antes e não churnada). |
| `active_at_end` | boolean |  | 0.00 | 2 | Conta ativa no fim do mês. |
| `prior_churns` | integer |  | 0.00 | 6 | Churns da conta antes do mês. |
| `churn_events` | integer |  | 0.00 | 4 | Eventos de churn no mês. |
| `mrr_churned` | numeric |  | 0.00 | 190 | MRR perdido nos churns do mês (US$). |
| `plan_tier` | text |  | 9.45 | 3 | Plano vigente no fim do mês. |
| `billing_frequency` | text |  | 9.45 | 2 | Cobrança vigente no fim do mês. |
| `seats` | integer |  | 9.45 | 114 | Licenças vigentes no fim do mês. |
| `auto_renew_flag` | boolean |  | 9.45 | 2 | Renovação automática vigente no fim do mês. |
| `mrr_end` | numeric |  | 0.00 | 270 | MRR vigente no fim do mês (0 se churnada). |

<a id="goldfctchurnevent"></a>
### `gold.fct_churn_event`

Um evento de churn por linha, com MRR, plano e tempo de casa na data do churn.  
*600 linhas · 16 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `churn_event_id` | text |  | 0.00 | 600 | Evento de churn. |
| `account_id` | text |  | 0.00 | 352 | Conta. |
| `churn_date` | date |  | 0.00 | 311 | Data do churn. |
| `churn_month` | date |  | 0.00 | 23 | Mês do churn. |
| `churn_quarter` | text |  | 0.00 | 8 | Trimestre do churn (AAAAQn). |
| `reason_code` | text |  | 0.00 | 6 | Motivo declarado. |
| `refund_amount_usd` | numeric(12,2) |  | 0.00 | 142 | Refund (US$). |
| `preceding_upgrade_flag` | boolean |  | 0.00 | 2 | Upgrade nos 90 dias anteriores. |
| `preceding_downgrade_flag` | boolean |  | 0.00 | 2 | Downgrade nos 90 dias anteriores. |
| `is_reactivation` | boolean |  | 0.00 | 2 | Flag de reativação da origem. |
| `plan_at_churn` | text |  | 8.83 | 3 | Plano vigente na data do churn. |
| `billing_at_churn` | text |  | 8.83 | 2 | Cobrança vigente na data do churn. |
| `mrr_at_churn` | numeric |  | 8.83 | 172 | MRR vigente na data do churn = MRR perdido (US$); nulo se não havia assinatura. |
| `nth_churn` | bigint |  | 0.00 | 5 | Ordem do churn na vida da conta (1 = primeiro). |
| `tenure_months_at_churn` | numeric |  | 0.00 | 324 | Meses desde o cadastro até o churn. |
| `churn_type` | text |  | 0.00 | 3 | primeiro_0_3m, primeiro_3m_mais ou repetido. |

<a id="goldkpichurnbysegment"></a>
### `gold.kpi_churn_by_segment`

Churn e MRR perdido por segmento, com exposição em contas-mês. Nenhum segmento de cadastro foi significativo após Bonferroni (H6).  
*29 linhas · 8 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `segment_type` | text |  | 0.00 | 7 |  |
| `segment_value` | text |  | 0.00 | 25 |  |
| `accounts` | bigint |  | 0.00 | 27 |  |
| `account_months` | bigint |  | 0.00 | 28 |  |
| `churn_events` | bigint |  | 0.00 | 26 |  |
| `churn_per_100_account_months` | numeric |  | 0.00 | 27 |  |
| `mrr_churned` | numeric |  | 0.00 | 28 |  |
| `pct_mrr_churned` | numeric |  | 0.00 | 26 |  |

<a id="goldkpichurntype"></a>
### `gold.kpi_churn_type`

Eventos e MRR perdido por trimestre e tipo de churn (primeiro em 0-3m, primeiro depois de 3m, repetido).  
*22 linhas · 4 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `churn_quarter` | text |  | 0.00 | 8 |  |
| `churn_type` | text |  | 0.00 | 3 |  |
| `churn_events` | bigint |  | 0.00 | 17 |  |
| `mrr_churned` | numeric |  | 0.00 | 22 |  |

<a id="goldkpicohort"></a>
### `gold.kpi_cohort`

% de contas da coorte com primeiro churn em 3 e 6 meses (só contas com tempo de observação suficiente).  
*8 linhas · 6 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `signup_cohort` | text |  | 0.00 | 8 |  |
| `accounts` | bigint |  | 0.00 | 7 |  |
| `accounts_with_3m` | bigint |  | 0.00 | 7 |  |
| `accounts_with_6m` | bigint |  | 0.00 | 6 |  |
| `churn_3m_pct` | numeric |  | 12.50 | 7 |  |
| `churn_6m_pct` | numeric |  | 25.00 | 6 |  |

<a id="goldkpifeaturehealth"></a>
### `gold.kpi_feature_health`

Adoção, taxa de erro e % de usuários que churnaram por feature.  
*40 linhas · 7 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `feature_name` | text |  | 0.00 | 40 |  |
| `is_beta` | boolean |  | 0.00 | 1 |  |
| `accounts` | bigint |  | 0.00 | 24 |  |
| `adoption_pct` | numeric |  | 0.00 | 24 |  |
| `usage_events` | bigint |  | 0.00 | 40 |  |
| `error_rate` | numeric |  | 0.00 | 32 |  |
| `pct_users_who_churned` | numeric |  | 0.00 | 26 |  |

<a id="goldkpilossconcentration"></a>
### `gold.kpi_loss_concentration`

% do MRR perdido vindo dos 10% maiores churns (total e por trimestre).  
*9 linhas · 4 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `period` | text |  | 0.00 | 9 |  |
| `churn_events` | bigint |  | 0.00 | 9 |  |
| `mrr_churned` | numeric |  | 0.00 | 9 |  |
| `top10pct_share_pct` | numeric |  | 0.00 | 9 |  |

<a id="goldkpipersonasummary"></a>
### `gold.kpi_persona_summary`

Contas, MRR e MRR em risco (90 dias) por persona de cliente.  
*8 linhas · 10 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `persona` | text |  | 0.00 | 8 |  |
| `label` | text |  | 0.00 | 8 |  |
| `accounts` | bigint |  | 0.00 | 8 |  |
| `mrr` | numeric |  | 0.00 | 8 |  |
| `pct_mrr` | numeric |  | 0.00 | 8 |  |
| `avg_probability_90d` | numeric |  | 0.00 | 8 |  |
| `mrr_at_risk_90d` | numeric |  | 0.00 | 8 |  |
| `pct_mrr_at_risk` | numeric |  | 0.00 | 8 |  |
| `why_it_matters` | text |  | 0.00 | 8 |  |
| `recommended_play` | text |  | 0.00 | 8 |  |

<a id="goldkpireactivation"></a>
### `gold.kpi_reactivation`

Taxa de reativação (churn seguido de nova assinatura) e intervalos até reativar e até o próximo churn.  
*1 linhas · 7 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `churn_events` | bigint |  | 0.00 | 1 |  |
| `followed_by_new_subscription` | bigint |  | 0.00 | 1 |  |
| `reactivation_pct` | numeric |  | 0.00 | 1 |  |
| `days_to_reactivate_p25` | double precision |  | 0.00 | 1 |  |
| `days_to_reactivate_median` | double precision |  | 0.00 | 1 |  |
| `days_to_reactivate_p75` | double precision |  | 0.00 | 1 |  |
| `days_between_churns_median` | double precision |  | 0.00 | 1 |  |

<a id="goldkpirevenuemonthly"></a>
### `gold.kpi_revenue_monthly`

KPIs mensais: logos e MRR por estado (ativa no início × no fim do mês), GRR/NRR, ARPA, e taxa de eventos de churn. Ressalva: churn e assinaturas são desacoplados na origem (87% dos churns têm nova assinatura depois, mediana 16 dias) — KPIs de receita são aproximados.  
*24 linhas · 21 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `month_start` | date |  | 0.00 | 24 |  |
| `quarter` | text |  | 0.00 | 8 |  |
| `active_accounts_start` | bigint |  | 0.00 | 24 |  |
| `active_accounts_end` | bigint |  | 0.00 | 23 |  |
| `lost_accounts` | bigint |  | 0.00 | 16 |  |
| `accounts_with_churn_event` | bigint |  | 0.00 | 18 |  |
| `churn_events` | bigint |  | 0.00 | 20 |  |
| `mrr_start` | numeric |  | 0.00 | 24 |  |
| `mrr_end` | numeric |  | 0.00 | 24 |  |
| `mrr_new_or_returning` | numeric |  | 0.00 | 24 |  |
| `mrr_lost` | numeric |  | 0.00 | 23 |  |
| `mrr_expansion` | numeric |  | 0.00 | 24 |  |
| `mrr_contraction` | numeric |  | 0.00 | 24 |  |
| `mrr_in_churn_events` | numeric |  | 0.00 | 23 |  |
| `arr_end` | numeric |  | 0.00 | 24 |  |
| `logo_churn_pct` | numeric |  | 4.17 | 23 |  |
| `churn_event_rate_pct` | numeric |  | 4.17 | 22 |  |
| `gross_mrr_churn_pct` | numeric |  | 4.17 | 23 |  |
| `grr_pct` | numeric |  | 4.17 | 23 |  |
| `nrr_pct` | numeric |  | 4.17 | 23 |  |
| `arpa` | numeric |  | 0.00 | 24 |  |

<a id="goldkpisilentchurn"></a>
### `gold.kpi_silent_churn`

Churn silencioso: eventos sem nenhum ticket nos 90 dias anteriores (o CS não vê).  
*8 linhas · 4 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `churn_quarter` | text |  | 0.00 | 8 |  |
| `churn_events` | bigint |  | 0.00 | 8 |  |
| `without_ticket_90d` | bigint |  | 0.00 | 8 |  |
| `silent_pct` | numeric |  | 0.00 | 8 |  |

<a id="goldkpisupporthealth"></a>
### `gold.kpi_support_health`

Saúde do suporte de contas que churnaram × nunca churnaram: são iguais (H1). CSAT só vai de 3 a 5 e 41% sem resposta.  
*2 linhas · 10 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `account_group` | text |  | 0.00 | 2 |  |
| `tickets` | bigint |  | 0.00 | 2 |  |
| `accounts` | bigint |  | 0.00 | 2 |  |
| `csat_avg` | numeric |  | 0.00 | 1 |  |
| `csat_response_pct` | numeric |  | 0.00 | 2 |  |
| `csat_min_observed` | smallint |  | 0.00 | 1 |  |
| `csat_max_observed` | smallint |  | 0.00 | 1 |  |
| `escalated_pct` | numeric |  | 0.00 | 2 |  |
| `frt_median_minutes` | double precision |  | 0.00 | 2 |  |
| `resolution_median_hours` | double precision |  | 0.00 | 1 |  |

<a id="goldkpitenurehazard"></a>
### `gold.kpi_tenure_hazard`

Churns por 100 contas-mês por trimestre e faixa de tempo de casa (exposição = todos os meses desde o cadastro, como no diagnóstico H8).  
*25 linhas · 6 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `quarter` | text |  | 0.00 | 8 |  |
| `tenure_bucket` | text |  | 0.00 | 4 |  |
| `account_months` | bigint |  | 0.00 | 15 |  |
| `churn_events` | bigint |  | 0.00 | 21 |  |
| `churn_per_100_account_months` | numeric |  | 0.00 | 24 |  |
| `mrr_churned` | numeric |  | 0.00 | 24 |  |

<a id="goldkpiusagesegmentmonthly"></a>
### `gold.kpi_usage_segment_monthly`

Uso por trimestre, plano e indústria. O uso é plano (~63/conta) e 53% tem data anterior ao cadastro: o log não está ancorado no tempo (H2).  
*120 linhas · 9 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `quarter` | text |  | 0.00 | 8 |  |
| `plan` | text |  | 0.00 | 3 |  |
| `industry` | text |  | 0.00 | 5 |  |
| `usage_events` | bigint |  | 0.00 | 117 |  |
| `accounts_with_usage` | bigint |  | 0.00 | 15 |  |
| `usage_per_account` | numeric |  | 0.00 | 95 |  |
| `error_rate` | numeric |  | 0.00 | 97 |  |
| `beta_pct` | numeric |  | 0.00 | 68 |  |
| `pct_before_signup` | numeric |  | 0.00 | 110 |  |

<a id="goldpersonacatalog"></a>
### `gold.persona_catalog`

Ficha de cada persona de cliente: regra, por que importa e jogada recomendada.  
*8 linhas · 5 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `persona` | text |  | 0.00 | 8 |  |
| `label` | text |  | 0.00 | 8 |  |
| `rule` | text |  | 0.00 | 8 |  |
| `why_it_matters` | text |  | 0.00 | 8 |  |
| `recommended_play` | text |  | 0.00 | 8 |  |

<a id="goldriskscores"></a>
### `gold.risk_scores`

Risco de churn em 90 dias por conta ativa: taxa empírica do último trimestre por faixa de tempo de casa × churn anterior (modelo do diagnóstico H8, em SQL).  
*432 linhas · 14 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `account_id` | text | 🔑 | 0.00 | 432 | Conta. |
| `scored_at` | date | 🔑 | 0.00 | 1 | Data de referência do score. |
| `model_version` | text | 🔑 | 0.00 | 1 | Versão do modelo. |
| `persona` | text |  | 0.00 | 8 | Persona de cliente na data. |
| `tenure_bucket_next` | text |  | 0.00 | 4 | Faixa de tempo de casa no próximo mês. |
| `prior_churns` | integer |  | 0.00 | 6 | Churns anteriores da conta. |
| `monthly_rate` | numeric(8,5) |  | 0.00 | 8 | Taxa mensal esperada de churn (eventos por conta-mês). |
| `probability_90d` | numeric(6,4) |  | 0.00 | 8 | Probabilidade de churn em 90 dias = 1 − exp(−3 × taxa mensal). |
| `mrr` | numeric(12,2) |  | 0.00 | 165 | MRR vigente (US$). |
| `mrr_at_risk_90d` | numeric(12,2) |  | 0.00 | 310 | Probabilidade × MRR (US$). |
| `driver_1` | text |  | 9.95 | 26 | Principal fator de risco (texto para o CS). |
| `driver_2` | text |  | 45.14 | 25 | Segundo fator. |
| `driver_3` | text |  | 78.01 | 12 | Terceiro fator. |
| `suggested_action` | text |  | 0.00 | 8 | Jogada recomendada (da persona). |

## Ops — operação do lake (ingestão, qualidade, catálogo)

<a id="opscatalogcolumns"></a>
### `ops.catalog_columns`

Catálogo: uma linha por coluna, com estatísticas.  
*257 linhas · 10 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `schema_name` | text | 🔑 |  |  | Schema. |
| `table_name` | text | 🔑 |  |  | Tabela ou view. |
| `column_name` | text | 🔑 |  |  | Coluna. |
| `ordinal` | integer |  |  |  | Posição da coluna. |
| `data_type` | text |  |  |  | Tipo de dado. |
| `description` | text |  |  |  | Descrição (COMMENT ON COLUMN). |
| `is_key` | boolean |  |  |  | Faz parte da chave primária. |
| `is_pii` | boolean |  |  |  | Dado que identifica cliente (o dataset é sintético). |
| `null_pct` | numeric(5,2) |  |  |  | % de nulos (só silver e gold). |
| `distinct_count` | bigint |  |  |  | Valores distintos (só silver e gold). |

<a id="opscatalogtables"></a>
### `ops.catalog_tables`

Catálogo: uma linha por tabela/view do lake.  
*25 linhas · 7 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `schema_name` | text | 🔑 |  |  | Schema. |
| `table_name` | text | 🔑 |  |  | Tabela ou view. |
| `layer` | text |  |  |  | Camada do lake (bronze, silver, gold, ops, app). |
| `description` | text |  |  |  | Descrição (COMMENT ON TABLE). |
| `row_count` | bigint |  |  |  | Quantidade de linhas na última atualização do catálogo. |
| `column_count` | integer |  |  |  | Quantidade de colunas. |
| `last_refreshed` | timestamp with time zone |  |  |  | Quando o catálogo foi atualizado. |

<a id="opsdqresults"></a>
### `ops.dq_results`

Resultado das checagens de qualidade de dados por execução.  
*16 linhas · 11 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `dq_id` | bigint | 🔑 |  |  | Identificador do resultado. |
| `run_id` | uuid |  |  |  | Execução avaliada. |
| `check_name` | text |  |  |  | Nome da checagem. |
| `table_name` | text |  |  |  | Tabela avaliada. |
| `severity` | text |  |  |  | error interrompe o pipeline antes do gold; warning e info viram achados. |
| `status` | text |  |  |  | pass ou fail. |
| `failing_rows` | integer |  |  |  | Linhas que falharam. |
| `total_rows` | integer |  |  |  | Linhas avaliadas. |
| `details` | text |  |  |  | Explicação em linguagem simples. |
| `sample` | jsonb |  |  |  | Amostra de até 5 registros que falharam. |
| `checked_at` | timestamp with time zone |  |  |  | Quando a checagem rodou. |

<a id="opsingestionruns"></a>
### `ops.ingestion_runs`

Uma linha por execução do pipeline ravenlake.  
*2 linhas · 10 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `run_id` | uuid | 🔑 |  |  | Identificador da execução. |
| `started_at` | timestamp with time zone |  |  |  | Início da execução. |
| `finished_at` | timestamp with time zone |  |  |  | Fim da execução (nulo enquanto roda). |
| `status` | text |  |  |  | running, success, failed ou skipped (fonte sem mudança). |
| `trigger` | text |  |  |  | Quem disparou: manual, cron (Render) ou test. |
| `source` | text |  |  |  | Fonte dos dados: kaggle_mcp ou local. |
| `source_ref` | text |  |  |  | Referência da fonte (ex.: rivalytics/saas-subscription-and-churn-analytics-dataset). |
| `source_version` | integer |  |  |  | Versão do dataset na fonte (Kaggle). |
| `git_sha` | text |  |  |  | Commit do código que executou. |
| `error` | text |  |  |  | Mensagem de erro, se falhou. |

<a id="opsingestionsteps"></a>
### `ops.ingestion_steps`

Uma linha por dataset × camada em cada execução; progresso atualizado a cada lote.  
*27 linhas · 15 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `step_id` | bigint | 🔑 |  |  | Identificador da etapa. |
| `run_id` | uuid |  |  |  | Execução a que a etapa pertence. |
| `dataset` | text |  |  |  | Dataset (accounts, subscriptions, feature_usage, support_tickets, churn_events) ou "all". |
| `layer` | text |  |  |  | Camada: raw, bronze, silver, dq, gold ou catalog. |
| `file_sha256` | text |  |  |  | Hash do arquivo de origem. |
| `bytes` | bigint |  |  |  | Tamanho do arquivo em bytes. |
| `storage_path` | text |  |  |  | Caminho do arquivo no bucket raw. |
| `rows_read` | integer |  |  |  | Linhas lidas da origem. |
| `rows_loaded` | integer |  |  |  | Linhas carregadas na camada. |
| `rows_rejected` | integer |  |  |  | Linhas rejeitadas (ver silver._rejects). |
| `status` | text |  |  |  | running, success, failed ou skipped. |
| `started_at` | timestamp with time zone |  |  |  | Início da etapa. |
| `finished_at` | timestamp with time zone |  |  |  | Fim da etapa. |
| `duration_ms` | integer |  |  |  | Duração em milissegundos. |
| `error` | text |  |  |  | Mensagem de erro, se falhou. |

## App — prompts, perfis, usuários e auditoria da IA

<a id="appairuns"></a>
### `app.ai_runs`

Auditoria de cada resposta do assistente (pergunta, tools, resposta, tokens).  
*2 linhas · 13 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `id` | bigint | 🔑 |  |  |  |
| `created_at` | timestamp with time zone |  |  |  |  |
| `profile_slug` | text |  |  |  |  |
| `prompt_slug` | text |  |  |  |  |
| `question` | text |  |  |  |  |
| `answer` | text |  |  |  |  |
| `model` | text |  |  |  |  |
| `tool_calls` | jsonb |  |  |  |  |
| `input_tokens` | integer |  |  |  |  |
| `output_tokens` | integer |  |  |  |  |
| `latency_ms` | integer |  |  |  |  |
| `error` | text |  |  |  |  |
| `user_email` | text |  |  |  |  |

<a id="appanalysisprofiles"></a>
### `app.analysis_profiles`

Perfis de análise por área (lente do assistente); editáveis com restauração do padrão.  
*8 linhas · 7 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `slug` | text | 🔑 |  |  |  |
| `name` | text |  |  |  |  |
| `question` | text |  |  |  |  |
| `instructions` | text |  |  |  |  |
| `default_instructions` | text |  |  |  |  |
| `version` | integer |  |  |  |  |
| `updated_at` | timestamp with time zone |  |  |  |  |

<a id="appprompttemplates"></a>
### `app.prompt_templates`

Prompts prontos do assistente (editáveis; default_body permite restaurar o padrão).  
*10 linhas · 9 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `slug` | text | 🔑 |  |  |  |
| `title` | text |  |  |  |  |
| `profile_slug` | text |  |  |  |  |
| `description` | text |  |  |  |  |
| `body` | text |  |  |  |  |
| `default_body` | text |  |  |  |  |
| `variables` | jsonb |  |  |  |  |
| `version` | integer |  |  |  |  |
| `updated_at` | timestamp with time zone |  |  |  |  |

<a id="approles"></a>
### `app.roles`

Papéis: quais abas do painel e qual perfil de análise cada área usa. Todos veem a visão geral.  
*9 linhas · 5 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `role` | text | 🔑 |  |  |  |
| `label` | text |  |  |  |  |
| `profile_slug` | text |  |  |  |  |
| `tabs` | text[] |  |  |  |  |
| `can_edit` | boolean |  |  |  |  |

<a id="appusers"></a>
### `app.users`

Usuários do painel; code_hash = pbkdf2_sha256$iter$salt$hash do código pessoal.  
*9 linhas · 7 colunas*

| Coluna | Tipo | Chave | % nulos | Distintos | Descrição |
|---|---|---|---|---|---|
| `email` | text | 🔑 |  |  |  |
| `name` | text |  |  |  |  |
| `role` | text |  |  |  |  |
| `code_hash` | text |  |  |  |  |
| `active` | boolean |  |  |  |  |
| `created_at` | timestamp with time zone |  |  |  |  |
| `last_login` | timestamp with time zone |  |  |  |  |
