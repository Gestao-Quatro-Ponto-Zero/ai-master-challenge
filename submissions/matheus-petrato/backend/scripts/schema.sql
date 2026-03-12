-- G4 Compass Schema

-- Enable UUID extension (though we'll use v7 from app, it's good for defaults)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── VENDEDORES / TIME ───────────────────────────────────────

CREATE TABLE IF NOT EXISTS regional_offices (
  id         UUID PRIMARY KEY,
  name       VARCHAR(100) NOT NULL UNIQUE,  -- 'Central', 'East', 'West'
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS managers (
  id              UUID PRIMARY KEY,
  name            VARCHAR(200) NOT NULL,
  regional_office_id UUID REFERENCES regional_offices(id),
  external_id     VARCHAR(100),           -- ID no CRM futuro
  source          VARCHAR(50) DEFAULT 'csv',
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sales_agents (
  id              UUID PRIMARY KEY,
  name            VARCHAR(200) NOT NULL,
  manager_id      UUID REFERENCES managers(id),
  regional_office_id UUID REFERENCES regional_offices(id),
  external_id     VARCHAR(100),
  source          VARCHAR(50) DEFAULT 'csv',
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─── CONTAS ──────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS accounts (
  id               UUID PRIMARY KEY,
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

CREATE TABLE IF NOT EXISTS products (
  id          UUID PRIMARY KEY,
  name        VARCHAR(200) NOT NULL UNIQUE,
  series      VARCHAR(100),
  sales_price DECIMAL(10,2),
  external_id VARCHAR(100),
  source      VARCHAR(50) DEFAULT 'csv',
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── DEALS (pipeline) ────────────────────────────────────────

DO $$ BEGIN
    CREATE TYPE deal_stage AS ENUM ('Prospecting', 'Engaging', 'Won', 'Lost');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS deals (
  id              UUID PRIMARY KEY,
  opportunity_id  VARCHAR(50) NOT NULL UNIQUE,  -- ID original do CSV
  sales_agent_id  UUID REFERENCES sales_agents(id),
  product_id      UUID REFERENCES products(id),
  account_id      UUID REFERENCES accounts(id), -- nullable
  stage           deal_stage NOT NULL,
  engage_date     DATE,                          -- nullable
  close_date      DATE,                          -- nullable
  close_value     DECIMAL(10,2),                 -- nullable
  external_id     VARCHAR(100),
  source          VARCHAR(50) DEFAULT 'csv',
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─── AUTH ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS users (
  id             UUID PRIMARY KEY,
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

CREATE TABLE IF NOT EXISTS deal_scores (
  id          UUID PRIMARY KEY,
  deal_id     UUID NOT NULL REFERENCES deals(id),
  score       SMALLINT NOT NULL CHECK (score BETWEEN 0 AND 100),
  label       VARCHAR(20) NOT NULL,  -- 'hot' | 'warm' | 'cold' | 'zombie'
  reasons     JSONB NOT NULL,        -- array de strings
  factors     JSONB NOT NULL,        -- breakdown
  calculated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(deal_id)
);

CREATE TABLE IF NOT EXISTS deal_score_history (
  id            UUID PRIMARY KEY,
  deal_id       UUID NOT NULL REFERENCES deals(id),
  score         SMALLINT NOT NULL,
  label         VARCHAR(20) NOT NULL,
  calculated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── ALERTAS ─────────────────────────────────────────────────

DO $$ BEGIN
    CREATE TYPE alert_type AS ENUM (
      'hot_window',
      'stale_deal',
      'weekly_briefing',
      'score_drop',
      'new_opportunity'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS alerts (
  id             UUID PRIMARY KEY,
  user_id        UUID NOT NULL REFERENCES users(id),
  deal_id        UUID REFERENCES deals(id),
  type           alert_type NOT NULL,
  title          VARCHAR(200) NOT NULL,
  body           TEXT NOT NULL,
  read_at        TIMESTAMPTZ,
  action_url     VARCHAR(500),
  created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- ─── CONVERSAS DO AGENTE ─────────────────────────────────────

CREATE TABLE IF NOT EXISTS conversations (
  id         UUID PRIMARY KEY,
  user_id    UUID NOT NULL REFERENCES users(id),
  context    JSONB,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  ended_at   TIMESTAMPTZ
);

DO $$ BEGIN
    CREATE TYPE message_role AS ENUM ('user', 'assistant', 'tool');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS messages (
  id              UUID PRIMARY KEY,
  conversation_id UUID NOT NULL REFERENCES conversations(id),
  role            message_role NOT NULL,
  content         TEXT NOT NULL,
  tool_name       VARCHAR(100),
  tool_input      JSONB,
  tool_result     JSONB,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─── MEMÓRIA DO AGENTE ───────────────────────────────────────

DO $$ BEGIN
    CREATE TYPE memory_type AS ENUM ('preference', 'pattern', 'fact', 'feedback');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE memory_source AS ENUM ('conversation', 'behavior', 'system');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS agent_memories (
  id           UUID PRIMARY KEY,
  user_id      UUID NOT NULL REFERENCES users(id),
  type         memory_type NOT NULL,
  content      TEXT NOT NULL,
  source       memory_source NOT NULL,
  confidence   DECIMAL(3,2) DEFAULT 0.5 CHECK (confidence BETWEEN 0 AND 1),
  observed_at  TIMESTAMPTZ DEFAULT NOW(),
  expires_at   TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS vendor_profiles (
  id                   UUID PRIMARY KEY,
  user_id              UUID NOT NULL UNIQUE REFERENCES users(id),
  top_products         JSONB,
  avoid_products       JSONB,
  preferred_sectors    JSONB,
  deal_size_sweet_spot JSONB,
  avg_cycle_days       DECIMAL(5,2),
  risk_tolerance       DECIMAL(3,2),
  follow_up_rate       DECIMAL(3,2),
  peak_usage_day       VARCHAR(20),
  common_queries       JSONB,
  updated_at           TIMESTAMPTZ DEFAULT NOW()
);

-- ─── IMPORT / DATA MANAGEMENT ────────────────────────────────

DO $$ BEGIN
    CREATE TYPE import_status AS ENUM ('pending', 'validating', 'preview', 'importing', 'done', 'failed', 'rolled_back');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE import_source_type AS ENUM ('deals', 'accounts', 'products', 'team');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS data_imports (
  id               UUID PRIMARY KEY,
  uploaded_by      UUID NOT NULL REFERENCES users(id),
  source_type      import_source_type NOT NULL,
  filename         VARCHAR(300) NOT NULL,
  file_size_bytes  BIGINT,
  status           import_status NOT NULL DEFAULT 'pending',
  validation_errors JSONB,
  rows_total       INT,
  rows_inserted    INT DEFAULT 0,
  rows_updated     INT DEFAULT 0,
  rows_skipped     INT DEFAULT 0,
  snapshot_table   VARCHAR(100),
  error_message    TEXT,
  started_at       TIMESTAMPTZ,
  finished_at      TIMESTAMPTZ,
  created_at       TIMESTAMPTZ DEFAULT NOW()
);
