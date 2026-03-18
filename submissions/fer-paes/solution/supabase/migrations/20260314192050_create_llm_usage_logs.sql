/*
  # Create LLM Usage Logs Table — Subfase 3.7

  ## Summary
  Creates the `llm_usage_logs` table to track every LLM API call made through
  the Multi-LLM Manager. Each row represents a single model invocation and
  records token consumption, cost, and the agent/ticket context for billing
  attribution and performance analysis.

  ## New Tables

  ### llm_usage_logs
  - `id`            – UUID primary key
  - `provider`      – LLM provider name (openai, anthropic, google)
  - `model_name`    – specific model used (e.g. claude-3-5-sonnet-20241022)
  - `input_tokens`  – number of prompt/input tokens consumed
  - `output_tokens` – number of completion/output tokens consumed
  - `cost_input`    – dollar cost of input tokens (input_tokens × price_per_token)
  - `cost_output`   – dollar cost of output tokens (output_tokens × price_per_token)
  - `total_cost`    – computed total cost (cost_input + cost_output)
  - `latency_ms`    – response latency in milliseconds
  - `status`        – call outcome: success | error | fallback
  - `fallback_from` – original provider/model if this was a fallback call
  - `error_message` – error details if status = error
  - `agent_id`      – FK to agents table (nullable, for attribution)
  - `ticket_id`     – FK to tickets table (nullable, for attribution)
  - `created_at`    – timestamp of the API call

  ## Security
  - RLS enabled
  - Authenticated users can read all usage logs
  - Only service role (edge functions) can insert records

  ## Notes
  1. cost_input and cost_output store per-call dollar amounts (not per-token rates).
  2. total_cost is a generated column: cost_input + cost_output.
  3. Indexes on provider, model_name, created_at, agent_id for efficient aggregations.
*/

CREATE TABLE IF NOT EXISTS llm_usage_logs (
  id             uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  provider       text        NOT NULL,
  model_name     text        NOT NULL,
  input_tokens   integer     NOT NULL DEFAULT 0,
  output_tokens  integer     NOT NULL DEFAULT 0,
  cost_input     numeric(12,8) NOT NULL DEFAULT 0,
  cost_output    numeric(12,8) NOT NULL DEFAULT 0,
  total_cost     numeric(12,8) GENERATED ALWAYS AS (cost_input + cost_output) STORED,
  latency_ms     integer     NOT NULL DEFAULT 0,
  status         text        NOT NULL DEFAULT 'success'
    CHECK (status IN ('success', 'error', 'fallback')),
  fallback_from  text,
  error_message  text,
  agent_id       uuid        REFERENCES agents(id) ON DELETE SET NULL,
  ticket_id      uuid        REFERENCES tickets(id) ON DELETE SET NULL,
  created_at     timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_llm_usage_provider    ON llm_usage_logs(provider);
CREATE INDEX IF NOT EXISTS idx_llm_usage_model       ON llm_usage_logs(model_name);
CREATE INDEX IF NOT EXISTS idx_llm_usage_created     ON llm_usage_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_llm_usage_agent       ON llm_usage_logs(agent_id);
CREATE INDEX IF NOT EXISTS idx_llm_usage_status      ON llm_usage_logs(status);

ALTER TABLE llm_usage_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read llm usage logs"
  ON llm_usage_logs FOR SELECT
  TO authenticated
  USING (true);
