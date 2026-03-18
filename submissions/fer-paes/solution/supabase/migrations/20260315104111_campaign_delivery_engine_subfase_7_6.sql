/*
  # Campaign Delivery Engine — Subfase 7.6

  ## Descrição
  Cria o motor de entrega de campanhas, responsável pelo envio de mensagens
  para clientes através de múltiplos canais (email, whatsapp, chat, sms).

  ## Nova Tabela
  - `campaign_deliveries`: registro individual de envio por cliente/campanha,
    com controle de status (pending → sent → delivered / failed), timestamps
    de cada transição e mensagem de erro para falhas.

  ## Campos Principais
  - `campaign_id`      — FK para campaigns
  - `customer_id`      — FK para customers
  - `channel`          — email | whatsapp | chat | sms
  - `status`           — pending | sending | sent | delivered | failed | skipped
  - `message_body`     — mensagem renderizada após template substitution
  - `sent_at`          — timestamp de envio confirmado
  - `delivered_at`     — timestamp de entrega confirmada
  - `failed_at`        — timestamp de falha
  - `error_message`    — detalhe do erro
  - `retry_count`      — número de tentativas de reenvio

  ## Funções SQL
  - `execute_campaign(UUID)`:           gera deliveries para clientes do segmento
  - `get_deliveries(...)`:              lista deliveries com filtros e paginação
  - `get_campaign_deliveries(UUID)`:    deliveries de uma campanha específica
  - `get_campaign_delivery_stats(UUID)`:stats de uma campanha (total/sent/failed/etc)
  - `get_pending_deliveries(INT)`:      deliveries prontos para envio pelo worker
  - `update_delivery_status(...)`:      atualiza status + timestamp da transição
  - `retry_failed_deliveries(UUID)`:    recoloca deliveries falhados em pending

  ## Segurança
  - RLS habilitado
  - Funções SECURITY DEFINER

  ## Permissões
  - `campaigns.view` já existe — nenhuma nova permissão necessária
*/

-- ─── Tabela: campaign_deliveries ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS campaign_deliveries (
  id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id   UUID        NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  customer_id   UUID        NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
  channel       TEXT        NOT NULL DEFAULT 'email'
                              CHECK (channel IN ('email','whatsapp','chat','sms')),
  status        TEXT        NOT NULL DEFAULT 'pending'
                              CHECK (status IN ('pending','sending','sent','delivered','failed','skipped')),
  message_body  TEXT,
  sent_at       TIMESTAMPTZ,
  delivered_at  TIMESTAMPTZ,
  failed_at     TIMESTAMPTZ,
  error_message TEXT,
  retry_count   INTEGER     NOT NULL DEFAULT 0,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (campaign_id, customer_id)
);

