/*
  # SLA Policies and Ticket SLA

  ## Summary
  Implements Service Level Agreement (SLA) tracking for tickets.

  ## New Tables

  ### sla_policies
  Defines SLA rules per priority level:
  - `id` – UUID primary key
  - `name` – Display name (e.g. "Urgent SLA")
  - `priority` – Ticket priority this policy applies to (low/medium/high/urgent)
  - `first_response_minutes` – Max minutes allowed before first operator response
  - `resolution_minutes` – Max minutes allowed before ticket is resolved
  - `is_active` – Whether this policy is active
  - `created_at`, `updated_at`

  ### ticket_sla
  Tracks SLA state for each ticket:
  - `id` – UUID primary key
  - `ticket_id` – FK to tickets (unique per ticket)
  - `sla_policy_id` – FK to sla_policies
  - `first_response_deadline` – Timestamp when first response is due
  - `resolution_deadline` – Timestamp when resolution is due
  - `first_response_at` – Actual timestamp of first operator response (null until responded)
  - `resolved_at` – Actual timestamp of resolution (null until resolved)
  - `status` – `within_sla` or `breached`
  - `created_at`

  ## Security
  - RLS enabled on both tables
  - Authenticated users can read both tables
  - Only service role writes sla_policies (managed via migrations)
  - Authenticated users can insert/update ticket_sla (needed for SLA tracking)

  ## Seed Data
  Default SLA policies seeded for all 4 priority levels.
*/

CREATE TABLE IF NOT EXISTS sla_policies (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  priority text NOT NULL CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
  first_response_minutes integer NOT NULL DEFAULT 60,
  resolution_minutes integer NOT NULL DEFAULT 480,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (priority)
);

CREATE TABLE IF NOT EXISTS ticket_sla (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ticket_id uuid NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
  sla_policy_id uuid NOT NULL REFERENCES sla_policies(id),
  first_response_deadline timestamptz NOT NULL,
  resolution_deadline timestamptz NOT NULL,
  first_response_at timestamptz,
  resolved_at timestamptz,
  status text NOT NULL DEFAULT 'within_sla' CHECK (status IN ('within_sla', 'breached')),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (ticket_id)
);

ALTER TABLE sla_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE ticket_sla ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read SLA policies"
  ON sla_policies FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can read ticket SLA"
  ON ticket_sla FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can insert ticket SLA"
  ON ticket_sla FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can update ticket SLA"
  ON ticket_sla FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE INDEX IF NOT EXISTS ticket_sla_ticket_id_idx ON ticket_sla(ticket_id);
CREATE INDEX IF NOT EXISTS ticket_sla_status_idx ON ticket_sla(status);

INSERT INTO sla_policies (name, priority, first_response_minutes, resolution_minutes)
VALUES
  ('Low Priority SLA',    'low',    240, 2880),
  ('Medium Priority SLA', 'medium',  60, 1440),
  ('High Priority SLA',   'high',    30,  480),
  ('Urgent SLA',          'urgent',   5,   60)
ON CONFLICT (priority) DO NOTHING;
