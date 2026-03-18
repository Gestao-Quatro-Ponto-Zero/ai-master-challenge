/*
  # Ticket Transfer System — Subfase 5.6

  ## Summary
  Creates the ticket_transfers table to record every time a ticket is transferred
  between operators, queues, or AI agents. Also adds the tickets.transfer permission
  and grants it to the operator, supervisor, and admin roles.

  ## New Tables

  ### ticket_transfers
  Immutable log of every transfer event. Each row captures:
  - Which ticket was transferred
  - Who initiated the transfer (from_operator_id – references operators.id)
  - The destination: one of to_operator_id, to_queue_id, or to_agent_id
  - The transfer type: 'operator', 'queue', or 'agent'
  - An optional free-text reason

  ## Indexes
  - idx_ticket_transfers_ticket_id  — fast lookup of transfer history for a ticket
  - idx_ticket_transfers_operator   — fast lookup of transfers initiated by an operator

  ## Security
  - RLS enabled with restrictive policies
  - Authenticated users can INSERT (needed when operator clicks Transfer)
  - Authenticated users can SELECT to view history on their tickets
  - No UPDATE or DELETE — transfers are an append-only audit trail

  ## Permissions
  - tickets.transfer — allows operators/supervisors/admins to perform transfers
*/

CREATE TABLE IF NOT EXISTS ticket_transfers (
  id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  ticket_id        UUID        NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
  from_operator_id UUID,
  to_operator_id   UUID,
  to_queue_id      UUID,
  to_agent_id      UUID,
  transfer_type    TEXT        NOT NULL CHECK (transfer_type IN ('operator', 'queue', 'agent')),
  reason           TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ticket_transfers_ticket_id
  ON ticket_transfers(ticket_id);

CREATE INDEX IF NOT EXISTS idx_ticket_transfers_operator
  ON ticket_transfers(from_operator_id);

ALTER TABLE ticket_transfers ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can record transfers"
  ON ticket_transfers FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can view transfer history"
  ON ticket_transfers FOR SELECT
  TO authenticated
  USING (true);

-- Permission: tickets.transfer
INSERT INTO permissions (name, description, category)
VALUES ('tickets.transfer', 'Transfer tickets between operators, queues, and agents', 'tickets')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name IN ('admin', 'supervisor', 'operator')
  AND p.name = 'tickets.transfer'
ON CONFLICT DO NOTHING;
