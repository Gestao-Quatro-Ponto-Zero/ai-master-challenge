/*
  # Campaign Analytics — Subfase 7.7

  ## Descrição
  Cria o sistema de métricas de performance de campanhas, permitindo medir
  envios, entregas, aberturas, cliques, respostas e conversões.

  ## Nova Tabela
  - `campaign_metrics`: uma linha por campanha com contadores agregados.
    Calculada a partir de campaign_deliveries e atualizada via eventos.
    Campos: sent_count, delivered_count, open_count, click_count,
            reply_count, conversion_count.

  ## Nova Tabela
  - `campaign_interaction_events`: log individual de interações por
    (campaign_id, customer_id, event_type). Garante idempotência via UNIQUE.

  ## Funções SQL
  - `sync_campaign_metrics(UUID)`:             recalcula contadores a partir de deliveries
  - `sync_all_campaign_metrics()`:             sincroniza todas as campanhas de uma vez
  - `register_campaign_event(UUID,UUID,TEXT)`: registra evento e incrementa contador
  - `get_campaign_metrics(UUID)`:              retorna métricas de uma campanha
  - `get_all_campaign_analytics()`:            todas as campanhas com métricas + taxas
  - `get_campaign_analytics_overview()`:       totais globais para overview cards
  - `get_campaign_events_timeseries(UUID,INT)`:série temporal de eventos

  ## Segurança
  - RLS habilitado em ambas as tabelas
  - Funções SECURITY DEFINER

  ## Permissões
  - Nova permissão `campaigns.analytics` para admin e supervisor

  ## Nota
  - customer_segments usa coluna `segment_name` (não `name`)
*/

