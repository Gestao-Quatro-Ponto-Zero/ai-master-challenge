/*
  # SUBFASE 6.3 — Token Usage Tracking

  ## Overview
  Creates a dedicated token usage table that stores granular token consumption data
  for every LLM API call. This table is the foundation for cost calculation,
  budget management, and AI usage analytics.

  ## New Tables

  ### llm_token_usage
  One row per LLM request response, recording exact token breakdown.
  - `id` — UUID primary key
  - `request_id` — FK to llm_requests.id (the originating request)
  - `model_id` — FK to llm_models.id (which model consumed the tokens)
  - `agent_id` — Optional FK to agents.id for per-agent analytics
  - `provider` — Snapshot of provider slug at recording time
  - `model_identifier` — Snapshot of model API id at recording time
  - `input_tokens` — Tokens sent in the prompt (prompt_tokens / input_tokens by provider)
  - `output_tokens` — Tokens generated in the response (completion_tokens)
  - `total_tokens` — input_tokens + output_tokens
  - `created_at` — Timestamp of recording

  ## Indexes
  - `idx_llm_token_usage_request_id` — Join with llm_requests
  - `idx_llm_token_usage_model_id` — Aggregate by model
  - `idx_llm_token_usage_agent_id` — Aggregate by agent
  - `idx_llm_token_usage_created_at` — Time-range queries
  - `idx_llm_token_usage_provider` — Filter by provider

  ## Permissions
  - New permission: `llm_usage.view`
  - Assigned to: admin, supervisor

  ## Security
  - RLS enabled — append-only for authenticated users, read restricted to `llm_usage.view` holders
  - No delete policy (records are immutable by design)

  ## Analytics RPCs
  - `get_token_usage_by_model(from_ts, to_ts)` — Aggregate tokens grouped by model
  - `get_token_usage_by_agent(from_ts, to_ts)` — Aggregate tokens grouped by agent
  - `get_token_usage_by_day(from_ts, to_ts)` — Daily aggregation for chart
*/

-- ── Table ─────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS llm_token_usage (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  request_id        UUID NOT NULL REFERENCES llm_requests(id) ON DELETE CASCADE,
  model_id          UUID REFERENCES llm_models(id) ON DELETE SET NULL,
  agent_id          UUID REFERENCES agents(id) ON DELETE SET NULL,
  provider          TEXT,
  model_identifier  TEXT,
  input_tokens      INTEGER NOT NULL DEFAULT 0,
  output_tokens     INTEGER NOT NULL DEFAULT 0,
  total_tokens      INTEGER NOT NULL DEFAULT 0,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT chk_llm_token_usage_total CHECK (total_tokens = input_tokens + output_tokens)
);

-- ── Indexes ───────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_llm_token_usage_request_id  ON llm_token_usage(request_id);
CREATE INDEX IF NOT EXISTS idx_llm_token_usage_model_id    ON llm_token_usage(model_id);
CREATE INDEX IF NOT EXISTS idx_llm_token_usage_agent_id    ON llm_token_usage(agent_id);
CREATE INDEX IF NOT EXISTS idx_llm_token_usage_created_at  ON llm_token_usage(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_llm_token_usage_provider    ON llm_token_usage(provider);

-- ── RLS ───────────────────────────────────────────────────────────────────────

ALTER TABLE llm_token_usage ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users with llm_usage.view can read token usage"
  ON llm_token_usage FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1
      FROM user_roles ur
      JOIN role_permissions rp ON rp.role_id = ur.role_id
      JOIN permissions p ON p.id = rp.permission_id
      WHERE ur.user_id = auth.uid()
        AND p.name = 'llm_usage.view'
    )
  );

CREATE POLICY "Authenticated users can insert token usage"
  ON llm_token_usage FOR INSERT
  TO authenticated
  WITH CHECK (true);

-- ── Permission ────────────────────────────────────────────────────────────────

INSERT INTO permissions (name, description, category)
VALUES ('llm_usage.view', 'View token usage analytics and consumption data', 'llm')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'admin' AND p.name = 'llm_usage.view'
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'supervisor' AND p.name = 'llm_usage.view'
ON CONFLICT DO NOTHING;

