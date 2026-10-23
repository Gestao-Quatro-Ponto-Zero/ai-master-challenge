# Modelo de dados — como elaboramos e resolvemos o data lake

Projeto Supabase **G4-Analysys**, Postgres 17, com o bucket `raw` no Storage. Tudo está versionado em [`supabase/migrations/`](../supabase/migrations/). O dicionário completo, gerado do catálogo, está em [`dicionario-de-dados.md`](dicionario-de-dados.md).

## 1. Arquitetura (medalhão)

```mermaid
flowchart LR
    K[("Kaggle<br/>(MCP remoto)")] -->|"ravenlake ingest<br/>sha256 + versão"| R[["Storage raw/<br/>CSV imutável"]]
    R -->|COPY em lotes| B["bronze.*<br/>1:1 com CSV, tudo texto"]
    B -->|"silver.refresh()"| S["silver.*<br/>tipado, PK/FK, dedup"]
    B -. linhas inválidas .-> RJ["silver._rejects"]
    S -->|"ops.run_dq()"| DQ{"16 checagens<br/>error bloqueia"}
    DQ -->|"gold.refresh()"| G["gold.*<br/>fatos, dimensões,<br/>KPIs, risco"]
    G --> A["api.*<br/>views só leitura"]
    A --> P["Painel React<br/>(login por área)"]
    A --> IA["Assistente Claude<br/>(tool use)"]
    A --> M["MCP /mcp<br/>(Claude, OpenAI, Gemini…)"]
    APP["app.*<br/>prompts, perfis,<br/>usuários, ai_runs"] --- IA
    OPS["ops.*<br/>runs, steps, DQ,<br/>catálogo"] --- P
```

| Camada | Papel | Regra principal |
|---|---|---|
| **raw** (Storage) | Prova original | Arquivo nomeado pelo sha256 e nunca editado; reprocessar = reler daqui |
| **bronze** | Cópia fiel | Todas as colunas em texto, mais `_run_id`, `_file_sha256`, `_row_number` e `_row_hash`. PK `(arquivo, linha)` torna a carga idempotente |
| **silver** | Verdade tipada | Conversões seguras (`try_date`, `try_int`…); o que falha vai para `_rejects` com o motivo; PK e FK declaradas |
| **gold** | Regras de negócio | Fatos e dimensões materializados; KPIs com as fórmulas do dicionário da skill de negócio |
| **api** | Interface | Único schema lido pelo painel, assistente e MCP; SQL livre só via `run_readonly_query` |
| **ops** / **app** | Operação e aplicação | Execuções, qualidade, catálogo; prompts, perfis, papéis, usuários, auditoria da IA |

## 2. DER — silver (origem: 5 CSVs do Kaggle)

```mermaid
erDiagram
    ACCOUNTS ||--o{ SUBSCRIPTIONS : "tem"
    ACCOUNTS ||--o{ SUPPORT_TICKETS : "abre"
    ACCOUNTS ||--o{ CHURN_EVENTS : "churna (0..n vezes)"
    ACCOUNTS ||--o{ FEATURE_USAGE : "usa (derivado)"
    SUBSCRIPTIONS ||--o{ FEATURE_USAGE : "registra"

    ACCOUNTS {
        text account_id PK
        text industry
        text country
        date signup_date
        text referral_source
        text plan_tier "plano inicial"
        int seats
        bool is_trial
        bool churn_flag "não confiável"
    }
    SUBSCRIPTIONS {
        text subscription_id PK
        text account_id FK
        date start_date
        date end_date "nulo = ativa"
        text plan_tier
        int seats
        numeric mrr_amount
        text billing_frequency
        bool upgrade_flag
        bool downgrade_flag
        bool auto_renew_flag
    }
    FEATURE_USAGE {
        text usage_key PK "usage_id#n"
        text subscription_id FK
        text account_id FK
        date usage_date
        text feature_name
        int usage_count
        int error_count
        bool is_beta_feature
        bool is_within_subscription
    }
    SUPPORT_TICKETS {
        text ticket_id PK
        text account_id FK
        timestamptz submitted_at
        int first_response_time_minutes
        numeric resolution_time_hours
        smallint satisfaction_score "3-5; nulo = sem resposta"
        bool escalation_flag
    }
    CHURN_EVENTS {
        text churn_event_id PK
        text account_id FK
        date churn_date
        text reason_code
        numeric refund_amount_usd
        bool preceding_downgrade_flag
        bool is_reactivation
    }
```

## 3. DER — gold, api e app

