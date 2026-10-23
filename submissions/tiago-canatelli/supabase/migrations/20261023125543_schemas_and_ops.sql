-- Schemas do lake e tabelas de operação (alimentam o painel de ingestão e o catálogo).

create schema if not exists bronze;
create schema if not exists silver;
create schema if not exists gold;
create schema if not exists ops;
create schema if not exists app;

comment on schema bronze is 'Camada bronze: cópia fiel dos CSVs (tudo texto) com metadados de ingestão.';
comment on schema silver is 'Camada silver: dados tipados, deduplicados e com chaves validadas.';
comment on schema gold   is 'Camada gold: KPIs e marts de negócio.';
comment on schema ops    is 'Operação do lake: execuções de ingestão, qualidade de dados e catálogo.';
comment on schema app    is 'Aplicação: prompts, perfis de análise, execuções de IA e base do RAG.';

revoke all on schema bronze, silver, gold, ops, app from public, anon, authenticated;

create table ops.ingestion_runs (
  run_id         uuid primary key default gen_random_uuid(),
  started_at     timestamptz not null default now(),
  finished_at    timestamptz,
  status         text not null default 'running'
                 check (status in ('running', 'success', 'failed', 'skipped')),
  trigger        text not null default 'manual' check (trigger in ('manual', 'cron', 'test')),
  source         text not null check (source in ('kaggle_mcp', 'local')),
  source_ref     text,
  source_version integer,
  git_sha        text,
  error          text
);
comment on table  ops.ingestion_runs is 'Uma linha por execução do pipeline ravenlake.';
comment on column ops.ingestion_runs.run_id is 'Identificador da execução.';
comment on column ops.ingestion_runs.started_at is 'Início da execução.';
comment on column ops.ingestion_runs.finished_at is 'Fim da execução (nulo enquanto roda).';
comment on column ops.ingestion_runs.status is 'running, success, failed ou skipped (fonte sem mudança).';
comment on column ops.ingestion_runs.trigger is 'Quem disparou: manual, cron (Render) ou test.';
comment on column ops.ingestion_runs.source is 'Fonte dos dados: kaggle_mcp ou local.';
comment on column ops.ingestion_runs.source_ref is 'Referência da fonte (ex.: rivalytics/saas-subscription-and-churn-analytics-dataset).';
comment on column ops.ingestion_runs.source_version is 'Versão do dataset na fonte (Kaggle).';
comment on column ops.ingestion_runs.git_sha is 'Commit do código que executou.';
comment on column ops.ingestion_runs.error is 'Mensagem de erro, se falhou.';

create table ops.ingestion_steps (
  step_id       bigint generated always as identity primary key,
  run_id        uuid not null references ops.ingestion_runs (run_id) on delete cascade,
  dataset       text not null,
  layer         text not null check (layer in ('raw', 'bronze', 'silver', 'dq', 'gold', 'catalog')),
  file_sha256   text,
  bytes         bigint,
  storage_path  text,
  rows_read     integer,
  rows_loaded   integer not null default 0,
  rows_rejected integer not null default 0,
  status        text not null default 'running'
                check (status in ('running', 'success', 'failed', 'skipped')),
  started_at    timestamptz not null default now(),
  finished_at   timestamptz,
  duration_ms   integer,
  error         text
);
create index ingestion_steps_run_id_idx on ops.ingestion_steps (run_id);
comment on table  ops.ingestion_steps is 'Uma linha por dataset × camada em cada execução; progresso atualizado a cada lote.';
comment on column ops.ingestion_steps.step_id is 'Identificador da etapa.';
comment on column ops.ingestion_steps.run_id is 'Execução a que a etapa pertence.';
comment on column ops.ingestion_steps.dataset is 'Dataset (accounts, subscriptions, feature_usage, support_tickets, churn_events) ou "all".';
comment on column ops.ingestion_steps.layer is 'Camada: raw, bronze, silver, dq, gold ou catalog.';
comment on column ops.ingestion_steps.file_sha256 is 'Hash do arquivo de origem.';
comment on column ops.ingestion_steps.bytes is 'Tamanho do arquivo em bytes.';
comment on column ops.ingestion_steps.storage_path is 'Caminho do arquivo no bucket raw.';
comment on column ops.ingestion_steps.rows_read is 'Linhas lidas da origem.';
comment on column ops.ingestion_steps.rows_loaded is 'Linhas carregadas na camada.';
comment on column ops.ingestion_steps.rows_rejected is 'Linhas rejeitadas (ver silver._rejects).';
comment on column ops.ingestion_steps.status is 'running, success, failed ou skipped.';
comment on column ops.ingestion_steps.started_at is 'Início da etapa.';
comment on column ops.ingestion_steps.finished_at is 'Fim da etapa.';
comment on column ops.ingestion_steps.duration_ms is 'Duração em milissegundos.';
comment on column ops.ingestion_steps.error is 'Mensagem de erro, se falhou.';

