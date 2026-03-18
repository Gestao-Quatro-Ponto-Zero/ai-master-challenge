/*
  # Customer Analytics — Subfase 7.1

  ## Descrição
  Cria o sistema de analytics de clientes que consolida métricas de comportamento
  e atividade (mensagens, tickets, tempo de resposta, engajamento).

  ## Novas Tabelas
  - `customer_analytics`: registro único por cliente com todas as métricas consolidadas
    - total_messages: total de mensagens enviadas pelo cliente
    - total_tickets: total de tickets abertos pelo cliente
    - resolved_tickets: tickets resolvidos/fechados
    - avg_response_time: tempo médio de resposta em segundos (primeira resposta do operador)
    - last_interaction: data/hora da última mensagem
    - engagement_score: pontuação de engajamento (0–100)

  ## Funções SQL
  - `refresh_customer_analytics(UUID)`: recalcula todas as métricas para um cliente e faz upsert
  - `refresh_all_customer_analytics()`: recalcula para todos os clientes
  - `get_customer_analytics_summary()`: retorna métricas globais (totais e médias)
  - `get_customer_analytics_list(TEXT, INT, INT)`: listagem paginada com busca
  - `get_top_customers_by_engagement(INT)`: top N clientes por engagement score

  ## Permissões
  - Nova permissão `analytics.view` (categoria: analytics)
  - Concedida para roles: admin, supervisor

  ## Segurança
  - RLS habilitado
  - SELECT restrito a usuários autenticados
  - Escrita apenas via funções internas (SECURITY DEFINER)
*/