-- ── Analytics RPCs ────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION get_token_usage_by_model(
  from_ts TIMESTAMPTZ DEFAULT NOW() - INTERVAL '30 days',
  to_ts   TIMESTAMPTZ DEFAULT NOW()
)
RETURNS TABLE (
  model_id         UUID,
  model_identifier TEXT,
  provider         TEXT,
  input_tokens     BIGINT,
  output_tokens    BIGINT,
  total_tokens     BIGINT,
  request_count    BIGINT
)
LANGUAGE sql STABLE SECURITY DEFINER
AS $$
  SELECT
    t.model_id,
    t.model_identifier,
    t.provider,
    SUM(t.input_tokens)::BIGINT  AS input_tokens,
    SUM(t.output_tokens)::BIGINT AS output_tokens,
    SUM(t.total_tokens)::BIGINT  AS total_tokens,
    COUNT(*)::BIGINT             AS request_count
  FROM llm_token_usage t
  WHERE t.created_at BETWEEN from_ts AND to_ts
  GROUP BY t.model_id, t.model_identifier, t.provider
  ORDER BY total_tokens DESC;
$$;

CREATE OR REPLACE FUNCTION get_token_usage_by_agent(
  from_ts TIMESTAMPTZ DEFAULT NOW() - INTERVAL '30 days',
  to_ts   TIMESTAMPTZ DEFAULT NOW()
)
RETURNS TABLE (
  agent_id      UUID,
  agent_name    TEXT,
  input_tokens  BIGINT,
  output_tokens BIGINT,
  total_tokens  BIGINT,
  request_count BIGINT
)
LANGUAGE sql STABLE SECURITY DEFINER
AS $$
  SELECT
    t.agent_id,
    a.name AS agent_name,
    SUM(t.input_tokens)::BIGINT  AS input_tokens,
    SUM(t.output_tokens)::BIGINT AS output_tokens,
    SUM(t.total_tokens)::BIGINT  AS total_tokens,
    COUNT(*)::BIGINT             AS request_count
  FROM llm_token_usage t
  LEFT JOIN agents a ON a.id = t.agent_id
  WHERE t.created_at BETWEEN from_ts AND to_ts
  GROUP BY t.agent_id, a.name
  ORDER BY total_tokens DESC;
$$;

CREATE OR REPLACE FUNCTION get_token_usage_by_day(
  from_ts TIMESTAMPTZ DEFAULT NOW() - INTERVAL '30 days',
  to_ts   TIMESTAMPTZ DEFAULT NOW()
)
RETURNS TABLE (
  day           DATE,
  input_tokens  BIGINT,
  output_tokens BIGINT,
  total_tokens  BIGINT,
  request_count BIGINT
)
LANGUAGE sql STABLE SECURITY DEFINER
AS $$
  SELECT
    DATE(t.created_at AT TIME ZONE 'UTC')  AS day,
    SUM(t.input_tokens)::BIGINT            AS input_tokens,
    SUM(t.output_tokens)::BIGINT           AS output_tokens,
    SUM(t.total_tokens)::BIGINT            AS total_tokens,
    COUNT(*)::BIGINT                       AS request_count
  FROM llm_token_usage t
  WHERE t.created_at BETWEEN from_ts AND to_ts
  GROUP BY DATE(t.created_at AT TIME ZONE 'UTC')
  ORDER BY day ASC;
$$;

-- ── Seed data (sync from existing llm_requests) ───────────────────────────────

DO $$
DECLARE
  rec RECORD;
BEGIN
  FOR rec IN
    SELECT id, model_id, agent_id, provider, model_identifier,
           prompt_tokens, completion_tokens, total_tokens, created_at
    FROM llm_requests
    WHERE status = 'success'
      AND prompt_tokens IS NOT NULL
      AND completion_tokens IS NOT NULL
  LOOP
    INSERT INTO llm_token_usage (
      request_id, model_id, agent_id, provider, model_identifier,
      input_tokens, output_tokens, total_tokens, created_at
    ) VALUES (
      rec.id,
      rec.model_id,
      rec.agent_id,
      rec.provider,
      rec.model_identifier,
      rec.prompt_tokens,
      rec.completion_tokens,
      rec.total_tokens,
      rec.created_at
    )
    ON CONFLICT DO NOTHING;
  END LOOP;
END $$;
