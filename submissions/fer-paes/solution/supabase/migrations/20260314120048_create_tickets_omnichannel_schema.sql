/*
  # Tickets Omnichannel Schema — Phase 2.1

  ## Summary
  Creates the full data layer for the omnichannel ticketing system.
  This schema supports tickets from multiple channels (chat, email, WhatsApp,
  social, etc.) with full conversation and message history, file attachments,
  and status change auditing.

  ## New Tables

  1. `customers` — People who contact support
     - id, name, email, phone
     - external_id / external_source: links to originating channel identity
     - Indexed on email, phone, external_id

  2. `channels` — Inbound communication channels
     - id, name, type (chat | email | social | phone | api | bot)
     - is_active flag, config JSONB for provider-specific settings

  3. `tickets` — Core support ticket
     - Links customer + channel
     - status: open | in_progress | waiting_customer | resolved | closed
     - priority: low | medium | high | urgent
     - assigned_user_id: FK to auth.users (operator from Phase 1 IAM)
     - agent_id: reserved for Phase 3 AI agents
     - Indexed on customer_id, status, assigned_user_id

  4. `conversations` — One-to-one with each ticket
     - Tracks last_message_at for inbox ordering
     - Indexed on ticket_id

  5. `messages` — Individual messages within a conversation
     - sender_type: customer | operator | agent | system | bot
     - message_type: text | image | file | audio | video | system
     - metadata JSONB for AI token usage, model info, tool calls
     - Indexed on conversation_id, created_at

  6. `attachments` — Files attached to messages
     - file_url, file_type, file_size
     - Indexed on message_id

  7. `ticket_status_history` — Immutable log of every status change
     - Records old_status → new_status and who made the change
     - Indexed on ticket_id

  ## Security
  - RLS enabled on all tables
  - Authenticated users can read/insert/update all operational tables
  - ticket_status_history is append-only (no update/delete policies)

  ## Important Notes
  - Every ticket must have a conversation (enforced at application layer)
  - Messages belong to conversations; attachments belong to messages
  - agent_id on tickets is nullable, reserved for future AI agent assignment
*/

CREATE TABLE IF NOT EXISTS customers (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text,
  email text,
  phone text,
  external_id text,
  external_source text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);
CREATE INDEX IF NOT EXISTS idx_customers_external_id ON customers(external_id);

CREATE TABLE IF NOT EXISTS channels (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  type text NOT NULL,
  is_active boolean NOT NULL DEFAULT true,
  config jsonb DEFAULT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tickets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id uuid REFERENCES customers(id) ON DELETE SET NULL,
  channel_id uuid REFERENCES channels(id) ON DELETE SET NULL,
  subject text,
  status text NOT NULL DEFAULT 'open',
  priority text NOT NULL DEFAULT 'medium',
  assigned_user_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  agent_id uuid DEFAULT NULL,
  source text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  closed_at timestamptz DEFAULT NULL
);

CREATE INDEX IF NOT EXISTS idx_tickets_customer_id ON tickets(customer_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_assigned_user ON tickets(assigned_user_id);

CREATE TABLE IF NOT EXISTS conversations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ticket_id uuid NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
  started_at timestamptz NOT NULL DEFAULT now(),
  last_message_at timestamptz DEFAULT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_conversations_ticket ON conversations(ticket_id);

CREATE TABLE IF NOT EXISTS messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid REFERENCES conversations(id) ON DELETE CASCADE,
  sender_type text NOT NULL,
  sender_id uuid DEFAULT NULL,
  message text,
  message_type text NOT NULL DEFAULT 'text',
  metadata jsonb DEFAULT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

CREATE TABLE IF NOT EXISTS attachments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id uuid REFERENCES messages(id) ON DELETE CASCADE,
  file_url text,
  file_type text,
  file_size integer,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_attachments_message ON attachments(message_id);

CREATE TABLE IF NOT EXISTS ticket_status_history (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ticket_id uuid REFERENCES tickets(id) ON DELETE CASCADE,
  old_status text,
  new_status text,
  changed_by uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ticket_history_ticket ON ticket_status_history(ticket_id);

ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE attachments ENABLE ROW LEVEL SECURITY;
ALTER TABLE ticket_status_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read customers"
  ON customers FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can insert customers"
  ON customers FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can update customers"
  ON customers FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Authenticated users can read channels"
  ON channels FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can insert channels"
  ON channels FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can update channels"
  ON channels FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Authenticated users can read tickets"
  ON tickets FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can insert tickets"
  ON tickets FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can update tickets"
  ON tickets FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Authenticated users can read conversations"
  ON conversations FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can insert conversations"
  ON conversations FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can update conversations"
  ON conversations FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Authenticated users can read messages"
  ON messages FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can insert messages"
  ON messages FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can read attachments"
  ON attachments FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can insert attachments"
  ON attachments FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can read ticket_status_history"
  ON ticket_status_history FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can insert ticket_status_history"
  ON ticket_status_history FOR INSERT
  TO authenticated
  WITH CHECK (true);
