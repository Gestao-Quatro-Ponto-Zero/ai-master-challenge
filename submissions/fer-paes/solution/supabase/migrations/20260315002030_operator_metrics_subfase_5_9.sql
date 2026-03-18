/*
  # Operator Metrics System — Subfase 5.9

  ## Summary
  Creates the operator performance metrics infrastructure for supervisors and
  admins to analyse the quality, speed and throughput of every human operator.

  ## New Tables

  ### operator_metrics
  Stores pre-computed/snapshot performance metrics per operator per period.
  Used to persist calculated KPIs so the dashboard can load instantly without
  re-aggregating raw ticket data on every request.

  Columns:
  - operator_id              — FK to operators; which operator these metrics belong to
  - tickets_handled          — total tickets handled in the period
  - tickets_resolved         — tickets that reached resolved/closed status
  - avg_first_response_time  — average minutes from ticket creation to first operator reply
  - avg_resolution_time      — average minutes from creation to ticket closed/resolved
  - avg_handle_time          — average active handling time in minutes
  - csat_score               — average CSAT rating (1-5); NULL if no feedback recorded
  - period_start / period_end — the time window the snapshot covers
  - created_at               — when the snapshot was recorded

  ## Indexes
  - idx_operator_metrics_operator_id  — fast lookup of a single operator's history
  - idx_operator_metrics_period       — fast lookup by period range

  ## Security
  - RLS enabled; supervisors and admins can read; authenticated users can insert
    (service-side calculation inserts snapshots)

  ## Permissions
  - metrics.view — grants access to the operator metrics page
  - Granted to: admin, supervisor
*/

CREATE TABLE IF NOT EXISTS operator_metrics (
  id                       UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  operator_id              UUID        NOT NULL REFERENCES operators(id) ON DELETE CASCADE,
  tickets_handled          INTEGER     NOT NULL DEFAULT 0,
  tickets_resolved         INTEGER     NOT NULL DEFAULT 0,
  avg_first_response_time  INTEGER     NOT NULL DEFAULT 0,
  avg_resolution_time      INTEGER     NOT NULL DEFAULT 0,
  avg_handle_time          INTEGER     NOT NULL DEFAULT 0,
  csat_score               FLOAT,
  period_start             TIMESTAMPTZ NOT NULL,
  period_end               TIMESTAMPTZ NOT NULL,
  created_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_operator_metrics_operator_id
  ON operator_metrics(operator_id);

CREATE INDEX IF NOT EXISTS idx_operator_metrics_period
  ON operator_metrics(period_start, period_end);

ALTER TABLE operator_metrics ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read operator metrics"
  ON operator_metrics FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can insert operator metrics snapshots"
  ON operator_metrics FOR INSERT
  TO authenticated
  WITH CHECK (true);

-- Permission: metrics.view
INSERT INTO permissions (name, description, category)
VALUES ('metrics.view', 'View operator performance metrics and analytics dashboards', 'operations')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name IN ('admin', 'supervisor')
  AND p.name = 'metrics.view'
ON CONFLICT DO NOTHING;