-- ─── Tabela: campaign_metrics ────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS campaign_metrics (
  id                UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id       UUID    NOT NULL UNIQUE REFERENCES campaigns(id) ON DELETE CASCADE,
  sent_count        INTEGER NOT NULL DEFAULT 0,
  delivered_count   INTEGER NOT NULL DEFAULT 0,
  open_count        INTEGER NOT NULL DEFAULT 0,
  click_count       INTEGER NOT NULL DEFAULT 0,
  reply_count       INTEGER NOT NULL DEFAULT 0,
  conversion_count  INTEGER NOT NULL DEFAULT 0,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_campaign_metrics_campaign ON campaign_metrics(campaign_id);

ALTER TABLE campaign_metrics ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated can read campaign_metrics"
  ON campaign_metrics FOR SELECT TO authenticated USING (true);

CREATE POLICY "Authenticated can insert campaign_metrics"
  ON campaign_metrics FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "Authenticated can update campaign_metrics"
  ON campaign_metrics FOR UPDATE TO authenticated USING (true) WITH CHECK (true);

-- ─── Tabela: campaign_interaction_events ─────────────────────────────────────

CREATE TABLE IF NOT EXISTS campaign_interaction_events (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id UUID        NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  customer_id UUID        NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
  event_type  TEXT        NOT NULL
                            CHECK (event_type IN (
                              'campaign_sent','campaign_delivered',
                              'campaign_opened','campaign_clicked',
                              'campaign_replied','campaign_converted'
                            )),
  metadata    JSONB,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (campaign_id, customer_id, event_type)
);

CREATE INDEX IF NOT EXISTS idx_camp_interaction_campaign ON campaign_interaction_events(campaign_id);
CREATE INDEX IF NOT EXISTS idx_camp_interaction_event    ON campaign_interaction_events(event_type);
CREATE INDEX IF NOT EXISTS idx_camp_interaction_created  ON campaign_interaction_events(created_at DESC);

ALTER TABLE campaign_interaction_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated can read campaign_interaction_events"
  ON campaign_interaction_events FOR SELECT TO authenticated USING (true);

CREATE POLICY "Authenticated can insert campaign_interaction_events"
  ON campaign_interaction_events FOR INSERT TO authenticated WITH CHECK (true);

-- ─── Trigger: updated_at para campaign_metrics ───────────────────────────────

CREATE OR REPLACE FUNCTION update_campaign_metrics_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END; $$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_campaign_metrics_updated_at') THEN
    CREATE TRIGGER trg_campaign_metrics_updated_at
      BEFORE UPDATE ON campaign_metrics
      FOR EACH ROW EXECUTE FUNCTION update_campaign_metrics_updated_at();
  END IF;
END $$;

-- ─── Função: sync_campaign_metrics ───────────────────────────────────────────

CREATE OR REPLACE FUNCTION sync_campaign_metrics(p_campaign_id UUID)
RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
DECLARE
  v_sent      INTEGER;
  v_delivered INTEGER;
BEGIN
  SELECT
    COUNT(*) FILTER (WHERE status IN ('sent','delivered')),
    COUNT(*) FILTER (WHERE status = 'delivered')
  INTO v_sent, v_delivered
  FROM campaign_deliveries
  WHERE campaign_id = p_campaign_id;

  INSERT INTO campaign_metrics (campaign_id, sent_count, delivered_count)
  VALUES (p_campaign_id, v_sent, v_delivered)
  ON CONFLICT (campaign_id) DO UPDATE
    SET sent_count      = EXCLUDED.sent_count,
        delivered_count = EXCLUDED.delivered_count;
END;
$$;

-- ─── Função: sync_all_campaign_metrics ───────────────────────────────────────

CREATE OR REPLACE FUNCTION sync_all_campaign_metrics()
RETURNS INTEGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
DECLARE
  v_rec   RECORD;
  v_count INTEGER := 0;
BEGIN
  FOR v_rec IN (SELECT DISTINCT campaign_id FROM campaign_deliveries) LOOP
    PERFORM sync_campaign_metrics(v_rec.campaign_id);
    v_count := v_count + 1;
  END LOOP;
  RETURN v_count;
END;
$$;

-- ─── Função: register_campaign_event ──────────────────────────────────────────

CREATE OR REPLACE FUNCTION register_campaign_event(
  p_campaign_id UUID,
  p_customer_id UUID,
  p_event_type  TEXT,
  p_metadata    JSONB DEFAULT NULL
)
RETURNS BOOLEAN
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
DECLARE
  v_count INTEGER;
BEGIN
  INSERT INTO campaign_interaction_events (campaign_id, customer_id, event_type, metadata)
  VALUES (p_campaign_id, p_customer_id, p_event_type, p_metadata)
  ON CONFLICT (campaign_id, customer_id, event_type) DO NOTHING;

  GET DIAGNOSTICS v_count = ROW_COUNT;

  IF v_count > 0 THEN
    INSERT INTO campaign_metrics (campaign_id,
      sent_count, delivered_count, open_count, click_count, reply_count, conversion_count)
    VALUES (p_campaign_id, 0, 0, 0, 0, 0, 0)
    ON CONFLICT (campaign_id) DO NOTHING;

    UPDATE campaign_metrics SET
      sent_count       = sent_count       + CASE WHEN p_event_type = 'campaign_sent'      THEN 1 ELSE 0 END,
      delivered_count  = delivered_count  + CASE WHEN p_event_type = 'campaign_delivered' THEN 1 ELSE 0 END,
      open_count       = open_count       + CASE WHEN p_event_type = 'campaign_opened'    THEN 1 ELSE 0 END,
      click_count      = click_count      + CASE WHEN p_event_type = 'campaign_clicked'   THEN 1 ELSE 0 END,
      reply_count      = reply_count      + CASE WHEN p_event_type = 'campaign_replied'   THEN 1 ELSE 0 END,
      conversion_count = conversion_count + CASE WHEN p_event_type = 'campaign_converted' THEN 1 ELSE 0 END
    WHERE campaign_id = p_campaign_id;
  END IF;

  RETURN v_count > 0;
END;
$$;

-- ─── Função: get_campaign_metrics ────────────────────────────────────────────

CREATE OR REPLACE FUNCTION get_campaign_metrics(p_campaign_id UUID)
RETURNS TABLE (
  campaign_id       UUID,
  sent_count        INTEGER,
  delivered_count   INTEGER,
  open_count        INTEGER,
  click_count       INTEGER,
  reply_count       INTEGER,
  conversion_count  INTEGER,
  open_rate         NUMERIC,
  click_rate        NUMERIC,
  reply_rate        NUMERIC,
  conversion_rate   NUMERIC,
  updated_at        TIMESTAMPTZ
)
LANGUAGE sql SECURITY DEFINER SET search_path = public
AS $$
  SELECT
    m.campaign_id,
    m.sent_count,
    m.delivered_count,
    m.open_count,
    m.click_count,
    m.reply_count,
    m.conversion_count,
    CASE WHEN m.delivered_count = 0 THEN 0
         ELSE ROUND(m.open_count::NUMERIC       / m.delivered_count * 100, 1) END,
    CASE WHEN m.delivered_count = 0 THEN 0
         ELSE ROUND(m.click_count::NUMERIC      / m.delivered_count * 100, 1) END,
    CASE WHEN m.delivered_count = 0 THEN 0
         ELSE ROUND(m.reply_count::NUMERIC      / m.delivered_count * 100, 1) END,
    CASE WHEN m.delivered_count = 0 THEN 0
         ELSE ROUND(m.conversion_count::NUMERIC / m.delivered_count * 100, 1) END,
    m.updated_at
  FROM campaign_metrics m
  WHERE m.campaign_id = p_campaign_id;
$$;

-- ─── Função: get_all_campaign_analytics ──────────────────────────────────────

CREATE OR REPLACE FUNCTION get_all_campaign_analytics()
RETURNS TABLE (
  campaign_id       UUID,
  campaign_name     TEXT,
  campaign_status   TEXT,
  campaign_channel  TEXT,
  segment_name      TEXT,
  sent_count        INTEGER,
  delivered_count   INTEGER,
  open_count        INTEGER,
  click_count       INTEGER,
  reply_count       INTEGER,
  conversion_count  INTEGER,
  open_rate         NUMERIC,
  click_rate        NUMERIC,
  reply_rate        NUMERIC,
  conversion_rate   NUMERIC,
  updated_at        TIMESTAMPTZ
)
LANGUAGE sql SECURITY DEFINER SET search_path = public
AS $$
  SELECT
    c.id            AS campaign_id,
    c.name          AS campaign_name,
    c.status        AS campaign_status,
    c.channel       AS campaign_channel,
    s.segment_name  AS segment_name,
    COALESCE(m.sent_count,       0) AS sent_count,
    COALESCE(m.delivered_count,  0) AS delivered_count,
    COALESCE(m.open_count,       0) AS open_count,
    COALESCE(m.click_count,      0) AS click_count,
    COALESCE(m.reply_count,      0) AS reply_count,
    COALESCE(m.conversion_count, 0) AS conversion_count,
    CASE WHEN COALESCE(m.delivered_count,0) = 0 THEN 0
         ELSE ROUND(COALESCE(m.open_count,0)::NUMERIC       / m.delivered_count * 100, 1) END AS open_rate,
    CASE WHEN COALESCE(m.delivered_count,0) = 0 THEN 0
         ELSE ROUND(COALESCE(m.click_count,0)::NUMERIC      / m.delivered_count * 100, 1) END AS click_rate,
    CASE WHEN COALESCE(m.delivered_count,0) = 0 THEN 0
         ELSE ROUND(COALESCE(m.reply_count,0)::NUMERIC      / m.delivered_count * 100, 1) END AS reply_rate,
    CASE WHEN COALESCE(m.delivered_count,0) = 0 THEN 0
         ELSE ROUND(COALESCE(m.conversion_count,0)::NUMERIC / m.delivered_count * 100, 1) END AS conversion_rate,
    m.updated_at
  FROM campaigns c
  LEFT JOIN customer_segments s ON s.id = c.segment_id
  LEFT JOIN campaign_metrics m  ON m.campaign_id = c.id
  ORDER BY COALESCE(m.sent_count, 0) DESC, c.created_at DESC;
$$;

-- ─── Função: get_campaign_analytics_overview ─────────────────────────────────

CREATE OR REPLACE FUNCTION get_campaign_analytics_overview()
RETURNS TABLE (
  total_campaigns     BIGINT,
  total_sent          BIGINT,
  total_delivered     BIGINT,
  total_opens         BIGINT,
  total_clicks        BIGINT,
  total_replies       BIGINT,
  total_conversions   BIGINT,
  avg_open_rate       NUMERIC,
  avg_click_rate      NUMERIC,
  avg_conversion_rate NUMERIC
)
LANGUAGE sql SECURITY DEFINER SET search_path = public
AS $$
  SELECT
    COUNT(DISTINCT c.id)                        AS total_campaigns,
    COALESCE(SUM(m.sent_count),        0)       AS total_sent,
    COALESCE(SUM(m.delivered_count),   0)       AS total_delivered,
    COALESCE(SUM(m.open_count),        0)       AS total_opens,
    COALESCE(SUM(m.click_count),       0)       AS total_clicks,
    COALESCE(SUM(m.reply_count),       0)       AS total_replies,
    COALESCE(SUM(m.conversion_count),  0)       AS total_conversions,
    CASE WHEN COALESCE(SUM(m.delivered_count),0) = 0 THEN 0
         ELSE ROUND(COALESCE(SUM(m.open_count),0)::NUMERIC       / SUM(m.delivered_count) * 100, 1) END AS avg_open_rate,
    CASE WHEN COALESCE(SUM(m.delivered_count),0) = 0 THEN 0
         ELSE ROUND(COALESCE(SUM(m.click_count),0)::NUMERIC      / SUM(m.delivered_count) * 100, 1) END AS avg_click_rate,
    CASE WHEN COALESCE(SUM(m.delivered_count),0) = 0 THEN 0
         ELSE ROUND(COALESCE(SUM(m.conversion_count),0)::NUMERIC / SUM(m.delivered_count) * 100, 1) END AS avg_conversion_rate
  FROM campaigns c
  LEFT JOIN campaign_metrics m ON m.campaign_id = c.id;
$$;

-- ─── Função: get_campaign_events_timeseries ──────────────────────────────────

CREATE OR REPLACE FUNCTION get_campaign_events_timeseries(
  p_campaign_id UUID    DEFAULT NULL,
  p_days        INTEGER DEFAULT 30
)
RETURNS TABLE (
  day        DATE,
  event_type TEXT,
  count      BIGINT
)
LANGUAGE sql SECURITY DEFINER SET search_path = public
AS $$
  SELECT
    DATE(created_at) AS day,
    event_type,
    COUNT(*)         AS count
  FROM campaign_interaction_events
  WHERE created_at >= NOW() - (p_days || ' days')::INTERVAL
    AND (p_campaign_id IS NULL OR campaign_id = p_campaign_id)
  GROUP BY DATE(created_at), event_type
  ORDER BY day ASC, event_type;
$$;

-- ─── Permissão: campaigns.analytics ─────────────────────────────────────────

INSERT INTO permissions (name, description, category)
VALUES ('campaigns.analytics', 'Visualizar analytics e métricas de campanhas', 'analytics')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
  FROM roles r, permissions p
 WHERE r.name IN ('admin', 'supervisor')
   AND p.name = 'campaigns.analytics'
ON CONFLICT DO NOTHING;

-- ─── Seed: sincronizar métricas de deliveries existentes ─────────────────────

SELECT sync_all_campaign_metrics();
