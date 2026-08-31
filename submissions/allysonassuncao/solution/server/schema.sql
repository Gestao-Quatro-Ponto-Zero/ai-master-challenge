CREATE TABLE IF NOT EXISTS accounts (
  account TEXT PRIMARY KEY,
  sector_raw TEXT,
  sector TEXT,
  year_established INTEGER,
  revenue NUMERIC,
  employees INTEGER,
  office_location TEXT,
  subsidiary_of TEXT
);

CREATE TABLE IF NOT EXISTS products (
  product TEXT PRIMARY KEY,
  series TEXT NOT NULL,
  sales_price NUMERIC NOT NULL CHECK (sales_price >= 0)
);

CREATE TABLE IF NOT EXISTS sales_agents (
  sales_agent TEXT PRIMARY KEY,
  manager TEXT NOT NULL,
  regional_office TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS opportunities (
  opportunity_id TEXT PRIMARY KEY,
  sales_agent TEXT NOT NULL REFERENCES sales_agents(sales_agent),
  product TEXT NOT NULL REFERENCES products(product),
  account TEXT REFERENCES accounts(account),
  deal_stage TEXT NOT NULL CHECK (deal_stage IN ('Prospecting', 'Engaging', 'Won', 'Lost')),
  engage_date DATE,
  close_date DATE,
  close_value NUMERIC
);

CREATE INDEX IF NOT EXISTS opportunities_agent_idx ON opportunities(sales_agent);
CREATE INDEX IF NOT EXISTS opportunities_stage_idx ON opportunities(deal_stage);
CREATE INDEX IF NOT EXISTS opportunities_account_idx ON opportunities(account);
CREATE INDEX IF NOT EXISTS opportunities_close_date_idx ON opportunities(close_date);

CREATE TABLE IF NOT EXISTS deal_actions (
  id BIGSERIAL PRIMARY KEY,
  opportunity_id TEXT NOT NULL REFERENCES opportunities(opportunity_id) ON DELETE CASCADE,
  actor_profile TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('pending', 'completed', 'snoozed')),
  note TEXT,
  next_step TEXT,
  due_date DATE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS deal_actions_opportunity_idx ON deal_actions(opportunity_id, created_at DESC);

CREATE TABLE IF NOT EXISTS scoring_versions (
  version TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  reference_date DATE NOT NULL,
  active BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scoring_parameters (
  version TEXT NOT NULL REFERENCES scoring_versions(version) ON DELETE CASCADE,
  parameter_key TEXT NOT NULL,
  label TEXT NOT NULL,
  value NUMERIC NOT NULL,
  unit TEXT NOT NULL,
  explanation TEXT NOT NULL,
  PRIMARY KEY (version, parameter_key)
);

INSERT INTO scoring_versions(version, label, reference_date, active)
VALUES ('v0.1', 'Modelo híbrido explicável', '2017-12-31', FALSE)
ON CONFLICT (version) DO UPDATE SET active = EXCLUDED.active;

INSERT INTO scoring_parameters(version, parameter_key, label, value, unit, explanation) VALUES
  ('v0.1', 'chance_weight', 'Chance estimada', 40, 'pontos', 'Histórico suavizado de vendedor, produto e setor.'),
  ('v0.1', 'value_weight', 'Impacto financeiro', 30, 'pontos', 'Preço de catálogo normalizado entre os produtos.'),
  ('v0.1', 'urgency_weight', 'Urgência comercial', 20, 'pontos', 'Idade em Engaging comparada ao ciclo histórico.'),
  ('v0.1', 'relationship_weight', 'Relacionamento', 10, 'pontos', 'Frequência, recência e variedade de compras da conta.'),
  ('v0.1', 'rescue_days', 'Início da faixa Resgatar', 90, 'dias', 'Deals acima desta idade exigem retomada.'),
  ('v0.1', 'review_days', 'Início da faixa Revisar', 138, 'dias', 'Limite máximo observado no ciclo histórico encerrado.')
ON CONFLICT (version, parameter_key) DO UPDATE SET
  label = EXCLUDED.label,
  value = EXCLUDED.value,
  unit = EXCLUDED.unit,
  explanation = EXCLUDED.explanation;

INSERT INTO scoring_versions(version, label, reference_date, active)
VALUES ('v0.2', 'Potencial separado da ação', '2017-12-31', FALSE)
ON CONFLICT (version) DO UPDATE SET active = EXCLUDED.active;

INSERT INTO scoring_parameters(version, parameter_key, label, value, unit, explanation) VALUES
  ('v0.2', 'potential_chance_weight', 'Chance no potencial', 45, 'pontos', 'Histórico suavizado de produto e setor, sem usar afinidade individual.'),
  ('v0.2', 'potential_value_weight', 'Valor no potencial', 35, 'pontos', 'Preço de catálogo normalizado entre os produtos.'),
  ('v0.2', 'potential_relationship_weight', 'Relacionamento no potencial', 20, 'pontos', 'Frequência, recência e variedade de compras da conta.'),
  ('v0.2', 'priority_potential_weight', 'Potencial na prioridade', 70, 'pontos', 'Quanto do ranking vem da qualidade comercial da oportunidade.'),
  ('v0.2', 'priority_timing_weight', 'Momento na prioridade', 30, 'pontos', 'Quanto do ranking vem do relógio histórico específico do produto.'),
  ('v0.2', 'product_clock_sample', 'Amostra mínima do relógio', 30, 'negócios', 'Abaixo desta amostra, usa-se o ciclo geral das vitórias.'),
  ('v0.2', 'affinity_min_sample', 'Amostra mínima da afinidade', 20, 'negócios', 'A afinidade só aparece como segundo motivo e não altera o score.')
ON CONFLICT (version, parameter_key) DO UPDATE SET
  label = EXCLUDED.label,
  value = EXCLUDED.value,
  unit = EXCLUDED.unit,
  explanation = EXCLUDED.explanation;

INSERT INTO scoring_versions(version, label, reference_date, active)
VALUES ('v0.3', 'Score de foco simples', '2017-12-31', TRUE)
ON CONFLICT (version) DO UPDATE SET active = EXCLUDED.active;

INSERT INTO scoring_parameters(version, parameter_key, label, value, unit, explanation) VALUES
  ('v0.3', 'value_points', 'Valor do produto', 40, 'pontos', 'Produtos mais caros recebem mais pontos, de 10 a 40.'),
  ('v0.3', 'history_points', 'Histórico do produto na região', 40, 'pontos', 'Taxa de vendas realizadas do produto na região multiplicada por 40; usa o produto geral quando a amostra regional é pequena.'),
  ('v0.3', 'moment_points', 'Momento do produto na região', 20, 'pontos', 'Compara o tempo em Engaging ao ciclo de vendas realizadas do produto na região.'),
  ('v0.3', 'product_clock_sample', 'Amostra mínima do relógio', 30, 'negócios', 'Abaixo desta amostra, usa-se o ciclo geral das vitórias.'),
  ('v0.3', 'regional_history_sample', 'Amostra mínima de produto por região', 30, 'negócios', 'Abaixo desta amostra, o Histórico usa a taxa geral do produto.'),
  ('v0.3', 'regional_clock_sample', 'Amostra mínima do relógio regional', 30, 'vendas realizadas', 'Abaixo desta amostra com datas válidas, o Momento usa o ciclo geral do produto.')
ON CONFLICT (version, parameter_key) DO UPDATE SET
  label = EXCLUDED.label,
  value = EXCLUDED.value,
  unit = EXCLUDED.unit,
  explanation = EXCLUDED.explanation;
