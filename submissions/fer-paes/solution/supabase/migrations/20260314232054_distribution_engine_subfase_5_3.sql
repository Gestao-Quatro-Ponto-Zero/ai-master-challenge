/*
  # Distribution Engine — Subfase 5.3

  ## Summary
  Adds the automatic ticket distribution engine infrastructure. Queues gain a
  configurable distribution strategy and a round-robin state tracker.
  Permission `tickets.assign` is added so supervisors/admins can manually
  assign tickets. An index on active_tickets speeds up least-loaded queries.

  ## Changes

  ### Modified Tables

  #### queues
  - `distribution_strategy` TEXT — strategy used for auto-distribution:
      round_robin | least_loaded | skill_based | manual
    Defaults to `least_loaded` (safest balance strategy).

  ### New Tables

  #### queue_distribution_state
  Tracks round-robin pointer per queue so distribution continues from where
  it left off instead of always starting at the first operator.
  - `queue_id`          – UUID PK, FK → queues
  - `last_operator_id`  – UUID nullable; last operator who received a ticket
  - `updated_at`        – timestamp

  ## Security
  - RLS enabled on `queue_distribution_state`
  - Authenticated users can read/upsert their queue state

  ## Permissions
  - `tickets.assign` added and granted to admin + supervisor roles

  ## Notes
  1. distribution_strategy uses a CHECK constraint to enforce valid values.
  2. `queue_distribution_state` uses queue_id as PK (one row per queue).
*/

-- ─── Add distribution_strategy to queues ─────────────────────────────────────

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'queues' AND column_name = 'distribution_strategy'
  ) THEN
    ALTER TABLE queues
      ADD COLUMN distribution_strategy TEXT NOT NULL DEFAULT 'least_loaded'
        CONSTRAINT queues_distribution_strategy_check
          CHECK (distribution_strategy IN ('round_robin','least_loaded','skill_based','manual'));
  END IF;
END $$;

-- ─── queue_distribution_state ────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS queue_distribution_state (
  queue_id         uuid        PRIMARY KEY REFERENCES queues(id) ON DELETE CASCADE,
  last_operator_id uuid,
  updated_at       timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE queue_distribution_state ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view distribution state"
  ON queue_distribution_state FOR SELECT TO authenticated USING (true);

CREATE POLICY "Authenticated users can insert distribution state"
  ON queue_distribution_state FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "Authenticated users can update distribution state"
  ON queue_distribution_state FOR UPDATE TO authenticated USING (true) WITH CHECK (true);

-- ─── Index on operator_ticket_load.active_tickets ────────────────────────────

CREATE INDEX IF NOT EXISTS idx_operator_load_active ON operator_ticket_load(active_tickets ASC);

-- ─── permissions ─────────────────────────────────────────────────────────────

INSERT INTO permissions (name, description, category)
VALUES ('tickets.assign', 'Manually assign tickets to operators', 'tickets')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name IN ('admin', 'supervisor') AND p.name = 'tickets.assign'
ON CONFLICT DO NOTHING;
