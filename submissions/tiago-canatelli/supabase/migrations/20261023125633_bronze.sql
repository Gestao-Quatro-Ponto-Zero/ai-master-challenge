-- Bronze: 1:1 com os CSVs do Kaggle (todas as colunas em texto) + metadados de ingestão.

create table bronze.accounts (
  account_id                   text,
  account_name                 text,
  industry                     text,
  country                      text,
  signup_date                  text,
  referral_source              text,
  plan_tier                    text,
  seats                        text,
  is_trial                     text,
  churn_flag                   text,
  _run_id                      uuid not null references ops.ingestion_runs (run_id) on delete cascade,
  _file_sha256                 text not null,
  _row_number                  integer not null,
  _row_hash                    text not null,
  _ingested_at                 timestamptz not null default now(),
  primary key (_file_sha256, _row_number)
);
create index accounts_run_id_idx on bronze.accounts (_run_id);
comment on table bronze.accounts is 'Cópia fiel de ravenstack_accounts.csv; uma linha por linha do arquivo.';
comment on column bronze.accounts.account_id is 'Valor bruto (texto) da coluna account_id do CSV.';
comment on column bronze.accounts.account_name is 'Valor bruto (texto) da coluna account_name do CSV.';
comment on column bronze.accounts.industry is 'Valor bruto (texto) da coluna industry do CSV.';
comment on column bronze.accounts.country is 'Valor bruto (texto) da coluna country do CSV.';
comment on column bronze.accounts.signup_date is 'Valor bruto (texto) da coluna signup_date do CSV.';
comment on column bronze.accounts.referral_source is 'Valor bruto (texto) da coluna referral_source do CSV.';
comment on column bronze.accounts.plan_tier is 'Valor bruto (texto) da coluna plan_tier do CSV.';
comment on column bronze.accounts.seats is 'Valor bruto (texto) da coluna seats do CSV.';
comment on column bronze.accounts.is_trial is 'Valor bruto (texto) da coluna is_trial do CSV.';
comment on column bronze.accounts.churn_flag is 'Valor bruto (texto) da coluna churn_flag do CSV.';
comment on column bronze.accounts._run_id is 'Execução que carregou a linha.';
comment on column bronze.accounts._file_sha256 is 'Hash do arquivo de origem (versão do arquivo).';
comment on column bronze.accounts._row_number is 'Número da linha no arquivo (1 = primeira linha de dados).';
comment on column bronze.accounts._row_hash is 'sha256 do conteúdo da linha.';
comment on column bronze.accounts._ingested_at is 'Momento da carga.';
alter table bronze.accounts enable row level security;

create table bronze.subscriptions (
  subscription_id              text,
  account_id                   text,
  start_date                   text,
  end_date                     text,
  plan_tier                    text,
  seats                        text,
  mrr_amount                   text,
  arr_amount                   text,
  is_trial                     text,
  upgrade_flag                 text,
  downgrade_flag               text,
  churn_flag                   text,
  billing_frequency            text,
  auto_renew_flag              text,
  _run_id                      uuid not null references ops.ingestion_runs (run_id) on delete cascade,
  _file_sha256                 text not null,
  _row_number                  integer not null,
  _row_hash                    text not null,
  _ingested_at                 timestamptz not null default now(),
  primary key (_file_sha256, _row_number)
);
create index subscriptions_run_id_idx on bronze.subscriptions (_run_id);
comment on table bronze.subscriptions is 'Cópia fiel de ravenstack_subscriptions.csv; uma linha por linha do arquivo.';
comment on column bronze.subscriptions.subscription_id is 'Valor bruto (texto) da coluna subscription_id do CSV.';
comment on column bronze.subscriptions.account_id is 'Valor bruto (texto) da coluna account_id do CSV.';
comment on column bronze.subscriptions.start_date is 'Valor bruto (texto) da coluna start_date do CSV.';
comment on column bronze.subscriptions.end_date is 'Valor bruto (texto) da coluna end_date do CSV.';
comment on column bronze.subscriptions.plan_tier is 'Valor bruto (texto) da coluna plan_tier do CSV.';
comment on column bronze.subscriptions.seats is 'Valor bruto (texto) da coluna seats do CSV.';
comment on column bronze.subscriptions.mrr_amount is 'Valor bruto (texto) da coluna mrr_amount do CSV.';
comment on column bronze.subscriptions.arr_amount is 'Valor bruto (texto) da coluna arr_amount do CSV.';
comment on column bronze.subscriptions.is_trial is 'Valor bruto (texto) da coluna is_trial do CSV.';
comment on column bronze.subscriptions.upgrade_flag is 'Valor bruto (texto) da coluna upgrade_flag do CSV.';
comment on column bronze.subscriptions.downgrade_flag is 'Valor bruto (texto) da coluna downgrade_flag do CSV.';
comment on column bronze.subscriptions.churn_flag is 'Valor bruto (texto) da coluna churn_flag do CSV.';
comment on column bronze.subscriptions.billing_frequency is 'Valor bruto (texto) da coluna billing_frequency do CSV.';
comment on column bronze.subscriptions.auto_renew_flag is 'Valor bruto (texto) da coluna auto_renew_flag do CSV.';
comment on column bronze.subscriptions._run_id is 'Execução que carregou a linha.';
comment on column bronze.subscriptions._file_sha256 is 'Hash do arquivo de origem (versão do arquivo).';
comment on column bronze.subscriptions._row_number is 'Número da linha no arquivo (1 = primeira linha de dados).';
comment on column bronze.subscriptions._row_hash is 'sha256 do conteúdo da linha.';
comment on column bronze.subscriptions._ingested_at is 'Momento da carga.';
alter table bronze.subscriptions enable row level security;

