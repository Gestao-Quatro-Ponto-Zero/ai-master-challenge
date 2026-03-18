/*
  # Event Tracking — Subfase 7.2

  ## Descrição
  Cria a infraestrutura de rastreamento de eventos do sistema.
  Registra ações importantes de clientes e do sistema de forma estruturada
  para alimentar analytics, segmentação e automações futuras.

  ## Nova Tabela
  - `customer_events`: log imutável de eventos
    - customer_id: cliente associado (pode ser nulo para eventos do sistema)
    - event_type: tipo do evento (message_sent, ticket_created, etc.)
    - event_data: dados adicionais flexíveis em JSONB
    - source: origem do evento (system, agent, campaign_engine, integration)
    - created_at: timestamp imutável da criação

  ## Tipos de Evento Suportados (exemplos)
  - message_sent, ticket_created, ticket_resolved
  - conversation_started, campaign_sent, campaign_opened, campaign_clicked
  - customer_created, ticket_assigned, ticket_escalated

  ## Funções SQL
  - `track_event(UUID, TEXT, JSONB, TEXT)`: registra novo evento
  - `get_events_paginated(TEXT, UUID, TEXT, TIMESTAMPTZ, TIMESTAMPTZ, INT, INT)`: listagem filtrada e paginada
  - `get_customer_events(UUID, INT, INT)`: histórico de eventos de um cliente
  - `get_events_by_type(TEXT, INT, INT)`: eventos por tipo
  - `get_event_type_summary()`: contagem de eventos por tipo (para analytics)

  ## Permissões
  - Nova permissão `events.view` (categoria: analytics)
  - Concedida para roles: admin, supervisor

  ## Segurança
  - RLS habilitado
  - Tabela é imutável: apenas INSERT é permitido via RLS (sem UPDATE, sem DELETE)
  - Leitura restrita a usuários autenticados
  - Escrita apenas via funções SECURITY DEFINER
*/

