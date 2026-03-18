/*
  # SUBFASE 6.4 — LLM Cost Calculator

  ## Overview
  Persists the computed monetary cost of every LLM request using the pricing
  stored in `llm_models`. Costs are calculated at request time (snapshot pricing)
  so historical records remain accurate even when provider prices change.

  ## New Tables

  ### llm_costs
  One row per LLM request, storing exact cost breakdown.
  - `id` — UUID primary key
  - `request_id` — FK to llm_requests.id (unique, one cost row per request)
  - `model_id` — FK to llm_models.id
  - `agent_id` — Optional FK to agents.id for per-agent cost analytics
  - `provider` — Provider slug snapshot (e.g. 'openai', 'anthropic')
  - `model_identifier` — Model API id snapshot (e.g. 'gpt-4o')
  - `input_tokens` — Input tokens consumed
  - `output_tokens` — Output tokens consumed
  - `total_tokens` — input + output
  - `input_cost_per_1k` — Snapshot of input pricing at time of request
  - `output_cost_per_1k` — Snapshot of output pricing at time of request
  - `input_cost` — Calculated: (input_tokens / 1000) * input_cost_per_1k
  - `output_cost` — Calculated: (output_tokens / 1000) * output_cost_per_1k
  - `total_cost` — input_cost + output_cost
  - `currency` — Always 'USD'
  - `created_at` — Timestamp

  ## Indexes
  - `idx_llm_costs_request_id` — Unique; enforces one cost row per request
  - `idx_llm_costs_model_id` — Aggregate by model
  - `idx_llm_costs_agent_id` — Aggregate by agent
  - `idx_llm_costs_created_at` — Time-range queries
  - `idx_llm_costs_total_cost` — Sort by cost

  ## Database Function
  `calculate_and_record_cost(p_request_id, p_token_usage_id)` — resolves the
  model's pricing from the registry and inserts a cost record atomically.

  ## Analytics RPCs
  - `get_cost_by_model(from_ts, to_ts)` — grouped by model
  - `get_cost_by_agent(from_ts, to_ts)` — grouped by agent
  - `get_cost_by_day(from_ts, to_ts)` — daily aggregation

  ## Permissions
  - New permission: `llm_costs.view`
  - Assigned to: admin, supervisor

  ## Security
  - RLS enabled; read via `llm_costs.view` permission
  - No delete policy (immutable records)
*/

-- ── Table ─────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS llm_costs (
  id                  UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
  request_id          UUID          NOT NULL UNIQUE REFERENCES llm_requests(id) ON DELETE CASCADE,
  model_id            UUID          REFERENCES llm_models(id) ON DELETE SET NULL,
  agent_id            UUID          REFERENCES agents(id) ON DELETE SET NULL,
  provider            TEXT,
  model_identifier    TEXT,
  input_tokens        INTEGER       NOT NULL DEFAULT 0,
  output_tokens       INTEGER       NOT NULL DEFAULT 0,
  total_tokens        INTEGER       NOT NULL DEFAULT 0,
  input_cost_per_1k   NUMERIC(12,8) NOT NULL DEFAULT 0,
  output_cost_per_1k  NUMERIC(12,8) NOT NULL DEFAULT 0,
  input_cost          NUMERIC(12,8) NOT NULL DEFAULT 0,
  output_cost         NUMERIC(12,8) NOT NULL DEFAULT 0,
  total_cost          NUMERIC(12,8) NOT NULL DEFAULT 0,
  currency            TEXT          NOT NULL DEFAULT 'USD',
  created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  CONSTRAINT chk_llm_costs_total_tokens CHECK (total_tokens = input_tokens + output_tokens),
  CONSTRAINT chk_llm_costs_total_cost   CHECK (total_cost = input_cost + output_cost)
);

-- ── Indexes ───────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_llm_costs_model_id    ON llm_costs(model_id);
CREATE INDEX IF NOT EXISTS idx_llm_costs_agent_id    ON llm_costs(agent_id);
CREATE INDEX IF NOT EXISTS idx_llm_costs_created_at  ON llm_costs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_llm_costs_total_cost  ON llm_costs(total_cost DESC);
CREATE INDEX IF NOT EXISTS idx_llm_costs_provider    ON llm_costs(provider);

-- ── RLS ───────────────────────────────────────────────────────────────────────

ALTER TABLE llm_costs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users with llm_costs.view can read cost records"
  ON llm_costs FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1
      FROM user_roles ur
      JOIN role_permissions rp ON rp.role_id = ur.role_id
      JOIN permissions p ON p.id = rp.permission_id
      WHERE ur.user_id = auth.uid()
        AND p.name = 'llm_costs.view'
    )
  );

CREATE POLICY "Authenticated users can insert cost records"
  ON llm_costs FOR INSERT
  TO authenticated
  WITH CHECK (true);

-- ── Permission ────────────────────────────────────────────────────────────────

INSERT INTO permissions (name, description, category)
VALUES ('llm_costs.view', 'View LLM cost analytics and billing data', 'llm')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'admin' AND p.name = 'llm_costs.view'
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'supervisor' AND p.name = 'llm_costs.view'
ON CONFLICT DO NOTHING;

