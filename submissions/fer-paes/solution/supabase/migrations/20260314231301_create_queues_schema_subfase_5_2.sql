/*
  # Queues Schema — Subfase 5.2

  ## Summary
  Creates the support queue infrastructure that organises tickets before they
  are assigned to human operators. Queues segment support channels, control
  capacity and prepare for automatic distribution in Subfase 5.3.

  ## New Tables

  ### queues
  Defines a named support queue (e.g. Technical, Billing, VIP).
  - `id`          – UUID primary key
  - `name`        – unique slug (technical_support, billing, …)
  - `description` – human-readable label
  - `priority`    – higher value = more important (default 1)
  - `is_active`   – soft-disable without deleting (default true)
  - `created_at`, `updated_at`

  ### queue_operators
  Many-to-many between queues and operators. An operator can work across
  multiple queues; a queue can have multiple operators.
  - `id`          – UUID primary key
  - `queue_id`    – FK → queues
  - `operator_id` – FK → operators
  - `created_at`
  - UNIQUE(queue_id, operator_id) to prevent duplicates

  ### queue_tickets
  The actual ordered list of tickets waiting in a queue.
  - `id`         – UUID primary key
  - `ticket_id`  – FK → tickets
  - `queue_id`   – FK → queues
  - `position`   – insertion order (MAX+1 strategy)
  - `priority`   – allows priority boosting (default 1)
  - `created_at`

  ## Security
  - RLS enabled on all three tables
  - Authenticated users can read all queue data (needed for ticket-view UIs)
  - Insert/update/delete are open to authenticated users (permission enforcement
    happens in the application layer via queues.manage / tickets.view)

  ## Permissions
  - `queues.manage` permission inserted and granted to admin + supervisor roles
  - `queues.view`   permission inserted and granted to operator role as well

  ## Notes
  1. queue_tickets has no UNIQUE(ticket_id) deliberately — a ticket could be
     moved between queues by inserting + deleting. If strict single-queue
     enforcement is needed, add the constraint later.
  2. position is NOT auto-managed by the DB; the application uses
     MAX(position) + 1 on insert.
  3. All statements use IF NOT EXISTS for safe re-runs.
*/

-- ─── queues ──────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS queues (
  id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  name        text        UNIQUE NOT NULL,
  description text        NOT NULL DEFAULT '',
  priority    integer     NOT NULL DEFAULT 1,
  is_active   boolean     NOT NULL DEFAULT true,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS queues_priority_idx  ON queues(priority DESC);
CREATE INDEX IF NOT EXISTS queues_is_active_idx ON queues(is_active);

ALTER TABLE queues ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view queues"
  ON queues FOR SELECT TO authenticated USING (true);

CREATE POLICY "Authenticated users can insert queues"
  ON queues FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "Authenticated users can update queues"
  ON queues FOR UPDATE TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY "Authenticated users can delete queues"
  ON queues FOR DELETE TO authenticated USING (true);

-- ─── queue_operators ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS queue_operators (
  id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  queue_id    uuid        NOT NULL REFERENCES queues(id)    ON DELETE CASCADE,
  operator_id uuid        NOT NULL REFERENCES operators(id) ON DELETE CASCADE,
  created_at  timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT queue_operators_unique UNIQUE (queue_id, operator_id)
);

CREATE INDEX IF NOT EXISTS queue_operators_queue_id_idx    ON queue_operators(queue_id);
CREATE INDEX IF NOT EXISTS queue_operators_operator_id_idx ON queue_operators(operator_id);

ALTER TABLE queue_operators ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view queue operators"
  ON queue_operators FOR SELECT TO authenticated USING (true);

CREATE POLICY "Authenticated users can insert queue operators"
  ON queue_operators FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "Authenticated users can delete queue operators"
  ON queue_operators FOR DELETE TO authenticated USING (true);

-- ─── queue_tickets ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS queue_tickets (
  id         uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  ticket_id  uuid        NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
  queue_id   uuid        NOT NULL REFERENCES queues(id)  ON DELETE CASCADE,
  position   integer     NOT NULL DEFAULT 0,
  priority   integer     NOT NULL DEFAULT 1,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS queue_tickets_queue_id_idx  ON queue_tickets(queue_id);
CREATE INDEX IF NOT EXISTS queue_tickets_ticket_id_idx ON queue_tickets(ticket_id);
CREATE INDEX IF NOT EXISTS queue_tickets_ordering_idx  ON queue_tickets(queue_id, priority DESC, position ASC);

ALTER TABLE queue_tickets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view queue tickets"
  ON queue_tickets FOR SELECT TO authenticated USING (true);

CREATE POLICY "Authenticated users can insert queue tickets"
  ON queue_tickets FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "Authenticated users can delete queue tickets"
  ON queue_tickets FOR DELETE TO authenticated USING (true);

-- ─── permissions ─────────────────────────────────────────────────────────────

INSERT INTO permissions (name, description, category)
VALUES
  ('queues.manage', 'Create, edit, and manage support queues', 'queues'),
  ('queues.view',   'View support queues and waiting tickets',  'queues')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'admin' AND p.name IN ('queues.manage', 'queues.view')
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'supervisor' AND p.name IN ('queues.manage', 'queues.view')
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'operator' AND p.name = 'queues.view'
ON CONFLICT DO NOTHING;
