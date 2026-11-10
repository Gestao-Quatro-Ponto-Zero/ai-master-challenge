-- 0005_system: auditoria (ARQ-04), eventos, importações CSV e lotes.
-- Fecha a FK core_deals.importacao_id.

create table system_lotes (
  id             bigint generated always as identity primary key,
  usuario_id     bigint not null references config_usuarios (id) on delete restrict,
  tipo           text not null check (tipo in ('tag', 'remover_tag', 'comentario', 'avancar_estagio', 'encerrar_perdido')),
  parametros     jsonb not null default '{}',
  etiquetas      jsonb,
  quantidade     integer not null check (quantidade >= 0),
  aplicados      integer not null default 0 check (aplicados >= 0),
  pulados        integer not null default 0 check (pulados >= 0),
  detalhe        jsonb not null default '{}',
  correlation_id uuid not null,
  criado_em      timestamptz not null default now(),
  desfeito_em    timestamptz,
  desfeito_por   bigint references config_usuarios (id) on delete restrict,
  constraint system_lotes_desfeito_ck check ((desfeito_em is null) = (desfeito_por is null))
);
create index system_lotes_usuario_id_idx on system_lotes (usuario_id);
create index system_lotes_desfeito_por_idx on system_lotes (desfeito_por);
create index system_lotes_correlation_id_idx on system_lotes (correlation_id);
comment on table system_lotes is 'Ações em lote da tela Leads. Desfazer em até 24 h lendo o antes da auditoria.';

create table system_auditoria (
  id             bigint generated always as identity primary key,
  tabela         text not null,
  registro_id    text not null,
  operacao       text not null check (operacao in ('insert', 'update')),
  antes          jsonb,
  depois         jsonb not null,
  usuario_id     bigint not null references config_usuarios (id) on delete restrict,
  papel          text not null,
  correlation_id uuid not null,
  lote_id        bigint references system_lotes (id) on delete restrict,
  data_negocio   date not null default config_data_negocio(),
  criado_em      timestamptz not null default now()
);
create index system_auditoria_usuario_idx on system_auditoria (usuario_id, criado_em desc);
create index system_auditoria_registro_idx on system_auditoria (tabela, registro_id, criado_em desc);
create index system_auditoria_deal_idx on system_auditoria ((depois ->> 'opportunity_id'), criado_em);
create index system_auditoria_correlation_id_idx on system_auditoria (correlation_id);
create index system_auditoria_lote_id_idx on system_auditoria (lote_id);
comment on table system_auditoria is 'Antes e depois de toda escrita auditada, com usuário, papel, momento, correlation_id e lote. Gravada só pelo gatilho system_auditar.';

create table system_eventos (
  id             bigint generated always as identity primary key,
  tipo           text not null check (tipo ~ '^[a-z_]+$'),
  detalhe        jsonb not null default '{}',
  usuario_id     bigint references config_usuarios (id) on delete restrict,
  correlation_id uuid,
  criado_em      timestamptz not null default now()
);
create index system_eventos_tipo_idx on system_eventos (tipo, criado_em desc);
create index system_eventos_usuario_id_idx on system_eventos (usuario_id);
create index system_eventos_correlation_id_idx on system_eventos (correlation_id);
comment on table system_eventos is 'carga_score, conflito_versao, banco_indisponivel, lote_aplicado, lote_desfeito, filtro_nao_entendido, roteamento_reserva.';

create table system_importacoes (
  id             bigint generated always as identity primary key,
  usuario_id     bigint not null references config_usuarios (id) on delete restrict,
  arquivo_nome   text not null check (char_length(arquivo_nome) between 1 and 255),
  arquivo_sha256 text not null check (arquivo_sha256 ~ '^[0-9a-f]{64}$'),
  linhas_total   integer not null check (linhas_total >= 0),
  aceitas        integer not null default 0 check (aceitas >= 0),
  ja_existiam    integer not null default 0 check (ja_existiam >= 0),
  recusadas      integer not null default 0 check (recusadas >= 0),
  recusas        jsonb not null default '[]',
  correlation_id uuid not null,
  criado_em      timestamptz not null default now()
);
create index system_importacoes_usuario_id_idx on system_importacoes (usuario_id);
create index system_importacoes_correlation_id_idx on system_importacoes (correlation_id);
comment on table system_importacoes is 'Resumo de cada importação CSV. recusas = [{linha, motivo}].';

alter table core_deals
  add constraint core_deals_importacao_id_fk foreign key (importacao_id) references system_importacoes (id) on delete restrict;
