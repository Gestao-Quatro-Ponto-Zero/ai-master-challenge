/*
  # Automation Rules

  ## Summary
  Adds a rule engine to automate actions based on ticket events.

  ## New Tables

  ### automation_rules
  Stores automation rules with trigger, conditions, and actions:
  - `id` – UUID primary key
  - `name` – Human-readable rule name
  - `trigger_event` – The event that fires this rule: ticket_created | message_received | ticket_updated
  - `conditions` – JSONB array of condition objects: [{ field, operator, value }]
  - `actions` – JSONB array of action objects: [{ type, value }]
  - `is_active` – Whether the rule is enabled
  - `created_by` – FK to profiles (nullable, for audit)
  - `created_at` / `updated_at`

  ## Condition Schema
  Each condition: { "field": "priority"|"tag"|"channel"|"status", "operator": "equals"|"not_equals"|"contains"|"is_empty", "value": string }

  ## Action Schema
  Each action: { "type": "assign_user"|"add_tag"|"change_priority"|"change_status", "value": string }

  ## Security
  - RLS enabled
  - Authenticated users can read, create, update automation rules

  ## Seed Data
  2 example rules to demonstrate the feature.
*/

CREATE TABLE IF NOT EXISTS automation_rules (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  trigger_event text NOT NULL CHECK (trigger_event IN ('ticket_created', 'message_received', 'ticket_updated')),
  conditions jsonb NOT NULL DEFAULT '[]',
  actions jsonb NOT NULL DEFAULT '[]',
  is_active boolean NOT NULL DEFAULT true,
  created_by uuid REFERENCES profiles(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE automation_rules ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read automation rules"
  ON automation_rules FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can create automation rules"
  ON automation_rules FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can update automation rules"
  ON automation_rules FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Authenticated users can delete automation rules"
  ON automation_rules FOR DELETE
  TO authenticated
  USING (true);

CREATE INDEX IF NOT EXISTS automation_rules_trigger_event_idx ON automation_rules(trigger_event);
CREATE INDEX IF NOT EXISTS automation_rules_is_active_idx ON automation_rules(is_active);

INSERT INTO automation_rules (name, trigger_event, conditions, actions, is_active) VALUES
  (
    'Escalate urgent tickets',
    'ticket_created',
    '[{"field":"priority","operator":"equals","value":"urgent"}]',
    '[{"type":"change_status","value":"open"}]',
    true
  ),
  (
    'Auto-tag billing channel',
    'ticket_created',
    '[{"field":"channel","operator":"equals","value":"email"}]',
    '[{"type":"change_priority","value":"high"}]',
    false
  )
ON CONFLICT DO NOTHING;
