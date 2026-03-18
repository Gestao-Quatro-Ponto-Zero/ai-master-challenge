/*
  # Campaign Management — Subfase 7.4

  ## Descrição
  Cria o sistema de gerenciamento de campanhas de comunicação com clientes.
  Uma campanha define o segmento alvo, canal, template de mensagem e status de execução.

  ## Nova Tabela
  - `campaigns`: armazena campanhas com nome, descrição, segmento, canal, template e status

  ## Campos Principais
  - `name`             — Nome da campanha
  - `description`      — Descrição opcional
  - `segment_id`       — FK para customer_segments (público-alvo)
  - `channel`          — Canal de envio: email | whatsapp | chat | sms
  - `message_template` — Template com suporte a variáveis: {{customer_name}}, etc.
  - `status`           — Ciclo de vida: draft → scheduled → running → completed | paused
  - `scheduled_at`     — Data/hora de execução agendada
  - `created_by`       — FK para profiles (usuário criador)

  ## Funções SQL
  - `create_campaign(...)`:      cria campanha com status draft
  - `update_campaign(...)`:      atualiza campos da campanha
  - `get_campaigns()`:           lista todas com info do segmento e criador
  - `get_campaign_by_id(UUID)`:  retorna campanha específica
  - `activate_campaign(UUID)`:   draft/paused → scheduled
  - `pause_campaign(UUID)`:      running/scheduled → paused
  - `complete_campaign(UUID)`:   running → completed
  - `delete_campaign(UUID)`:     remove campanha em draft

  ## Permissões
  - Nova permissão `campaigns.manage` (categoria: analytics)
  - Concedida para roles: admin, supervisor

  ## Segurança
  - RLS habilitado
  - Funções SECURITY DEFINER para escritas seguras
*/

