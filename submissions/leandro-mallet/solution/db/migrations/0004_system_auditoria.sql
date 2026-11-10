-- 0004_system_auditoria.sql  [LOTE 1]
-- Auditoria (ARQ-04): antes, depois, usuário, papel, correlation_id, lote e data do negócio de cada escrita.
-- Gravada só pelo gatilho system_auditar (0005). Não aceita UPDATE nem DELETE.
-- lote_id já existe como coluna, com índice; a FK para system_lotes é criada no lote 2.

create table system_auditoria (
  id             bigint generated always as identity primary key,
  tabela         text not null,
  registro_id    text not null,
  operacao       text not null check (operacao in ('insert', 'update')),
  antes          jsonb,                                -- nulo no insert
  depois         jsonb not null,
  usuario_id     bigint not null references config_usuarios (id) on delete restrict,
  papel          text not null,
  correlation_id uuid not null,
  lote_id        bigint,                               -- FK para system_lotes no lote 2
  data_negocio   date not null,                        -- relógio do CRM (modo demonstração)
  criado_em      timestamptz not null default now()
);
create index system_auditoria_usuario_id_criado_em_idx on system_auditoria (usuario_id, criado_em desc);
create index system_auditoria_tabela_registro_idx on system_auditoria (tabela, registro_id, criado_em desc);
create index system_auditoria_correlation_id_idx on system_auditoria (correlation_id);
create index system_auditoria_lote_id_idx on system_auditoria (lote_id);
