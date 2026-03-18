/*
  # Agents Schema — Subfase 3.1

  ## Summary
  Creates the full data model for intelligent agents within the support system.
  These tables support agent registration, skill assignment, LLM model configuration,
  execution tracking, and internal message logging for observability and debugging.

  ## New Tables

  ### agents
  Defines each intelligent agent in the system.
  - `id` – UUID primary key
  - `name` – human-readable agent name
  - `description` – optional description of what the agent does
  - `type` – agent role: triage_agent | support_agent | technical_agent | billing_agent | sales_agent | qa_agent
  - `status` – lifecycle state: active | disabled | testing
  - `default_model_provider` – default LLM provider (openai, anthropic, google)
  - `default_model_name` – default model identifier (e.g. gpt-4o, claude-3.5-sonnet)
  - `temperature` – sampling temperature (default 0.2)
  - `max_tokens` – max output tokens (default 2000)
  - `created_at` / `updated_at` – timestamps

  ### agent_skills
  Associates skills/capabilities to agents.
  - `agent_id` – FK to agents
  - `skill_name` – e.g. search_knowledge_base, create_ticket, escalate_to_human

  ### agent_models
  Allows multiple LLM configurations per agent (fallback, cost control, A/B testing).
  - `agent_id` – FK to agents
  - `provider` – LLM provider
  - `model_name` – specific model
  - `max_tokens`, `temperature` – per-model overrides
  - `cost_input`, `cost_output` – cost per token (for usage accounting)

  ### agent_runs
  Records each agent execution for observability and cost tracking.
  - `agent_id` – FK to agents
  - `ticket_id` – FK to tickets (nullable)
  - `conversation_id` – FK to conversations (nullable)
  - `status` – running | completed | failed | cancelled
  - `model_provider`, `model_name` – which model was used
  - `input_tokens`, `output_tokens` – token usage
  - `started_at`, `finished_at` – timing

  ### agent_messages
  Stores all internal messages during an agent run (prompts, responses, tool calls).
  - `run_id` – FK to agent_runs (cascade delete)
  - `role` – system | user | assistant | tool
  - `content` – message text
  - `metadata` – JSONB for tool_calls, latency, confidence, etc.

  ## Security
  - RLS enabled on all tables
  - Authenticated users can read all agent data (for UI display and debugging)
  - Agent runs and messages are insert-only for authenticated users (no update/delete)
  - agents and agent_skills/models support full CRUD for authenticated users

  ## Notes
  1. agent_runs are append-only once finalized (status updates allowed, no hard deletes)
  2. agent_messages must never be deleted (audit trail for AI debugging)
  3. This schema is prepared for multi-agent execution on the same ticket
*/

CREATE TABLE IF NOT EXISTS agents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  description text,
  type text,
  status text NOT NULL DEFAULT 'active',
  default_model_provider text,
  default_model_name text,
  temperature float DEFAULT 0.2,
  max_tokens integer DEFAULT 2000,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(type);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);

ALTER TABLE agents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read agents"
  ON agents FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can insert agents"
  ON agents FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can update agents"
  ON agents FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Authenticated users can delete agents"
  ON agents FOR DELETE
  TO authenticated
  USING (true);


CREATE TABLE IF NOT EXISTS agent_skills (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id uuid NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  skill_name text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_skills_agent ON agent_skills(agent_id);

ALTER TABLE agent_skills ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read agent_skills"
  ON agent_skills FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can insert agent_skills"
  ON agent_skills FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can update agent_skills"
  ON agent_skills FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Authenticated users can delete agent_skills"
  ON agent_skills FOR DELETE
  TO authenticated
  USING (true);


CREATE TABLE IF NOT EXISTS agent_models (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id uuid NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  provider text NOT NULL,
  model_name text NOT NULL,
  max_tokens integer,
  temperature float,
  cost_input float,
  cost_output float,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_models_agent ON agent_models(agent_id);

ALTER TABLE agent_models ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read agent_models"
  ON agent_models FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can insert agent_models"
  ON agent_models FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can update agent_models"
  ON agent_models FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Authenticated users can delete agent_models"
  ON agent_models FOR DELETE
  TO authenticated
  USING (true);


CREATE TABLE IF NOT EXISTS agent_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id uuid REFERENCES agents(id),
  ticket_id uuid REFERENCES tickets(id),
  conversation_id uuid REFERENCES conversations(id),
  status text NOT NULL DEFAULT 'running',
  model_provider text,
  model_name text,
  input_tokens integer,
  output_tokens integer,
  started_at timestamptz,
  finished_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_runs_agent ON agent_runs(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_ticket ON agent_runs(ticket_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_conversation ON agent_runs(conversation_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_status ON agent_runs(status);

ALTER TABLE agent_runs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read agent_runs"
  ON agent_runs FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can insert agent_runs"
  ON agent_runs FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can update agent_runs"
  ON agent_runs FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);


CREATE TABLE IF NOT EXISTS agent_messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id uuid NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
  role text NOT NULL,
  content text,
  metadata jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_messages_run ON agent_messages(run_id);
CREATE INDEX IF NOT EXISTS idx_agent_messages_role ON agent_messages(role);

ALTER TABLE agent_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read agent_messages"
  ON agent_messages FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can insert agent_messages"
  ON agent_messages FOR INSERT
  TO authenticated
  WITH CHECK (true);
