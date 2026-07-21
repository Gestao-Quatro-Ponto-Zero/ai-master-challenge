-- 0001_reference.sql --- Grupo de referencia do modelo relacional (Fase B).
--
-- Cria as seis tabelas de referencia especificadas em
-- 'docs/concepcao-inicial.md' (secao "Modelo relacional") e fixadas no ADR
-- N4P8. As entidades sao semeadas dos CSV normalizados e sao imutaveis no MVP.
-- Valores monetarios: inteiro na menor unidade da moeda acompanhado do codigo
-- ISO 4217. Nomenclatura conforme 'std-sql.md' (tabelas no plural, colunas no
-- singular, sem repeticao do nome da tabela).
--
-- Dialeto: PostgreSQL. Aplicada pelo runner idempotente de 'src/migrate.lisp';
-- a execucao repetida e no-op via o controle em 'schema_migrations'.

CREATE TABLE regional_offices (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE sales_managers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL UNIQUE,
    regional_office_id INTEGER NOT NULL REFERENCES regional_offices (id)
);

CREATE TABLE sales_agents (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL UNIQUE,
    sales_manager_id INTEGER NOT NULL REFERENCES sales_managers (id)
);

CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    sector TEXT NOT NULL,
    year_established INTEGER,
    revenue_amount BIGINT NOT NULL,
    revenue_currency CHAR(3) NOT NULL,
    employees INTEGER,
    location TEXT,
    subsidiary_of_id INTEGER REFERENCES accounts (id)
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    series TEXT NOT NULL,
    list_price_amount INTEGER NOT NULL,
    list_price_currency CHAR(3) NOT NULL
);

CREATE TABLE engagement_justifications (
    id SERIAL PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL
);
