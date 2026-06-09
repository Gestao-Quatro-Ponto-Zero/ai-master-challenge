-- RotaDesk — schema inicial
-- Challenge 002 · Jean Felipe

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Filas (mapeamento DS2 → operação)
CREATE TABLE queues (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  topic_group TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO queues (slug, name, topic_group) VALUES
  ('hardware', 'Infra / Dispositivos', 'Hardware'),
  ('hr-support', 'RH', 'HR Support'),
  ('access', 'Acessos e senhas', 'Access'),
  ('miscellaneous', 'Geral', 'Miscellaneous'),
  ('storage', 'Armazenamento', 'Storage'),
  ('purchase', 'Compras', 'Purchase'),
  ('internal-project', 'Projetos internos', 'Internal Project'),
  ('admin-rights', 'Direitos administrativos', 'Administrative rights'),
  ('human-priority', 'Fila humana prioritária', NULL);

CREATE TABLE tickets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticket_number SERIAL,
  customer_name TEXT NOT NULL,
  customer_email TEXT,
  channel TEXT NOT NULL CHECK (channel IN ('Email', 'Phone', 'Chat', 'Social media')),
  ticket_type TEXT NOT NULL,
  ticket_priority TEXT NOT NULL DEFAULT 'Medium'
    CHECK (ticket_priority IN ('Low', 'Medium', 'High', 'Critical')),
  subject TEXT NOT NULL,
  description TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open'
    CHECK (status IN (
      'open', 'triagem', 'pending_review', 'routed',
      'human_required', 'pending_customer', 'closed'
    )),
  scenario TEXT CHECK (scenario IN (
    'auto_routed', 'human_required', 'pending_review',
    'llm_reclassified', 'auto_resolved', 'ack_only'
  )),
  topic_group TEXT,
  topic_group_llm TEXT,
  confidence NUMERIC(5, 2),
  queue_slug TEXT REFERENCES queues(slug),
  human_required_reason TEXT,
  first_response_at TIMESTAMPTZ,
  ack_message TEXT,
  resolved_at TIMESTAMPTZ,
  resolved_by TEXT CHECK (resolved_by IS NULL OR resolved_by IN ('auto_ia', 'human')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_created_at ON tickets(created_at DESC);
CREATE INDEX idx_tickets_scenario ON tickets(scenario);

CREATE TABLE ticket_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticket_id UUID NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('customer', 'agent', 'system')),
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_ticket_messages_ticket ON ticket_messages(ticket_id, created_at);

CREATE TABLE ticket_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticket_id UUID NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,
  payload JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_ticket_events_ticket ON ticket_events(ticket_id, created_at DESC);

-- Base de conhecimento para RAG (protótipo)
CREATE TABLE knowledge_articles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  topic_group TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO knowledge_articles (title, content, topic_group) VALUES
  ('Reset de senha', 'Para reset de senha: abra o portal de identidade, clique em Esqueci minha senha e siga o fluxo MFA. Prazo: até 15 minutos.', 'Access'),
  ('Solicitação de hardware', 'Notebooks e periféricos: abra chamado com justificativa e aprovação do gestor. SLA de entrega: 5 dias úteis.', 'Hardware'),
  ('Reembolso', 'Reembolsos exigem atendimento humano. Documentos: nota fiscal, comprovante e motivo. Prazo de análise: 7 dias úteis.', 'Miscellaneous'),
  ('Cancelamento', 'Cancelamentos são tratados por agente humano. Informe número do pedido e motivo do cancelamento.', 'Miscellaneous'),
  ('Compras', 'Compras acima de R$ 5.000 precisam de cotação com 3 fornecedores e aprovação financeira.', 'Purchase'),
  ('Armazenamento', 'Quotas de storage: solicite aumento via chamado com área e justificativa de uso.', 'Storage'),
  ('RH', 'Questões de RH (férias, benefícios) são direcionadas ao time de People Ops.', 'HR Support'),
  ('Direitos administrativos', 'Permissões elevadas exigem revisão de segurança e aprovação do owner da aplicação.', 'Administrative rights');

CREATE OR REPLACE FUNCTION update_tickets_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tickets_updated_at
  BEFORE UPDATE ON tickets
  FOR EACH ROW EXECUTE FUNCTION update_tickets_updated_at();
