/*
  # Operator Presence — Subfase 5.5

  ## Summary
  Adds performance indexes to the `operator_presence` table and creates the
  `operators.presence` permission required for operators to update their own
  presence status.

  ## Changes

  ### Indexes Added
  - `idx_operator_presence_status` on `operator_presence(status)` — speeds up
    queries that filter for all online/busy operators.
  - `idx_operator_presence_last_seen` on `operator_presence(last_seen)` — speeds
    up the stale-detection query (last_seen < threshold).

  ## Permissions
  - `operators.presence` — allows an authenticated user to read and update their
    own operator presence status. Granted to operator, supervisor, and admin roles.

  ## Notes
  1. Indexes are created with IF NOT EXISTS to be safe on re-runs.
  2. The `operator_presence` table already exists from subfase 5.1 — no schema
     changes are made to it here.
*/

CREATE INDEX IF NOT EXISTS idx_operator_presence_status
  ON operator_presence(status);

CREATE INDEX IF NOT EXISTS idx_operator_presence_last_seen
  ON operator_presence(last_seen);

-- Permission: operators.presence
INSERT INTO permissions (name, description, category)
VALUES ('operators.presence', 'Read and update operator presence status', 'operators')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name IN ('admin', 'supervisor', 'operator')
  AND p.name = 'operators.presence'
ON CONFLICT DO NOTHING;
