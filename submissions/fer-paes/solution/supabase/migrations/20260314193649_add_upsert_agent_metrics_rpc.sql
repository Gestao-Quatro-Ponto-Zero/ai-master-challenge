/*
  # Add Atomic Agent Metrics Upsert RPC

  Creates a function that atomically upserts the per-agent metrics cache
  using a running average formula. Called by the agent-executor edge function
  after each completed run to keep the dashboard cache up to date.
*/

CREATE OR REPLACE FUNCTION upsert_agent_metrics(
  p_agent_id      uuid,
  p_latency_ms    integer,
  p_input_tokens  integer,
  p_output_tokens integer,
  p_tool_calls    integer,
  p_success       boolean
) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
  INSERT INTO agent_metrics (
    agent_id,
    total_runs,
    successful_runs,
    failed_runs,
    avg_latency_ms,
    total_input_tokens,
    total_output_tokens,
    total_tool_calls,
    updated_at
  ) VALUES (
    p_agent_id,
    1,
    CASE WHEN p_success THEN 1 ELSE 0 END,
    CASE WHEN NOT p_success THEN 1 ELSE 0 END,
    p_latency_ms,
    p_input_tokens,
    p_output_tokens,
    p_tool_calls,
    NOW()
  )
  ON CONFLICT (agent_id) DO UPDATE SET
    total_runs          = agent_metrics.total_runs + 1,
    successful_runs     = agent_metrics.successful_runs + CASE WHEN p_success THEN 1 ELSE 0 END,
    failed_runs         = agent_metrics.failed_runs + CASE WHEN NOT p_success THEN 1 ELSE 0 END,
    avg_latency_ms      = (
      (agent_metrics.avg_latency_ms * agent_metrics.total_runs + p_latency_ms)
      / (agent_metrics.total_runs + 1)
    ),
    total_input_tokens  = agent_metrics.total_input_tokens  + p_input_tokens,
    total_output_tokens = agent_metrics.total_output_tokens + p_output_tokens,
    total_tool_calls    = agent_metrics.total_tool_calls    + p_tool_calls,
    updated_at          = NOW();
END;
$$;
