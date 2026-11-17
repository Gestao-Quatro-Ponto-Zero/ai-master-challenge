-- Camada analítica de confiança — RavenStack (desafio 001)
-- Duas camadas:
--   raw_*  : texto exatamente como veio do CSV, mais _linha (número do registro no arquivo).
--   tabelas tipadas : tipos, domínios, chaves primárias e estrangeiras impostos pelo banco.
-- Regra de datas: tudo vira TEXT 'YYYY-MM-DD HH:MM:SS'. Data sem hora recebe 00:00:00;
-- data com hora mantém a hora do arquivo. O CHECK col = datetime(col) rejeita data inválida
-- (ex.: 2023-02-30) e qualquer formato fora do padrão.
-- Falha estrutural bloqueia a carga; inconsistências entre campos só são contadas (ver 03_checagens.sql).

PRAGMA foreign_keys = ON;

CREATE TABLE accounts (
  account_id      TEXT    PRIMARY KEY CHECK (account_id GLOB 'A-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'),
  account_name    TEXT    NOT NULL UNIQUE,
  industry        TEXT    NOT NULL CHECK (industry IN ('Cybersecurity','DevTools','EdTech','FinTech','HealthTech')),
  country         TEXT    NOT NULL CHECK (country IN ('AU','CA','DE','FR','IN','UK','US')),
  signup_date     TEXT    NOT NULL CHECK (signup_date = datetime(signup_date)),
  referral_source TEXT    NOT NULL CHECK (referral_source IN ('ads','event','organic','other','partner')),
  plan_tier       TEXT    NOT NULL CHECK (plan_tier IN ('Basic','Pro','Enterprise')),
  seats           INTEGER NOT NULL CHECK (seats > 0),
  is_trial        INTEGER NOT NULL CHECK (is_trial IN (0,1)),
  churn_flag      INTEGER NOT NULL CHECK (churn_flag IN (0,1))
) STRICT;

CREATE TABLE subscriptions (
  subscription_id   TEXT    PRIMARY KEY CHECK (subscription_id GLOB 'S-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'),
  account_id        TEXT    NOT NULL REFERENCES accounts(account_id),
  start_date        TEXT    NOT NULL CHECK (start_date = datetime(start_date)),
  end_date          TEXT             CHECK (end_date IS NULL OR end_date = datetime(end_date)),
  plan_tier         TEXT    NOT NULL CHECK (plan_tier IN ('Basic','Pro','Enterprise')),
  seats             INTEGER NOT NULL CHECK (seats > 0),
  mrr_amount        INTEGER NOT NULL CHECK (mrr_amount >= 0),
  arr_amount        INTEGER NOT NULL CHECK (arr_amount >= 0),
  is_trial          INTEGER NOT NULL CHECK (is_trial IN (0,1)),
  upgrade_flag      INTEGER NOT NULL CHECK (upgrade_flag IN (0,1)),
  downgrade_flag    INTEGER NOT NULL CHECK (downgrade_flag IN (0,1)),
  churn_flag        INTEGER NOT NULL CHECK (churn_flag IN (0,1)),
  billing_frequency TEXT    NOT NULL CHECK (billing_frequency IN ('monthly','annual')),
  auto_renew_flag   INTEGER NOT NULL CHECK (auto_renew_flag IN (0,1))
) STRICT;
CREATE INDEX ix_subscriptions_account ON subscriptions(account_id);

-- usage_id NÃO é único no arquivo: 21 ids aparecem 2 vezes, com conteúdo diferente nas duas linhas.
-- Por isso a chave é substituta (usage_pk = número do registro no CSV) e o par
-- (usage_id, subscription_id) é a chave natural.
CREATE TABLE feature_usage (
  usage_pk            INTEGER PRIMARY KEY,
  usage_id            TEXT    NOT NULL CHECK (usage_id GLOB 'U-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'),
  subscription_id     TEXT    NOT NULL REFERENCES subscriptions(subscription_id),
  usage_date          TEXT    NOT NULL CHECK (usage_date = datetime(usage_date)),
  feature_name        TEXT    NOT NULL CHECK (feature_name GLOB 'feature_[0-9]*'),
  usage_count         INTEGER NOT NULL CHECK (usage_count >= 0),
  usage_duration_secs INTEGER NOT NULL CHECK (usage_duration_secs >= 0),
  error_count         INTEGER NOT NULL CHECK (error_count >= 0),
  is_beta_feature     INTEGER NOT NULL CHECK (is_beta_feature IN (0,1)),
  UNIQUE (usage_id, subscription_id)
) STRICT;
CREATE INDEX ix_usage_subscription ON feature_usage(subscription_id);

