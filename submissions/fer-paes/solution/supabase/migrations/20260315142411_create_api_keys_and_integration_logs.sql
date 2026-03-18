/*
  # API Keys and Integration Logs

  ## Overview
  Creates the infrastructure needed for external system integrations (bots, websites,
  CRM connectors, etc.) to authenticate with and send data into the platform without
  requiring a Supabase user account.

  ## New Tables

  ### api_keys
  Manages application-level API keys issued to external integrations.
  - `id` — UUID primary key
  - `name` — Human-friendly label (e.g. "Website Chat Widget")
  - `key_prefix` — First 8 chars of the key shown in the UI (e.g. "sk_live_")
  - `key_hash` — SHA-256 hash of the full key (never stored in plaintext)
  - `scopes` — Array of permitted scopes (e.g. ['channel:ingest', 'events:write'])
  - `channel_type` — Optional: locks key to a specific channel (chat|email|api|bot)
  - `rate_limit_per_minute` — Max requests per minute (default 60)
  - `is_active` — Whether the key can be used
  - `last_used_at` — Timestamp of last successful request
  - `request_count` — Running total of requests made with this key
  - `expires_at` — Optional expiry date
  - `created_by` — FK to auth.users (who created this key)
  - `created_at` / `updated_at`

  ### integration_logs
  Append-only log of every inbound request authenticated with an API key.
  - `id` — UUID primary key
  - `api_key_id` — FK to api_keys.id (nullable: keeps logs if key is deleted)
  - `key_prefix` — Snapshot of prefix for display even if key is deleted
  - `endpoint` — Which endpoint was called (e.g. "/channel-ingest/chat")
  - `method` — HTTP method
  - `status_code` — HTTP response status
  - `ip_address` — Source IP (text)
  - `request_payload` — JSONB snapshot of the incoming body (truncated for large payloads)
  - `response_payload` — JSONB snapshot of the outgoing body
  - `error_message` — Error description when status >= 400
  - `duration_ms` — Request processing time
  - `created_at`

  ## Security
  - RLS enabled on both tables
  - api_keys: authenticated users with `integrations.manage` permission can CRUD
  - integration_logs: read via `integrations.manage`, insert by service role
  - No delete on integration_logs (immutable audit trail)

  ## New Permission
  - `integrations.manage` — Full access to API keys and integration logs
    Assigned to: admin, supervisor
*/

-- ── api_keys ──────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS api_keys (
  id                    UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  name                  TEXT        NOT NULL,
  key_prefix            TEXT        NOT NULL,
  key_hash              TEXT        NOT NULL,
  scopes                TEXT[]      NOT NULL DEFAULT '{}',
  channel_type          TEXT,
  rate_limit_per_minute INTEGER     NOT NULL DEFAULT 60,
  is_active             BOOLEAN     NOT NULL DEFAULT true,
  last_used_at          TIMESTAMPTZ,
  request_count         BIGINT      NOT NULL DEFAULT 0,
  expires_at            TIMESTAMPTZ,
  created_by            UUID        REFERENCES auth.users(id) ON DELETE SET NULL,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_api_keys_created_by ON api_keys(created_by);
CREATE INDEX IF NOT EXISTS idx_api_keys_is_active  ON api_keys(is_active);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash   ON api_keys(key_hash);

CREATE OR REPLACE FUNCTION set_api_keys_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END; $$;

DROP TRIGGER IF EXISTS trg_api_keys_updated_at ON api_keys;
CREATE TRIGGER trg_api_keys_updated_at
  BEFORE UPDATE ON api_keys
  FOR EACH ROW EXECUTE FUNCTION set_api_keys_updated_at();

ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY "integrations.manage can view api_keys"
  ON api_keys FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM user_roles ur
      JOIN role_permissions rp ON rp.role_id = ur.role_id
      JOIN permissions p       ON p.id = rp.permission_id
      WHERE ur.user_id = auth.uid() AND p.name = 'integrations.manage'
    )
  );

CREATE POLICY "integrations.manage can insert api_keys"
  ON api_keys FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM user_roles ur
      JOIN role_permissions rp ON rp.role_id = ur.role_id
      JOIN permissions p       ON p.id = rp.permission_id
      WHERE ur.user_id = auth.uid() AND p.name = 'integrations.manage'
    )
  );

CREATE POLICY "integrations.manage can update api_keys"
  ON api_keys FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM user_roles ur
      JOIN role_permissions rp ON rp.role_id = ur.role_id
      JOIN permissions p       ON p.id = rp.permission_id
      WHERE ur.user_id = auth.uid() AND p.name = 'integrations.manage'
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM user_roles ur
      JOIN role_permissions rp ON rp.role_id = ur.role_id
      JOIN permissions p       ON p.id = rp.permission_id
      WHERE ur.user_id = auth.uid() AND p.name = 'integrations.manage'
    )
  );

CREATE POLICY "integrations.manage can delete api_keys"
  ON api_keys FOR DELETE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM user_roles ur
      JOIN role_permissions rp ON rp.role_id = ur.role_id
      JOIN permissions p       ON p.id = rp.permission_id
      WHERE ur.user_id = auth.uid() AND p.name = 'integrations.manage'
    )
  );

-- ── integration_logs ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS integration_logs (
  id               UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  api_key_id       UUID        REFERENCES api_keys(id) ON DELETE SET NULL,
  key_prefix       TEXT,
  endpoint         TEXT        NOT NULL,
  method           TEXT        NOT NULL DEFAULT 'POST',
  status_code      INTEGER     NOT NULL DEFAULT 200,
  ip_address       TEXT,
  request_payload  JSONB,
  response_payload JSONB,
  error_message    TEXT,
  duration_ms      INTEGER,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_integration_logs_api_key_id  ON integration_logs(api_key_id);
CREATE INDEX IF NOT EXISTS idx_integration_logs_created_at  ON integration_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_integration_logs_status_code ON integration_logs(status_code);
CREATE INDEX IF NOT EXISTS idx_integration_logs_key_prefix  ON integration_logs(key_prefix);

ALTER TABLE integration_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "integrations.manage can view integration_logs"
  ON integration_logs FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM user_roles ur
      JOIN role_permissions rp ON rp.role_id = ur.role_id
      JOIN permissions p       ON p.id = rp.permission_id
      WHERE ur.user_id = auth.uid() AND p.name = 'integrations.manage'
    )
  );

CREATE POLICY "Authenticated users can insert integration_logs"
  ON integration_logs FOR INSERT
  TO authenticated
  WITH CHECK (true);

-- ── Permission ─────────────────────────────────────────────────────────────────

INSERT INTO permissions (name, description, category)
VALUES ('integrations.manage', 'Manage API keys and view integration logs', 'system')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'admin' AND p.name = 'integrations.manage'
ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'supervisor' AND p.name = 'integrations.manage'
ON CONFLICT DO NOTHING;
