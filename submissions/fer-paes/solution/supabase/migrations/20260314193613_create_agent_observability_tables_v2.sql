/*
  # Create Agent Observability Tables — Subfase 3.9 (v2)

  Same as v1 but uses DO blocks to safely skip duplicate RLS policies,
  and IF NOT EXISTS on all DDL. Safe to run on a fresh or existing database.
*/

CREATE TABLE IF NOT EXISTS agent_execution_logs (
  id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id         uuid        REFERENCES agents(id) ON DELETE SET NULL,
  run_id           uuid        REFERENCES agent_runs(id) ON DELETE CASCADE,
  ticket_id        uuid        REFERENCES tickets(id) ON DELETE SET NULL,
  conversation_id  uuid        REFERENCES conversations(id) ON DELETE SET NULL,
  model_provider   text        NOT NULL DEFAULT '',
  model_name       text        NOT NULL DEFAULT '',
  latency_ms       integer     NOT NULL DEFAULT 0,
  input_tokens     integer     NOT NULL DEFAULT 0,
  output_tokens    integer     NOT NULL DEFAULT 0,
  tool_calls_count integer     NOT NULL DEFAULT 0,
  iterations       integer     NOT NULL DEFAULT 1,
  status           text        NOT NULL DEFAULT 'success'
    CHECK (status IN ('success', 'error', 'timeout', 'cancelled')),
  error_message    text        NOT NULL DEFAULT '',
  created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_exec_logs_agent     ON agent_execution_logs(agent_id);
CREATE INDEX IF NOT EXISTS idx_exec_logs_ticket    ON agent_execution_logs(ticket_id);
CREATE INDEX IF NOT EXISTS idx_exec_logs_status    ON agent_execution_logs(status);
CREATE INDEX IF NOT EXISTS idx_exec_logs_created   ON agent_execution_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_exec_logs_run       ON agent_execution_logs(run_id);

ALTER TABLE agent_execution_logs ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'agent_execution_logs'
      AND policyname = 'Authenticated users can read execution logs'
  ) THEN
    EXECUTE 'CREATE POLICY "Authenticated users can read execution logs"
      ON agent_execution_logs FOR SELECT TO authenticated USING (true)';
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS agent_tool_calls (
  id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id      uuid        NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
  agent_id    uuid        REFERENCES agents(id) ON DELETE SET NULL,
  tool_name   text        NOT NULL DEFAULT '',
  arguments   jsonb       NOT NULL DEFAULT '{}'::jsonb,
  result      jsonb       NOT NULL DEFAULT '{}'::jsonb,
  latency_ms  integer     NOT NULL DEFAULT 0,
  success     boolean     NOT NULL DEFAULT true,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tool_calls_run     ON agent_tool_calls(run_id);
CREATE INDEX IF NOT EXISTS idx_tool_calls_agent   ON agent_tool_calls(agent_id);
CREATE INDEX IF NOT EXISTS idx_tool_calls_name    ON agent_tool_calls(tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_calls_created ON agent_tool_calls(created_at DESC);

ALTER TABLE agent_tool_calls ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'agent_tool_calls'
      AND policyname = 'Authenticated users can read tool calls'
  ) THEN
    EXECUTE 'CREATE POLICY "Authenticated users can read tool calls"
      ON agent_tool_calls FOR SELECT TO authenticated USING (true)';
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS agent_metrics (
  id                  uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id            uuid        UNIQUE NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  total_runs          integer     NOT NULL DEFAULT 0,
  successful_runs     integer     NOT NULL DEFAULT 0,
  failed_runs         integer     NOT NULL DEFAULT 0,
  avg_latency_ms      integer     NOT NULL DEFAULT 0,
  total_input_tokens  bigint      NOT NULL DEFAULT 0,
  total_output_tokens bigint      NOT NULL DEFAULT 0,
  total_tool_calls    integer     NOT NULL DEFAULT 0,
  updated_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_metrics_agent ON agent_metrics(agent_id);

ALTER TABLE agent_metrics ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'agent_metrics'
      AND policyname = 'Authenticated users can read agent metrics'
  ) THEN
    EXECUTE 'CREATE POLICY "Authenticated users can read agent metrics"
      ON agent_metrics FOR SELECT TO authenticated USING (true)';
  END IF;
END $$;

CREATE OR REPLACE FUNCTION get_agents_metrics_summary()
RETURNS TABLE (
  agent_id            uuid,
  agent_name          text,
  agent_type          text,
  total_runs          bigint,
  successful_runs     bigint,
  failed_runs         bigint,
  success_rate        numeric,
  avg_latency_ms      numeric,
  p95_latency_ms      numeric,
  total_input_tokens  bigint,
  total_output_tokens bigint,
  total_tool_calls    bigint,
  last_run_at         timestamptz
) LANGUAGE sql STABLE AS $$
  SELECT
    a.id,
    a.name,
    a.type,
    COUNT(el.id),
    COUNT(el.id) FILTER (WHERE el.status = 'success'),
    COUNT(el.id) FILTER (WHERE el.status <> 'success'),
    CASE WHEN COUNT(el.id) > 0
      THEN ROUND(COUNT(el.id) FILTER (WHERE el.status = 'success')::numeric / COUNT(el.id)::numeric * 100, 1)
      ELSE 0
    END,
    COALESCE(ROUND(AVG(el.latency_ms)::numeric, 0), 0),
    COALESCE(ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY el.latency_ms)::numeric, 0), 0),
    COALESCE(SUM(el.input_tokens), 0),
    COALESCE(SUM(el.output_tokens), 0),
    COALESCE(SUM(el.tool_calls_count), 0),
    MAX(el.created_at)
  FROM agents a
  LEFT JOIN agent_execution_logs el ON el.agent_id = a.id
  GROUP BY a.id, a.name, a.type
  ORDER BY COUNT(el.id) DESC;
$$;

CREATE OR REPLACE FUNCTION get_tool_usage_summary()
RETURNS TABLE (
  tool_name    text,
  call_count   bigint,
  success_rate numeric,
  avg_latency  numeric
) LANGUAGE sql STABLE AS $$
  SELECT
    tool_name,
    COUNT(*),
    CASE WHEN COUNT(*) > 0
      THEN ROUND(COUNT(*) FILTER (WHERE success)::numeric / COUNT(*)::numeric * 100, 1)
      ELSE 0
    END,
    ROUND(AVG(latency_ms)::numeric, 0)
  FROM agent_tool_calls
  GROUP BY tool_name
  ORDER BY COUNT(*) DESC;
$$;

CREATE OR REPLACE FUNCTION get_execution_timeline(p_days integer DEFAULT 7)
RETURNS TABLE (
  day           date,
  total_runs    bigint,
  success_runs  bigint,
  error_runs    bigint,
  avg_latency   numeric,
  total_tokens  bigint
) LANGUAGE sql STABLE AS $$
  SELECT
    DATE(created_at),
    COUNT(*),
    COUNT(*) FILTER (WHERE status = 'success'),
    COUNT(*) FILTER (WHERE status <> 'success'),
    ROUND(AVG(latency_ms)::numeric, 0),
    SUM(input_tokens + output_tokens)
  FROM agent_execution_logs
  WHERE created_at >= NOW() - (p_days || ' days')::interval
  GROUP BY DATE(created_at)
  ORDER BY DATE(created_at) ASC;
$$;
