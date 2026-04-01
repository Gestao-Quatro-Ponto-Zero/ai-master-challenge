-- ============================================================
-- LEAD SCORER — Schema Completo
-- Supabase PostgreSQL
-- ============================================================

-- ============================================================
-- 1. TABELAS
-- ============================================================

-- Contas/clientes do CRM
CREATE TABLE accounts (
  id                serial PRIMARY KEY,
  name              text UNIQUE NOT NULL,
  sector            text,
  year_established  integer,
  revenue           numeric,              -- em milhões USD
  employees         integer,
  office_location   text,
  subsidiary_of     text                  -- nome da empresa pai (informativo)
);

-- Catálogo de produtos (gerenciado pelo admin)
CREATE TABLE products (
  id              serial PRIMARY KEY,
  name            text UNIQUE NOT NULL,
  series          text,
  sales_price     numeric NOT NULL
);

-- Vendedores, managers e escritórios regionais
CREATE TABLE sales_teams (
  id              serial PRIMARY KEY,
  sales_agent     text UNIQUE NOT NULL,
  manager         text NOT NULL,
  regional_office text NOT NULL
);

-- Oportunidades de venda (tabela central)
CREATE TABLE sales_pipeline (
  id              serial PRIMARY KEY,
  opportunity_id  text UNIQUE NOT NULL,
  sales_agent_id  integer NOT NULL REFERENCES sales_teams(id),
  product_id      integer NOT NULL REFERENCES products(id),
  account_id      integer NOT NULL REFERENCES accounts(id),
  deal_stage      text NOT NULL,
  engage_date     date,
  close_date      date,
  close_value     numeric DEFAULT 0,

  -- Integridade por stage
  CONSTRAINT valid_stage CHECK (deal_stage IN ('Prospecting', 'Engaging', 'Won', 'Lost')),
  CONSTRAINT won_rules CHECK (deal_stage != 'Won' OR (engage_date IS NOT NULL AND close_date IS NOT NULL AND close_value > 0)),
  CONSTRAINT lost_rules CHECK (deal_stage != 'Lost' OR (engage_date IS NOT NULL AND close_date IS NOT NULL AND close_value = 0)),
  CONSTRAINT engaging_rules CHECK (deal_stage != 'Engaging' OR (engage_date IS NOT NULL AND close_date IS NULL)),
  CONSTRAINT prospecting_rules CHECK (deal_stage != 'Prospecting' OR (engage_date IS NULL AND close_date IS NULL))
);

-- Mapeamento auth → perfil do usuário
CREATE TABLE users (
  id              uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email           text UNIQUE NOT NULL,
  role            text NOT NULL CHECK (role IN ('admin', 'vendedor', 'manager')),
  sales_team_id   integer REFERENCES sales_teams(id),   -- preenchido para vendedores
  manager_name    text,                                  -- preenchido para managers
  created_at      timestamptz DEFAULT now()
);

-- ============================================================
-- 2. ÍNDICES
-- ============================================================

CREATE INDEX idx_pipeline_agent ON sales_pipeline(sales_agent_id);
CREATE INDEX idx_pipeline_product ON sales_pipeline(product_id);
CREATE INDEX idx_pipeline_account ON sales_pipeline(account_id);
CREATE INDEX idx_pipeline_stage ON sales_pipeline(deal_stage);
CREATE INDEX idx_accounts_sector ON accounts(sector);
CREATE INDEX idx_sales_teams_manager ON sales_teams(manager);
CREATE INDEX idx_sales_teams_office ON sales_teams(regional_office);
CREATE INDEX idx_users_role ON users(role);

-- ============================================================
-- 3. TABELAS TEMPORÁRIAS PARA IMPORT (colunas texto para mapeamento)
-- ============================================================

-- Usada durante o import do CSV sales_pipeline.csv
-- Os campos texto serão resolvidos para IDs e depois removidos
CREATE TABLE sales_pipeline_staging (
  opportunity_id  text UNIQUE NOT NULL,
  sales_agent     text NOT NULL,
  product         text NOT NULL,
  account         text NOT NULL,
  deal_stage      text NOT NULL,
  engage_date     date,
  close_date      date,
  close_value     numeric DEFAULT 0
);

-- ============================================================
-- 4. ROW LEVEL SECURITY (RLS)
-- ============================================================

-- Habilitar RLS em todas as tabelas
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales_teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales_pipeline ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Helper: função para pegar o role do usuário autenticado
CREATE OR REPLACE FUNCTION get_user_role()
RETURNS text AS $$
  SELECT role FROM users WHERE id = auth.uid();
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- Helper: função para pegar o sales_team_id do usuário autenticado
CREATE OR REPLACE FUNCTION get_user_sales_team_id()
RETURNS integer AS $$
  SELECT sales_team_id FROM users WHERE id = auth.uid();
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- Helper: função para pegar o manager_name do usuário autenticado
CREATE OR REPLACE FUNCTION get_user_manager_name()
RETURNS text AS $$
  SELECT manager_name FROM users WHERE id = auth.uid();
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- ---- ACCOUNTS ----
-- Todos os roles autenticados podem ver todas as contas
CREATE POLICY "accounts_select" ON accounts
  FOR SELECT USING (auth.uid() IS NOT NULL);

-- Admin pode inserir/atualizar/deletar
CREATE POLICY "accounts_admin_all" ON accounts
  FOR ALL USING (get_user_role() = 'admin');

-- ---- PRODUCTS ----
-- Todos os roles autenticados podem ver todos os produtos
CREATE POLICY "products_select" ON products
  FOR SELECT USING (auth.uid() IS NOT NULL);

-- Admin pode inserir/atualizar/deletar
CREATE POLICY "products_admin_all" ON products
  FOR ALL USING (get_user_role() = 'admin');

-- ---- SALES_TEAMS ----
-- Todos os roles autenticados podem ver todos os times
CREATE POLICY "sales_teams_select" ON sales_teams
  FOR SELECT USING (auth.uid() IS NOT NULL);

-- Admin pode inserir/atualizar/deletar
CREATE POLICY "sales_teams_admin_all" ON sales_teams
  FOR ALL USING (get_user_role() = 'admin');

-- ---- SALES_PIPELINE ----
-- Admin: acesso total
CREATE POLICY "pipeline_admin_all" ON sales_pipeline
  FOR ALL USING (get_user_role() = 'admin');

-- Vendedor: vê apenas seus deals
CREATE POLICY "pipeline_vendedor_select" ON sales_pipeline
  FOR SELECT USING (
    get_user_role() = 'vendedor'
    AND sales_agent_id = get_user_sales_team_id()
  );

-- Manager: vê deals do seu time
CREATE POLICY "pipeline_manager_select" ON sales_pipeline
  FOR SELECT USING (
    get_user_role() = 'manager'
    AND sales_agent_id IN (
      SELECT id FROM sales_teams WHERE manager = get_user_manager_name()
    )
  );

-- ---- USERS ----
-- Usuário pode ver seu próprio registro
CREATE POLICY "users_self_select" ON users
  FOR SELECT USING (id = auth.uid());

-- Admin pode gerenciar todos os usuários
CREATE POLICY "users_admin_all" ON users
  FOR ALL USING (get_user_role() = 'admin');
