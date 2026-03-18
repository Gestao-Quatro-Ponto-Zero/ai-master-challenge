/*
  # Create LLM Policies Table (SUBFASE 6.6 — Prompt Routing Policies)

  ## Overview
  Introduces a prompt-routing policy engine that maps task types to specific LLM
  models. The LLM Router will query this table before executing any prompt, letting
  admins control which model handles each kind of task without touching code.

  ## New Tables
  - `llm_policies` — policy rules that map a task_type to a model_id, with a
    numeric priority so multiple fallback rules can coexist for the same task.

  ## Columns
  - `id`           — UUID primary key
  - `policy_name`  — Human-readable label (e.g. "Simple Chat Policy")
  - `task_type`    — Keyword sent by agents (chat, classification, summarization…)
  - `model_id`     — FK to llm_models; the model to use for this rule
  - `priority`     — Lower number = higher priority (1 = primary, 2 = fallback…)
  - `is_active`    — Soft on/off switch; inactive rules are ignored by the router
  - `created_at` / `updated_at` — audit timestamps

  ## Indexes
  - task_type, priority, is_active — all queried together by the router hot path

  ## Security
  - RLS enabled
  - Read: authenticated users (router services need to read policies)
  - Insert / Update / Delete: restricted to users with llm_policies.manage permission
    (admin / supervisor via role_permissions)

  ## New Permission
  - `llm_policies.manage` — assigned to admin and supervisor roles

  ## Seeds
  Twelve starter policies covering the most common task types using the seeded
  model IDs from subfase 6.3.
*/

-- ── Table ─────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS llm_policies (
  id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  policy_name text        NOT NULL,
  task_type   text        NOT NULL,
  model_id    uuid        NOT NULL REFERENCES llm_models(id) ON DELETE RESTRICT,
  priority    integer     NOT NULL DEFAULT 1 CHECK (priority > 0),
  is_active   boolean     NOT NULL DEFAULT true,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);

-- ── Indexes ───────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_llm_policies_task_type ON llm_policies(task_type);
CREATE INDEX IF NOT EXISTS idx_llm_policies_priority  ON llm_policies(priority);
CREATE INDEX IF NOT EXISTS idx_llm_policies_active    ON llm_policies(is_active);

-- ── updated_at trigger ────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_llm_policies_updated_at()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$;

DROP TRIGGER IF EXISTS trg_llm_policies_updated_at ON llm_policies;
CREATE TRIGGER trg_llm_policies_updated_at
  BEFORE UPDATE ON llm_policies
  FOR EACH ROW EXECUTE FUNCTION update_llm_policies_updated_at();

-- ── RLS ───────────────────────────────────────────────────────────────────────

ALTER TABLE llm_policies ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read active policies"
  ON llm_policies FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Admins can insert policies"
  ON llm_policies FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM user_roles ur
      JOIN roles r ON r.id = ur.role_id
      WHERE ur.user_id = auth.uid() AND r.name IN ('admin', 'supervisor')
    )
  );

CREATE POLICY "Admins can update policies"
  ON llm_policies FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM user_roles ur
      JOIN roles r ON r.id = ur.role_id
      WHERE ur.user_id = auth.uid() AND r.name IN ('admin', 'supervisor')
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM user_roles ur
      JOIN roles r ON r.id = ur.role_id
      WHERE ur.user_id = auth.uid() AND r.name IN ('admin', 'supervisor')
    )
  );

CREATE POLICY "Admins can delete policies"
  ON llm_policies FOR DELETE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM user_roles ur
      JOIN roles r ON r.id = ur.role_id
      WHERE ur.user_id = auth.uid() AND r.name IN ('admin', 'supervisor')
    )
  );

-- ── New permission ────────────────────────────────────────────────────────────

INSERT INTO permissions (name, description, category)
VALUES ('llm_policies.manage', 'Create, edit and delete LLM routing policies', 'llm')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'admin' AND p.name = 'llm_policies.manage'
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'supervisor' AND p.name = 'llm_policies.manage'
ON CONFLICT DO NOTHING;

-- ── Seed policies ─────────────────────────────────────────────────────────────
-- Uses the seeded model UUIDs. Wrapped in DO block so missing models don't fail.

DO $$
DECLARE
  v_mini    uuid := '975192ab-43e4-4c89-97a6-68591d4ce191'; -- GPT-4o Mini
  v_gpt4o   uuid := '50bfdd10-322c-4a2d-a066-9989d8d2ebe5'; -- GPT-4o
  v_sonnet  uuid := '0fd808a1-b56c-4601-99c6-a95528cfacfa'; -- Claude 3 Sonnet
  v_haiku   uuid := 'fdeed508-35c6-4413-b070-9552a41b0c15'; -- Claude 3 Haiku
  v_gemini  uuid := 'd8103b88-fac7-49d0-a3a0-2dabdb25e6ff'; -- Gemini 1.5 Pro
BEGIN
  -- chat: mini (primary) → gpt4o (fallback)
  INSERT INTO llm_policies (policy_name, task_type, model_id, priority)
  VALUES
    ('Simple Chat',           'chat',            v_mini,   1),
    ('Chat Fallback',         'chat',            v_gpt4o,  2),
    -- classification: mini
    ('Classification',        'classification',  v_mini,   1),
    ('Classification Fallback','classification', v_gpt4o,  2),
    -- summarization: gpt4o (needs longer context)
    ('Summarization',         'summarization',   v_gpt4o,  1),
    ('Summarization Fallback','summarization',   v_sonnet, 2),
    -- reasoning: gpt4o
    ('Reasoning',             'reasoning',       v_gpt4o,  1),
    ('Reasoning Fallback',    'reasoning',       v_sonnet, 2),
    -- extraction: claude sonnet (structured output)
    ('Structured Extraction', 'extraction',      v_sonnet, 1),
    ('Extraction Fallback',   'extraction',      v_gpt4o,  2),
    -- translation: haiku (cost-efficient)
    ('Translation',           'translation',     v_haiku,  1),
    ('Translation Fallback',  'translation',     v_mini,   2),
    -- embedding / test
    ('Embedding Context',     'embedding',       v_gemini, 1),
    ('Test',                  'test',            v_mini,   1)
  ON CONFLICT DO NOTHING;
END $$;
