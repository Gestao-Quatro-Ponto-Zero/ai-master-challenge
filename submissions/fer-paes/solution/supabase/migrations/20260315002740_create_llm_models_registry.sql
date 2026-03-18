/*
  # SUBFASE 6.1 — Model Registry

  ## Overview
  Creates a central registry for Language Model (LLM) configurations used throughout the system.
  This catalog allows dynamic model selection, cost control, and provider management without code changes.

  ## New Tables

  ### llm_models
  Central catalog of available LLM models.
  - `id` — UUID primary key
  - `name` — Human-friendly display name (e.g. "GPT-4o")
  - `provider` — Provider slug: openai | anthropic | google | mistral
  - `model_identifier` — API identifier sent in requests (e.g. "gpt-4o")
  - `description` — Optional notes about the model
  - `input_cost_per_1k_tokens` — USD cost per 1,000 input tokens
  - `output_cost_per_1k_tokens` — USD cost per 1,000 output tokens
  - `max_tokens` — Maximum context window
  - `is_active` — Whether the model is available for use by the router
  - `created_at` / `updated_at` — Timestamps

  ## Indexes
  - `idx_llm_models_provider` — Fast lookup by provider
  - `idx_llm_models_active` — Fast lookup of active models for the router

  ## Constraints
  - `uq_llm_models_provider_identifier` — model_identifier must be unique per provider

  ## Seeds
  Pre-populates four commonly-used models: GPT-4o, GPT-4o Mini, Claude 3 Sonnet, Claude 3 Haiku

  ## Permissions
  - New permission: `llm_models.manage`
  - Assigned to roles: admin, supervisor

  ## Security
  - RLS enabled; access restricted to authenticated users with `llm_models.manage` permission via RPC helper
*/

-- ── Table ────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS llm_models (
  id                        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name                      TEXT NOT NULL,
  provider                  TEXT NOT NULL,
  model_identifier          TEXT NOT NULL,
  description               TEXT,
  input_cost_per_1k_tokens  FLOAT,
  output_cost_per_1k_tokens FLOAT,
  max_tokens                INTEGER,
  is_active                 BOOLEAN NOT NULL DEFAULT true,
  created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Unique model per provider
ALTER TABLE llm_models
  ADD CONSTRAINT uq_llm_models_provider_identifier
  UNIQUE (provider, model_identifier);

-- ── Indexes ───────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_llm_models_provider ON llm_models(provider);
CREATE INDEX IF NOT EXISTS idx_llm_models_active   ON llm_models(is_active);

-- ── Updated-at trigger ────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION set_llm_models_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_llm_models_updated_at ON llm_models;
CREATE TRIGGER trg_llm_models_updated_at
  BEFORE UPDATE ON llm_models
  FOR EACH ROW EXECUTE FUNCTION set_llm_models_updated_at();

-- ── RLS ───────────────────────────────────────────────────────────────────────

ALTER TABLE llm_models ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view llm_models"
  ON llm_models FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Users with llm_models.manage can insert llm_models"
  ON llm_models FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1
      FROM user_roles ur
      JOIN role_permissions rp ON rp.role_id = ur.role_id
      JOIN permissions p ON p.id = rp.permission_id
      WHERE ur.user_id = auth.uid()
        AND p.name = 'llm_models.manage'
    )
  );

CREATE POLICY "Users with llm_models.manage can update llm_models"
  ON llm_models FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1
      FROM user_roles ur
      JOIN role_permissions rp ON rp.role_id = ur.role_id
      JOIN permissions p ON p.id = rp.permission_id
      WHERE ur.user_id = auth.uid()
        AND p.name = 'llm_models.manage'
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1
      FROM user_roles ur
      JOIN role_permissions rp ON rp.role_id = ur.role_id
      JOIN permissions p ON p.id = rp.permission_id
      WHERE ur.user_id = auth.uid()
        AND p.name = 'llm_models.manage'
    )
  );

CREATE POLICY "Users with llm_models.manage can delete llm_models"
  ON llm_models FOR DELETE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1
      FROM user_roles ur
      JOIN role_permissions rp ON rp.role_id = ur.role_id
      JOIN permissions p ON p.id = rp.permission_id
      WHERE ur.user_id = auth.uid()
        AND p.name = 'llm_models.manage'
    )
  );

-- ── Permission ────────────────────────────────────────────────────────────────

INSERT INTO permissions (name, description, category)
VALUES ('llm_models.manage', 'Create, update, and deactivate LLM models in the registry', 'llm')
ON CONFLICT (name) DO NOTHING;

-- Assign to admin
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'admin' AND p.name = 'llm_models.manage'
ON CONFLICT DO NOTHING;

-- Assign to supervisor
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'supervisor' AND p.name = 'llm_models.manage'
ON CONFLICT DO NOTHING;

-- ── Seed data ─────────────────────────────────────────────────────────────────

INSERT INTO llm_models (name, provider, model_identifier, description, input_cost_per_1k_tokens, output_cost_per_1k_tokens, max_tokens)
VALUES
  ('GPT-4o',         'openai',    'gpt-4o',                    'OpenAI''s flagship multimodal model',              0.005,   0.015,   128000),
  ('GPT-4o Mini',    'openai',    'gpt-4o-mini',               'Fast, cost-efficient OpenAI model',                0.00015, 0.0006,  128000),
  ('Claude 3 Sonnet','anthropic', 'claude-3-sonnet-20240229',  'Anthropic''s balanced intelligence model',         0.003,   0.015,   200000),
  ('Claude 3 Haiku', 'anthropic', 'claude-3-haiku-20240307',   'Anthropic''s fastest and most compact model',      0.00025, 0.00125, 200000),
  ('Gemini 1.5 Pro', 'google',    'gemini-1.5-pro',            'Google''s multimodal model with long context',     0.0035,  0.0105,  1000000),
  ('Mistral Large',  'mistral',   'mistral-large-latest',      'Mistral''s top-tier reasoning model',              0.008,   0.024,   32000)
ON CONFLICT (provider, model_identifier) DO NOTHING;
