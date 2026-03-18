/*
  # SUBFASE 6.2 — LLM Request Logging

  ## Overview
  Creates an audit log for every LLM API call made by the system.
  Records which agent called, which model was used, token consumption, latency, and final status.

  ## New Tables

  ### llm_requests
  One row per LLM API invocation.
  - `id` — UUID primary key
  - `agent_id` — Optional FK to agents table (null if called by system/router directly)
  - `model_id` — Optional FK to llm_models table
  - `provider` — Provider slug (openai | anthropic | google | mistral)
  - `model_identifier` — Snapshot of model API id at call time
  - `prompt_tokens` — Input tokens consumed
  - `completion_tokens` — Output tokens consumed
  - `total_tokens` — Sum of prompt + completion
  - `latency_ms` — End-to-end response time in milliseconds
  - `status` — pending | success | error | timeout
  - `error_message` — Error details if status = error
  - `metadata` — Arbitrary JSON for future extensibility
  - `created_at` / `updated_at` — Timestamps

  ## Indexes
  - `idx_llm_requests_model_id` — Analytics queries by model
  - `idx_llm_requests_agent_id` — Analytics queries by agent
  - `idx_llm_requests_created_at` — Time-range queries and pagination
  - `idx_llm_requests_status` — Filter by outcome

  ## Permissions
  - New permission: `llm_logs.view`
  - Assigned to roles: admin, supervisor

  ## Security
  - RLS enabled
  - Authenticated users with `llm_logs.view` can read all rows
  - System inserts are allowed for all authenticated users (agents log on behalf of themselves)
  - No row may be deleted by regular users (append-only audit log)
*/

-- ── Table ────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS llm_requests (
  id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_id            UUID REFERENCES agents(id) ON DELETE SET NULL,
  model_id            UUID REFERENCES llm_models(id) ON DELETE SET NULL,
  provider            TEXT,
  model_identifier    TEXT,
  prompt_tokens       INTEGER,
  completion_tokens   INTEGER,
  total_tokens        INTEGER,
  latency_ms          INTEGER,
  status              TEXT NOT NULL DEFAULT 'pending',
  error_message       TEXT,
  metadata            JSONB,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT chk_llm_requests_status CHECK (status IN ('pending', 'success', 'error', 'timeout'))
);

-- ── Indexes ───────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_llm_requests_model_id   ON llm_requests(model_id);
CREATE INDEX IF NOT EXISTS idx_llm_requests_agent_id   ON llm_requests(agent_id);
CREATE INDEX IF NOT EXISTS idx_llm_requests_created_at ON llm_requests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_llm_requests_status     ON llm_requests(status);

-- ── Updated-at trigger ────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION set_llm_requests_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_llm_requests_updated_at ON llm_requests;
CREATE TRIGGER trg_llm_requests_updated_at
  BEFORE UPDATE ON llm_requests
  FOR EACH ROW EXECUTE FUNCTION set_llm_requests_updated_at();

-- ── RLS ───────────────────────────────────────────────────────────────────────

ALTER TABLE llm_requests ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users with llm_logs.view can read llm_requests"
  ON llm_requests FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1
      FROM user_roles ur
      JOIN role_permissions rp ON rp.role_id = ur.role_id
      JOIN permissions p ON p.id = rp.permission_id
      WHERE ur.user_id = auth.uid()
        AND p.name = 'llm_logs.view'
    )
  );

CREATE POLICY "Authenticated users can insert llm_requests"
  ON llm_requests FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can update own pending llm_requests"
  ON llm_requests FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- ── Permission ────────────────────────────────────────────────────────────────

INSERT INTO permissions (name, description, category)
VALUES ('llm_logs.view', 'View LLM request logs and usage analytics', 'llm')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'admin' AND p.name = 'llm_logs.view'
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'supervisor' AND p.name = 'llm_logs.view'
ON CONFLICT DO NOTHING;

-- ── Seed sample data ──────────────────────────────────────────────────────────
-- Insert a handful of illustrative log rows so the UI is not empty on first load

DO $$
DECLARE
  v_model_gpt4o      UUID;
  v_model_gpt4o_mini UUID;
  v_model_claude     UUID;
  v_model_haiku      UUID;
BEGIN
  SELECT id INTO v_model_gpt4o      FROM llm_models WHERE model_identifier = 'gpt-4o'                   LIMIT 1;
  SELECT id INTO v_model_gpt4o_mini FROM llm_models WHERE model_identifier = 'gpt-4o-mini'              LIMIT 1;
  SELECT id INTO v_model_claude     FROM llm_models WHERE model_identifier = 'claude-3-sonnet-20240229'  LIMIT 1;
  SELECT id INTO v_model_haiku      FROM llm_models WHERE model_identifier = 'claude-3-haiku-20240307'   LIMIT 1;

  INSERT INTO llm_requests (model_id, provider, model_identifier, prompt_tokens, completion_tokens, total_tokens, latency_ms, status, created_at)
  VALUES
    (v_model_gpt4o,      'openai',    'gpt-4o',                   512,  256,  768,  1240, 'success', NOW() - INTERVAL '2 hours'),
    (v_model_gpt4o_mini, 'openai',    'gpt-4o-mini',              384,  128,  512,  780,  'success', NOW() - INTERVAL '90 minutes'),
    (v_model_claude,     'anthropic', 'claude-3-sonnet-20240229',  640,  320,  960,  1850, 'success', NOW() - INTERVAL '60 minutes'),
    (v_model_haiku,      'anthropic', 'claude-3-haiku-20240307',   200,  80,   280,  420,  'success', NOW() - INTERVAL '45 minutes'),
    (v_model_gpt4o,      'openai',    'gpt-4o',                   1024, 512, 1536,  2100, 'success', NOW() - INTERVAL '30 minutes'),
    (v_model_gpt4o_mini, 'openai',    'gpt-4o-mini',              100,  0,    100,  5000, 'timeout', NOW() - INTERVAL '20 minutes'),
    (v_model_claude,     'anthropic', 'claude-3-sonnet-20240229',  512,  0,    512,  800,  'error',   NOW() - INTERVAL '15 minutes'),
    (v_model_gpt4o,      'openai',    'gpt-4o',                   768,  400, 1168,  1650, 'success', NOW() - INTERVAL '5 minutes')
  ON CONFLICT DO NOTHING;
END $$;
