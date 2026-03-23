-- OptiFlow Initial Schema
-- Dataset 1: Customer Support Tickets + Dataset 2: IT Service Tickets
-- Classification tracking + Process analysis findings

-- Dataset 1: Customer Support Tickets
CREATE TABLE support_tickets (
  id SERIAL PRIMARY KEY,
  ticket_id TEXT UNIQUE NOT NULL,
  customer_name TEXT,
  customer_email TEXT,
  customer_age INT,
  customer_gender TEXT,
  product_purchased TEXT,
  ticket_type TEXT,
  ticket_subject TEXT,
  ticket_description TEXT,
  ticket_status TEXT,
  resolution TEXT,
  ticket_priority TEXT,
  ticket_channel TEXT,
  first_response_time TEXT,
  time_to_resolution TEXT,
  customer_satisfaction_rating INT,
  -- Enrichment columns (added by our analysis)
  frt_minutes INT,
  ttr_minutes INT,
  llm_category TEXT,
  llm_confidence FLOAT,
  llm_model TEXT,
  llm_reasoning TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Dataset 2: IT Service Tickets (classification training)
CREATE TABLE it_tickets (
  id SERIAL PRIMARY KEY,
  document TEXT NOT NULL,
  topic_group TEXT NOT NULL,
  -- Enrichment
  llm_category TEXT,
  llm_confidence FLOAT,
  llm_model TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Classification runs (track experiments)
CREATE TABLE classification_runs (
  id SERIAL PRIMARY KEY,
  model TEXT NOT NULL,
  dataset TEXT NOT NULL,
  total_records INT,
  classified INT,
  accuracy FLOAT,
  avg_confidence FLOAT,
  taxonomy JSONB,
  config JSONB,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Process analysis results
CREATE TABLE process_findings (
  id SERIAL PRIMARY KEY,
  phase TEXT NOT NULL,
  category TEXT,
  title TEXT NOT NULL,
  description TEXT,
  evidence JSONB,
  impact_hours_month FLOAT,
  impact_cost_month FLOAT,
  priority TEXT,
  recommendation TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for common query patterns
CREATE INDEX idx_support_tickets_channel ON support_tickets(ticket_channel);
CREATE INDEX idx_support_tickets_type ON support_tickets(ticket_type);
CREATE INDEX idx_support_tickets_priority ON support_tickets(ticket_priority);
CREATE INDEX idx_support_tickets_status ON support_tickets(ticket_status);
CREATE INDEX idx_support_tickets_product ON support_tickets(product_purchased);
CREATE INDEX idx_support_tickets_csat ON support_tickets(customer_satisfaction_rating);
CREATE INDEX idx_it_tickets_topic ON it_tickets(topic_group);
CREATE INDEX idx_classification_runs_model ON classification_runs(model);