CREATE INDEX IF NOT EXISTS idx_campaign_deliveries_campaign ON campaign_deliveries(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaign_deliveries_customer ON campaign_deliveries(customer_id);
CREATE INDEX IF NOT EXISTS idx_campaign_deliveries_status   ON campaign_deliveries(status);
CREATE INDEX IF NOT EXISTS idx_campaign_deliveries_channel  ON campaign_deliveries(channel);
CREATE INDEX IF NOT EXISTS idx_campaign_deliveries_created  ON campaign_deliveries(created_at DESC);

ALTER TABLE campaign_deliveries ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated can read campaign_deliveries"
  ON campaign_deliveries FOR SELECT TO authenticated USING (true);

CREATE POLICY "Authenticated can insert campaign_deliveries"
  ON campaign_deliveries FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "Authenticated can update campaign_deliveries"
  ON campaign_deliveries FOR UPDATE TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY "Authenticated can delete campaign_deliveries"
  ON campaign_deliveries FOR DELETE TO authenticated USING (true);

-- ─── Trigger: updated_at ─────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_campaign_delivery_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END; $$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_campaign_deliveries_updated_at') THEN
    CREATE TRIGGER trg_campaign_deliveries_updated_at
      BEFORE UPDATE ON campaign_deliveries
      FOR EACH ROW EXECUTE FUNCTION update_campaign_delivery_updated_at();
  END IF;
END $$;

-- ─── Função: render_template ──────────────────────────────────────────────────
-- Substitui {{customer_name}}, {{customer_email}}, {{customer_phone}} no template.

CREATE OR REPLACE FUNCTION render_template(
  p_template TEXT,
  p_name     TEXT,
  p_email    TEXT,
  p_phone    TEXT
)
RETURNS TEXT
LANGUAGE sql IMMUTABLE
AS $$
  SELECT
    replace(
      replace(
        replace(p_template, '{{customer_name}}',  COALESCE(p_name,  '')),
        '{{customer_email}}', COALESCE(p_email, '')
      ),
      '{{customer_phone}}', COALESCE(p_phone, '')
    );
$$;

-- ─── Função: execute_campaign ─────────────────────────────────────────────────
-- Gera registros campaign_deliveries para cada membro do segmento da campanha.
-- Respeita unicidade (campaign_id, customer_id) — não duplica.

CREATE OR REPLACE FUNCTION execute_campaign(p_campaign_id UUID)
RETURNS INTEGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
DECLARE
  v_campaign  RECORD;
  v_customer  RECORD;
  v_body      TEXT;
  v_count     INTEGER := 0;
BEGIN
  SELECT * INTO v_campaign FROM campaigns WHERE id = p_campaign_id;
  IF NOT FOUND THEN RAISE EXCEPTION 'Campaign not found: %', p_campaign_id; END IF;

  FOR v_customer IN (
    SELECT c.id, c.name, c.email, c.phone
    FROM customers c
    WHERE (
      v_campaign.segment_id IS NULL
      OR EXISTS (
        SELECT 1 FROM segment_members sm
        WHERE sm.segment_id = v_campaign.segment_id
          AND sm.customer_id = c.id
      )
    )
  ) LOOP
    v_body := render_template(
      COALESCE(v_campaign.message_template, v_campaign.content, ''),
      v_customer.name,
      v_customer.email,
      v_customer.phone
    );

    INSERT INTO campaign_deliveries (campaign_id, customer_id, channel, status, message_body)
    VALUES (p_campaign_id, v_customer.id, v_campaign.channel, 'pending', v_body)
    ON CONFLICT (campaign_id, customer_id) DO NOTHING;

    v_count := v_count + 1;
  END LOOP;

  RETURN v_count;
END;
$$;

-- ─── Função: get_deliveries ───────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION get_deliveries(
  p_campaign_id UUID    DEFAULT NULL,
  p_status      TEXT    DEFAULT NULL,
  p_channel     TEXT    DEFAULT NULL,
  p_limit       INTEGER DEFAULT 100,
  p_offset      INTEGER DEFAULT 0
)
RETURNS TABLE (
  id            UUID,
  campaign_id   UUID,
  campaign_name TEXT,
  customer_id   UUID,
  customer_name TEXT,
  customer_email TEXT,
  channel       TEXT,
  status        TEXT,
  message_body  TEXT,
  sent_at       TIMESTAMPTZ,
  delivered_at  TIMESTAMPTZ,
  failed_at     TIMESTAMPTZ,
  error_message TEXT,
  retry_count   INTEGER,
  created_at    TIMESTAMPTZ
)
LANGUAGE sql SECURITY DEFINER SET search_path = public
AS $$
  SELECT
    cd.id,
    cd.campaign_id,  c.name  AS campaign_name,
    cd.customer_id,  cu.name AS customer_name, cu.email AS customer_email,
    cd.channel, cd.status, cd.message_body,
    cd.sent_at, cd.delivered_at, cd.failed_at,
    cd.error_message, cd.retry_count, cd.created_at
  FROM campaign_deliveries cd
  JOIN campaigns  c  ON c.id  = cd.campaign_id
  JOIN customers  cu ON cu.id = cd.customer_id
  WHERE (p_campaign_id IS NULL OR cd.campaign_id = p_campaign_id)
    AND (p_status      IS NULL OR cd.status      = p_status)
    AND (p_channel     IS NULL OR cd.channel     = p_channel)
  ORDER BY cd.created_at DESC
  LIMIT p_limit OFFSET p_offset;
$$;

-- ─── Função: get_campaign_delivery_stats ──────────────────────────────────────

CREATE OR REPLACE FUNCTION get_campaign_delivery_stats(p_campaign_id UUID)
RETURNS TABLE (
  total         BIGINT,
  pending       BIGINT,
  sending       BIGINT,
  sent          BIGINT,
  delivered     BIGINT,
  failed        BIGINT,
  skipped       BIGINT,
  delivery_rate NUMERIC
)
LANGUAGE sql SECURITY DEFINER SET search_path = public
AS $$
  SELECT
    COUNT(*)                                                          AS total,
    COUNT(*) FILTER (WHERE status = 'pending')                        AS pending,
    COUNT(*) FILTER (WHERE status = 'sending')                        AS sending,
    COUNT(*) FILTER (WHERE status = 'sent')                           AS sent,
    COUNT(*) FILTER (WHERE status = 'delivered')                      AS delivered,
    COUNT(*) FILTER (WHERE status = 'failed')                         AS failed,
    COUNT(*) FILTER (WHERE status = 'skipped')                        AS skipped,
    CASE WHEN COUNT(*) = 0 THEN 0
         ELSE ROUND(
           COUNT(*) FILTER (WHERE status IN ('sent','delivered'))::NUMERIC
           / COUNT(*)::NUMERIC * 100, 1
         )
    END                                                               AS delivery_rate
  FROM campaign_deliveries
  WHERE campaign_id = p_campaign_id;
$$;

-- ─── Função: get_pending_deliveries ───────────────────────────────────────────
-- Usado pelo worker para buscar próximas mensagens a enviar.

CREATE OR REPLACE FUNCTION get_pending_deliveries(p_limit INTEGER DEFAULT 50)
RETURNS TABLE (
  id           UUID,
  campaign_id  UUID,
  customer_id  UUID,
  customer_name TEXT,
  customer_email TEXT,
  customer_phone TEXT,
  channel      TEXT,
  message_body TEXT,
  retry_count  INTEGER
)
LANGUAGE sql SECURITY DEFINER SET search_path = public
AS $$
  SELECT
    cd.id, cd.campaign_id, cd.customer_id,
    cu.name AS customer_name, cu.email AS customer_email, cu.phone AS customer_phone,
    cd.channel, cd.message_body, cd.retry_count
  FROM campaign_deliveries cd
  JOIN customers cu ON cu.id = cd.customer_id
  JOIN campaigns c  ON c.id  = cd.campaign_id
  WHERE cd.status = 'pending'
    AND c.status IN ('running','scheduled')
  ORDER BY cd.created_at ASC
  LIMIT p_limit;
$$;

-- ─── Função: update_delivery_status ──────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_delivery_status(
  p_id          UUID,
  p_status      TEXT,
  p_error       TEXT DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  UPDATE campaign_deliveries SET
    status        = p_status,
    sent_at       = CASE WHEN p_status = 'sent'       THEN NOW() ELSE sent_at       END,
    delivered_at  = CASE WHEN p_status = 'delivered'  THEN NOW() ELSE delivered_at  END,
    failed_at     = CASE WHEN p_status = 'failed'     THEN NOW() ELSE failed_at     END,
    error_message = CASE WHEN p_status = 'failed'     THEN p_error ELSE error_message END,
    retry_count   = CASE WHEN p_status = 'failed'     THEN retry_count + 1 ELSE retry_count END
  WHERE id = p_id;
END;
$$;

-- ─── Função: retry_failed_deliveries ────────────────────────────────────────

CREATE OR REPLACE FUNCTION retry_failed_deliveries(p_campaign_id UUID)
RETURNS INTEGER
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
DECLARE v_count INTEGER;
BEGIN
  UPDATE campaign_deliveries
  SET status        = 'pending',
      failed_at     = NULL,
      error_message = NULL
  WHERE campaign_id = p_campaign_id
    AND status      = 'failed'
    AND retry_count < 3;

  GET DIAGNOSTICS v_count = ROW_COUNT;
  RETURN v_count;
END;
$$;

-- ─── Permissão campaigns.view para marketing ────────────────────────────────

INSERT INTO permissions (name, description, category)
VALUES ('campaigns.view', 'Visualizar campanhas e entregas', 'analytics')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
  FROM roles r, permissions p
 WHERE r.name IN ('admin', 'supervisor')
   AND p.name = 'campaigns.view'
ON CONFLICT DO NOTHING;
