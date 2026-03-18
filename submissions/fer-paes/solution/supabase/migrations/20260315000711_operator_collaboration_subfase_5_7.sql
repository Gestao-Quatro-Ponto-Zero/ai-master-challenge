/*
  # Operator Collaboration System — Subfase 5.7

  ## Summary
  Implements internal notes and @-mention collaboration for operators working on tickets.
  Notes are strictly internal — they are never visible to customers.

  ## New Tables

  ### internal_notes
  Stores free-text internal comments left by operators on a ticket.
  - ticket_id  → which ticket this note belongs to
  - operator_id → which operator wrote the note (references operators.id)
  - note       → free-text content (may contain @mentions)
  - created_at / updated_at timestamps

  ### internal_note_mentions
  Junction table recording which operators were @-mentioned in a note.
  - note_id                → the note that contains the mention
  - mentioned_operator_id  → the operator who was mentioned

  ## Indexes
  - idx_internal_notes_ticket_id            — fast retrieval of all notes for a ticket
  - idx_internal_note_mentions_operator_id  — fast lookup of all mentions for an operator

  ## Security
  - RLS enabled on both tables
  - Only authenticated users can read/write notes
  - No customer-facing access paths; this table is never exposed via public API routes

  ## Permissions
  - tickets.collaborate — granted to operator, supervisor, admin roles
*/

CREATE TABLE IF NOT EXISTS internal_notes (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  ticket_id   UUID        NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
  operator_id UUID        NOT NULL REFERENCES operators(id) ON DELETE CASCADE,
  note        TEXT        NOT NULL DEFAULT '',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_internal_notes_ticket_id
  ON internal_notes(ticket_id);

CREATE INDEX IF NOT EXISTS idx_internal_notes_operator_id
  ON internal_notes(operator_id);

ALTER TABLE internal_notes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Operators can create internal notes"
  ON internal_notes FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Operators can view internal notes"
  ON internal_notes FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authors can update their own notes"
  ON internal_notes FOR UPDATE
  TO authenticated
  USING (
    operator_id IN (
      SELECT id FROM operators WHERE user_id = auth.uid()
    )
  )
  WITH CHECK (
    operator_id IN (
      SELECT id FROM operators WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "Authors can delete their own notes"
  ON internal_notes FOR DELETE
  TO authenticated
  USING (
    operator_id IN (
      SELECT id FROM operators WHERE user_id = auth.uid()
    )
  );

CREATE TABLE IF NOT EXISTS internal_note_mentions (
  id                     UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  note_id                UUID        NOT NULL REFERENCES internal_notes(id) ON DELETE CASCADE,
  mentioned_operator_id  UUID        NOT NULL REFERENCES operators(id) ON DELETE CASCADE,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_internal_note_mentions_operator_id
  ON internal_note_mentions(mentioned_operator_id);

CREATE INDEX IF NOT EXISTS idx_internal_note_mentions_note_id
  ON internal_note_mentions(note_id);

ALTER TABLE internal_note_mentions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can create mentions"
  ON internal_note_mentions FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can view mentions"
  ON internal_note_mentions FOR SELECT
  TO authenticated
  USING (true);

-- Permission: tickets.collaborate
INSERT INTO permissions (name, description, category)
VALUES ('tickets.collaborate', 'Add internal notes and @mention colleagues on tickets', 'tickets')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name IN ('admin', 'supervisor', 'operator')
  AND p.name = 'tickets.collaborate'
ON CONFLICT DO NOTHING;
