# G4 Compass — Backend Implementation
## Referência técnica para o desenvolvedor

---

## Stack

```
Linguagem:   Go
Framework:   Fiber (fasthttp)
Banco:       PostgreSQL 16 (local via Docker → CockroachDB em produção)
Driver:      pgx/v5
Auth:        JWT (HS256)
LLM:         Claude (Anthropic API) — agente ReAct
IDs:         UUID v7
```

---

## Infraestrutura local

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: compass
      POSTGRES_USER: compass
      POSTGRES_PASSWORD: compass
    ports:
      - "5432:5432"
    volumes:
      - ./scripts/schema.sql:/docker-entrypoint-initdb.d/schema.sql
      - postgres_data:/var/lib/postgresql/data
```

A connection string usa o mesmo formato do CockroachDB (`pgx`-compatible).
Trocar de Postgres local para CockroachDB em produção = só mudar a `DATABASE_URL`.

---

## Schema do banco

### Convenções
- Todos os IDs são `UUID` gerados com UUID v7
- Toda tabela tem `created_at` e `updated_at`
- Tabelas que recebem dados externos têm `external_id` + `source` para futura integração com CRM
- Soft delete via `deleted_at` onde fizer sentido

---

### Tabelas base (populadas via CSV / futuro CRM)

```sql
-- ─── VENDEDORES / TIME ───────────────────────────────────────

