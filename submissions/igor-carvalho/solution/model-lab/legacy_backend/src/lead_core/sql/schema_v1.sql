-- ESQUEMA v1 DO SQLITE — CONGELADO.
-- Não alterar sem pedido explícito do dono do projeto. Há um teste (tests/core/test_schema_frozen.py)
-- que falha se este arquivo mudar (compara com schema_v1.sha256).
-- Os scores dos deals NÃO ficam aqui: vêm dos artefatos do modelo (artifacts/v{N}/scored_deals.parquet).
-- Aqui ficam apenas dados gerados pela operação: usuários, feedback, versões do modelo e jobs.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_info (
    id          INTEGER PRIMARY KEY CHECK (id = 1),
    version     INTEGER NOT NULL,
    applied_at  TEXT    NOT NULL
);

-- Usuários do MVP (login por user_key). Vendedores e managers vêm de sales_teams; "revops" é administrador.
CREATE TABLE IF NOT EXISTS users (
    user_key        TEXT PRIMARY KEY,
    full_name       TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('seller', 'manager', 'revops')),
    manager         TEXT,
    regional_office TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at      TEXT NOT NULL
);

-- Feedback do vendedor sobre um deal (contrato: POST /deals/{id}/feedback). Só se acrescenta; nunca se edita.
CREATE TABLE IF NOT EXISTS deal_feedback (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id     TEXT    NOT NULL,
    user_key           TEXT    NOT NULL REFERENCES users (user_key),
    action             TEXT    NOT NULL CHECK (action IN ('worked', 'disagree', 'ignore')),
    comment            TEXT    CHECK (comment IS NULL OR length(comment) <= 280),
    model_version      TEXT,
    score_at_feedback  INTEGER CHECK (score_at_feedback IS NULL OR (score_at_feedback BETWEEN 0 AND 100)),
    band_at_feedback   TEXT,
    created_at         TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_feedback_deal ON deal_feedback (opportunity_id, created_at);
CREATE INDEX IF NOT EXISTS ix_feedback_user ON deal_feedback (user_key, created_at);

-- Registro das versões treinadas. Exatamente UMA pode estar 'active' (índice parcial abaixo).
CREATE TABLE IF NOT EXISTS model_versions (
    version         TEXT PRIMARY KEY,
    engine          TEXT NOT NULL,
    trained_at      TEXT NOT NULL,
    reference_date  TEXT NOT NULL,
    artifact_path   TEXT NOT NULL,
    metrics_json    TEXT NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('candidate', 'active', 'retired', 'rejected')),
    promoted_at     TEXT,
    reject_reason   TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_model_single_active ON model_versions (status) WHERE status = 'active';

-- Jobs administrativos (POST /admin/retrain, /admin/refresh). Só um retrain pode estar na fila/rodando.
CREATE TABLE IF NOT EXISTS jobs (
    job_id        TEXT PRIMARY KEY,
    kind          TEXT NOT NULL CHECK (kind IN ('retrain', 'refresh')),
    status        TEXT NOT NULL CHECK (status IN ('queued', 'running', 'succeeded', 'failed')),
    requested_by  TEXT REFERENCES users (user_key),
    params_json   TEXT,
    result_json   TEXT,
    error         TEXT,
    created_at    TEXT NOT NULL,
    started_at    TEXT,
    finished_at   TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_job_one_retrain ON jobs (kind)
    WHERE kind = 'retrain' AND status IN ('queued', 'running');
