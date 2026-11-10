-- 0007_core_contatos.sql  [LOTE 2]
-- Contatos (pessoas) das empresas, e a FK core_deals.contato_id que ficou pendente no lote 1.
-- O dataset não tem contatos: a tabela nasce vazia. Sem DELETE: inativo_em.

create table core_contatos (
  id             bigint generated always as identity primary key,
  conta_nome     text references core_contas (nome) on delete restrict,   -- nulo: contato de deal ainda sem empresa
  nome           text not null check (char_length(btrim(nome)) between 1 and 120),
  cargo          text check (char_length(cargo) <= 80),
  email          text check (email is null or email ~* '^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$'),
  telefone       text check (telefone is null or telefone ~ '^[0-9 +().-]{6,25}$'),
  criado_por     bigint not null references config_usuarios (id) on delete restrict,
  criado_em      timestamptz not null default now(),
  atualizado_em  timestamptz not null default now(),
  atualizado_por bigint references config_usuarios (id) on delete restrict,
  inativo_em     timestamptz                                             -- não há DELETE
);
create index core_contatos_conta_nome_idx on core_contatos (conta_nome);
create index core_contatos_criado_por_idx on core_contatos (criado_por);
create index core_contatos_atualizado_por_idx on core_contatos (atualizado_por);

-- FK pendente do lote 1 (o índice core_deals_contato_id_idx já existe)
alter table core_deals
  add constraint core_deals_contato_id_fkey foreign key (contato_id) references core_contatos (id) on delete restrict;
