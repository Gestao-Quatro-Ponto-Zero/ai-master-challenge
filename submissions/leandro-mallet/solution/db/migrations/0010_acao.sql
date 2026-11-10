-- 0010_acao.sql  [LOTE 2]
-- Cria o que as pessoas registram no CRM (acao_): ações e prioridades do dia, comentários (com remoção
-- lógica), tags nos deals (com remoção lógica), a lista de prioridades do dia e as reatribuições.

create table acao_registros (
  id             bigint generated always as identity primary key,
  opportunity_id text not null references core_deals (opportunity_id) on delete restrict,
  usuario_id     bigint not null references config_usuarios (id) on delete restrict,
  papel          text not null check (papel in ('vendedor', 'manager', 'admin')),   -- papel na hora da ação
  execucao_id    bigint references score_execucoes (id) on delete restrict,         -- nota que estava na tela
  acao           text not null check (acao in ('liguei', 'requalifiquei', 'desisti', 'prioridade_feita', 'prioridade_pulada')),
  nota           text check (char_length(nota) <= 280),
  data_negocio   date not null,                                                      -- relógio do CRM
  criado_em      timestamptz not null default now(),
  desfeita_em    timestamptz,                                                        -- desfazer = update
  desfeita_por   bigint references config_usuarios (id) on delete restrict
);
create index acao_registros_opportunity_criado_idx on acao_registros (opportunity_id, criado_em desc);
create index acao_registros_usuario_criado_idx on acao_registros (usuario_id, criado_em desc);
create index acao_registros_execucao_id_idx on acao_registros (execucao_id);
create index acao_registros_desfeita_por_idx on acao_registros (desfeita_por);

create table acao_comentarios (
  id             bigint generated always as identity primary key,
  opportunity_id text not null references core_deals (opportunity_id) on delete restrict,
  usuario_id     bigint not null references config_usuarios (id) on delete restrict,
  texto          text not null check (char_length(btrim(texto)) between 1 and 1000),
  data_negocio   date not null,
  criado_em      timestamptz not null default now(),
  editado_em     timestamptz,
  removido_em    timestamptz,                    -- "apagar" na tela = remoção lógica
  removido_por   bigint references config_usuarios (id) on delete restrict
);
create index acao_comentarios_opportunity_criado_idx on acao_comentarios (opportunity_id, criado_em desc);
create index acao_comentarios_usuario_id_idx on acao_comentarios (usuario_id);
create index acao_comentarios_removido_por_idx on acao_comentarios (removido_por);

create table acao_deal_tags (
  id             bigint generated always as identity primary key,
  opportunity_id text not null references core_deals (opportunity_id) on delete restrict,
  tag_id         bigint not null references config_tags (id) on delete restrict,
  usuario_id     bigint not null references config_usuarios (id) on delete restrict,
  criado_em      timestamptz not null default now(),
  removida_em    timestamptz,                    -- remover tag = remoção lógica
  removida_por   bigint references config_usuarios (id) on delete restrict
);
create unique index acao_deal_tags_ativa_unica_idx on acao_deal_tags (opportunity_id, tag_id) where removida_em is null;
create index acao_deal_tags_opportunity_id_idx on acao_deal_tags (opportunity_id);
create index acao_deal_tags_tag_id_idx on acao_deal_tags (tag_id);
create index acao_deal_tags_usuario_id_idx on acao_deal_tags (usuario_id);
create index acao_deal_tags_removida_por_idx on acao_deal_tags (removida_por);

-- Lista do dia: montada na primeira abertura do dia (dia real, no fuso configurado) e estável até o dia acabar
create table acao_prioridades (
  id             bigint generated always as identity primary key,
  usuario_id     bigint not null references config_usuarios (id) on delete restrict,
  dia            date not null,
  posicao        smallint not null check (posicao > 0),
  opportunity_id text not null references core_deals (opportunity_id) on delete restrict,
  criado_em      timestamptz not null default now(),
  constraint acao_prioridades_deal_unico_uk unique (usuario_id, dia, opportunity_id),
  constraint acao_prioridades_posicao_unica_uk unique (usuario_id, dia, posicao)
);
create index acao_prioridades_opportunity_id_idx on acao_prioridades (opportunity_id);

-- Reatribuição pelo manager ou admin (passar o deal para outro vendedor)
create table acao_reatribuicoes (
  id             bigint generated always as identity primary key,
  opportunity_id text not null references core_deals (opportunity_id) on delete restrict,
  de_vendedor    text not null references core_vendedores (nome) on delete restrict,
  para_vendedor  text not null references core_vendedores (nome) on delete restrict,
  usuario_id     bigint not null references config_usuarios (id) on delete restrict,
  motivo         text check (char_length(motivo) <= 280),
  criado_em      timestamptz not null default now(),
  constraint acao_reatribuicoes_vendedores_diferentes_chk check (de_vendedor <> para_vendedor)
);
create index acao_reatribuicoes_opportunity_id_idx on acao_reatribuicoes (opportunity_id);
create index acao_reatribuicoes_de_vendedor_idx on acao_reatribuicoes (de_vendedor);
create index acao_reatribuicoes_para_vendedor_idx on acao_reatribuicoes (para_vendedor);
create index acao_reatribuicoes_usuario_id_idx on acao_reatribuicoes (usuario_id);
