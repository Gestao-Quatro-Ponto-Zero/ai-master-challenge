/*
  # Customer Segmentation — Subfase 7.3

  ## Descrição
  Cria o sistema de segmentação dinâmica de clientes.
  Permite agrupar clientes com base em regras de comportamento e atividade,
  servindo de base para campanhas, automações e análises.

  ## Novas Tabelas
  - `customer_segments`: define segmentos com nome, descrição, regras (JSONB) e flags de status
  - `segment_members`: relaciona clientes a segmentos, garantindo unicidade por par (segment, customer)

  ## Regras de Segmentação Suportadas (campo `rules`)
  - `last_interaction_days` (INT)  — dias desde a última interação (tickets, mensagens)
  - `min_messages`          (INT)  — mínimo de mensagens enviadas
  - `min_tickets`           (INT)  — mínimo de tickets criados
  - `min_engagement_score`  (FLOAT)— score mínimo de engajamento
  - `max_engagement_score`  (FLOAT)— score máximo de engajamento
  - `event_type`            (TEXT) — cliente deve ter gerado pelo menos um evento desse tipo
  - `min_events`            (INT)  — número mínimo de eventos do tipo acima

  ## Funções SQL
  - `create_segment(TEXT, TEXT, JSONB, BOOL)`: cria segmento
  - `update_segment(UUID, TEXT, TEXT, JSONB, BOOL, BOOL)`: atualiza segmento
  - `get_segments()`: lista todos os segmentos com contagem de membros
  - `get_segment_members(UUID, INT, INT)`: lista membros com dados do cliente
  - `refresh_segment_members(UUID)`: recalcula membros de um segmento dinâmico
  - `refresh_all_segments()`: recalcula todos os segmentos dinâmicos ativos

  ## Permissões
  - Nova permissão `segments.manage` (categoria: analytics)
  - Concedida para roles: admin, supervisor

  ## Segurança
  - RLS habilitado em ambas as tabelas
  - Restrição de unicidade (segment_id, customer_id) em segment_members
  - Funções SECURITY DEFINER para escritas seguras
*/

-- ─── Tabela: customer_segments ───────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS customer_segments (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  segment_name      TEXT        NOT NULL CHECK (char_length(segment_name) BETWEEN 1 AND 200),
  description       TEXT        NOT NULL DEFAULT '',
  rules             JSONB       NOT NULL DEFAULT '{}',
  is_dynamic        BOOLEAN     NOT NULL DEFAULT true,
  is_active         BOOLEAN     NOT NULL DEFAULT true,
  member_count      INTEGER     NOT NULL DEFAULT 0,
  last_refreshed_at TIMESTAMPTZ,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_customer_segments_active
  ON customer_segments(is_active);

CREATE INDEX IF NOT EXISTS idx_customer_segments_dynamic
  ON customer_segments(is_dynamic, is_active);

ALTER TABLE customer_segments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read segments"
  ON customer_segments FOR SELECT
  TO authenticated USING (true);

CREATE POLICY "Authenticated users can insert segments"
  ON customer_segments FOR INSERT
  TO authenticated WITH CHECK (true);

CREATE POLICY "Authenticated users can update segments"
  ON customer_segments FOR UPDATE
  TO authenticated USING (true) WITH CHECK (true);

-- ─── Tabela: segment_members ─────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS segment_members (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  segment_id  UUID        NOT NULL REFERENCES customer_segments(id) ON DELETE CASCADE,
  customer_id UUID        NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
  added_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (segment_id, customer_id)
);

CREATE INDEX IF NOT EXISTS idx_segment_members_segment
  ON segment_members(segment_id);

CREATE INDEX IF NOT EXISTS idx_segment_members_customer
  ON segment_members(customer_id);

ALTER TABLE segment_members ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read segment members"
  ON segment_members FOR SELECT
  TO authenticated USING (true);

CREATE POLICY "Authenticated users can insert segment members"
  ON segment_members FOR INSERT
  TO authenticated WITH CHECK (true);

CREATE POLICY "Authenticated users can delete segment members"
  ON segment_members FOR DELETE
  TO authenticated USING (true);

-- ─── Trigger: updated_at ─────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_segment_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'trg_customer_segments_updated_at'
  ) THEN
    CREATE TRIGGER trg_customer_segments_updated_at
      BEFORE UPDATE ON customer_segments
      FOR EACH ROW EXECUTE FUNCTION update_segment_updated_at();
  END IF;