-- ─── Tabela: campaigns ───────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS campaigns (
  id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  name             TEXT        NOT NULL CHECK (char_length(name) BETWEEN 1 AND 300),
  description      TEXT        NOT NULL DEFAULT '',
  segment_id       UUID        NOT NULL REFERENCES customer_segments(id) ON DELETE RESTRICT,
  channel          TEXT        NOT NULL CHECK (channel IN ('email','whatsapp','chat','sms')),
  message_template TEXT        NOT NULL DEFAULT '',
  status           TEXT        NOT NULL DEFAULT 'draft'
                               CHECK (status IN ('draft','scheduled','running','completed','paused')),
  scheduled_at     TIMESTAMPTZ,
  started_at       TIMESTAMPTZ,
  completed_at     TIMESTAMPTZ,
  created_by       UUID        REFERENCES profiles(id) ON DELETE SET NULL,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_campaigns_segment  ON campaigns(segment_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_status   ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_channel  ON campaigns(channel);
CREATE INDEX IF NOT EXISTS idx_campaigns_created  ON campaigns(created_at DESC);

-- RLS
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read campaigns"
  ON campaigns FOR SELECT TO authenticated USING (true);

CREATE POLICY "Authenticated users can insert campaigns"
  ON campaigns FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "Authenticated users can update campaigns"
  ON campaigns FOR UPDATE TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY "Authenticated users can delete campaigns"
  ON campaigns FOR DELETE TO authenticated USING (true);

-- ─── Trigger: updated_at ─────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_campaign_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END; $$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_campaigns_updated_at') THEN
    CREATE TRIGGER trg_campaigns_updated_at
      BEFORE UPDATE ON campaigns
      FOR EACH ROW EXECUTE FUNCTION update_campaign_updated_at();
  END IF;
END $$;

-- ─── Função: create_campaign ─────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION create_campaign(
  p_name             TEXT,
  p_description      TEXT     DEFAULT '',
  p_segment_id       UUID     DEFAULT NULL,
  p_channel          TEXT     DEFAULT 'email',
  p_message_template TEXT     DEFAULT '',
  p_scheduled_at     TIMESTAMPTZ DEFAULT NULL,
  p_created_by       UUID     DEFAULT NULL
)
RETURNS UUID
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
DECLARE v_id UUID;
BEGIN
  INSERT INTO campaigns (name, description, segment_id, channel, message_template, scheduled_at, created_by)
  VALUES (
    p_name,
    COALESCE(p_description, ''),
    p_segment_id,
    COALESCE(p_channel, 'email'),
    COALESCE(p_message_template, ''),
    p_scheduled_at,
    p_created_by
  )
  RETURNING id INTO v_id;
  RETURN v_id;
END;
$$;

-- ─── Função: update_campaign ─────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_campaign(
  p_id               UUID,
  p_name             TEXT        DEFAULT NULL,
  p_description      TEXT        DEFAULT NULL,
  p_segment_id       UUID        DEFAULT NULL,
  p_channel          TEXT        DEFAULT NULL,
  p_message_template TEXT        DEFAULT NULL,
  p_scheduled_at     TIMESTAMPTZ DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  UPDATE campaigns SET
    name             = COALESCE(p_name,             name),
    description      = COALESCE(p_description,      description),
    segment_id       = COALESCE(p_segment_id,       segment_id),
    channel          = COALESCE(p_channel,           channel),
    message_template = COALESCE(p_message_template,  message_template),
    scheduled_at     = CASE WHEN p_scheduled_at IS NOT NULL THEN p_scheduled_at ELSE scheduled_at END
  WHERE id = p_id AND status IN ('draft','paused');
END;
$$;

-- ─── Função: get_campaigns ───────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION get_campaigns()
RETURNS TABLE (
  id               UUID,
  name             TEXT,
  description      TEXT,
  segment_id       UUID,
  segment_name     TEXT,
  segment_active   BOOLEAN,
  member_count     INTEGER,
  channel          TEXT,
  message_template TEXT,
  status           TEXT,
  scheduled_at     TIMESTAMPTZ,
  started_at       TIMESTAMPTZ,
  completed_at     TIMESTAMPTZ,
  created_by       UUID,
  creator_name     TEXT,
  created_at       TIMESTAMPTZ,
  updated_at       TIMESTAMPTZ
)
LANGUAGE sql SECURITY DEFINER SET search_path = public
AS $$
  SELECT
    c.id,
    c.name,
    c.description,
    c.segment_id,
    cs.segment_name,
    cs.is_active        AS segment_active,
    cs.member_count,
    c.channel,
    c.message_template,
    c.status,
    c.scheduled_at,
    c.started_at,
    c.completed_at,
    c.created_by,
    p.full_name         AS creator_name,
    c.created_at,
    c.updated_at
  FROM campaigns c
  JOIN  customer_segments cs ON cs.id = c.segment_id
  LEFT JOIN profiles p        ON p.id  = c.created_by
  ORDER BY c.created_at DESC;
$$;

-- ─── Função: get_campaign_by_id ──────────────────────────────────────────────

CREATE OR REPLACE FUNCTION get_campaign_by_id(p_id UUID)
RETURNS TABLE (
  id               UUID,
  name             TEXT,
  description      TEXT,
  segment_id       UUID,
  segment_name     TEXT,
  segment_active   BOOLEAN,
  member_count     INTEGER,
  channel          TEXT,
  message_template TEXT,
  status           TEXT,
  scheduled_at     TIMESTAMPTZ,
  started_at       TIMESTAMPTZ,
  completed_at     TIMESTAMPTZ,
  created_by       UUID,
  creator_name     TEXT,
  created_at       TIMESTAMPTZ,
  updated_at       TIMESTAMPTZ
)
LANGUAGE sql SECURITY DEFINER SET search_path = public
AS $$
  SELECT
    c.id, c.name, c.description, c.segment_id,
    cs.segment_name, cs.is_active AS segment_active, cs.member_count,
    c.channel, c.message_template, c.status,
    c.scheduled_at, c.started_at, c.completed_at,
    c.created_by, p.full_name AS creator_name,
    c.created_at, c.updated_at
  FROM campaigns c
  JOIN  customer_segments cs ON cs.id = c.segment_id
  LEFT JOIN profiles p        ON p.id  = c.created_by
  WHERE c.id = p_id;
$$;

-- ─── Função: activate_campaign ───────────────────────────────────────────────

CREATE OR REPLACE FUNCTION activate_campaign(p_id UUID)
RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  UPDATE campaigns
     SET status = 'scheduled'
   WHERE id = p_id AND status IN ('draft','paused');
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Campanha não encontrada ou não pode ser ativada no status atual.';
  END IF;
END;
$$;

-- ─── Função: pause_campaign ──────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION pause_campaign(p_id UUID)
RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  UPDATE campaigns
     SET status = 'paused'
   WHERE id = p_id AND status IN ('running','scheduled');
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Campanha não encontrada ou não pode ser pausada no status atual.';
  END IF;
END;
$$;

-- ─── Função: complete_campaign ───────────────────────────────────────────────

CREATE OR REPLACE FUNCTION complete_campaign(p_id UUID)
RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  UPDATE campaigns
     SET status = 'completed', completed_at = NOW()
   WHERE id = p_id AND status IN ('running','scheduled');
END;
$$;

-- ─── Função: delete_campaign ─────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION delete_campaign(p_id UUID)
RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  DELETE FROM campaigns WHERE id = p_id AND status = 'draft';
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Somente campanhas em rascunho podem ser excluídas.';
  END IF;
END;
$$;

-- ─── Permissão campaigns.manage ──────────────────────────────────────────────

INSERT INTO permissions (name, description, category)
VALUES ('campaigns.manage', 'Criar e gerenciar campanhas de comunicação', 'analytics')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
  FROM roles r, permissions p
 WHERE r.name IN ('admin', 'supervisor')
   AND p.name = 'campaigns.manage'
ON CONFLICT DO NOTHING;
