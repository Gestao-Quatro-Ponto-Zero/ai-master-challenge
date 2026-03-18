/*
  # Operators Schema — Subfase 5.1

  ## Summary
  Creates the infrastructure for human operators within the support system.
  Operators are users with a dedicated operational profile that tracks their
  availability, ticket capacity, and skill set.

  ## New Tables

  ### operators
  Central profile for a human operator. Each operator maps 1:1 to a user.
  - `id`                – UUID primary key
  - `user_id`           – FK to profiles (unique; one user → one operator)
  - `status`            – offline | online | busy | away
  - `max_active_tickets`– capacity cap (default 5)
  - `created_at`, `updated_at`

  ### operator_skills
  Specialisation tags for routing and reporting.
  - `id`          – UUID primary key
  - `operator_id` – FK to operators
  - `skill_name`  – free-text label (billing, technical, sales, …)
  - `skill_level` – 1 basic · 2 intermediate · 3 specialist
  - `created_at`

  ### operator_ticket_load
  Lightweight counter for active ticket capacity enforcement.
  - `operator_id`    – UUID PK (FK to operators)
  - `active_tickets` – current open ticket count (default 0)
  - `max_tickets`    – mirrors operators.max_active_tickets for fast reads
  - `updated_at`

  ## Modified Tables

  ### permissions
  Inserts `operators.manage` permission under the "operators" category.

  ### role_permissions
  Grants `operators.manage` to the admin role (and supervisor role if it exists).

  ## Security
  - RLS enabled on all new tables
  - Authenticated users can read all operator records (for assignment UIs)
  - Only users with operators.manage may insert/update operators (enforced in app)
  - Operators can update their own status row

  ## Notes
  1. `operator_presence` from Subfase 3.x is reused as-is (keyed by user_id).
  2. All CREATE statements use IF NOT EXISTS for safe re-runs.
  3. Permission seeding uses INSERT … ON CONFLICT DO NOTHING.
*/

-- ─── operators ────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS operators (
  id                  uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             uuid        NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  status              text        NOT NULL DEFAULT 'offline'
                                  CHECK (status IN ('offline','online','busy','away')),
  max_active_tickets  integer     NOT NULL DEFAULT 5,
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT operators_user_id_unique UNIQUE (user_id)
);

CREATE INDEX IF NOT EXISTS operators_user_id_idx ON operators(user_id);
CREATE INDEX IF NOT EXISTS operators_status_idx  ON operators(status);

ALTER TABLE operators ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view operators"
  ON operators FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can insert operators"
  ON operators FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can update operators"
  ON operators FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Authenticated users can delete operators"
  ON operators FOR DELETE
  TO authenticated
  USING (true);

-- ─── operator_skills ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS operator_skills (
  id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  operator_id uuid        NOT NULL REFERENCES operators(id) ON DELETE CASCADE,
  skill_name  text        NOT NULL,
  skill_level integer     NOT NULL DEFAULT 1
                          CHECK (skill_level BETWEEN 1 AND 3),
  created_at  timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT operator_skills_unique UNIQUE (operator_id, skill_name)
);

CREATE INDEX IF NOT EXISTS operator_skills_operator_id_idx ON operator_skills(operator_id);

ALTER TABLE operator_skills ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view operator skills"
  ON operator_skills FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can manage operator skills"
  ON operator_skills FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can update operator skills"
  ON operator_skills FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Authenticated users can delete operator skills"
  ON operator_skills FOR DELETE
  TO authenticated
  USING (true);

-- ─── operator_ticket_load ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS operator_ticket_load (
  operator_id    uuid        PRIMARY KEY REFERENCES operators(id) ON DELETE CASCADE,
  active_tickets integer     NOT NULL DEFAULT 0,
  max_tickets    integer     NOT NULL DEFAULT 5,
  updated_at     timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE operator_ticket_load ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can view ticket load"
  ON operator_ticket_load FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can upsert ticket load"
  ON operator_ticket_load FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can update ticket load"
  ON operator_ticket_load FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- ─── operators.manage permission ─────────────────────────────────────────────

INSERT INTO permissions (name, description, category)
VALUES ('operators.manage', 'Create, edit, and manage human operators', 'operators')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'admin' AND p.name = 'operators.manage'
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'supervisor' AND p.name = 'operators.manage'
ON CONFLICT DO NOTHING;