create table ops.dq_results (
  dq_id        bigint generated always as identity primary key,
  run_id       uuid not null references ops.ingestion_runs (run_id) on delete cascade,
  check_name   text not null,
  table_name   text not null,
  severity     text not null check (severity in ('error', 'warning', 'info')),
  status       text not null check (status in ('pass', 'fail')),
  failing_rows integer not null default 0,
  total_rows   integer,
  details      text,
  sample       jsonb,
  checked_at   timestamptz not null default now()
);
create index dq_results_run_id_idx on ops.dq_results (run_id);
comment on table  ops.dq_results is 'Resultado das checagens de qualidade de dados por execução.';
comment on column ops.dq_results.dq_id is 'Identificador do resultado.';
comment on column ops.dq_results.run_id is 'Execução avaliada.';
comment on column ops.dq_results.check_name is 'Nome da checagem.';
comment on column ops.dq_results.table_name is 'Tabela avaliada.';
comment on column ops.dq_results.severity is 'error interrompe o pipeline antes do gold; warning e info viram achados.';
comment on column ops.dq_results.status is 'pass ou fail.';
comment on column ops.dq_results.failing_rows is 'Linhas que falharam.';
comment on column ops.dq_results.total_rows is 'Linhas avaliadas.';
comment on column ops.dq_results.details is 'Explicação em linguagem simples.';
comment on column ops.dq_results.sample is 'Amostra de até 5 registros que falharam.';
comment on column ops.dq_results.checked_at is 'Quando a checagem rodou.';

create table ops.catalog_tables (
  schema_name    text not null,
  table_name     text not null,
  layer          text not null,
  description    text,
  row_count      bigint,
  column_count   integer,
  last_refreshed timestamptz not null default now(),
  primary key (schema_name, table_name)
);
comment on table  ops.catalog_tables is 'Catálogo: uma linha por tabela/view do lake.';
comment on column ops.catalog_tables.schema_name is 'Schema.';
comment on column ops.catalog_tables.table_name is 'Tabela ou view.';
comment on column ops.catalog_tables.layer is 'Camada do lake (bronze, silver, gold, ops, app).';
comment on column ops.catalog_tables.description is 'Descrição (COMMENT ON TABLE).';
comment on column ops.catalog_tables.row_count is 'Quantidade de linhas na última atualização do catálogo.';
comment on column ops.catalog_tables.column_count is 'Quantidade de colunas.';
comment on column ops.catalog_tables.last_refreshed is 'Quando o catálogo foi atualizado.';

create table ops.catalog_columns (
  schema_name    text not null,
  table_name     text not null,
  column_name    text not null,
  ordinal        integer not null,
  data_type      text not null,
  description    text,
  is_key         boolean not null default false,
  is_pii         boolean not null default false,
  null_pct       numeric(5, 2),
  distinct_count bigint,
  primary key (schema_name, table_name, column_name),
  foreign key (schema_name, table_name) references ops.catalog_tables on delete cascade
);
comment on table  ops.catalog_columns is 'Catálogo: uma linha por coluna, com estatísticas.';
comment on column ops.catalog_columns.schema_name is 'Schema.';
comment on column ops.catalog_columns.table_name is 'Tabela ou view.';
comment on column ops.catalog_columns.column_name is 'Coluna.';
comment on column ops.catalog_columns.ordinal is 'Posição da coluna.';
comment on column ops.catalog_columns.data_type is 'Tipo de dado.';
comment on column ops.catalog_columns.description is 'Descrição (COMMENT ON COLUMN).';
comment on column ops.catalog_columns.is_key is 'Faz parte da chave primária.';
comment on column ops.catalog_columns.is_pii is 'Dado que identifica cliente (o dataset é sintético).';
comment on column ops.catalog_columns.null_pct is '% de nulos (só silver e gold).';
comment on column ops.catalog_columns.distinct_count is 'Valores distintos (só silver e gold).';

alter table ops.ingestion_runs  enable row level security;
alter table ops.ingestion_steps enable row level security;
alter table ops.dq_results      enable row level security;
alter table ops.catalog_tables  enable row level security;
alter table ops.catalog_columns enable row level security;

insert into storage.buckets (id, name, public)
values ('raw', 'raw', false)
on conflict (id) do nothing;
