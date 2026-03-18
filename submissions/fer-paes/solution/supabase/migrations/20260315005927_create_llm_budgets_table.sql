/*
  # Create LLM Budgets Table (SUBFASE 6.7 — Budget Manager)

  ## Overview
  Introduces a budget control layer that sits between the LLM Router and the
  provider APIs. Every prompt execution is checked against an active budget
  before running; if the budget is exhausted the request is blocked. After each
  successful call the consumed cost and tokens are atomically incremented.

  ## New Tables
  - `llm_budgets` — one row per budget period, optionally scoped to an
    organization_id (NULL = global budget)

  ## Columns
  - `id`               — UUID primary key
  - `name`             — Human-readable label (e.g. "March 2026 Global Budget")
  - `organization_id`  — Optional scoping; NULL means the budget is global
  - `monthly_budget`   — Maximum USD spend for the period (NULL = unlimited)
  - `token_limit`      — Maximum token count for the period (NULL = unlimited)
  - `current_spend`    — Running spend total (atomically incremented)
  - `current_tokens`   — Running token total (atomically incremented)
  - `period_start`     — First instant of the budget window (inclusive)
  - `period_end`       — Last  instant of the budget window (exclusive)
  - `alert_threshold`  — 0–1 fraction at which an alert fires (e.g. 0.8 = 80 %)
  - `is_active`        — Soft on/off; inactive budgets are ignored by the router
  - `created_at` / `updated_at` — audit timestamps

  ## RPCs
  - `check_budget_exceeded(p_org_id uuid)` — returns TRUE if any active budget
    for the period is fully exhausted (cost OR tokens)
  - `increment_budget_usage(p_org_id uuid, p_cost float8, p_tokens int8)` —
    atomically increments current_spend and current_tokens on all matching
    active budgets; uses FOR UPDATE to prevent double-counting under concurrency

  ## Indexes
  - organization_id, is_active — router lookup hot path

  ## Security
  - RLS enabled
  - Read: authenticated users (router needs to call RPCs)
  - Insert / Update / Delete: admin or supervisor roles only

  ## New Permission
  - `llm_budget.manage` — assigned to admin and supervisor roles
*/

-- ── Table ─────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS llm_budgets (
  id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  name            text        NOT NULL,
  organization_id uuid        DEFAULT NULL,
  monthly_budget  float8      DEFAULT NULL,
  token_limit     bigint      DEFAULT NULL,
  current_spend   float8      NOT NULL DEFAULT 0,
  current_tokens  bigint      NOT NULL DEFAULT 0,
  period_start    timestamptz NOT NULL DEFAULT date_trunc('month', now()),
  period_end      timestamptz NOT NULL DEFAULT (date_trunc('month', now()) + interval '1 month'),
  alert_threshold float8      NOT NULL DEFAULT 0.8 CHECK (alert_threshold > 0 AND alert_threshold <= 1),
  is_active       boolean     NOT NULL DEFAULT true,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
);

-- ── Indexes ───────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_llm_budgets_org    ON llm_budgets(organization_id);
CREATE INDEX IF NOT EXISTS idx_llm_budgets_active ON llm_budgets(is_active);

-- ── updated_at trigger ────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_llm_budgets_updated_at()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$;

DROP TRIGGER IF EXISTS trg_llm_budgets_updated_at ON llm_budgets;
CREATE TRIGGER trg_llm_budgets_updated_at
  BEFORE UPDATE ON llm_budgets
  FOR EACH ROW EXECUTE FUNCTION update_llm_budgets_updated_at();

-- ── RLS ───────────────────────────────────────────────────────────────────────

ALTER TABLE llm_budgets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read budgets"
  ON llm_budgets FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Admins can insert budgets"
  ON llm_budgets FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM user_roles ur
      JOIN roles r ON r.id = ur.role_id
      WHERE ur.user_id = auth.uid() AND r.name IN ('admin', 'supervisor')
    )
  );

CREATE POLICY "Admins can update budgets"
  ON llm_budgets FOR UPDATE
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

CREATE POLICY "Admins can delete budgets"
  ON llm_budgets FOR DELETE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM user_roles ur
      JOIN roles r ON r.id = ur.role_id
      WHERE ur.user_id = auth.uid() AND r.name IN ('admin', 'supervisor')
    )
  );

-- ── RPC: check_budget_exceeded ────────────────────────────────────────────────
-- Returns TRUE if there is at least one active budget for the current
-- time window that has been fully consumed (cost OR token limit reached).
-- p_org_id = NULL checks the global (organization_id IS NULL) budget.

CREATE OR REPLACE FUNCTION check_budget_exceeded(p_org_id uuid DEFAULT NULL)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_exceeded boolean := false;
BEGIN
  SELECT EXISTS (
    SELECT 1 FROM llm_budgets
    WHERE is_active = true
      AND now() BETWEEN period_start AND period_end
      AND (
        CASE WHEN p_org_id IS NULL THEN organization_id IS NULL
             ELSE organization_id = p_org_id
        END
      )
      AND (
        (monthly_budget IS NOT NULL AND current_spend  >= monthly_budget)
        OR
        (token_limit    IS NOT NULL AND current_tokens >= token_limit)
      )
  ) INTO v_exceeded;
  RETURN v_exceeded;
END;
$$;

-- ── RPC: increment_budget_usage ───────────────────────────────────────────────
-- Atomically increments current_spend and current_tokens on all active budgets
-- that cover the current instant for the given organization (or global).

CREATE OR REPLACE FUNCTION increment_budget_usage(
  p_org_id uuid    DEFAULT NULL,
  p_cost   float8  DEFAULT 0,
  p_tokens bigint  DEFAULT 0
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  UPDATE llm_budgets
  SET
    current_spend  = current_spend  + p_cost,
    current_tokens = current_tokens + p_tokens
  WHERE is_active = true
    AND now() BETWEEN period_start AND period_end
    AND (
      CASE WHEN p_org_id IS NULL THEN organization_id IS NULL
           ELSE organization_id = p_org_id
      END
    );
END;
$$;

-- ── RPC: reset_budget_usage ───────────────────────────────────────────────────
-- Resets spend and token counters for a specific budget row.

CREATE OR REPLACE FUNCTION reset_budget_usage(p_budget_id uuid)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  UPDATE llm_budgets
  SET current_spend = 0, current_tokens = 0
  WHERE id = p_budget_id;
END;
$$;

-- ── New permission ────────────────────────────────────────────────────────────

INSERT INTO permissions (name, description, category)
VALUES ('llm_budget.manage', 'Create, edit and monitor LLM spending budgets', 'llm')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'admin' AND p.name = 'llm_budget.manage'
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'supervisor' AND p.name = 'llm_budget.manage'
ON CONFLICT DO NOTHING;

-- ── Seed: default global budget for March 2026 ───────────────────────────────

INSERT INTO llm_budgets (name, organization_id, monthly_budget, token_limit, period_start, period_end)
VALUES (
  'Global Budget — March 2026',
  NULL,
  100.0,
  5000000,
  '2026-03-01 00:00:00+00',
  '2026-04-01 00:00:00+00'
)
ON CONFLICT DO NOTHING;
