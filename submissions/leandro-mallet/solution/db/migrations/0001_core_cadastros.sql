-- 0001_core_cadastros.sql  [LOTE 1]
-- Cadastro do CRM (core_): escritórios, managers, vendedores, produtos e contas (accounts).
-- Dinheiro em inteiro de dólar (BD-05). Toda chave estrangeira com índice e ON DELETE RESTRICT (BD-02).

create table core_escritorios (
  nome text primary key check (char_length(btrim(nome)) between 1 and 60)
);

create table core_managers (
  nome            text primary key check (char_length(btrim(nome)) between 1 and 120),
  escritorio_nome text not null references core_escritorios (nome) on delete restrict
);
create index core_managers_escritorio_nome_idx on core_managers (escritorio_nome);

create table core_vendedores (
  nome         text primary key check (char_length(btrim(nome)) between 1 and 120),
  manager_nome text not null references core_managers (nome) on delete restrict
);
create index core_vendedores_manager_nome_idx on core_vendedores (manager_nome);

create table core_produtos (
  nome  text primary key check (char_length(btrim(nome)) between 1 and 60),
  serie text not null check (char_length(btrim(serie)) between 1 and 30),
  preco integer not null check (preco > 0)                         -- preço de tabela, inteiro em dólar
);

create table core_contas (
  nome             text primary key check (char_length(btrim(nome)) between 1 and 120),
  setor            text,
  ano_fundacao     integer check (ano_fundacao between 1800 and 2100),
  receita_milhoes  numeric(14, 2) check (receita_milhoes >= 0),   -- medida do dataset, não dinheiro do CRM
  funcionarios     integer check (funcionarios >= 0),
  porte            text check (porte in ('pequena', 'media', 'grande')),  -- tercis de funcionários (P3)
  pais             text,
  empresa_mae_nome text references core_contas (nome) on delete restrict  -- nula para empresa independente
);
create index core_contas_empresa_mae_nome_idx on core_contas (empresa_mae_nome);
create index core_contas_setor_porte_idx on core_contas (setor, porte);
