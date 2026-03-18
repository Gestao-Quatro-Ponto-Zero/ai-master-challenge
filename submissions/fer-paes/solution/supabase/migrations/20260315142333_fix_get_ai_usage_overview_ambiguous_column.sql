/*
  # Fix ambiguous column reference in get_ai_usage_overview

  ## Problem
  The RETURNS TABLE declaration for `get_ai_usage_overview` defines a column named
  `total_tokens`, which conflicts with the same column name in `llm_token_usage`
  inside the function body subquery, causing PostgreSQL to raise an ambiguous
  column reference error.

  ## Fix
  Recreate the function using an explicit table alias `t` for all column
  references inside `llm_token_usage`, eliminating any ambiguity.
*/

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
    (SELECT COUNT(*)::bigint                    FROM llm_requests r    WHERE r.created_at BETWEEN from_ts AND to_ts)                                     AS total_requests,
    (SELECT COALESCE(SUM(t.total_tokens),0)::bigint FROM llm_token_usage t WHERE t.created_at BETWEEN from_ts AND to_ts)                                 AS total_tokens,
    (SELECT COALESCE(SUM(c.total_cost),  0)         FROM llm_costs c        WHERE c.created_at BETWEEN from_ts AND to_ts)                                AS total_cost,
    (SELECT COALESCE(AVG(r2.latency_ms), 0)         FROM llm_requests r2   WHERE r2.created_at BETWEEN from_ts AND to_ts AND r2.status = 'success')      AS avg_latency_ms,
    (SELECT COUNT(*)::bigint                    FROM llm_requests r3   WHERE r3.created_at BETWEEN from_ts AND to_ts AND r3.status = 'error')             AS error_count,
    (SELECT COUNT(*)::bigint                    FROM llm_requests r4   WHERE r4.created_at BETWEEN from_ts AND to_ts AND (r4.metadata->>'fallback')::boolean IS TRUE) AS fallback_count;
END;
$$;