create table bronze.feature_usage (
  usage_id                     text,
  subscription_id              text,
  usage_date                   text,
  feature_name                 text,
  usage_count                  text,
  usage_duration_secs          text,
  error_count                  text,
  is_beta_feature              text,
  _run_id                      uuid not null references ops.ingestion_runs (run_id) on delete cascade,
  _file_sha256                 text not null,
  _row_number                  integer not null,
  _row_hash                    text not null,
  _ingested_at                 timestamptz not null default now(),
  primary key (_file_sha256, _row_number)
);
create index feature_usage_run_id_idx on bronze.feature_usage (_run_id);
comment on table bronze.feature_usage is 'Cópia fiel de ravenstack_feature_usage.csv; uma linha por linha do arquivo.';
comment on column bronze.feature_usage.usage_id is 'Valor bruto (texto) da coluna usage_id do CSV.';
comment on column bronze.feature_usage.subscription_id is 'Valor bruto (texto) da coluna subscription_id do CSV.';
comment on column bronze.feature_usage.usage_date is 'Valor bruto (texto) da coluna usage_date do CSV.';
comment on column bronze.feature_usage.feature_name is 'Valor bruto (texto) da coluna feature_name do CSV.';
comment on column bronze.feature_usage.usage_count is 'Valor bruto (texto) da coluna usage_count do CSV.';
comment on column bronze.feature_usage.usage_duration_secs is 'Valor bruto (texto) da coluna usage_duration_secs do CSV.';
comment on column bronze.feature_usage.error_count is 'Valor bruto (texto) da coluna error_count do CSV.';
comment on column bronze.feature_usage.is_beta_feature is 'Valor bruto (texto) da coluna is_beta_feature do CSV.';
comment on column bronze.feature_usage._run_id is 'Execução que carregou a linha.';
comment on column bronze.feature_usage._file_sha256 is 'Hash do arquivo de origem (versão do arquivo).';
comment on column bronze.feature_usage._row_number is 'Número da linha no arquivo (1 = primeira linha de dados).';
comment on column bronze.feature_usage._row_hash is 'sha256 do conteúdo da linha.';
comment on column bronze.feature_usage._ingested_at is 'Momento da carga.';
alter table bronze.feature_usage enable row level security;

