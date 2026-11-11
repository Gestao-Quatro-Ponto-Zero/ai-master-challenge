-- 0011_system.sql  [LOTE 2]
-- Registros do sistema (system_): lotes, importações, eventos e roteamento de lead novo.
-- Fecha as FKs pendentes do lote 1: system_auditoria.lote_id e core_deals.importacao_id.

create table system_lotes (
  id             bigint generated always as identity primary key,
  usuario_id     bigint not null references config_usuarios (id) on delete restrict,
  tipo           text not null check (tipo in ('aplicar_tag', 'remover_tag', 'comentar', 'avancar_estagio', 'encerrar_perdido')),
  parametros     jsonb not null default '{}'::jsonb,
  etiquetas      jsonb not null default '{}'::jsonb,   -- o filtro usado para selecionar
  quantidade     integer not null check (quantidade >= 0),
  aplicados      integer not null default 0 check (aplicados >= 0),
  pulados        integer not null default 0 check (pulados >= 0),
  correlation_id uuid not null,
  criado_em      timestamptz not null default now(),
  desfeito_em    timestamptz,
  desfeito_por   bigint references config_usuarios (id) on delete restrict
);
create index system_lotes_usuario_id_idx on system_lotes (usuario_id);
create index system_lotes_desfeito_por_idx on system_lotes (desfeito_por);
create index system_lotes_correlation_id_idx on system_lotes (correlation_id);

create table system_importacoes (
  id             bigint generated always as identity primary key,
  usuario_id     bigint not null references config_usuarios (id) on delete restrict,
  arquivo_nome   text not null check (char_length(arquivo_nome) between 1 and 255),
  arquivo_sha256 text not null check (arquivo_sha256 ~ '^[0-9a-f]{64}$'),
  linhas_total   integer not null check (linhas_total >= 0),
  aceitas        integer not null default 0 check (aceitas >= 0),
  ja_existiam    integer not null default 0 check (ja_existiam >= 0),
  recusadas      integer not null default 0 check (recusadas >= 0),
  recusas        jsonb not null default '[]'::jsonb,   -- [{linha, motivo}]
  correlation_id uuid not null,
  criado_em      timestamptz not null default now()
);
create index system_importacoes_usuario_id_idx on system_importacoes (usuario_id);
create index system_importacoes_correlation_id_idx on system_importacoes (correlation_id);
create index system_importacoes_arquivo_sha256_idx on system_importacoes (arquivo_sha256);

create table system_eventos (
  id             bigint generated always as identity primary key,
  tipo           text not null check (tipo ~ '^[a-z][a-z_]*$'),
  detalhe        jsonb not null default '{}'::jsonb,
  usuario_id     bigint references config_usuarios (id) on delete restrict,
  correlation_id uuid,
  criado_em      timestamptz not null default now()
);
create index system_eventos_tipo_criado_em_idx on system_eventos (tipo, criado_em desc);
create index system_eventos_usuario_id_idx on system_eventos (usuario_id);
create index system_eventos_correlation_id_idx on system_eventos (correlation_id);

-- Roteamento de lead novo: para quem foi, por qual regra, com o FIT e os candidatos considerados
create table system_roteamentos (
  id             bigint generated always as identity primary key,
  opportunity_id text not null references core_deals (opportunity_id) on delete restrict,
  vendedor_nome  text not null references core_vendedores (nome) on delete restrict,
  regra          text not null check (regra in ('escolhido', 'maior_fit', 'menos_abertos', 'todos_no_teto')),
  execucao_id    bigint references score_execucoes (id) on delete restrict,
  cohort         text,
  fit            smallint check (fit between 0 and 100),
  candidatos     jsonb not null default '[]'::jsonb,
  usuario_id     bigint not null references config_usuarios (id) on delete restrict,
  correlation_id uuid not null,
  criado_em      timestamptz not null default now()
);
create index system_roteamentos_opportunity_id_idx on system_roteamentos (opportunity_id);
create index system_roteamentos_vendedor_nome_idx on system_roteamentos (vendedor_nome);
create index system_roteamentos_execucao_id_idx on system_roteamentos (execucao_id);
create index system_roteamentos_usuario_id_idx on system_roteamentos (usuario_id);

-- FKs pendentes do lote 1 (os índices já existem)
alter table system_auditoria
  add constraint system_auditoria_lote_id_fkey foreign key (lote_id) references system_lotes (id) on delete restrict;
alter table core_deals
  add constraint core_deals_importacao_id_fkey foreign key (importacao_id) references system_importacoes (id) on delete restrict;
