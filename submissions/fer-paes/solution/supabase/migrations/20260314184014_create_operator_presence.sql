/*
  # Create Operator Presence Table

  ## Summary
  Tracks real-time availability status of operators.

  ## New Tables

  ### operator_presence
  Stores each operator's current availability status:
  - `id` – UUID primary key
  - `user_id` – FK to profiles (unique; one row per operator)
  - `status` – enum: 'online' | 'away' | 'busy' | 'offline'
  - `last_seen` – timestamp of last heartbeat
  - `updated_at` – timestamp of last status change

  ## Security
  - RLS enabled
  - Authenticated users can read all presence records (to show team availability)
  - Users can only insert/update their own presence record

  ## Indexes
  - `user_id` unique index
  - `status` index for filtering online operators
*/

CREATE TYPE operator_status AS ENUM ('online', 'away', 'busy', 'offline');

CREATE TABLE IF NOT EXISTS operator_presence (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  status operator_status NOT NULL DEFAULT 'offline',
  last_seen timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT operator_presence_user_id_unique UNIQUE (user_id)
);

ALTER TABLE operator_presence ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read all presence"
  ON operator_presence FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Users can insert own presence"
  ON operator_presence FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own presence"
  ON operator_presence FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS operator_presence_user_id_idx ON operator_presence(user_id);
CREATE INDEX IF NOT EXISTS operator_presence_status_idx ON operator_presence(status);