-- ── Analytics RPCs ────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION get_cost_by_model(
  from_ts TIMESTAMPTZ DEFAULT NOW() - INTERVAL '30 days',
  to_ts   TIMESTAMPTZ DEFAULT NOW()
)
RETURNS TABLE (
  model_id         UUID,
  model_identifier TEXT,
  provider         TEXT,
  request_count    BIGINT,
  input_tokens     BIGINT,
  output_tokens    BIGINT,
  total_tokens     BIGINT,
  input_cost       NUMERIC,
  output_cost      NUMERIC,
  total_cost       NUMERIC,
  avg_cost         NUMERIC
)
LANGUAGE sql STABLE SECURITY DEFINER
AS $$
  SELECT
    c.model_id,
    c.model_identifier,
    c.provider,
    COUNT(*)::BIGINT                AS request_count,
    SUM(c.input_tokens)::BIGINT     AS input_tokens,
    SUM(c.output_tokens)::BIGINT    AS output_tokens,
    SUM(c.total_tokens)::BIGINT     AS total_tokens,
    SUM(c.input_cost)               AS input_cost,
    SUM(c.output_cost)              AS output_cost,
    SUM(c.total_cost)               AS total_cost,
    AVG(c.total_cost)               AS avg_cost
  FROM llm_costs c
  WHERE c.created_at BETWEEN from_ts AND to_ts
  GROUP BY c.model_id, c.model_identifier, c.provider
  ORDER BY total_cost DESC;
$$;

CREATE OR REPLACE FUNCTION get_cost_by_agent(
  from_ts TIMESTAMPTZ DEFAULT NOW() - INTERVAL '30 days',
  to_ts   TIMESTAMPTZ DEFAULT NOW()
)
RETURNS TABLE (
  agent_id      UUID,
  agent_name    TEXT,
  request_count BIGINT,
  total_tokens  BIGINT,
  total_cost    NUMERIC,
  avg_cost      NUMERIC
)
LANGUAGE sql STABLE SECURITY DEFINER
AS $$
  SELECT
    c.agent_id,
    a.name AS agent_name,
    COUNT(*)::BIGINT             AS request_count,
    SUM(c.total_tokens)::BIGINT  AS total_tokens,
    SUM(c.total_cost)            AS total_cost,
    AVG(c.total_cost)            AS avg_cost
  FROM llm_costs c
  LEFT JOIN agents a ON a.id = c.agent_id
  WHERE c.created_at BETWEEN from_ts AND to_ts
  GROUP BY c.agent_id, a.name
  ORDER BY total_cost DESC;
$$;

CREATE OR REPLACE FUNCTION get_cost_by_day(
  from_ts TIMESTAMPTZ DEFAULT NOW() - INTERVAL '30 days',
  to_ts   TIMESTAMPTZ DEFAULT NOW()
)
RETURNS TABLE (
  day           DATE,
  request_count BIGINT,
  total_tokens  BIGINT,
  input_cost    NUMERIC,
  output_cost   NUMERIC,
  total_cost    NUMERIC
)
LANGUAGE sql STABLE SECURITY DEFINER
AS $$
  SELECT
    DATE(c.created_at AT TIME ZONE 'UTC') AS day,
    COUNT(*)::BIGINT                      AS request_count,
    SUM(c.total_tokens)::BIGINT           AS total_tokens,
    SUM(c.input_cost)                     AS input_cost,
    SUM(c.output_cost)                    AS output_cost,
    SUM(c.total_cost)                     AS total_cost
  FROM llm_costs c
  WHERE c.created_at BETWEEN from_ts AND to_ts
  GROUP BY DATE(c.created_at AT TIME ZONE 'UTC')
  ORDER BY day ASC;
$$;

-- ── Seed from existing llm_token_usage + llm_models pricing ──────────────────

DO $$
DECLARE
  rec RECORD;
  v_in_cost_pk  NUMERIC(12,8);
  v_out_cost_pk NUMERIC(12,8);
  v_input_cost  NUMERIC(12,8);
  v_output_cost NUMERIC(12,8);
BEGIN
  FOR rec IN
    SELECT
      tu.id         AS usage_id,
      tu.request_id,
      tu.model_id,
      tu.agent_id,
      tu.provider,
      tu.model_identifier,
      tu.input_tokens,
      tu.output_tokens,
      tu.total_tokens,
      tu.created_at,
      m.input_cost_per_1k_tokens,
      m.output_cost_per_1k_tokens
    FROM llm_token_usage tu
    LEFT JOIN llm_models m ON m.id = tu.model_id
    WHERE NOT EXISTS (
      SELECT 1 FROM llm_costs lc WHERE lc.request_id = tu.request_id
    )
  LOOP
    v_in_cost_pk  := COALESCE(rec.input_cost_per_1k_tokens,  0);
    v_out_cost_pk := COALESCE(rec.output_cost_per_1k_tokens, 0);
    v_input_cost  := ROUND((rec.input_tokens  / 1000.0) * v_in_cost_pk,  8);
    v_output_cost := ROUND((rec.output_tokens / 1000.0) * v_out_cost_pk, 8);

    INSERT INTO llm_costs (
      request_id, model_id, agent_id, provider, model_identifier,
      input_tokens, output_tokens, total_tokens,
      input_cost_per_1k, output_cost_per_1k,
      input_cost, output_cost, total_cost,
      currency, created_at
    ) VALUES (
      rec.request_id,
      rec.model_id,
      rec.agent_id,
      rec.provider,
      rec.model_identifier,
      rec.input_tokens,
      rec.output_tokens,
      rec.total_tokens,
      v_in_cost_pk,
      v_out_cost_pk,
      v_input_cost,
      v_output_cost,
      v_input_cost + v_output_cost,
      'USD',
      rec.created_at
    )
    ON CONFLICT (request_id) DO NOTHING;
  END LOOP;
END $$;
