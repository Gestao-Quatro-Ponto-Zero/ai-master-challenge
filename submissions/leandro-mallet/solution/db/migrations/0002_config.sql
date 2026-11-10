-- 0002_config: usuários (sem login, decisão 12/15), parâmetros, tags e motivos de perda.
-- Fecha as FKs de core_ que apontam para config_ e cria as funções de leitura de parâmetro.

create table config_usuarios (
  id            bigint generated always as identity primary key,
  papel         text not null check (papel in ('vendedor', 'manager', 'admin', 'sistema')),
  nome_exibicao text not null check (char_length(nome_exibicao) between 1 and 120),
  vendedor_nome text unique references core_vendedores (nome) on delete restrict,
  manager_nome  text unique references core_managers (nome) on delete restrict,
  ativo         boolean not null default true,
  criado_em     timestamptz not null default now(),
  constraint config_usuarios_papel_ck check (
    (papel = 'vendedor' and vendedor_nome is not null and manager_nome is null) or
    (papel = 'manager' and manager_nome is not null and vendedor_nome is null) or
    (papel in ('admin', 'sistema') and vendedor_nome is null and manager_nome is null)
  )
);
comment on table config_usuarios is 'Usuários escolhidos na tela (sem senha). Gerada do dataset: vendedores, managers, 1 admin e 1 usuário sistema (assina cargas).';

create table config_parametros (
  chave          text primary key check (chave ~ '^[a-z0-9_]+$'),
  valor          jsonb not null,
  descricao      text,
  atualizado_em  timestamptz not null default now(),
  atualizado_por bigint references config_usuarios (id) on delete restrict
);
create index config_parametros_atualizado_por_idx on config_parametros (atualizado_por);
comment on table config_parametros is 'Parâmetros do CRM e do score (data de referência, cortes, limites, execução ativa).';

create table config_tags (
  id            bigint generated always as identity primary key,
  nome          text not null check (char_length(nome) between 1 and 30),
  cor_token     text not null check (cor_token ~ '^[a-z0-9-]+$'),
  ativa         boolean not null default true,
  criada_por    bigint not null references config_usuarios (id) on delete restrict,
  criada_em     timestamptz not null default now(),
  arquivada_em  timestamptz,
  arquivada_por bigint references config_usuarios (id) on delete restrict,
  constraint config_tags_arquivo_ck check (ativa = (arquivada_em is null))
);
create unique index config_tags_nome_unq on config_tags (lower(nome));
create index config_tags_criada_por_idx on config_tags (criada_por);
create index config_tags_arquivada_por_idx on config_tags (arquivada_por);
comment on table config_tags is 'Tags. cor_token = um dos tokens de cor do tema (lista em config_parametros.tag_cores). Arquivar = ativa false.';

create table config_motivos_perda (
  codigo        text primary key check (codigo ~ '^[a-z_]+$'),
  rotulo        text not null,
  exige_detalhe boolean not null default false,
  ordem         smallint not null default 0,
  ativo         boolean not null default true
);
comment on table config_motivos_perda is 'Lista curta de motivo de perda (P14).';

-- FKs de core_ para config_ (índices já criados em 0001)
alter table core_contas
  add constraint core_contas_atualizado_por_fk foreign key (atualizado_por) references config_usuarios (id) on delete restrict;
alter table core_contatos
  add constraint core_contatos_criado_por_fk foreign key (criado_por) references config_usuarios (id) on delete restrict,
  add constraint core_contatos_atualizado_por_fk foreign key (atualizado_por) references config_usuarios (id) on delete restrict;
alter table core_deals
  add constraint core_deals_criado_por_fk foreign key (criado_por) references config_usuarios (id) on delete restrict,
  add constraint core_deals_atualizado_por_fk foreign key (atualizado_por) references config_usuarios (id) on delete restrict,
  add constraint core_deals_motivo_perda_fk foreign key (motivo_perda) references config_motivos_perda (codigo) on delete restrict;

-- Leitura de parâmetros (usadas por views, gatilhos e functions)
create function config_valor(p_chave text) returns jsonb
language sql stable
set search_path = public
as $$
  select valor from config_parametros where chave = p_chave
$$;

create function config_inteiro(p_chave text, p_padrao integer) returns integer
language sql stable
set search_path = public
as $$
  select coalesce((select (valor #>> '{}')::integer from config_parametros where chave = p_chave), p_padrao)
$$;

create function config_data_negocio() returns date
language sql stable
set search_path = public
as $$
  -- relógio do CRM (P6): a data de referência enquanto estiver em demonstração; sem ela, a data real
  select coalesce((select (valor #>> '{}')::date from config_parametros where chave = 'data_referencia'), current_date)
$$;

create function config_execucao_ativa() returns bigint
language sql stable
set search_path = public
as $$
  select (valor #>> '{}')::bigint from config_parametros where chave = 'execucao_ativa'
$$;
