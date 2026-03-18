/*
  # AI Usage Dashboard — SUBFASE 6.8

  ## Overview
  Adds the analytics layer required by the AI Usage Dashboard. No new tables
  are created; all metrics are derived from existing tables:
    - llm_requests       — request counts, latency
    - llm_token_usage    — token breakdown
    - llm_costs          — spend breakdown
    - llm_models         — model metadata
    - llm_budgets        — active budget status

  ## New Permission
  - `ai_usage.view` — allows reading the AI usage dashboard
    Assigned to: admin, supervisor

  ## New RPC
  - `get_ai_usage_overview(from_ts, to_ts)` — returns a single JSON row with:
      total_requests   INTEGER   — number of llm_requests in the window
      total_tokens     BIGINT    — sum of total_tokens from llm_token_usage
      total_cost       FLOAT8    — sum of total_cost from llm_costs
      avg_latency_ms   FLOAT8    — average latency_ms from llm_requests (success only)
      error_count      INTEGER   — requests with status = 'error'
      fallback_count   INTEGER   — requests that used a fallback provider
*/

-- ── Permission ────────────────────────────────────────────────────────────────

INSERT INTO permissions (name, description, category)
VALUES ('ai_usage.view', 'View the AI usage analytics dashboard', 'llm')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'admin' AND p.name = 'ai_usage.view'
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'supervisor' AND p.name = 'ai_usage.view'
ON CONFLICT DO NOTHING;

-- ── RPC: get_ai_usage_overview ────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION get_ai_usage_overview(
  from_ts timestamptz DEFAULT now() - interval '30 days',
  to_ts   timestamptz DEFAULT now()
)
RETURNS TABLE (
  total_requests  bigint,
  total_tokens    bigint,
  total_cost      float8,
  avg_latency_ms  float8,
  error_count     bigint,
  fallback_count  bigint
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  RETURN QUERY
  SELECT
    (SELECT COUNT(*)::bigint                FROM llm_requests    WHERE created_at BETWEEN from_ts AND to_ts)                          AS total_requests,
    (SELECT COALESCE(SUM(total_tokens), 0)::bigint FROM llm_token_usage WHERE created_at BETWEEN from_ts AND to_ts)                   AS total_tokens,
    (SELECT COALESCE(SUM(total_cost),   0)         FROM llm_costs        WHERE created_at BETWEEN from_ts AND to_ts)                  AS total_cost,
    (SELECT COALESCE(AVG(latency_ms),   0)         FROM llm_requests     WHERE created_at BETWEEN from_ts AND to_ts AND status = 'success') AS avg_latency_ms,
    (SELECT COUNT(*)::bigint                FROM llm_requests    WHERE created_at BETWEEN from_ts AND to_ts AND status = 'error')     AS error_count,
    (SELECT COUNT(*)::bigint                FROM llm_requests    WHERE created_at BETWEEN from_ts AND to_ts AND (metadata->>'fallback')::boolean IS TRUE) AS fallback_count;
END;
$$;
