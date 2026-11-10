-- 0001_core: cadastro do CRM (escritórios, managers, vendedores, produtos, contas, contatos e deals).
-- Nomes de tabelas e colunas seguem app/ESPEC-TELAS.md, seção 8.
-- As FKs que apontam para config_ e system_ são fechadas em 0002 e 0005, quando as tabelas de destino existem.
-- Dinheiro em inteiro de dólar (BD-05). Deal sem empresa = conta_nome nula (BD-02).

create table core_escritorios (
  nome text primary key check (char_length(nome) between 1 and 60)
);
comment on table core_escritorios is 'Escritórios regionais (Central, East, West).';

create table core_managers (
  nome            text primary key check (char_length(nome) between 1 and 120),
  escritorio_nome text not null references core_escritorios (nome) on delete restrict
);
create index core_managers_escritorio_nome_idx on core_managers (escritorio_nome);
comment on table core_managers is 'Managers e o escritório de cada um.';

create table core_vendedores (
  nome         text primary key check (char_length(nome) between 1 and 120),
  manager_nome text not null references core_managers (nome) on delete restrict,
  ativo        boolean not null default true
);
create index core_vendedores_manager_nome_idx on core_vendedores (manager_nome);
comment on table core_vendedores is 'Vendedores. ativo = recebe lead novo no roteamento.';

create table core_produtos (
  nome  text primary key check (char_length(nome) between 1 and 60),
  serie text not null,
  preco integer not null check (preco > 0)
);
comment on table core_produtos is 'Catálogo. preco = preço de tabela em dólar inteiro.';

create table core_contas (
  nome             text primary key check (char_length(nome) between 1 and 120),
  setor            text,
  ano_fundacao     integer,
  receita_milhoes  numeric(14, 2),
  funcionarios     integer check (funcionarios >= 0),
  porte            text check (porte in ('pequena', 'media', 'grande')),
  pais             text,
  empresa_mae_nome text references core_contas (nome) on delete restrict,
  atualizado_em    timestamptz not null default now(),
  atualizado_por   bigint
);
create index core_contas_empresa_mae_nome_idx on core_contas (empresa_mae_nome);
create index core_contas_atualizado_por_idx on core_contas (atualizado_por);
create index core_contas_setor_porte_idx on core_contas (setor, porte);
comment on table core_contas is 'Empresas. receita_milhoes é medida do dataset, não dinheiro do CRM. porte = tercis de funcionários gravados na carga.';

create table core_contatos (
  id             bigint generated always as identity primary key,
  conta_nome     text references core_contas (nome) on delete restrict,
  nome           text not null check (char_length(nome) between 1 and 120),
  cargo          text check (char_length(cargo) <= 120),
  email          text check (email is null or email ~* '^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$'),
  telefone       text check (char_length(telefone) <= 40),
  criado_por     bigint not null,
  criado_em      timestamptz not null default now(),
  atualizado_em  timestamptz not null default now(),
  atualizado_por bigint,
  inativo_em     timestamptz
);
create index core_contatos_conta_nome_idx on core_contatos (conta_nome);
create index core_contatos_criado_por_idx on core_contatos (criado_por);
create index core_contatos_atualizado_por_idx on core_contatos (atualizado_por);
comment on table core_contatos is 'Pessoas de contato. conta_nome nula para contato de deal sem empresa. Sem DELETE: inativo_em.';

create table core_deals (
  opportunity_id       text primary key check (opportunity_id ~ '^[A-Z0-9]{8}$'),
  nome                 text not null check (char_length(nome) between 1 and 120),
  vendedor_nome        text not null references core_vendedores (nome) on delete restrict,
  produto_nome         text not null references core_produtos (nome) on delete restrict,
  conta_nome           text references core_contas (nome) on delete restrict,
  contato_id           bigint references core_contatos (id) on delete restrict,
  estagio              text not null check (estagio in ('Prospecting', 'Engaging', 'Won', 'Lost')),
  engage_date          date,
  data_abertura        date,
  close_date           date,
  close_value          integer,
  motivo_perda         text,
  motivo_perda_detalhe text check (char_length(motivo_perda_detalhe) <= 280),
  ultimo_contato_carga date,
  ultimo_contato_em    date,
  criado_em            timestamptz,
  criado_por           bigint,
  importacao_id        bigint,
  atualizado_em        timestamptz not null default now(),
  atualizado_por       bigint,
  constraint core_deals_abertura_ck check (estagio not in ('Engaging', 'Won') or data_abertura is not null),
  constraint core_deals_fechamento_ck check ((estagio in ('Won', 'Lost')) = (close_date is not null)),
  constraint core_deals_valor_won_ck check (estagio <> 'Won' or close_value > 0),
  constraint core_deals_valor_lost_ck check (estagio <> 'Lost' or coalesce(close_value, 0) = 0),
  constraint core_deals_valor_aberto_ck check (estagio not in ('Prospecting', 'Engaging') or close_value is null),
  constraint core_deals_datas_ck check (close_date is null or data_abertura is null or close_date >= data_abertura),
  constraint core_deals_motivo_ck check (motivo_perda is null or estagio = 'Lost')
);
create index core_deals_vendedor_nome_idx on core_deals (vendedor_nome);
create index core_deals_produto_nome_idx on core_deals (produto_nome);
create index core_deals_conta_nome_idx on core_deals (conta_nome);
create index core_deals_contato_id_idx on core_deals (contato_id);
create index core_deals_motivo_perda_idx on core_deals (motivo_perda);
create index core_deals_criado_por_idx on core_deals (criado_por);
create index core_deals_importacao_id_idx on core_deals (importacao_id);
create index core_deals_atualizado_por_idx on core_deals (atualizado_por);
create index core_deals_estagio_vendedor_idx on core_deals (estagio, vendedor_nome);
create index core_deals_data_abertura_idx on core_deals (data_abertura);
create index core_deals_ultimo_contato_em_idx on core_deals (ultimo_contato_em);
create index core_deals_close_date_idx on core_deals (close_date);
create index core_deals_estagio_close_date_idx on core_deals (estagio, close_date);
comment on table core_deals is 'Deals (= leads). engage_date guarda o valor original do dataset; data_abertura é a data operacional (P4/P6).';
comment on column core_deals.ultimo_contato_carga is 'Primeiro contato vindo da carga (proposta P5). O gatilho de contato nunca fica abaixo dele.';
comment on column core_deals.atualizado_em is 'Também é a versão do deal: a tela envia o valor lido e o gatilho recusa se mudou (409).';
