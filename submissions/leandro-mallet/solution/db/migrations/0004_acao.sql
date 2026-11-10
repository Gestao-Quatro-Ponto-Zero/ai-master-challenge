-- 0004_acao: o que as pessoas registram (ações, prioridades do dia, comentários, tags no deal e atribuições).
-- Nada aqui é apagado: desfazer e remover são updates (desfeita_em, removido_em, removida_em).

create table acao_registros (
  id             bigint generated always as identity primary key,
  opportunity_id text not null references core_deals (opportunity_id) on delete restrict,
  usuario_id     bigint not null references config_usuarios (id) on delete restrict,
  papel          text not null,
  execucao_id    bigint references score_execucoes (id) on delete restrict,
  acao           text not null check (acao in ('liguei', 'requalifiquei', 'desisti', 'resposta_recebida', 'prioridade_feita', 'prioridade_pulada')),
  nota           text check (char_length(nota) <= 280),
  data_negocio   date not null,
  correlation_id uuid not null,
  criado_em      timestamptz not null default now(),
  desfeita_em    timestamptz,
  desfeita_por   bigint references config_usuarios (id) on delete restrict,
  constraint acao_registros_desfeita_ck check ((desfeita_em is null) = (desfeita_por is null))
);
create index acao_registros_opportunity_idx on acao_registros (opportunity_id, criado_em desc);
create index acao_registros_usuario_dia_idx on acao_registros (usuario_id, data_negocio);
create index acao_registros_execucao_id_idx on acao_registros (execucao_id);
create index acao_registros_desfeita_por_idx on acao_registros (desfeita_por);
comment on table acao_registros is 'Liguei, Requalifiquei, Desisti, resposta_recebida (prevista; sem dado no dataset) e as marcas da prioridade do dia.';

create table acao_prioridades (
  id             bigint generated always as identity primary key,
  usuario_id     bigint not null references config_usuarios (id) on delete restrict,
  data_negocio   date not null,
  posicao        integer not null check (posicao >= 1),
  opportunity_id text not null references core_deals (opportunity_id) on delete restrict,
  criado_em      timestamptz not null default now(),
  constraint acao_prioridades_deal_unq unique (usuario_id, data_negocio, opportunity_id),
  constraint acao_prioridades_posicao_unq unique (usuario_id, data_negocio, posicao)
);
create index acao_prioridades_opportunity_id_idx on acao_prioridades (opportunity_id);
comment on table acao_prioridades is 'Fila do dia de cada usuário, montada na primeira abertura e estável no dia.';

create table acao_comentarios (
  id             bigint generated always as identity primary key,
  opportunity_id text not null references core_deals (opportunity_id) on delete restrict,
  usuario_id     bigint not null references config_usuarios (id) on delete restrict,
  texto          text not null check (char_length(texto) between 1 and 1000),
  data_negocio   date not null,
  criado_em      timestamptz not null default now(),
  editado_em     timestamptz,
  removido_em    timestamptz,
  removido_por   bigint references config_usuarios (id) on delete restrict,
  constraint acao_comentarios_removido_ck check ((removido_em is null) = (removido_por is null))
);
create index acao_comentarios_opportunity_id_idx on acao_comentarios (opportunity_id);
create index acao_comentarios_ativos_idx on acao_comentarios (opportunity_id, criado_em desc) where removido_em is null;
create index acao_comentarios_usuario_id_idx on acao_comentarios (usuario_id);
create index acao_comentarios_removido_por_idx on acao_comentarios (removido_por);
comment on table acao_comentarios is 'Comentários. Apagar = remoção lógica (removido_em/removido_por).';

create table acao_deal_tags (
  id             bigint generated always as identity primary key,
  opportunity_id text not null references core_deals (opportunity_id) on delete restrict,
  tag_id         bigint not null references config_tags (id) on delete restrict,
  usuario_id     bigint not null references config_usuarios (id) on delete restrict,
  criado_em      timestamptz not null default now(),
  removida_em    timestamptz,
  removida_por   bigint references config_usuarios (id) on delete restrict,
  constraint acao_deal_tags_removida_ck check ((removida_em is null) = (removida_por is null))
);
create unique index acao_deal_tags_ativa_unq on acao_deal_tags (opportunity_id, tag_id) where removida_em is null;
create index acao_deal_tags_opportunity_id_idx on acao_deal_tags (opportunity_id);
create index acao_deal_tags_tag_id_idx on acao_deal_tags (tag_id);
create index acao_deal_tags_tag_ativa_idx on acao_deal_tags (tag_id) where removida_em is null;
create index acao_deal_tags_usuario_id_idx on acao_deal_tags (usuario_id);
create index acao_deal_tags_removida_por_idx on acao_deal_tags (removida_por);
comment on table acao_deal_tags is 'Tags aplicadas a deals. Remover = removida_em.';

create table acao_atribuicoes (
  id             bigint generated always as identity primary key,
  opportunity_id text not null references core_deals (opportunity_id) on delete restrict,
  vendedor_de    text references core_vendedores (nome) on delete restrict,
  vendedor_para  text not null references core_vendedores (nome) on delete restrict,
  origem         text not null check (origem in ('roteamento', 'roteamento_reserva', 'reatribuicao')),
  usuario_id     bigint not null references config_usuarios (id) on delete restrict,
  execucao_id    bigint references score_execucoes (id) on delete restrict,
  fit            numeric(5, 4),
  criterio       jsonb not null default '{}',
  motivo         text check (char_length(motivo) <= 280),
  data_negocio   date not null,
  correlation_id uuid not null,
  criado_em      timestamptz not null default now()
);
create index acao_atribuicoes_opportunity_idx on acao_atribuicoes (opportunity_id, criado_em desc);
create index acao_atribuicoes_vendedor_de_idx on acao_atribuicoes (vendedor_de);
create index acao_atribuicoes_vendedor_para_idx on acao_atribuicoes (vendedor_para);
create index acao_atribuicoes_usuario_id_idx on acao_atribuicoes (usuario_id);
create index acao_atribuicoes_execucao_id_idx on acao_atribuicoes (execucao_id);
comment on table acao_atribuicoes is 'Quem recebeu cada lead e por quê: roteamento pelo FIT, reserva (sem candidato) ou reatribuição pelo manager.';
