-- 0012_guardas.sql  [LOTE 2]
-- Guardas das tabelas do lote 2 (as funções de auditoria, bloqueio, relógio e versão estão em 0005):
--   1. integridade: contato da mesma empresa, limite de tags por deal, último contato mantido pelas ações;
--   2. versão de core_contatos;
--   3. auditoria por gatilho nas tabelas novas; eventos sem UPDATE;
--   4. DELETE, TRUNCATE e RLS nas tabelas novas (mesmo laço idempotente de 0005) e revokes.

-- 1. Integridade ------------------------------------------------------------------------------------

create or replace function core_validar_contato() returns trigger
language plpgsql set search_path = public as $$
declare
  v_conta  text;
  v_inativo timestamptz;
begin
  if new.contato_id is null then
    return new;
  end if;
  select conta_nome, inativo_em into v_conta, v_inativo from core_contatos where id = new.contato_id;
  if v_inativo is not null then
    raise exception 'Este contato está inativo.' using errcode = 'GS422';
  end if;
  if v_conta is not null and v_conta is distinct from new.conta_nome then
    raise exception 'O contato é de outra empresa.' using errcode = 'GS422';
  end if;
  return new;
end $$;

create or replace function acao_limitar_tags() returns trigger
language plpgsql set search_path = public as $$
declare
  v_ativas integer;
begin
  if new.removida_em is not null then
    return new;
  end if;
  select count(*) into v_ativas
    from acao_deal_tags
   where opportunity_id = new.opportunity_id and removida_em is null and id <> new.id;
  if v_ativas >= coalesce(config_inteiro('max_tags_por_deal'), 10) then
    raise exception 'Este deal já tem o máximo de tags.' using errcode = 'GS422';
  end if;
  return new;
end $$;

create or replace function acao_atualizar_ultimo_contato() returns trigger
language plpgsql set search_path = public as $$
declare
  v_ultimo date;
begin
  select max(data_negocio) into v_ultimo
    from acao_registros
   where opportunity_id = new.opportunity_id
     and desfeita_em is null
     and acao = any (config_lista('acoes_contato'));
  update core_deals
     set ultimo_contato_em = v_ultimo
   where opportunity_id = new.opportunity_id
     and ultimo_contato_em is distinct from v_ultimo;
  return new;
end $$;

create trigger core_deals_validar_contato before insert or update of contato_id, conta_nome on core_deals
  for each row execute function core_validar_contato();
create trigger acao_deal_tags_limitar before insert or update on acao_deal_tags
  for each row execute function acao_limitar_tags();
create trigger acao_registros_ultimo_contato after insert or update on acao_registros
  for each row execute function acao_atualizar_ultimo_contato();

-- 2. Versão de core_contatos (a função está em 0005) ------------------------------------------------

create trigger core_contatos_marcar_atualizacao before update on core_contatos
  for each row execute function core_marcar_atualizacao();

-- 3. Auditoria nas tabelas novas. Ficam fora: score_* (carga do Python, registrada em system_eventos)
--    e os eventos. ---------------------------------------------------------------------------------

create trigger core_contatos_auditar after insert or update on core_contatos for each row execute function system_auditar('id');
create trigger config_tags_auditar after insert or update on config_tags for each row execute function system_auditar('id');
create trigger acao_registros_auditar after insert or update on acao_registros for each row execute function system_auditar('id');
create trigger acao_comentarios_auditar after insert or update on acao_comentarios for each row execute function system_auditar('id');
create trigger acao_deal_tags_auditar after insert or update on acao_deal_tags for each row execute function system_auditar('id');
create trigger acao_prioridades_auditar after insert or update on acao_prioridades for each row execute function system_auditar('id');
create trigger acao_reatribuicoes_auditar after insert or update on acao_reatribuicoes for each row execute function system_auditar('id');
create trigger system_lotes_auditar after insert or update on system_lotes for each row execute function system_auditar('id');
create trigger system_importacoes_auditar after insert or update on system_importacoes for each row execute function system_auditar('id');
create trigger system_roteamentos_auditar after insert or update on system_roteamentos for each row execute function system_auditar('id');

create trigger system_eventos_bloquear_alteracao before update on system_eventos
  for each row execute function system_bloquear_alteracao();

-- 4. DELETE, TRUNCATE e RLS em todas as tabelas com prefixo (idempotente; cobre as novas) --------------

do $$
declare
  t text;
begin
  for t in
    select tablename from pg_tables
     where schemaname = 'public' and tablename ~ '^(core|config|score|acao|system)_'
  loop
    if not exists (select 1 from pg_trigger where tgrelid = format('%I', t)::regclass and tgname = t || '_bloquear_delete') then
      execute format('create trigger %I before delete on %I for each row execute function system_bloquear_delete()',
                     t || '_bloquear_delete', t);
    end if;
    if not exists (select 1 from pg_trigger where tgrelid = format('%I', t)::regclass and tgname = t || '_bloquear_truncate') then
      execute format('create trigger %I before truncate on %I for each statement execute function system_bloquear_delete()',
                     t || '_bloquear_truncate', t);
    end if;
    execute format('alter table %I enable row level security', t);
  end loop;
end $$;

do $$
declare
  r text;
begin
  foreach r in array array['anon', 'authenticated', 'service_role'] loop
    if exists (select 1 from pg_roles where rolname = r) then
      execute format('revoke delete, truncate on all tables in schema public from %I', r);
    end if;
  end loop;
  foreach r in array array['anon', 'authenticated'] loop
    if exists (select 1 from pg_roles where rolname = r) then
      execute format('revoke all on all tables in schema public from %I', r);
      execute format('revoke all on all sequences in schema public from %I', r);
    end if;
  end loop;
end $$;

-- Conferência: toda tabela com prefixo tem RLS e os dois gatilhos de bloqueio
do $$
declare
  v_faltando text;
begin
  select string_agg(c.relname, ', ') into v_faltando
    from pg_class c
    join pg_namespace n on n.oid = c.relnamespace and n.nspname = 'public'
   where c.relkind = 'r'
     and c.relname ~ '^(core|config|score|acao|system)_'
     and (not c.relrowsecurity
          or not exists (select 1 from pg_trigger g where g.tgrelid = c.oid and g.tgname = c.relname || '_bloquear_delete')
          or not exists (select 1 from pg_trigger g where g.tgrelid = c.oid and g.tgname = c.relname || '_bloquear_truncate'));
  if v_faltando is not null then
    raise exception 'Tabelas sem RLS ou sem bloqueio de DELETE/TRUNCATE: %', v_faltando;
  end if;
end $$;
