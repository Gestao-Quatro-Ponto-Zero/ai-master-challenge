/*
  # Create Macros Table

  ## Summary
  Adds a macros system for quick-response templates that operators can insert while composing messages.

  ## New Tables

  ### macros
  Stores reusable message templates with variable interpolation support:
  - `id` – UUID primary key
  - `name` – Short label shown in the selector list (e.g. "Greeting", "Billing intro")
  - `content` – The template text, supports {{customer_name}}, {{ticket_id}}, {{agent_name}} placeholders
  - `category` – Optional grouping label (e.g. "Greetings", "Billing", "Technical")
  - `created_by` – FK to profiles (nullable)
  - `created_at` / `updated_at`

  ## Security
  - RLS enabled
  - Authenticated users can read all macros
  - Authenticated users can create, update, delete macros

  ## Seed Data
  3 example macros to demonstrate the feature.
*/

CREATE TABLE IF NOT EXISTS macros (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  content text NOT NULL,
  category text NOT NULL DEFAULT '',
  created_by uuid REFERENCES profiles(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE macros ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read macros"
  ON macros FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can create macros"
  ON macros FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can update macros"
  ON macros FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Authenticated users can delete macros"
  ON macros FOR DELETE
  TO authenticated
  USING (true);

CREATE INDEX IF NOT EXISTS macros_name_idx ON macros(name);
CREATE INDEX IF NOT EXISTS macros_category_idx ON macros(category);

INSERT INTO macros (name, content, category) VALUES
  (
    'Greeting',
    'Olá {{customer_name}}, obrigado por entrar em contato! Estamos verificando seu problema e retornaremos em breve.',
    'Greetings'
  ),
  (
    'Confirmation',
    'Olá {{customer_name}}, confirmamos o recebimento do seu ticket #{{ticket_id}}. Nossa equipe está analisando o caso.',
    'Greetings'
  ),
  (
    'Resolution',
    'Olá {{customer_name}}, informamos que o seu problema foi resolvido. Caso precise de mais assistência, não hesite em nos contatar.',
    'Closing'
  )
ON CONFLICT DO NOTHING;