END $$;

-- ─── Função: create_segment ──────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION create_segment(
  p_name        TEXT,
  p_description TEXT   DEFAULT '',
  p_rules       JSONB  DEFAULT '{}',
  p_is_dynamic  BOOL   DEFAULT true
)
RETURNS UUID
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
DECLARE v_id UUID;
BEGIN
  INSERT INTO customer_segments (segment_name, description, rules, is_dynamic)
  VALUES (p_name, COALESCE(p_description, ''), COALESCE(p_rules, '{}'), COALESCE(p_is_dynamic, true))
  RETURNING id INTO v_id;
  RETURN v_id;
END;
$$;

-- ─── Função: update_segment ──────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_segment(
  p_id          UUID,
  p_name        TEXT  DEFAULT NULL,
  p_description TEXT  DEFAULT NULL,
  p_rules       JSONB DEFAULT NULL,
  p_is_dynamic  BOOL  DEFAULT NULL,
  p_is_active   BOOL  DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  UPDATE customer_segments SET
    segment_name = COALESCE(p_name,        segment_name),
    description  = COALESCE(p_description, description),
    rules        = COALESCE(p_rules,       rules),
    is_dynamic   = COALESCE(p_is_dynamic,  is_dynamic),
    is_active    = COALESCE(p_is_active,   is_active)
  WHERE id = p_id;
END;
$$;

-- ─── Função: get_segments ────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION get_segments()
RETURNS TABLE (
  id                UUID,
  segment_name      TEXT,
  description       TEXT,
  rules             JSONB,
  is_dynamic        BOOLEAN,
  is_active         BOOLEAN,
  member_count      BIGINT,
  last_refreshed_at TIMESTAMPTZ,
  created_at        TIMESTAMPTZ,
  updated_at        TIMESTAMPTZ
)
LANGUAGE sql SECURITY DEFINER SET search_path = public
AS $$
  SELECT
    cs.id,
    cs.segment_name,
    cs.description,
    cs.rules,
    cs.is_dynamic,
    cs.is_active,
    COUNT(sm.id)         AS member_count,
    cs.last_refreshed_at,
    cs.created_at,
    cs.updated_at
  FROM customer_segments cs
  LEFT JOIN segment_members sm ON sm.segment_id = cs.id
  GROUP BY cs.id
  ORDER BY cs.created_at DESC;
$$;

-- ─── Função: get_segment_members ─────────────────────────────────────────────

CREATE OR REPLACE FUNCTION get_segment_members(
  p_segment_id UUID,
  p_limit      INTEGER DEFAULT 100,
  p_offset     INTEGER DEFAULT 0
)
RETURNS TABLE (
  member_id        UUID,
  customer_id      UUID,
  customer_name    TEXT,
  customer_email   TEXT,
  engagement_score NUMERIC,
  total_tickets    BIGINT,
  total_messages   BIGINT,
  added_at         TIMESTAMPTZ,
  total_count      BIGINT
)
LANGUAGE sql SECURITY DEFINER SET search_path = public
AS $$
  WITH members AS (
    SELECT
      sm.id                              AS member_id,
      sm.customer_id,
      c.name                             AS customer_name,
      c.email                            AS customer_email,
      COALESCE(ca.engagement_score, 0)   AS engagement_score,
      COALESCE(ca.total_tickets,    0)   AS total_tickets,
      COALESCE(ca.total_messages,   0)   AS total_messages,
      sm.added_at
    FROM segment_members sm
    JOIN  customers c  ON c.id  = sm.customer_id
    LEFT JOIN customer_analytics ca ON ca.customer_id = sm.customer_id
    WHERE sm.segment_id = p_segment_id
  )
  SELECT
    m.*,
    COUNT(*) OVER () AS total_count
  FROM members m
  ORDER BY m.added_at DESC
  LIMIT  p_limit
  OFFSET p_offset;
$$;

-- ─── Função: refresh_segment_members ─────────────────────────────────────────

CREATE OR REPLACE FUNCTION refresh_segment_members(p_segment_id UUID)
RETURNS INTEGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
DECLARE
  v_rules                 JSONB;
  v_is_dynamic            BOOLEAN;
  v_last_interaction_days INT;
  v_min_messages          INT;
  v_min_tickets           INT;
  v_min_eng               NUMERIC;
  v_max_eng               NUMERIC;
  v_event_type            TEXT;
  v_min_events            INT;
  v_count                 INT;
BEGIN
  SELECT rules, is_dynamic INTO v_rules, v_is_dynamic
    FROM customer_segments WHERE id = p_segment_id;

  IF NOT FOUND OR NOT v_is_dynamic THEN
    RETURN 0;
  END IF;

  v_last_interaction_days := (v_rules->>'last_interaction_days')::INT;
  v_min_messages          := (v_rules->>'min_messages')::INT;
  v_min_tickets           := (v_rules->>'min_tickets')::INT;
  v_min_eng               := (v_rules->>'min_engagement_score')::NUMERIC;
  v_max_eng               := (v_rules->>'max_engagement_score')::NUMERIC;
  v_event_type            :=  v_rules->>'event_type';
  v_min_events            := COALESCE((v_rules->>'min_events')::INT, 1);

  DELETE FROM segment_members WHERE segment_id = p_segment_id;

  INSERT INTO segment_members (segment_id, customer_id)
  SELECT DISTINCT p_segment_id, c.id
  FROM customers c
  LEFT JOIN customer_analytics ca ON ca.customer_id = c.id
  WHERE
    (v_last_interaction_days IS NULL
     OR ca.last_interaction IS NULL
     OR ca.last_interaction <= NOW() - (v_last_interaction_days || ' days')::INTERVAL)
    AND (v_min_messages IS NULL
         OR COALESCE(ca.total_messages, 0) >= v_min_messages)
    AND (v_min_tickets IS NULL
         OR COALESCE(ca.total_tickets, 0) >= v_min_tickets)
    AND (v_min_eng IS NULL
         OR COALESCE(ca.engagement_score, 0) >= v_min_eng)
    AND (v_max_eng IS NULL
         OR COALESCE(ca.engagement_score, 0) <= v_max_eng)
    AND (v_event_type IS NULL
         OR (
           SELECT COUNT(*)
             FROM customer_events ce
            WHERE ce.customer_id = c.id
              AND ce.event_type  = v_event_type
         ) >= v_min_events)
  ON CONFLICT (segment_id, customer_id) DO NOTHING;

  GET DIAGNOSTICS v_count = ROW_COUNT;

  UPDATE customer_segments
     SET member_count = v_count, last_refreshed_at = NOW()
   WHERE id = p_segment_id;

  RETURN v_count;
END;
$$;

-- ─── Função: refresh_all_segments ────────────────────────────────────────────

CREATE OR REPLACE FUNCTION refresh_all_segments()
RETURNS INTEGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
DECLARE
  v_seg   RECORD;
  v_total INT := 0;
BEGIN
  FOR v_seg IN
    SELECT id FROM customer_segments WHERE is_dynamic = true AND is_active = true
  LOOP
    PERFORM refresh_segment_members(v_seg.id);
    v_total := v_total + 1;
  END LOOP;
  RETURN v_total;
END;
$$;

-- ─── Permissão segments.manage ───────────────────────────────────────────────

INSERT INTO permissions (name, description, category)
VALUES ('segments.manage', 'Criar e gerenciar segmentos de clientes', 'analytics')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
  FROM roles r, permissions p
 WHERE r.name IN ('admin', 'supervisor')
   AND p.name = 'segments.manage'
ON CONFLICT DO NOTHING;
