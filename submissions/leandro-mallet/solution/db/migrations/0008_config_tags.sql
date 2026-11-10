-- 0008_config_tags.sql  [LOTE 2]
-- Catálogo de tags. Nome único sem diferenciar maiúsculas; cor = um dos 6 tokens do tema (FE-03).
-- Arquivar = ativa false (não há DELETE).

create table config_tags (
  id         bigint generated always as identity primary key,
  nome       text not null check (char_length(btrim(nome)) between 1 and 30),
  cor_token  text not null check (cor_token in ('tag-1', 'tag-2', 'tag-3', 'tag-4', 'tag-5', 'tag-6')),
  ativa      boolean not null default true,
  criada_por bigint not null references config_usuarios (id) on delete restrict,
  criada_em  timestamptz not null default now()
);
create unique index config_tags_nome_unico_idx on config_tags (lower(btrim(nome)));
create index config_tags_criada_por_idx on config_tags (criada_por);