-- ─── Tabela principal ────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS customer_events (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id UUID        REFERENCES customers(id) ON DELETE SET NULL,
  event_type  TEXT        NOT NULL CHECK (char_length(event_type) BETWEEN 1 AND 100),
  event_data  JSONB       NOT NULL DEFAULT '{}',
  source      TEXT        NOT NULL DEFAULT 'system' CHECK (char_length(source) BETWEEN 1 AND 100),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_customer_events_customer
  ON customer_events(customer_id)
  WHERE customer_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_customer_events_type
  ON customer_events(event_type);

CREATE INDEX IF NOT EXISTS idx_customer_events_created
  ON customer_events(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_customer_events_source
  ON customer_events(source);

-- Índice composto para filtros frequentes
CREATE INDEX IF NOT EXISTS idx_customer_events_customer_type
  ON customer_events(customer_id, event_type)
  WHERE customer_id IS NOT NULL;

-- RLS
ALTER TABLE customer_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read events"
  ON customer_events FOR SELECT
  TO authenticated
  USING (true);

-- Inserção via funções SECURITY DEFINER apenas (não há policy INSERT pública)

-- ─── Função: track_event ─────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION track_event(
  p_customer_id UUID,
  p_event_type  TEXT,
  p_event_data  JSONB   DEFAULT '{}',
  p_source      TEXT    DEFAULT 'system'
)
RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_id UUID;
BEGIN
  INSERT INTO customer_events (customer_id, event_type, event_data, source)
  VALUES (p_customer_id, p_event_type, COALESCE(p_event_data, '{}'), COALESCE(p_source, 'system'))
  RETURNING id INTO v_id;
  RETURN v_id;
END;
$$;

-- ─── Função: get_events_paginated ─────────────────────────────────────────────

CREATE OR REPLACE FUNCTION get_events_paginated(
  p_search      TEXT        DEFAULT '',
  p_customer_id UUID        DEFAULT NULL,
  p_event_type  TEXT        DEFAULT NULL,
  p_source      TEXT        DEFAULT NULL,
  p_date_from   TIMESTAMPTZ DEFAULT NULL,
  p_date_to     TIMESTAMPTZ DEFAULT NULL,
  p_limit       INTEGER     DEFAULT 50,
  p_offset      INTEGER     DEFAULT 0
)
RETURNS TABLE (
  id            UUID,
  customer_id   UUID,
  customer_name TEXT,
  customer_email TEXT,
  event_type    TEXT,
  event_data    JSONB,
  source        TEXT,
  created_at    TIMESTAMPTZ,
  total_count   BIGINT
)
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  WITH filtered AS (
    SELECT
      ce.id,
      ce.customer_id,
      cu.name   AS customer_name,
      cu.email  AS customer_email,
      ce.event_type,
      ce.event_data,
      ce.source,
      ce.created_at
    FROM customer_events ce
    LEFT JOIN customers cu ON cu.id = ce.customer_id
    WHERE
      (p_customer_id IS NULL OR ce.customer_id = p_customer_id)
      AND (p_event_type IS NULL OR ce.event_type = p_event_type)
      AND (p_source     IS NULL OR ce.source     = p_source)
      AND (p_date_from  IS NULL OR ce.created_at >= p_date_from)
      AND (p_date_to    IS NULL OR ce.created_at <= p_date_to)
      AND (
        p_search = ''
        OR p_search IS NULL
        OR ce.event_type ILIKE '%' || p_search || '%'
        OR cu.name       ILIKE '%' || p_search || '%'
        OR cu.email      ILIKE '%' || p_search || '%'
        OR ce.source     ILIKE '%' || p_search || '%'
      )
  )
  SELECT
    f.id,
    f.customer_id,
    f.customer_name,
    f.customer_email,
    f.event_type,
    f.event_data,
    f.source,
    f.created_at,
    COUNT(*) OVER () AS total_count
  FROM filtered f
  ORDER BY f.created_at DESC
  LIMIT  p_limit
  OFFSET p_offset;
$$;

-- ─── Função: get_customer_events ─────────────────────────────────────────────

CREATE OR REPLACE FUNCTION get_customer_events(
  p_customer_id UUID,
  p_limit       INTEGER DEFAULT 100,
  p_offset      INTEGER DEFAULT 0
)
RETURNS TABLE (
  id          UUID,
  event_type  TEXT,
  event_data  JSONB,
  source      TEXT,
  created_at  TIMESTAMPTZ
)
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT id, event_type, event_data, source, created_at
  FROM customer_events
  WHERE customer_id = p_customer_id
  ORDER BY created_at DESC
  LIMIT  p_limit
  OFFSET p_offset;
$$;

-- ─── Função: get_events_by_type ──────────────────────────────────────────────

CREATE OR REPLACE FUNCTION get_events_by_type(
  p_event_type TEXT,
  p_limit      INTEGER DEFAULT 100,
  p_offset     INTEGER DEFAULT 0
)
RETURNS TABLE (
  id            UUID,
  customer_id   UUID,
  customer_name TEXT,
  event_data    JSONB,
  source        TEXT,
  created_at    TIMESTAMPTZ
)
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT
    ce.id,
    ce.customer_id,
    cu.name AS customer_name,
    ce.event_data,
    ce.source,
    ce.created_at
  FROM customer_events ce
  LEFT JOIN customers cu ON cu.id = ce.customer_id
  WHERE ce.event_type = p_event_type
  ORDER BY ce.created_at DESC
  LIMIT  p_limit
  OFFSET p_offset;
$$;

-- ─── Função: get_event_type_summary ──────────────────────────────────────────

CREATE OR REPLACE FUNCTION get_event_type_summary()
RETURNS TABLE (
  event_type TEXT,
  count      BIGINT,
  last_seen  TIMESTAMPTZ
)
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT
    event_type,
    COUNT(*)          AS count,
    MAX(created_at)   AS last_seen
  FROM customer_events
  GROUP BY event_type
  ORDER BY count DESC;
$$;

-- ─── Permissão events.view ───────────────────────────────────────────────────

INSERT INTO permissions (name, description, category)
VALUES ('events.view', 'Ver e monitorar eventos do sistema', 'analytics')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
  FROM roles r, permissions p
 WHERE r.name IN ('admin', 'supervisor')
   AND p.name = 'events.view'
ON CONFLICT DO NOTHING;