CREATE TABLE support_tickets (
  ticket_id                   TEXT    PRIMARY KEY CHECK (ticket_id GLOB 'T-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'),
  account_id                  TEXT    NOT NULL REFERENCES accounts(account_id),
  submitted_at                TEXT    NOT NULL CHECK (submitted_at = datetime(submitted_at)),
  closed_at                   TEXT             CHECK (closed_at IS NULL OR closed_at = datetime(closed_at)),
  resolution_time_hours       REAL             CHECK (resolution_time_hours >= 0),
  priority                    TEXT    NOT NULL CHECK (priority IN ('low','medium','high','urgent')),
  first_response_time_minutes INTEGER          CHECK (first_response_time_minutes >= 0),
  satisfaction_score          INTEGER          CHECK (satisfaction_score BETWEEN 1 AND 5),
  escalation_flag             INTEGER NOT NULL CHECK (escalation_flag IN (0,1))
) STRICT;
CREATE INDEX ix_tickets_account ON support_tickets(account_id);

CREATE TABLE churn_events (
  churn_event_id           TEXT    PRIMARY KEY CHECK (churn_event_id GLOB 'C-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]'),
  account_id               TEXT    NOT NULL REFERENCES accounts(account_id),
  churn_date               TEXT    NOT NULL CHECK (churn_date = datetime(churn_date)),
  reason_code              TEXT    NOT NULL CHECK (reason_code IN ('budget','competitor','features','pricing','support','unknown')),
  refund_amount_usd        REAL    NOT NULL CHECK (refund_amount_usd >= 0),
  preceding_upgrade_flag   INTEGER NOT NULL CHECK (preceding_upgrade_flag IN (0,1)),
  preceding_downgrade_flag INTEGER NOT NULL CHECK (preceding_downgrade_flag IN (0,1)),
  is_reactivation          INTEGER NOT NULL CHECK (is_reactivation IN (0,1)),
  feedback_text            TEXT
) STRICT;
CREATE INDEX ix_churn_account ON churn_events(account_id);

-- Auditoria da carga e resultado das checagens
CREATE TABLE dq_carga (
  tabela TEXT PRIMARY KEY, arquivo TEXT NOT NULL, registros_csv INTEGER NOT NULL,
  linhas_raw INTEGER, linhas_tipadas INTEGER, sha256 TEXT NOT NULL, carregado_em TEXT NOT NULL
) STRICT;

CREATE TABLE dq_checks (
  check_id TEXT PRIMARY KEY, camada TEXT NOT NULL, tabela TEXT NOT NULL, regra TEXT NOT NULL,
  severidade TEXT NOT NULL CHECK (severidade IN ('bloqueante','alerta','info')),
  violacoes INTEGER NOT NULL, base INTEGER, tratamento TEXT
) STRICT;

-- Parâmetros fixos da análise (decisão humana, D17). Toda consulta lê daqui; nenhum valor é repetido no SQL.
CREATE TABLE parametros (
  nome TEXT PRIMARY KEY, valor TEXT NOT NULL, descricao TEXT NOT NULL
) STRICT;
INSERT INTO parametros VALUES
  ('data_corte', '2024-12-31 00:00:00',
   'Data de corte da análise (31/12/2024). O dia inteiro entra: eventos até 2024-12-31 23:59:59 estão dentro da janela.'),
  ('data_inicio', '2023-01-01 00:00:00',
   'Primeiro dia da janela mensal (jan/2023, mês do primeiro cadastro de conta). A vw_mes gera um mês por linha daqui até data_corte.');