-- ─── Tabela principal ────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS customer_analytics (
  id                 UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id        UUID        NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
  total_messages     INTEGER     NOT NULL DEFAULT 0,
  total_tickets      INTEGER     NOT NULL DEFAULT 0,
  resolved_tickets   INTEGER     NOT NULL DEFAULT 0,
  avg_response_time  INTEGER,
  last_interaction   TIMESTAMPTZ,
  engagement_score   FLOAT       NOT NULL DEFAULT 0,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT customer_analytics_customer_unique UNIQUE (customer_id)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_customer_analytics_customer
  ON customer_analytics(customer_id);

CREATE INDEX IF NOT EXISTS idx_customer_analytics_engagement
  ON customer_analytics(engagement_score DESC);

CREATE INDEX IF NOT EXISTS idx_customer_analytics_last_interaction
  ON customer_analytics(last_interaction DESC NULLS LAST);

-- RLS
ALTER TABLE customer_analytics ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read customer analytics"
  ON customer_analytics FOR SELECT
  TO authenticated
  USING (true);

-- ─── Função: refresh_customer_analytics ─────────────────────────────────────

CREATE OR REPLACE FUNCTION refresh_customer_analytics(p_customer_id UUID)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_total_messages    INTEGER;
  v_total_tickets     INTEGER;
  v_resolved_tickets  INTEGER;
  v_avg_response      INTEGER;
  v_last_interaction  TIMESTAMPTZ;
  v_engagement_score  FLOAT;
  v_recency_bonus     FLOAT;
BEGIN
  -- Total de mensagens do cliente
  SELECT COUNT(*)
    INTO v_total_messages
    FROM messages m
    JOIN conversations c ON c.id = m.conversation_id
    JOIN tickets t ON t.id = c.ticket_id
   WHERE t.customer_id = p_customer_id;

  -- Total de tickets
  SELECT COUNT(*)
    INTO v_total_tickets
    FROM tickets
   WHERE customer_id = p_customer_id;

  -- Tickets resolvidos ou fechados
  SELECT COUNT(*)
    INTO v_resolved_tickets
    FROM tickets
   WHERE customer_id = p_customer_id
     AND status IN ('resolved', 'closed');

  -- Última interação (última mensagem)
  SELECT MAX(m.created_at)
    INTO v_last_interaction
    FROM messages m
    JOIN conversations c ON c.id = m.conversation_id
    JOIN tickets t ON t.id = c.ticket_id
   WHERE t.customer_id = p_customer_id;

  -- Tempo médio de resposta (em segundos) — primeira resposta do operador por conversa
  WITH first_customer AS (
    SELECT DISTINCT ON (m.conversation_id)
           m.conversation_id,
           m.created_at AS customer_msg_at
      FROM messages m
      JOIN conversations c ON c.id = m.conversation_id
      JOIN tickets t ON t.id = c.ticket_id
     WHERE t.customer_id = p_customer_id
       AND m.sender_type = 'customer'
     ORDER BY m.conversation_id, m.created_at ASC
  ),
  first_reply AS (
    SELECT DISTINCT ON (m.conversation_id)
           m.conversation_id,
           m.created_at AS reply_at
      FROM messages m
      JOIN conversations c ON c.id = m.conversation_id
      JOIN tickets t ON t.id = c.ticket_id
     WHERE t.customer_id = p_customer_id
       AND m.sender_type IN ('operator', 'agent')
     ORDER BY m.conversation_id, m.created_at ASC
  )
  SELECT ROUND(AVG(EXTRACT(EPOCH FROM (r.reply_at - fc.customer_msg_at))))::INTEGER
    INTO v_avg_response
    FROM first_customer fc
    JOIN first_reply r ON r.conversation_id = fc.conversation_id
   WHERE r.reply_at > fc.customer_msg_at;

  -- Bônus de recência para o engagement score
  v_recency_bonus := CASE
    WHEN v_last_interaction > NOW() - INTERVAL '7 days'  THEN 20.0
    WHEN v_last_interaction > NOW() - INTERVAL '30 days' THEN 12.0
    WHEN v_last_interaction > NOW() - INTERVAL '90 days' THEN 5.0
    ELSE 0.0
  END;

  -- Engagement score (0–100)
  v_engagement_score := LEAST(100.0,
    (COALESCE(v_total_messages, 0)::FLOAT * 2.0) +
    (COALESCE(v_total_tickets,  0)::FLOAT * 5.0) +
    v_recency_bonus
  );

  -- Upsert
  INSERT INTO customer_analytics (
    customer_id, total_messages, total_tickets, resolved_tickets,
    avg_response_time, last_interaction, engagement_score, updated_at
  ) VALUES (
    p_customer_id, v_total_messages, v_total_tickets, v_resolved_tickets,
    v_avg_response, v_last_interaction, v_engagement_score, NOW()
  )
  ON CONFLICT (customer_id) DO UPDATE SET
    total_messages   = EXCLUDED.total_messages,
    total_tickets    = EXCLUDED.total_tickets,
    resolved_tickets = EXCLUDED.resolved_tickets,
    avg_response_time = EXCLUDED.avg_response_time,
    last_interaction = EXCLUDED.last_interaction,
    engagement_score = EXCLUDED.engagement_score,
    updated_at       = NOW();
END;
$$;

-- ─── Função: refresh_all_customer_analytics ─────────────────────────────────

CREATE OR REPLACE FUNCTION refresh_all_customer_analytics()
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_count INTEGER := 0;
  r RECORD;
BEGIN
  FOR r IN SELECT id FROM customers LOOP
    PERFORM refresh_customer_analytics(r.id);
    v_count := v_count + 1;
  END LOOP;
  RETURN v_count;
END;
$$;

-- ─── Função: get_customer_analytics_summary ──────────────────────────────────

CREATE OR REPLACE FUNCTION get_customer_analytics_summary()
RETURNS TABLE (
  total_customers      BIGINT,
  active_customers     BIGINT,
  avg_engagement_score FLOAT,
  avg_tickets_per_customer FLOAT
)
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT
    (SELECT COUNT(*) FROM customers)                                      AS total_customers,
    (SELECT COUNT(*) FROM customer_analytics
      WHERE last_interaction > NOW() - INTERVAL '30 days')               AS active_customers,
    COALESCE(AVG(engagement_score), 0)                                   AS avg_engagement_score,
    COALESCE(AVG(total_tickets::FLOAT), 0)                               AS avg_tickets_per_customer
  FROM customer_analytics;
$$;

-- ─── Função: get_customer_analytics_list ─────────────────────────────────────

CREATE OR REPLACE FUNCTION get_customer_analytics_list(
  p_search TEXT    DEFAULT '',
  p_limit  INTEGER DEFAULT 50,
  p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
  customer_id       UUID,
  customer_name     TEXT,
  customer_email    TEXT,
  total_messages    INTEGER,
  total_tickets     INTEGER,
  resolved_tickets  INTEGER,
  avg_response_time INTEGER,
  last_interaction  TIMESTAMPTZ,
  engagement_score  FLOAT,
  updated_at        TIMESTAMPTZ
)
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT
    ca.customer_id,
    cu.name               AS customer_name,
    cu.email              AS customer_email,
    ca.total_messages,
    ca.total_tickets,
    ca.resolved_tickets,
    ca.avg_response_time,
    ca.last_interaction,
    ca.engagement_score,
    ca.updated_at
  FROM customer_analytics ca
  JOIN customers cu ON cu.id = ca.customer_id
  WHERE (
    p_search = ''
    OR cu.name  ILIKE '%' || p_search || '%'
    OR cu.email ILIKE '%' || p_search || '%'
  )
  ORDER BY ca.engagement_score DESC NULLS LAST
  LIMIT  p_limit
  OFFSET p_offset;
$$;

-- ─── Função: get_top_customers_by_engagement ─────────────────────────────────

CREATE OR REPLACE FUNCTION get_top_customers_by_engagement(p_limit INTEGER DEFAULT 10)
RETURNS TABLE (
  customer_id      UUID,
  customer_name    TEXT,
  customer_email   TEXT,
  total_messages   INTEGER,
  total_tickets    INTEGER,
  engagement_score FLOAT,
  last_interaction TIMESTAMPTZ
)
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT
    ca.customer_id,
    cu.name  AS customer_name,
    cu.email AS customer_email,
    ca.total_messages,
    ca.total_tickets,
    ca.engagement_score,
    ca.last_interaction
  FROM customer_analytics ca
  JOIN customers cu ON cu.id = ca.customer_id
  ORDER BY ca.engagement_score DESC NULLS LAST
  LIMIT p_limit;
$$;

-- ─── Permissão analytics.view ────────────────────────────────────────────────

INSERT INTO permissions (name, description, category)
VALUES ('analytics.view', 'Ver analytics de clientes', 'analytics')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
  FROM roles r, permissions p
 WHERE r.name IN ('admin', 'supervisor')
   AND p.name = 'analytics.view'
ON CONFLICT DO NOTHING;

-- ─── Seed inicial de analytics ────────────────────────────────────────────────
-- Garante que todos os clientes existentes já tenham um registro base

INSERT INTO customer_analytics (customer_id)
SELECT id FROM customers
ON CONFLICT (customer_id) DO NOTHING;
