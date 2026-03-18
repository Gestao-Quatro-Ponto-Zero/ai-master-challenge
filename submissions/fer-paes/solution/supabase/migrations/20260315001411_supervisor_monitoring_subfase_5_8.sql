/*
  # Supervisor Monitoring System — Subfase 5.8

  ## Summary
  Adds the infrastructure for real-time operational monitoring by supervisors.

  ## New Tables

  ### operation_metrics
  Optional snapshot table for recording point-in-time operational metrics.
  Allows historical trending and dashboards over time.
  - active_tickets      — count of in-progress / open tickets at snapshot time
  - queued_tickets      — count of tickets pending in queues
  - online_operators    — count of operators with status = online
  - busy_operators      — count of operators with status = busy
  - avg_response_time   — average first-response time in minutes (sampled period)
  - created_at          — when the snapshot was taken

  ## Indexes
  - idx_operation_metrics_created_at — enables fast time-range queries for trend analysis

  ## Security
  - RLS enabled; only authenticated users can read; only service-role / authenticated can insert

  ## Permissions
  - operations.monitor — grants access to the supervisor monitoring dashboard
  - Granted to: admin, supervisor
*/

CREATE TABLE IF NOT EXISTS operation_metrics (
  id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  active_tickets   INTEGER     NOT NULL DEFAULT 0,
  queued_tickets   INTEGER     NOT NULL DEFAULT 0,
  online_operators INTEGER     NOT NULL DEFAULT 0,
  busy_operators   INTEGER     NOT NULL DEFAULT 0,
  avg_response_time INTEGER    NOT NULL DEFAULT 0,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_operation_metrics_created_at
  ON operation_metrics(created_at DESC);

ALTER TABLE operation_metrics ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can insert snapshots"
  ON operation_metrics FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Authenticated users can read snapshots"
  ON operation_metrics FOR SELECT
  TO authenticated
  USING (true);

-- Permission: operations.monitor
INSERT INTO permissions (name, description, category)
VALUES ('operations.monitor', 'Access the supervisor monitoring dashboard and operational metrics', 'operations')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name IN ('admin', 'supervisor')
  AND p.name = 'operations.monitor'
ON CONFLICT DO NOTHING;
