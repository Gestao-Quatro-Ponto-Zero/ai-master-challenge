-- 0001_init — Schema base do Lead Scorer (Foco)
-- Espelha as 4 tabelas do CRM. SQLite (portável, zero-install).
-- Convenções: PK textual natural dos CSVs; FKs explícitas; índices nas colunas de join/filtro.

PRAGMA foreign_keys = ON;

-- Catálogo de produtos (7 linhas)
CREATE TABLE IF NOT EXISTS products (
    product      TEXT PRIMARY KEY,           -- nome do produto (chave natural)
    series       TEXT NOT NULL,              -- GTX, MG, GTK...
    sales_price  REAL NOT NULL CHECK (sales_price >= 0)
);

-- Contas/clientes (~85 linhas)
CREATE TABLE IF NOT EXISTS accounts (
    account          TEXT PRIMARY KEY,
    sector           TEXT,
    year_established INTEGER,
    revenue          REAL,                   -- em milhões
    employees        INTEGER,
    office_location  TEXT,
    subsidiary_of    TEXT                    -- conta-mãe (nullable)
);

-- Vendedores (35 linhas)
CREATE TABLE IF NOT EXISTS sales_teams (
    sales_agent     TEXT PRIMARY KEY,
    manager         TEXT NOT NULL,
    regional_office TEXT NOT NULL
);

-- Pipeline — tabela central (~8.800 oportunidades)
CREATE TABLE IF NOT EXISTS sales_pipeline (
    opportunity_id TEXT PRIMARY KEY,
    sales_agent    TEXT NOT NULL REFERENCES sales_teams(sales_agent),
    product        TEXT NOT NULL REFERENCES products(product),
    account        TEXT REFERENCES accounts(account),   -- NULLABLE: ~16% sem conta atribuída (achado de RevOps)
    deal_stage     TEXT NOT NULL CHECK (deal_stage IN ('Prospecting','Engaging','Won','Lost')),
    engage_date    TEXT,                                 -- ISO date; NULL para Prospecting (não engajado)
    close_date     TEXT,                                 -- ISO date; NULL para deals abertos
    close_value    REAL                                  -- NULL/0 para Lost e abertos
);

-- Índices para as queries de scoring/filtro
CREATE INDEX IF NOT EXISTS idx_pipeline_agent   ON sales_pipeline(sales_agent);
CREATE INDEX IF NOT EXISTS idx_pipeline_stage   ON sales_pipeline(deal_stage);
CREATE INDEX IF NOT EXISTS idx_pipeline_product ON sales_pipeline(product);
CREATE INDEX IF NOT EXISTS idx_pipeline_account ON sales_pipeline(account);
