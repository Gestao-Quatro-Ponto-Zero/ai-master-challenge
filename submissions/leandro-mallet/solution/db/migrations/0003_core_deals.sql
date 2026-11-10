-- 0003_core_deals.sql  [LOTE 1]
-- Deals (= leads). Deal sem empresa = conta_nome nula (BD-02). Valores em inteiro de dólar (BD-05).
-- data_abertura = engage_date do dataset (início da negociação); Prospecting fica sem data (P4).
-- contato_id e importacao_id já existem como coluna, com índice; as FKs para core_contatos e
-- system_importacoes são criadas no lote 2, junto com essas tabelas.

create table core_deals (
  opportunity_id       text primary key check (opportunity_id ~ '^[A-Z0-9]{8}$'),
  nome                 text not null check (char_length(btrim(nome)) between 1 and 120),
  vendedor_nome        text not null references core_vendedores (nome) on delete restrict,
  produto_nome         text not null references core_produtos (nome) on delete restrict,
  conta_nome           text references core_contas (nome) on delete restrict,
  contato_id           bigint,                   -- FK para core_contatos no lote 2
  estagio              text not null check (estagio in ('Prospecting', 'Engaging', 'Won', 'Lost')),
  data_abertura        date,
  close_date           date,
  close_value          integer,
  motivo_perda         text check (motivo_perda in ('preco', 'concorrente', 'sem_orcamento', 'sem_resposta', 'cadastro_desfeito', 'outro')),
  motivo_perda_detalhe text check (char_length(motivo_perda_detalhe) <= 280),
  ultimo_contato_em    date,                     -- mantido pelo gatilho de acao_registros (lote 2)
  criado_em            timestamptz,              -- nulo nos deals vindos do dataset
  criado_por           bigint references config_usuarios (id) on delete restrict,
  importacao_id        bigint,                   -- FK para system_importacoes no lote 2
  atualizado_em        timestamptz not null default now(),   -- também é a versão (conflito de edição)
  atualizado_por       bigint references config_usuarios (id) on delete restrict,
  constraint core_deals_engaging_tem_abertura_chk check (estagio <> 'Engaging' or data_abertura is not null),
  constraint core_deals_aberto_sem_fechamento_chk check (estagio not in ('Prospecting', 'Engaging') or (close_date is null and close_value is null)),
  constraint core_deals_fechado_tem_data_chk check (estagio not in ('Won', 'Lost') or close_date is not null),
  constraint core_deals_won_tem_valor_chk check (estagio <> 'Won' or close_value > 0),
  constraint core_deals_lost_valor_zero_chk check (estagio <> 'Lost' or coalesce(close_value, 0) = 0),
  constraint core_deals_datas_em_ordem_chk check (close_date is null or data_abertura is null or close_date >= data_abertura),
  constraint core_deals_motivo_so_em_lost_chk check (motivo_perda is null or estagio = 'Lost')
);
create index core_deals_vendedor_estagio_idx on core_deals (vendedor_nome, estagio);
create index core_deals_produto_nome_idx on core_deals (produto_nome);
create index core_deals_conta_nome_idx on core_deals (conta_nome);
create index core_deals_contato_id_idx on core_deals (contato_id);
create index core_deals_criado_por_idx on core_deals (criado_por);
create index core_deals_importacao_id_idx on core_deals (importacao_id);
create index core_deals_atualizado_por_idx on core_deals (atualizado_por);
create index core_deals_estagio_close_date_idx on core_deals (estagio, close_date);
create index core_deals_data_abertura_idx on core_deals (data_abertura);
create index core_deals_ultimo_contato_em_idx on core_deals (ultimo_contato_em);