CREATE TABLE regional_offices (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name       VARCHAR(100) NOT NULL UNIQUE,  -- 'Central', 'East', 'West'
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE managers (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name            VARCHAR(200) NOT NULL,
  regional_office_id UUID REFERENCES regional_offices(id),
  external_id     VARCHAR(100),           -- ID no CRM futuro
  source          VARCHAR(50) DEFAULT 'csv',
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE sales_agents (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name            VARCHAR(200) NOT NULL,
  manager_id      UUID REFERENCES managers(id),
  regional_office_id UUID REFERENCES regional_offices(id),
  external_id     VARCHAR(100),
  source          VARCHAR(50) DEFAULT 'csv',
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─── CONTAS ──────────────────────────────────────────────────

CREATE TABLE accounts (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name             VARCHAR(200) NOT NULL,
  sector           VARCHAR(100),
  year_established INT,
  revenue_millions DECIMAL(12,2),
  employees        INT,
  office_location  VARCHAR(200),
  subsidiary_of    VARCHAR(200),
  external_id      VARCHAR(100),
  source           VARCHAR(50) DEFAULT 'csv',
  created_at       TIMESTAMPTZ DEFAULT NOW(),
  updated_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ─── PRODUTOS ────────────────────────────────────────────────

CREATE TABLE products (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        VARCHAR(200) NOT NULL UNIQUE,
  series      VARCHAR(100),
  sales_price DECIMAL(10,2),
  external_id VARCHAR(100),
  source      VARCHAR(50) DEFAULT 'csv',
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── DEALS (pipeline) ────────────────────────────────────────

CREATE TYPE deal_stage AS ENUM ('Prospecting', 'Engaging', 'Won', 'Lost');

CREATE TABLE deals (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  opportunity_id  VARCHAR(50) NOT NULL UNIQUE,  -- ID original do CSV
  sales_agent_id  UUID REFERENCES sales_agents(id),
  product_id      UUID REFERENCES products(id),
  account_id      UUID REFERENCES accounts(id), -- nullable (1.425 sem conta)
  stage           deal_stage NOT NULL,
  engage_date     DATE,                          -- nullable (Prospecting sem data)
  close_date      DATE,                          -- nullable (deals ativos)
  close_value     DECIMAL(10,2),                 -- nullable (deals ativos)
  external_id     VARCHAR(100),
  source          VARCHAR(50) DEFAULT 'csv',
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

### Tabelas de aplicação (geradas pelo sistema)

```sql
-- ─── AUTH ────────────────────────────────────────────────────

CREATE TABLE users (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email          VARCHAR(200) NOT NULL UNIQUE,
  password_hash  VARCHAR(200) NOT NULL,
  role           VARCHAR(20) NOT NULL DEFAULT 'agent',  -- 'agent' | 'manager' | 'admin'
  sales_agent_id UUID REFERENCES sales_agents(id),      -- NULL se manager/admin
  manager_id     UUID REFERENCES managers(id),           -- NULL se agent/admin
  last_login_at  TIMESTAMPTZ,
  created_at     TIMESTAMPTZ DEFAULT NOW(),
  updated_at     TIMESTAMPTZ DEFAULT NOW()
);

-- ─── SCORES ──────────────────────────────────────────────────

-- Score atual de cada deal (recalculado periodicamente)
CREATE TABLE deal_scores (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id     UUID NOT NULL REFERENCES deals(id),
  score       SMALLINT NOT NULL CHECK (score BETWEEN 0 AND 100),
  label       VARCHAR(20) NOT NULL,  -- 'hot' | 'warm' | 'cold' | 'zombie'
  reasons     JSONB NOT NULL,        -- array de strings em linguagem natural
  factors     JSONB NOT NULL,        -- breakdown dos fatores e pesos
  calculated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(deal_id)  -- só o score mais recente
);

-- Histórico de scores para mostrar evolução no Deal Detail
CREATE TABLE deal_score_history (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id       UUID NOT NULL REFERENCES deals(id),
  score         SMALLINT NOT NULL,
  label         VARCHAR(20) NOT NULL,
  calculated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── ALERTAS ─────────────────────────────────────────────────

CREATE TYPE alert_type AS ENUM (
  'hot_window',      -- deal entrou na janela ideal de fechamento
  'stale_deal',      -- deal parado além do ciclo médio
  'weekly_briefing', -- resumo semanal
  'score_drop',      -- score caiu significativamente
  'new_opportunity'  -- deal novo com score alto
);

CREATE TABLE alerts (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        UUID NOT NULL REFERENCES users(id),
  deal_id        UUID REFERENCES deals(id),  -- nullable (alertas gerais)
  type           alert_type NOT NULL,
  title          VARCHAR(200) NOT NULL,
  body           TEXT NOT NULL,
  read_at        TIMESTAMPTZ,               -- NULL = não lido
  action_url     VARCHAR(500),              -- deep link pro deal
  created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- ─── CONVERSAS DO AGENTE ─────────────────────────────────────

CREATE TABLE conversations (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID NOT NULL REFERENCES users(id),
  context    JSONB,          -- {deal_id?, filter?} contexto inicial
  started_at TIMESTAMPTZ DEFAULT NOW(),
  ended_at   TIMESTAMPTZ
);

CREATE TYPE message_role AS ENUM ('user', 'assistant', 'tool');

CREATE TABLE messages (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID NOT NULL REFERENCES conversations(id),
  role            message_role NOT NULL,
  content         TEXT NOT NULL,
  tool_name       VARCHAR(100),   -- preenchido se role = 'tool'
  tool_input      JSONB,
  tool_result     JSONB,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─── MEMÓRIA DO AGENTE ───────────────────────────────────────

CREATE TYPE memory_type AS ENUM ('preference', 'pattern', 'fact', 'feedback');
CREATE TYPE memory_source AS ENUM ('conversation', 'behavior', 'system');

CREATE TABLE agent_memories (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID NOT NULL REFERENCES users(id),
  type         memory_type NOT NULL,
  content      TEXT NOT NULL,       -- linguagem natural
  source       memory_source NOT NULL,
  confidence   DECIMAL(3,2) DEFAULT 0.5 CHECK (confidence BETWEEN 0 AND 1),
  observed_at  TIMESTAMPTZ DEFAULT NOW(),
  expires_at   TIMESTAMPTZ          -- NULL = não expira
);

-- Perfil comportamental consolidado (1:1 com user)
CREATE TABLE vendor_profiles (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id              UUID NOT NULL UNIQUE REFERENCES users(id),
  top_products         JSONB,   -- [{product_id, win_rate, count}]
  avoid_products       JSONB,
  preferred_sectors    JSONB,
  deal_size_sweet_spot JSONB,   -- {min, max}
  avg_cycle_days       DECIMAL(5,2),
  risk_tolerance       DECIMAL(3,2),  -- 0=conservador, 1=arrojado
  follow_up_rate       DECIMAL(3,2),  -- taxa de ação após alertas
  peak_usage_day       VARCHAR(20),
  common_queries       JSONB,
  updated_at           TIMESTAMPTZ DEFAULT NOW()
);

-- ─── IMPORT / DATA MANAGEMENT ────────────────────────────────

CREATE TYPE import_status AS ENUM ('pending', 'validating', 'preview', 'importing', 'done', 'failed', 'rolled_back');
CREATE TYPE import_source_type AS ENUM ('deals', 'accounts', 'products', 'team');

CREATE TABLE data_imports (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  uploaded_by      UUID NOT NULL REFERENCES users(id),
  source_type      import_source_type NOT NULL,
  filename         VARCHAR(300) NOT NULL,
  file_size_bytes  BIGINT,
  status           import_status NOT NULL DEFAULT 'pending',
  
  -- resultado da validação
  validation_errors JSONB,   -- [{row, field, error}]
  
  -- preview do diff
  rows_total       INT,
  rows_inserted    INT DEFAULT 0,
  rows_updated     INT DEFAULT 0,
  rows_skipped     INT DEFAULT 0,
  
  -- rollback: guarda snapshot do estado anterior
  snapshot_table   VARCHAR(100),  -- nome da tabela de snapshot
  
  error_message    TEXT,
  started_at       TIMESTAMPTZ,
  finished_at      TIMESTAMPTZ,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Lógica de upload e import

### Fluxo completo

```
1. Manager faz upload do CSV
         ↓
2. Backend salva arquivo temporariamente
   Cria registro em data_imports (status: 'pending')
         ↓
3. Validação (status: 'validating')
   - Colunas obrigatórias presentes?
   - Tipos de dados corretos?
   - Referências cruzadas válidas? (product existe? agent existe?)
   → Se inválido: status 'failed' + validation_errors preenchido
   → Frontend exibe erros linha a linha
         ↓
4. Geração do diff / preview (status: 'preview')
   - Compara com dados atuais no banco
   - Calcula: rows_inserted, rows_updated, rows_skipped
   - Retorna resumo pro frontend
   → Frontend exibe: "312 deals novos · 47 atualizados · 8 ignorados"
   → Manager confirma ou cancela
         ↓
5. Snapshot (antes de alterar qualquer dado)
   - Copia tabela atual para tabela de backup:
     deals_snapshot_{import_id}
   - Registra nome da tabela em data_imports.snapshot_table
         ↓
6. Import (status: 'importing')
   - Upsert por opportunity_id / external_id
   - Normalização de dados sujos durante import:
       "technolgy" → "technology"
       "GTXPro"    → "GTX Pro"
   - Tudo dentro de uma transaction
   → Se falhar: rollback automático, status 'failed'
         ↓
7. Pós-import (status: 'done')
   - Recalcula scores de todos os deals afetados
   - Gera alertas para vendedores com deals novos ou atualizados
   - Limpa arquivo temporário
```

---

### Validação por tipo de arquivo

```
DEALS (sales_pipeline.csv)
  Obrigatórios: opportunity_id, sales_agent, product, deal_stage
  Opcionais:    account, engage_date, close_date, close_value
  Regras:       deal_stage ∈ {Prospecting, Engaging, Won, Lost}
                close_date e close_value obrigatórios se Won ou Lost
                engage_date obrigatório se Engaging, Won ou Lost

ACCOUNTS (accounts.csv)
  Obrigatórios: account
  Opcionais:    sector, year_established, revenue, employees, office_location, subsidiary_of
  Regras:       revenue ≥ 0 se presente

PRODUCTS (products.csv)
  Obrigatórios: product, sales_price
  Opcionais:    series
  Regras:       sales_price > 0

TEAM (sales_teams.csv)
  Obrigatórios: sales_agent, manager, regional_office
  Regras:       nenhum campo nulo aceito
```

---

### Rollback

O manager pode reverter qualquer import bem-sucedido:

```
GET  /api/imports                → lista histórico de imports
POST /api/imports/:id/rollback   → reverte para snapshot anterior
```

O rollback trunca a tabela atual e restaura a partir de `snapshot_table`.
Após rollback, recalcula scores novamente.

---

## Scoring Engine

Cada deal ativo recebe um score 0–100 composto por 5 fatores:

```
FATOR                PESO    LÓGICA
────────────────────────────────────────────────────────
timing               30%     dias no pipeline vs ciclo médio do produto
                             → ideal: entre 50%-100% do ciclo médio Won
                             → decay progressivo acima de 2x ciclo Lost

stage                20%     Engaging = 100pts | Prospecting = 40pts

win_rate_product     20%     win rate histórico do produto (normalizado)

win_rate_agent       20%     win rate histórico do vendedor nesse stage

account_fit          10%     revenue da conta normalizado pela média
                             + boost se setor tem win rate acima da média
────────────────────────────────────────────────────────
TOTAL                100%

LABELS:
  85-100 → hot    (gold)
  70-84  → warm   (green)
  41-69  → cold   (amber)
  0-40   → zombie (red)
```

O campo `reasons` do `deal_scores` é um array gerado durante o cálculo:

```json
{
  "score": 82,
  "label": "warm",
  "reasons": [
    "✓ Deal no dia 38 — dentro da janela ideal (ciclo médio: 52 dias)",
    "✓ GTX Plus Pro tem 64% de win rate histórico",
    "✓ Sua taxa de conversão nesse stage é 68%",
    "⚠ Conta sem histórico de revenue registrado"
  ],
  "factors": {
    "timing": { "score": 88, "weight": 0.30 },
    "stage":  { "score": 100, "weight": 0.20 },
    "win_rate_product": { "score": 72, "weight": 0.20 },
    "win_rate_agent":   { "score": 80, "weight": 0.20 },
    "account_fit":      { "score": 50, "weight": 0.10 }
  }
}
```

---

## ReAct Agent — Tools disponíveis

```go
type DataConnector interface {
    FetchDeals(agentID string, filters DealFilters) ([]Deal, error)
    FetchDealDetail(dealID string)                  (DealDetail, error)
    FetchAgentStats(agentID string)                 (AgentStats, error)
    FetchTeamStats(managerID string)                (TeamStats, error)
}

// Tools expostas ao agente LLM:
get_my_deals(stage?, label?, limit?)
get_deal_detail(deal_id)
get_hot_deals(limit?)
get_at_risk_deals(limit?)
get_agent_stats()
compare_deal_to_avg(deal_id)
search_deals(query)         // busca por nome de conta ou produto
```

Cada tool retorna dados estruturados. O LLM sintetiza em linguagem natural com contexto do `vendor_profile` do vendedor.

---

## Endpoints da API

```
AUTH
POST   /api/auth/login
POST   /api/auth/refresh

ME
GET    /api/me
GET    /api/me/stats
GET    /api/me/profile

DEALS
GET    /api/deals              ?stage=&label=&limit=&offset=
GET    /api/deals/:id
GET    /api/deals/:id/score

ALERTS
GET    /api/alerts
PATCH  /api/alerts/:id/read
DELETE /api/alerts/:id

CHAT
GET    /api/conversations
POST   /api/conversations
POST   /api/conversations/:id/messages    (stream SSE)

MANAGER
GET    /api/team/stats
GET    /api/team/deals
GET    /api/team/agents

DATA MANAGEMENT (manager only)
GET    /api/imports
POST   /api/imports/upload     multipart/form-data
GET    /api/imports/:id/preview
POST   /api/imports/:id/confirm
POST   /api/imports/:id/rollback
DELETE /api/imports/:id/cancel
```

---

## Jobs assíncronos (scheduler)

```
CRON                    JOB
──────────────────────────────────────────────────────
Toda hora              recalculate_scores()
                        → recalcula deals modificados nas últimas 2h

Todo dia às 07:00      daily_briefing()
                        → gera alert 'weekly_briefing' pra cada vendedor

Todo domingo às 18:00  consolidate_memories()
                        → LLM analisa conversas da semana
                        → extrai agent_memories novas
                        → atualiza vendor_profiles

A cada 6 horas         detect_at_risk_deals()
                        → deals que cruzaram threshold de risco
                        → gera alerts 'stale_deal' e 'hot_window'

Após cada import       post_import_pipeline()
                        → recalcula scores dos deals afetados
                        → gera alerts para vendedores impactados
```

*Versão: 1.0 — MVP | Março 2026*