```mermaid
erDiagram
    DIM_ACCOUNT ||--o{ FCT_ACCOUNT_MONTH : "conta × mês"
    DIM_ACCOUNT ||--o{ FCT_CHURN_EVENT : "eventos"
    DIM_ACCOUNT ||--o| DIM_CUSTOMER_PERSONA : "persona (ativas)"
    DIM_ACCOUNT ||--o| RISK_SCORES : "score 90 dias"
    PERSONA_CATALOG ||--o{ DIM_CUSTOMER_PERSONA : "ficha"
    ROLES ||--o{ USERS : "papel"
    ANALYSIS_PROFILES ||--o| ROLES : "lente da área"
    ANALYSIS_PROFILES ||--o{ PROMPT_TEMPLATES : "prompts do perfil"
    USERS ||--o{ AI_RUNS : "perguntas"

    DIM_ACCOUNT {
        text account_id PK
        text current_plan
        numeric current_mrr "assinatura ativa mais recente"
        bool is_active
        int churn_count
        numeric tenure_months
    }
    FCT_ACCOUNT_MONTH {
        text account_id PK
        date month_start PK
        text tenure_bucket "0-3m 3-6m 6-12m 12m+"
        bool active_at_start
        int churn_events
        numeric mrr_end
        numeric mrr_churned
    }
    FCT_CHURN_EVENT {
        text churn_event_id PK
        text account_id
        date churn_date
        numeric mrr_at_churn
        text plan_at_churn
        int nth_churn
        text churn_type "primeiro_0_3m / primeiro_3m_mais / repetido"
    }
    DIM_CUSTOMER_PERSONA {
        text account_id PK
        text persona
        text rule_version
    }
    PERSONA_CATALOG {
        text persona PK
        text rule
        text recommended_play
    }
    RISK_SCORES {
        text account_id PK
        date scored_at PK
        text model_version PK
        numeric probability_90d
        numeric mrr_at_risk_90d
        text driver_1
        text suggested_action
    }
    ROLES {
        text role PK
        text profile_slug FK
        text_array tabs
        bool can_edit
    }
    USERS {
        text email PK
        text role FK
        text code_hash "PBKDF2"
    }
    ANALYSIS_PROFILES {
        text slug PK
        text instructions
        text default_instructions
    }
    PROMPT_TEMPLATES {
        text slug PK
        text profile_slug
        text body
        text default_body
    }
    AI_RUNS {
        bigint id PK
        text user_email
        text question
        jsonb tool_calls
        text answer
    }
```

As views de KPI (`gold.kpi_*`) agregam esses fatos: hazard por tempo de casa, coortes, segmentos, concentração, tipo de churn, reativação, suporte, churn silencioso, uso e features. Cada uma é exposta como `api.<nome>`.

## 4. ops — operação e observabilidade

```mermaid
erDiagram
    INGESTION_RUNS ||--o{ INGESTION_STEPS : "dataset × camada"
    INGESTION_RUNS ||--o{ DQ_RESULTS : "checagens"
    INGESTION_RUNS ||--o{ REJECTS : "linhas rejeitadas"
    CATALOG_TABLES ||--o{ CATALOG_COLUMNS : "colunas"
    INGESTION_RUNS {
        uuid run_id PK
        text status "running/success/failed/skipped"
        text source "kaggle_mcp/local"
        int source_version
    }
    INGESTION_STEPS {
        bigint step_id PK
        uuid run_id FK
        text dataset
        text layer "raw→bronze→silver→dq→gold→catalog"
        int rows_read
        int rows_loaded
        int rows_rejected
    }
    DQ_RESULTS {
        bigint dq_id PK
        uuid run_id FK
        text check_name
        text severity
        int failing_rows
    }
    REJECTS {
        bigint reject_id PK
        uuid run_id FK
        text reason
        jsonb payload
    }
    CATALOG_TABLES {
        text schema_name PK
        text table_name PK
        bigint row_count
    }
    CATALOG_COLUMNS {
        text column_name PK
        text data_type
        numeric null_pct
        bigint distinct_count
    }
```

## 5. Problemas encontrados e como resolvemos

| Problema nos dados | Evidência | Solução no modelo |
|---|---|---|
| Três definições de churn discordam | 277 contas com evento e `churn_flag` falsa; 35 com a flag sem evento; só 6 de 600 churns coincidem com o fim de uma assinatura | `churn_events` é a fonte de verdade (decidido com o Tiago); as flags viram checagem de qualidade |
| Contas com várias assinaturas abertas ao mesmo tempo | Todas as 500 contas têm 2 ou mais; somando tudo daria mediana de 225 licenças por conta | **MRR vigente = assinatura ativa mais recente** (`gold.subscription_at`), com o mesmo desempate em SQL e em Python |
| Uso fora do tempo | 78% fora do período da assinatura; 53% antes do cadastro | Coluna `is_within_subscription`; a análise usa conta + data do uso; registrado como achado |
| `usage_id` repetido | 21 ids em eventos **diferentes** | Mantidos todos, com `usage_key = usage_id#n` e `has_id_collision` |
| CSAT truncado | Só notas 3–5; 41% nulos | Checagem `csat_escala_incompleta`; nulo = "não respondeu" (`kpi_support_health`) |
| Churn e volta | 87% dos churns seguidos de nova assinatura, mediana de 16 dias | Estado "churnada" = churn sem assinatura posterior (`gold.is_churned_on`); KPIs de receita com ressalva (H9) |
| Funções lentas em views | Funções SQL com `search_path` fixo não são incorporadas na consulta → timeout | `dim_account` e `dim_customer_persona` materializadas; data de referência calculada uma vez |
| Recarga do mesmo arquivo | Reexecução do pipeline | PK `(sha256, linha)` no bronze, mais o salto por versão e hash (run `skipped`) |
| Segurança | Painel e IA lendo o banco | Schemas internos revogados de `anon`/`authenticated`; RLS ligado; leitura só via `api.*`; SQL da IA com validação e transação read-only |

## 6. Como regenerar

```bash
uv run python scripts/apply_sql.py supabase/migrations/<arquivo>.sql   # migrations, em ordem
cd packages/ravenlake && uv run ravenlake ingest                       # carga + DQ + gold + catálogo
uv run python scripts/gen_data_dictionary.py                           # atualiza o dicionário
```
