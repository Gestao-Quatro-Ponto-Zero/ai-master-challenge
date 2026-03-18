/*
  # Tags System

  ## Summary
  Adds a tagging system to classify and filter tickets.

  ## New Tables

  ### tags
  Global tag definitions:
  - `id` – UUID primary key
  - `name` – Unique tag name (e.g. "billing", "vip", "bug")
  - `color` – Hex color string for UI display (e.g. "#3B82F6")
  - `created_at`

  ### ticket_tags
  Many-to-many join between tickets and tags:
  - `id` – UUID primary key
  - `ticket_id` – FK to tickets
  - `tag_id` – FK to tags
  - `created_at`
  - UNIQUE constraint on (ticket_id, tag_id) prevents duplicates

  ## Security
  - RLS enabled on both tables
  - Authenticated users can read all tags
  - Authenticated users can create new tags
  - Authenticated users can insert/delete ticket_tags

  ## Seed Data
  8 default tags seeded with distinct colors.
*/

CREATE TABLE IF NOT EXISTS tags (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  color text NOT NULL DEFAULT '#6B7280',
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS ticket_tags (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ticket_id uuid NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
  tag_id uuid NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (ticket_id, tag_id)
);

ALTER TABLE tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE ticket_tags ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read tags"
  ON tags FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can create tags"
  ON tags FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can read ticket tags"
  ON ticket_tags FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can assign tags to tickets"
  ON ticket_tags FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can remove tags from tickets"
  ON ticket_tags FOR DELETE
  TO authenticated
  USING (true);

CREATE INDEX IF NOT EXISTS ticket_tags_ticket_id_idx ON ticket_tags(ticket_id);
CREATE INDEX IF NOT EXISTS ticket_tags_tag_id_idx ON ticket_tags(tag_id);

INSERT INTO tags (name, color) VALUES
  ('billing',   '#3B82F6'),
  ('refund',    '#EF4444'),
  ('technical', '#8B5CF6'),
  ('vip',       '#F59E0B'),
  ('bug',       '#DC2626'),
  ('feature',   '#10B981'),
  ('urgent',    '#F97316'),
  ('feedback',  '#06B6D4')
ON CONFLICT (name) DO NOTHING;
