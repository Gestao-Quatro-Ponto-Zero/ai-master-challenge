/*
  # Operator Workspace — Subfase 5.4

  ## Summary
  Adds the supporting database structures for the Operator Workspace.
  Two timestamp columns are added to `tickets` to enable response-time
  analytics and workspace sorting. The `tickets.handle` permission is
  created and granted to operator, supervisor and admin roles.

  ## Changes

  ### Modified Tables

  #### tickets
  - `assigned_at` TIMESTAMPTZ — set when a ticket is assigned to an operator.
    Used for calculating time-to-first-assignment KPIs.
  - `last_operator_reply` TIMESTAMPTZ — updated every time an operator
    sends a message. Used for calculating first/average response time.

  ## Permissions
  - `tickets.handle` — allows accessing and replying within the Operator
    Workspace. Granted to operator, supervisor, admin.

  ## Notes
  1. Both new columns are nullable — they will be NULL for legacy tickets
     created before this migration.
  2. No RLS changes needed; tickets table already has policies in place.
*/

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'tickets' AND column_name = 'assigned_at'
  ) THEN
    ALTER TABLE tickets ADD COLUMN assigned_at timestamptz;
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'tickets' AND column_name = 'last_operator_reply'
  ) THEN
    ALTER TABLE tickets ADD COLUMN last_operator_reply timestamptz;
  END IF;
END $$;

-- Permission: tickets.handle
INSERT INTO permissions (name, description, category)
VALUES ('tickets.handle', 'Access the Operator Workspace and reply to tickets', 'tickets')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name IN ('admin', 'supervisor', 'operator') AND p.name = 'tickets.handle'
ON CONFLICT DO NOTHING;
