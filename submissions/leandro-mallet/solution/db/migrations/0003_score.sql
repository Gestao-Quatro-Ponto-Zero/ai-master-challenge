-- 0003_score: estrutura das notas (gravadas pelo Python, uma execução por rodada).
-- SCORE = 0,70 x FIT + 0,30 x HEAT. Os pesos ficam em score_execucoes.pesos; a fórmula de FIT e HEAT
-- é da sessão do score e NÃO está cravada aqui. Este arquivo só guarda o resultado e a explicação.

create table score_execucoes (
  id             bigint generated always as identity primary key,
  reference_date date not null,
  gerado_em      timestamptz not null default now(),
  versao         text not null,
  pesos          jsonb not null,
  parametros     jsonb not null default '{}',
  origem         text not null check (origem in ('arquivo', 'banco')),
  arquivo_sha256 text unique,
  notas          integer not null default 0 check (notas >= 0),
  criado_por     bigint not null references config_usuarios (id) on delete restrict
);
create index score_execucoes_criado_por_idx on score_execucoes (criado_por);
comment on table score_execucoes is 'Uma rodada do score. pesos = {"fit":0.70,"heat":0.30} na proposta atual. A ativa fica em config_parametros.execucao_ativa.';

create table score_deals (
  execucao_id      bigint not null references score_execucoes (id) on delete restrict,
  opportunity_id   text not null references core_deals (opportunity_id) on delete restrict,
  vendedor_nome    text not null references core_vendedores (nome) on delete restrict,
  score            integer not null check (score between 0 and 100),
  fit              integer check (fit between 0 and 100),
  heat             integer check (heat between 0 and 100),
  acao_sugerida    text not null check (acao_sugerida in ('focar', 'requalificar', 'desistir')),
  dias_no_pipeline integer,
  valor_esperado   integer not null check (valor_esperado >= 0),
  marcadores       text[] not null default '{}',
  primary key (execucao_id, opportunity_id)
);
create index score_deals_opportunity_id_idx on score_deals (opportunity_id);
create index score_deals_vendedor_nome_idx on score_deals (vendedor_nome);
create index score_deals_execucao_score_idx on score_deals (execucao_id, score desc);
comment on table score_deals is 'Nota por deal aberto numa execução. vendedor_nome = dono na hora da nota (o FIT é por vendedor). fit e heat nulos = componente sem dado.';

create table score_componentes (
  execucao_id    bigint not null,
  opportunity_id text not null,
  componente     text not null check (componente ~ '^[a-z0-9_]+$'),
  grupo          text not null check (grupo in ('fit', 'heat', 'outro')),
  rotulo         text not null,
  pontos         numeric(6, 2) not null,
  maximo         numeric(6, 2) not null check (maximo > 0),
  ordem          smallint not null default 0,
  primary key (execucao_id, opportunity_id, componente),
  constraint score_componentes_deal_fk foreign key (execucao_id, opportunity_id)
    references score_deals (execucao_id, opportunity_id) on delete restrict
);
comment on table score_componentes is 'Partes da nota para o modal ("X de Y pontos"). Nomes vêm da decisão do score.';

create table score_motivos (
  execucao_id    bigint not null,
  opportunity_id text not null,
  ordem          smallint not null,
  texto          text not null check (char_length(texto) between 1 and 280),
  componente     text,
  primary key (execucao_id, opportunity_id, ordem),
  constraint score_motivos_deal_fk foreign key (execucao_id, opportunity_id)
    references score_deals (execucao_id, opportunity_id) on delete restrict
);
comment on table score_motivos is 'Motivos em frase simples, na ordem de exibição.';

create table score_vendedor_cohorts (
  execucao_id    bigint not null references score_execucoes (id) on delete restrict,
  vendedor_nome  text not null references core_vendedores (nome) on delete restrict,
  dimensao       text not null check (dimensao in ('produto', 'serie', 'setor', 'porte', 'receita', 'empresa', 'sede', 'tempo_venda')),
  valor          text not null,
  janela_inicio  date not null,
  janela_fim     date not null,
  n              integer not null check (n >= 0),
  ganhos         integer not null check (ganhos between 0 and n),
  taxa           numeric(5, 4) check (taxa between 0 and 1),
  taxa_encolhida numeric(5, 4) check (taxa_encolhida between 0 and 1),
  primary key (execucao_id, vendedor_nome, dimensao, valor),
  constraint score_vendedor_cohorts_janela_ck check (janela_fim >= janela_inicio)
);
create index score_vendedor_cohorts_vendedor_nome_idx on score_vendedor_cohorts (vendedor_nome);
create index score_vendedor_cohorts_rota_idx on score_vendedor_cohorts (execucao_id, dimensao, valor, taxa_encolhida desc);
comment on table score_vendedor_cohorts is 'Base do FIT e do roteamento: taxa de ganho do vendedor por cohort em média móvel de 3 meses, com encolhimento. Calculada pelo Python.';
