/*
  # Create Agent Memory Tables — Subfase 3.8

  ## Summary
  Creates two tables that power the Agent Memory system:
  `agent_memories` for persistent cross-run memory and
  `agent_scratchpads` for ephemeral per-run reasoning steps.

  ## New Tables

  ### agent_memories
  Persistent memory records that survive across runs. Each record captures
  a summarized piece of context tied to an agent, ticket, conversation, or
  customer. Three memory types are supported:
  - conversation — key facts from a specific conversation
  - ticket       — context and history about a specific ticket
  - customer     — long-lived preferences and profile facts about a customer

  Columns:
  - `id`              – UUID primary key
  - `memory_type`     – one of: conversation | ticket | customer
  - `agent_id`        – agent that created this memory (nullable)
  - `ticket_id`       – ticket context (nullable)
  - `conversation_id` – conversation context (nullable)
  - `customer_id`     – customer context (nullable)
  - `content`         – the memory text (summary, fact, preference, etc.)
  - `metadata`        – arbitrary JSON for extra fields (tags, scores, etc.)
  - `created_at`      – creation timestamp
  - `updated_at`      – last update timestamp (auto-updated by trigger)

  ### agent_scratchpads
  Ephemeral step-by-step reasoning log scoped to a single agent_run.
  Rows are automatically deleted when the parent run is deleted (CASCADE).
  Columns:
  - `id`         – UUID primary key
  - `run_id`     – FK → agent_runs.id (CASCADE DELETE)
  - `step`       – sequential step number within the run
  - `step_type`  – type of step: thought | tool_call | tool_result | observation
  - `content`    – step description or reasoning text
  - `metadata`   – optional JSON (tool name, tool input, etc.)
  - `created_at` – creation timestamp

  ## Indexes
  - agent_memories: by agent_id, ticket_id, customer_id, conversation_id, memory_type
  - agent_scratchpads: by run_id, step

  ## Security
  - RLS enabled on both tables
  - Authenticated users can read all memory records (admin visibility)
  - Only service role (edge functions) can insert/update/delete
*/

CREATE TABLE IF NOT EXISTS agent_memories (
  id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  memory_type     text        NOT NULL CHECK (memory_type IN ('conversation', 'ticket', 'customer')),
  agent_id        uuid        REFERENCES agents(id) ON DELETE SET NULL,
  ticket_id       uuid        REFERENCES tickets(id) ON DELETE CASCADE,
  conversation_id uuid        REFERENCES conversations(id) ON DELETE CASCADE,
  customer_id     uuid        REFERENCES customers(id) ON DELETE CASCADE,
  content         text        NOT NULL DEFAULT '',
  metadata        jsonb       NOT NULL DEFAULT '{}'::jsonb,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_memories_agent    ON agent_memories(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_memories_ticket   ON agent_memories(ticket_id);
CREATE INDEX IF NOT EXISTS idx_agent_memories_customer ON agent_memories(customer_id);
CREATE INDEX IF NOT EXISTS idx_agent_memories_conv     ON agent_memories(conversation_id);
CREATE INDEX IF NOT EXISTS idx_agent_memories_type     ON agent_memories(memory_type);

CREATE OR REPLACE FUNCTION update_agent_memories_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.triggers
    WHERE trigger_name = 'trg_agent_memories_updated_at'
  ) THEN
    CREATE TRIGGER trg_agent_memories_updated_at
      BEFORE UPDATE ON agent_memories
      FOR EACH ROW EXECUTE FUNCTION update_agent_memories_updated_at();
  END IF;
END $$;

ALTER TABLE agent_memories ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read agent memories"
  ON agent_memories FOR SELECT
  TO authenticated
  USING (true);

CREATE TABLE IF NOT EXISTS agent_scratchpads (
  id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id      uuid        NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
  step        integer     NOT NULL DEFAULT 0,
  step_type   text        NOT NULL DEFAULT 'thought'
    CHECK (step_type IN ('thought', 'tool_call', 'tool_result', 'observation', 'memory_load')),
  content     text        NOT NULL DEFAULT '',
  metadata    jsonb       NOT NULL DEFAULT '{}'::jsonb,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_scratchpad_run  ON agent_scratchpads(run_id);
CREATE INDEX IF NOT EXISTS idx_scratchpad_step ON agent_scratchpads(run_id, step);

ALTER TABLE agent_scratchpads ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read agent scratchpads"
  ON agent_scratchpads FOR SELECT
  TO authenticated
  USING (true);
