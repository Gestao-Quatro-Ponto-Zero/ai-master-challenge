/*
  # Campaign Scheduler — Subfase 7.5

  ## Descrição
  Cria o motor de agendamento de campanhas, permitindo execução
  automática em hora definida, recorrente via cron ou disparada por evento.

  ## Nova Tabela
  - `campaign_schedules`: armazena agendamentos com tipo, expressão cron/evento,
    controle de próxima e última execução, e flag de ativo.

  ## Campos Principais
  - `campaign_id`      — FK para campaigns
  - `schedule_type`    — once | recurring | event_triggered
  - `run_at`           — timestamp para execução única
  - `cron_expression`  — expressão cron para recorrência (ex: "0 9 * * 1")
  - `event_type`       — evento disparador (ex: ticket_resolved)
  - `next_run_at`      — próxima execução calculada
  - `last_run_at`      — última execução registrada
  - `is_active`        — ativa/inativa
  - `execution_count`  — quantas vezes foi executado

  ## Funções SQL
  - `create_schedule(...)`:           cria agendamento
  - `get_schedules()`:                lista com info da campanha
  - `get_schedule_by_id(UUID)`:       busca por id
  - `update_schedule(...)`:           atualiza campos editáveis
  - `disable_schedule(UUID)`:         desativa sem apagar
  - `enable_schedule(UUID)`:          reativa
  - `delete_schedule(UUID)`:          remove agendamento inativo
  - `get_due_schedules()`:            retorna schedules prontos para execução
  - `mark_schedule_executed(UUID)`:   atualiza last/next_run_at e incrementa contador

  ## Permissões
  - Nova permissão `campaign_scheduler.manage`
  - Concedida para: admin, supervisor

  ## Segurança
  - RLS habilitado
  - Funções SECURITY DEFINER
*/

