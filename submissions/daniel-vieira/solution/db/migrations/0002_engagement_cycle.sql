-- 0002_engagement_cycle.sql --- Grupo do ciclo de engajamento (Fase B).
--
-- Cria as tres tabelas operacionais especificadas em
-- 'docs/concepcao-inicial.md' (secao "Modelo relacional") e fixadas no ADR
-- N4P8. A oportunidade e o par conta-produto com estado ativo unico; o
-- historico imutavel de ciclos reside em 'engagements'; o ranqueamento
-- personalizado por agente reside em 'opportunity_scores'.
--
-- Instantes: UNIX em milissegundos, UTC (BIGINT). Valores monetarios: inteiro
-- na menor unidade da moeda com codigo ISO 4217. Dialeto: PostgreSQL.

CREATE TABLE opportunities (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts (id),
    product_id INTEGER NOT NULL REFERENCES products (id),
    status TEXT NOT NULL CHECK (status IN ('prospecting', 'engaging')),
    engaged_by_id INTEGER REFERENCES sales_agents (id),
    engaged_at BIGINT,
    created_at BIGINT NOT NULL,
    UNIQUE (account_id, product_id),
    -- O estado 'engaging' exige agente e instante de engajamento; o estado
    -- 'prospecting' exige a ausencia de ambos.
    CONSTRAINT opportunities_active_state CHECK (
        (status = 'engaging'
            AND engaged_by_id IS NOT NULL AND engaged_at IS NOT NULL)
        OR (status = 'prospecting'
            AND engaged_by_id IS NULL AND engaged_at IS NULL)
    )
);

CREATE TABLE opportunity_scores (
    id SERIAL PRIMARY KEY,
    opportunity_id INTEGER NOT NULL REFERENCES opportunities (id),
    sales_agent_id INTEGER NOT NULL REFERENCES sales_agents (id),
    score_overall INTEGER NOT NULL CHECK (score_overall BETWEEN 0 AND 100),
    score_economic INTEGER NOT NULL CHECK (score_economic BETWEEN 0 AND 100),
    score_affinity INTEGER NOT NULL CHECK (score_affinity BETWEEN 0 AND 100),
    score_momentum INTEGER NOT NULL CHECK (score_momentum BETWEEN 0 AND 100),
    score_adherence INTEGER NOT NULL CHECK (score_adherence BETWEEN 0 AND 100),
    -- Dimensoes inertes (peso zero): nulas no MVP, exibidas com traco.
    score_closing_time INTEGER CHECK (score_closing_time BETWEEN 0 AND 100),
    score_inactivity INTEGER CHECK (score_inactivity BETWEEN 0 AND 100),
    computed_at BIGINT NOT NULL,
    UNIQUE (opportunity_id, sales_agent_id)
);

CREATE TABLE engagements (
    id SERIAL PRIMARY KEY,
    opportunity_id INTEGER NOT NULL REFERENCES opportunities (id),
    sales_agent_id INTEGER NOT NULL REFERENCES sales_agents (id),
    justification_id INTEGER REFERENCES engagement_justifications (id),
    engaged_at BIGINT NOT NULL,
    closed_at BIGINT,
    outcome TEXT CHECK (outcome IN ('won', 'lost')),
    expired BOOLEAN NOT NULL DEFAULT FALSE,
    close_value_amount INTEGER,
    close_value_currency CHAR(3),
    -- Proveniencia: o opportunity_id da linha original de sales_pipeline.csv,
    -- preservado apenas para rastreio, pois a oportunidade aqui e o par
    -- conta-produto e cada linha do pipeline e um ciclo.
    source_opportunity_id TEXT,
    -- A moeda acompanha o valor de fechamento quando este esta presente.
    CONSTRAINT engagements_close_currency CHECK (
        (close_value_amount IS NULL AND close_value_currency IS NULL)
        OR (close_value_amount IS NOT NULL AND close_value_currency IS NOT NULL)
    )
);
