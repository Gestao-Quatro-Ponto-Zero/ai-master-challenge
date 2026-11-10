-- 0009_score.sql  [LOTE 2]
-- Estrutura do score (score_): execuções, nota por deal, componentes, motivos, FIT do vendedor por cohort
-- (base do roteamento) e padrão de compra por conta.
-- Regra decidida (decisão 33): NOTA = 0,70 × FIT + 0,30 × HEAT + BONUS, com BONUS de 0 a 20 e nota de 0 a 120.
-- A fórmula exata fica no Python (não no SQL): aqui só a estrutura e os limites.
-- Os pesos usados em cada execução ficam em score_execucoes.pesos.

create table score_execucoes (
  id             bigint generated always as identity primary key,
  reference_date date not null,
  gerado_em      timestamptz not null,
  versao         text not null check (char_length(versao) between 1 and 40),   -- versão das regras do score
  pesos          jsonb not null default '{"fit": 0.70, "heat": 0.30, "bonus_max": 20}'::jsonb,
  parametros     jsonb not null default '{}'::jsonb,                           -- janelas, mínimos e cortes usados
  arquivo_sha256 text not null unique check (arquivo_sha256 ~ '^[0-9a-f]{64}$'),
  observacao     text
);

create table score_deals (
  execucao_id      bigint not null references score_execucoes (id) on delete restrict,
  opportunity_id   text not null references core_deals (opportunity_id) on delete restrict,
  vendedor_nome    text not null references core_vendedores (nome) on delete restrict,  -- dono na hora da nota (o FIT é dele)
  cohort           text,
  fit              smallint check (fit between 0 and 100),
  heat             smallint check (heat between 0 and 100),
  bonus            smallint not null default 0 check (bonus between 0 and 20),       -- padrão de compra da conta
  score            smallint not null check (score between 0 and 120),
  acao_sugerida    text not null check (acao_sugerida in ('focar', 'requalificar', 'desistir')),
  dias_no_pipeline integer check (dias_no_pipeline >= 0),
  valor_esperado   integer not null check (valor_esperado >= 0),
  marcadores       text[] not null default '{}'::text[],
  primary key (execucao_id, opportunity_id)
);
create index score_deals_execucao_score_idx on score_deals (execucao_id, score desc);
create index score_deals_opportunity_id_idx on score_deals (opportunity_id);
create index score_deals_vendedor_nome_idx on score_deals (vendedor_nome);

create table score_componentes (
  execucao_id    bigint not null,
  opportunity_id text not null,
  grupo          text not null check (grupo in ('fit', 'heat', 'bonus')),
  componente     text not null check (char_length(componente) between 1 and 60),
  pontos         numeric(6, 2) not null,
  maximo         numeric(6, 2),
  primary key (execucao_id, opportunity_id, grupo, componente),
  foreign key (execucao_id, opportunity_id) references score_deals (execucao_id, opportunity_id) on delete restrict
);

create table score_motivos (
  execucao_id    bigint not null,
  opportunity_id text not null,
  ordem          smallint not null check (ordem between 1 and 10),
  grupo          text check (grupo in ('fit', 'heat', 'bonus')),
  texto          text not null check (char_length(texto) between 1 and 280),
  primary key (execucao_id, opportunity_id, ordem),
  foreign key (execucao_id, opportunity_id) references score_deals (execucao_id, opportunity_id) on delete restrict
);

-- FIT do vendedor por cohort: taxa de ganho em média móvel (janela definida pelo Python, ex.: 3 meses)
create table score_fit_vendedores (
  execucao_id      bigint not null references score_execucoes (id) on delete restrict,
  vendedor_nome    text not null references core_vendedores (nome) on delete restrict,
  cohort           text not null check (char_length(cohort) between 1 and 200),
  produto_nome     text references core_produtos (nome) on delete restrict,
  taxa_media_movel numeric(6, 4) check (taxa_media_movel between 0 and 1),
  casos            integer not null check (casos >= 0),
  fit              smallint not null check (fit between 0 and 100),
  janela_inicio    date,
  janela_fim       date,
  primary key (execucao_id, vendedor_nome, cohort)
);
create index score_fit_vendedores_roteamento_idx on score_fit_vendedores (execucao_id, cohort, fit desc);
create index score_fit_vendedores_vendedor_nome_idx on score_fit_vendedores (vendedor_nome);
create index score_fit_vendedores_produto_nome_idx on score_fit_vendedores (produto_nome);

-- Padrão de compra por conta, recalculado a cada execução (proposta: todo domingo).
-- Base do BONUS e da aba "Contas" da tela Leads. O cálculo fica no Python.
create table score_padroes_conta (
  execucao_id             bigint not null references score_execucoes (id) on delete restrict,
  conta_nome              text not null references core_contas (nome) on delete restrict,
  compras_ganhas          integer not null check (compras_ganhas >= 0),          -- tamanho do histórico: deals ganhos
  receita_ganha           integer not null check (receita_ganha >= 0),           -- soma de close_value dos ganhos
  intervalo_tipico_dias   integer check (intervalo_tipico_dias > 0),             -- intervalo típico entre compras
  mes_habitual            smallint check (mes_habitual between 1 and 12),        -- mês em que a conta costuma comprar
  ultima_compra           date,
  proxima_compra_esperada date,
  na_janela               boolean not null default false,                        -- a data de referência está na janela esperada
  bonus                   smallint not null default 0 check (bonus between 0 and 20),
  explicacao              text check (char_length(explicacao) <= 400),           -- frase simples para a tela
  primary key (execucao_id, conta_nome)
);
create index score_padroes_conta_conta_nome_idx on score_padroes_conta (conta_nome);
create index score_padroes_conta_janela_idx on score_padroes_conta (execucao_id, na_janela, bonus desc);