create table bronze.support_tickets (
  ticket_id                    text,
  account_id                   text,
  submitted_at                 text,
  closed_at                    text,
  resolution_time_hours        text,
  priority                     text,
  first_response_time_minutes  text,
  satisfaction_score           text,
  escalation_flag              text,
  _run_id                      uuid not null references ops.ingestion_runs (run_id) on delete cascade,
  _file_sha256                 text not null,
  _row_number                  integer not null,
  _row_hash                    text not null,
  _ingested_at                 timestamptz not null default now(),
  primary key (_file_sha256, _row_number)
);
create index support_tickets_run_id_idx on bronze.support_tickets (_run_id);
comment on table bronze.support_tickets is 'Cópia fiel de ravenstack_support_tickets.csv; uma linha por linha do arquivo.';
comment on column bronze.support_tickets.ticket_id is 'Valor bruto (texto) da coluna ticket_id do CSV.';
comment on column bronze.support_tickets.account_id is 'Valor bruto (texto) da coluna account_id do CSV.';
comment on column bronze.support_tickets.submitted_at is 'Valor bruto (texto) da coluna submitted_at do CSV.';
comment on column bronze.support_tickets.closed_at is 'Valor bruto (texto) da coluna closed_at do CSV.';
comment on column bronze.support_tickets.resolution_time_hours is 'Valor bruto (texto) da coluna resolution_time_hours do CSV.';
comment on column bronze.support_tickets.priority is 'Valor bruto (texto) da coluna priority do CSV.';
comment on column bronze.support_tickets.first_response_time_minutes is 'Valor bruto (texto) da coluna first_response_time_minutes do CSV.';
comment on column bronze.support_tickets.satisfaction_score is 'Valor bruto (texto) da coluna satisfaction_score do CSV.';
comment on column bronze.support_tickets.escalation_flag is 'Valor bruto (texto) da coluna escalation_flag do CSV.';
comment on column bronze.support_tickets._run_id is 'Execução que carregou a linha.';
comment on column bronze.support_tickets._file_sha256 is 'Hash do arquivo de origem (versão do arquivo).';
comment on column bronze.support_tickets._row_number is 'Número da linha no arquivo (1 = primeira linha de dados).';
comment on column bronze.support_tickets._row_hash is 'sha256 do conteúdo da linha.';
comment on column bronze.support_tickets._ingested_at is 'Momento da carga.';
alter table bronze.support_tickets enable row level security;

create table bronze.churn_events (
  churn_event_id               text,
  account_id                   text,
  churn_date                   text,
  reason_code                  text,
  refund_amount_usd            text,
  preceding_upgrade_flag       text,
  preceding_downgrade_flag     text,
  is_reactivation              text,
  feedback_text                text,
  _run_id                      uuid not null references ops.ingestion_runs (run_id) on delete cascade,
  _file_sha256                 text not null,
  _row_number                  integer not null,
  _row_hash                    text not null,
  _ingested_at                 timestamptz not null default now(),
  primary key (_file_sha256, _row_number)
);
create index churn_events_run_id_idx on bronze.churn_events (_run_id);
comment on table bronze.churn_events is 'Cópia fiel de ravenstack_churn_events.csv; uma linha por linha do arquivo.';
comment on column bronze.churn_events.churn_event_id is 'Valor bruto (texto) da coluna churn_event_id do CSV.';
comment on column bronze.churn_events.account_id is 'Valor bruto (texto) da coluna account_id do CSV.';
comment on column bronze.churn_events.churn_date is 'Valor bruto (texto) da coluna churn_date do CSV.';
comment on column bronze.churn_events.reason_code is 'Valor bruto (texto) da coluna reason_code do CSV.';
comment on column bronze.churn_events.refund_amount_usd is 'Valor bruto (texto) da coluna refund_amount_usd do CSV.';
comment on column bronze.churn_events.preceding_upgrade_flag is 'Valor bruto (texto) da coluna preceding_upgrade_flag do CSV.';
comment on column bronze.churn_events.preceding_downgrade_flag is 'Valor bruto (texto) da coluna preceding_downgrade_flag do CSV.';
comment on column bronze.churn_events.is_reactivation is 'Valor bruto (texto) da coluna is_reactivation do CSV.';
comment on column bronze.churn_events.feedback_text is 'Valor bruto (texto) da coluna feedback_text do CSV.';
comment on column bronze.churn_events._run_id is 'Execução que carregou a linha.';
comment on column bronze.churn_events._file_sha256 is 'Hash do arquivo de origem (versão do arquivo).';
comment on column bronze.churn_events._row_number is 'Número da linha no arquivo (1 = primeira linha de dados).';
comment on column bronze.churn_events._row_hash is 'sha256 do conteúdo da linha.';
comment on column bronze.churn_events._ingested_at is 'Momento da carga.';
alter table bronze.churn_events enable row level security;
