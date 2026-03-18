/*
  # Create Tool Definitions Table — Subfase 3.5

  ## Summary
  Creates a persistent registry of all tools available to AI agents.
  Each row describes one executable tool: its name, description, JSON input
  schema, and internal handler identifier used by the executor.

  Seeded with 8 core tools aligned with the existing agent skill names.

  ## New Table

  ### tool_definitions
  - `id`           – UUID primary key
  - `name`         – unique tool identifier (matches agent_skills.skill_name)
  - `display_name` – human-readable label shown in UI
  - `description`  – natural-language description for the LLM and admin UI
  - `input_schema` – JSON Schema of the tool's accepted parameters
  - `handler_name` – internal key used by the executor switch statement
  - `category`     – grouping label (customer | ticket | knowledge | order | system)
  - `is_active`    – whether the tool can be dispatched (default true)
  - `created_at`   – insertion timestamp

  ## Security
  - RLS enabled; all authenticated users can read active tools
  - Only insert / update via service role (edge functions); no UI mutations
    needed for base tools

  ## Notes
  1. The `name` field is the canonical key — it must match skill_name entries
     in agent_skills so the executor can filter tools per agent.
  2. `handler_name` is the internal string used in the executor's switch
     statement and in the agent-tools edge function.
  3. Seeding is done with INSERT … ON CONFLICT DO NOTHING so re-running the
     migration is safe.
*/

CREATE TABLE IF NOT EXISTS tool_definitions (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name         text UNIQUE NOT NULL,
  display_name text NOT NULL,
  description  text NOT NULL,
  input_schema jsonb NOT NULL DEFAULT '{}',
  handler_name text NOT NULL,
  category     text NOT NULL DEFAULT 'general',
  is_active    boolean NOT NULL DEFAULT true,
  created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tool_definitions_name       ON tool_definitions(name);
CREATE INDEX IF NOT EXISTS idx_tool_definitions_category   ON tool_definitions(category);
CREATE INDEX IF NOT EXISTS idx_tool_definitions_is_active  ON tool_definitions(is_active);

ALTER TABLE tool_definitions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read tool definitions"
  ON tool_definitions FOR SELECT
  TO authenticated
  USING (true);

INSERT INTO tool_definitions (name, display_name, description, input_schema, handler_name, category) VALUES

(
  'search_knowledge_base',
  'Search Knowledge Base',
  'Search the internal knowledge base for relevant articles, FAQs, and policy documents.',
  '{
    "type": "object",
    "properties": {
      "query": { "type": "string", "description": "Search query or question to look up" }
    },
    "required": ["query"]
  }'::jsonb,
  'search_knowledge_base',
  'knowledge'
),

(
  'lookup_customer',
  'Lookup Customer',
  'Retrieve customer profile and account information by customer ID or email address.',
  '{
    "type": "object",
    "properties": {
      "customer_id": { "type": "string", "description": "Customer UUID" },
      "email":       { "type": "string", "description": "Customer email address" }
    }
  }'::jsonb,
  'lookup_customer',
  'customer'
),

(
  'get_ticket_info',
  'Get Ticket Info',
  'Fetch detailed information about a support ticket, including status, priority, and customer.',
  '{
    "type": "object",
    "properties": {
      "ticket_id": { "type": "string", "description": "Ticket UUID" }
    },
    "required": ["ticket_id"]
  }'::jsonb,
  'get_ticket_info',
  'ticket'
),

(
  'update_ticket_status',
  'Update Ticket Status',
  'Change the status of a support ticket (open, in_progress, waiting_customer, resolved, closed).',
  '{
    "type": "object",
    "properties": {
      "ticket_id": { "type": "string", "description": "Ticket UUID" },
      "status":    {
        "type": "string",
        "enum": ["open", "in_progress", "waiting_customer", "resolved", "closed"],
        "description": "New ticket status"
      }
    },
    "required": ["ticket_id", "status"]
  }'::jsonb,
  'update_ticket_status',
  'ticket'
),

(
  'add_ticket_note',
  'Add Ticket Note',
  'Add an internal note to a support ticket visible only to agents and operators.',
  '{
    "type": "object",
    "properties": {
      "ticket_id": { "type": "string", "description": "Ticket UUID (uses current ticket if omitted)" },
      "note":      { "type": "string", "description": "The note content to add" }
    },
    "required": ["note"]
  }'::jsonb,
  'add_ticket_note',
  'ticket'
),

(
  'create_ticket',
  'Create Ticket',
  'Open a new support ticket on behalf of a customer.',
  '{
    "type": "object",
    "properties": {
      "customer_id": { "type": "string", "description": "Customer UUID" },
      "subject":     { "type": "string", "description": "Short ticket subject line" },
      "message":     { "type": "string", "description": "Initial message or description of the issue" },
      "priority":    { "type": "string", "enum": ["low", "normal", "high", "urgent"], "description": "Ticket priority" }
    },
    "required": ["customer_id", "subject", "message"]
  }'::jsonb,
  'create_ticket',
  'ticket'
),

(
  'lookup_order',
  'Lookup Order',
  'Retrieve order status, tracking details, and delivery information by order ID.',
  '{
    "type": "object",
    "properties": {
      "order_id": { "type": "string", "description": "Order ID or reference number" }
    },
    "required": ["order_id"]
  }'::jsonb,
  'lookup_order',
  'order'
),

(
  'escalate_to_human',
  'Escalate to Human',
  'Hand off the current conversation to a human operator with an optional escalation reason.',
  '{
    "type": "object",
    "properties": {
      "reason":    { "type": "string", "description": "Reason for escalating to a human" },
      "ticket_id": { "type": "string", "description": "Ticket UUID to escalate" }
    },
    "required": ["reason"]
  }'::jsonb,
  'escalate_to_human',
  'system'
)

ON CONFLICT (name) DO NOTHING;