-- ─── Tabela: campaign_schedules ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS campaign_schedules (
  id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id      UUID        NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  schedule_type    TEXT        NOT NULL CHECK (schedule_type IN ('once','recurring','event_triggered')),
  run_at           TIMESTAMPTZ,
  cron_expression  TEXT,
  event_type       TEXT,
  next_run_at      TIMESTAMPTZ,
  last_run_at      TIMESTAMPTZ,
  is_active        BOOLEAN     NOT NULL DEFAULT true,
  execution_count  INTEGER     NOT NULL DEFAULT 0,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_campaign_schedules_campaign  ON campaign_schedules(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaign_schedules_next_run  ON campaign_schedules(next_run_at);
CREATE INDEX IF NOT EXISTS idx_campaign_schedules_active    ON campaign_schedules(is_active);
CREATE INDEX IF NOT EXISTS idx_campaign_schedules_type      ON campaign_schedules(schedule_type);

ALTER TABLE campaign_schedules ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated can read campaign_schedules"
  ON campaign_schedules FOR SELECT TO authenticated USING (true);

CREATE POLICY "Authenticated can insert campaign_schedules"
  ON campaign_schedules FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "Authenticated can update campaign_schedules"
  ON campaign_schedules FOR UPDATE TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY "Authenticated can delete campaign_schedules"
  ON campaign_schedules FOR DELETE TO authenticated USING (true);

-- ─── Trigger: updated_at ─────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_campaign_schedule_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END; $$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_campaign_schedules_updated_at') THEN
    CREATE TRIGGER trg_campaign_schedules_updated_at
      BEFORE UPDATE ON campaign_schedules
      FOR EACH ROW EXECUTE FUNCTION update_campaign_schedule_updated_at();
  END IF;
END $$;

-- ─── Função: create_schedule ─────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION create_schedule(
  p_campaign_id     UUID,
  p_schedule_type   TEXT,
  p_run_at          TIMESTAMPTZ DEFAULT NULL,
  p_cron_expression TEXT        DEFAULT NULL,
  p_event_type      TEXT        DEFAULT NULL,
  p_next_run_at     TIMESTAMPTZ DEFAULT NULL
)
RETURNS UUID
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
DECLARE v_id UUID;
BEGIN
  INSERT INTO campaign_schedules (
    campaign_id, schedule_type, run_at, cron_expression, event_type, next_run_at
  )
  VALUES (
    p_campaign_id,
    p_schedule_type,
    p_run_at,
    p_cron_expression,
    p_event_type,
    COALESCE(p_next_run_at, p_run_at)
  )
  RETURNING id INTO v_id;
  RETURN v_id;
END;
$$;

-- ─── Função: get_schedules ────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION get_schedules()
RETURNS TABLE (
  id               UUID,
  campaign_id      UUID,
  campaign_name    TEXT,
  campaign_status  TEXT,
  campaign_channel TEXT,
  schedule_type    TEXT,
  run_at           TIMESTAMPTZ,
  cron_expression  TEXT,
  event_type       TEXT,
  next_run_at      TIMESTAMPTZ,
  last_run_at      TIMESTAMPTZ,
  is_active        BOOLEAN,
  execution_count  INTEGER,
  created_at       TIMESTAMPTZ,
  updated_at       TIMESTAMPTZ
)
LANGUAGE sql SECURITY DEFINER SET search_path = public
AS $$
  SELECT
    cs.id, cs.campaign_id,
    c.name            AS campaign_name,
    c.status          AS campaign_status,
    c.channel         AS campaign_channel,
    cs.schedule_type,
    cs.run_at,
    cs.cron_expression,
    cs.event_type,
    cs.next_run_at,
    cs.last_run_at,
    cs.is_active,
    cs.execution_count,
    cs.created_at,
    cs.updated_at
  FROM campaign_schedules cs
  JOIN campaigns c ON c.id = cs.campaign_id
  ORDER BY cs.created_at DESC;
$$;

-- ─── Função: get_schedule_by_id ───────────────────────────────────────────────

CREATE OR REPLACE FUNCTION get_schedule_by_id(p_id UUID)
RETURNS TABLE (
  id               UUID,
  campaign_id      UUID,
  campaign_name    TEXT,
  campaign_status  TEXT,
  campaign_channel TEXT,
  schedule_type    TEXT,
  run_at           TIMESTAMPTZ,
  cron_expression  TEXT,
  event_type       TEXT,
  next_run_at      TIMESTAMPTZ,
  last_run_at      TIMESTAMPTZ,
  is_active        BOOLEAN,
  execution_count  INTEGER,
  created_at       TIMESTAMPTZ,
  updated_at       TIMESTAMPTZ
)
LANGUAGE sql SECURITY DEFINER SET search_path = public
AS $$
  SELECT
    cs.id, cs.campaign_id,
    c.name AS campaign_name, c.status AS campaign_status, c.channel AS campaign_channel,
    cs.schedule_type, cs.run_at, cs.cron_expression, cs.event_type,
    cs.next_run_at, cs.last_run_at, cs.is_active, cs.execution_count,
    cs.created_at, cs.updated_at
  FROM campaign_schedules cs
  JOIN campaigns c ON c.id = cs.campaign_id
  WHERE cs.id = p_id;
$$;

-- ─── Função: update_schedule ──────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_schedule(
  p_id              UUID,
  p_run_at          TIMESTAMPTZ DEFAULT NULL,
  p_cron_expression TEXT        DEFAULT NULL,
  p_event_type      TEXT        DEFAULT NULL,
  p_next_run_at     TIMESTAMPTZ DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  UPDATE campaign_schedules SET
    run_at          = COALESCE(p_run_at,          run_at),
    cron_expression = COALESCE(p_cron_expression,  cron_expression),
    event_type      = COALESCE(p_event_type,       event_type),
    next_run_at     = COALESCE(p_next_run_at,      COALESCE(p_run_at, next_run_at))
  WHERE id = p_id;
END;
$$;

-- ─── Função: disable_schedule ────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION disable_schedule(p_id UUID)
RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  UPDATE campaign_schedules SET is_active = false WHERE id = p_id;
END;
$$;

-- ─── Função: enable_schedule ─────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION enable_schedule(p_id UUID)
RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  UPDATE campaign_schedules SET is_active = true WHERE id = p_id;
END;
$$;

-- ─── Função: delete_schedule ─────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION delete_schedule(p_id UUID)
RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  DELETE FROM campaign_schedules WHERE id = p_id;
END;
$$;

-- ─── Função: get_due_schedules ───────────────────────────────────────────────
-- Retorna schedules prontos para execução: ativos, com next_run_at <= now().
-- Usado pelo worker do scheduler.

CREATE OR REPLACE FUNCTION get_due_schedules()
RETURNS TABLE (
  id               UUID,
  campaign_id      UUID,
  campaign_name    TEXT,
  campaign_status  TEXT,
  campaign_channel TEXT,
  schedule_type    TEXT,
  cron_expression  TEXT,
  event_type       TEXT,
  next_run_at      TIMESTAMPTZ,
  last_run_at      TIMESTAMPTZ,
  execution_count  INTEGER
)
LANGUAGE sql SECURITY DEFINER SET search_path = public
AS $$
  SELECT
    cs.id, cs.campaign_id,
    c.name AS campaign_name, c.status AS campaign_status, c.channel AS campaign_channel,
    cs.schedule_type, cs.cron_expression, cs.event_type,
    cs.next_run_at, cs.last_run_at, cs.execution_count
  FROM campaign_schedules cs
  JOIN campaigns c ON c.id = cs.campaign_id
  WHERE cs.is_active = true
    AND cs.next_run_at IS NOT NULL
    AND cs.next_run_at <= NOW()
    AND c.status IN ('scheduled','running')
  ORDER BY cs.next_run_at ASC;
$$;

-- ─── Função: mark_schedule_executed ──────────────────────────────────────────
-- Chamada após execução bem-sucedida.
-- Para "once": desativa o schedule.
-- Para "recurring": atualiza last_run_at; next_run_at deve vir do worker.

CREATE OR REPLACE FUNCTION mark_schedule_executed(
  p_id          UUID,
  p_next_run_at TIMESTAMPTZ DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
DECLARE v_type TEXT;
BEGIN
  SELECT schedule_type INTO v_type FROM campaign_schedules WHERE id = p_id;

  UPDATE campaign_schedules SET
    last_run_at     = NOW(),
    execution_count = execution_count + 1,
    next_run_at     = CASE
                        WHEN v_type = 'once' THEN NULL
                        ELSE p_next_run_at
                      END,
    is_active       = CASE
                        WHEN v_type = 'once' THEN false
                        ELSE is_active
                      END
  WHERE id = p_id;
END;
$$;

-- ─── Permissão campaign_scheduler.manage ─────────────────────────────────────

INSERT INTO permissions (name, description, category)
VALUES ('campaign_scheduler.manage', 'Agendar e gerenciar execução de campanhas', 'analytics')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
  FROM roles r, permissions p
 WHERE r.name IN ('admin', 'supervisor')
   AND p.name = 'campaign_scheduler.manage'
ON CONFLICT DO NOTHING;
