-- 0025_permissoes_e_guardas.sql  [LOTE 2]
-- Fecha as proteções das tabelas e funções criadas em 0022–0024 e define o papel de carga
-- (a auditoria de config_tipos_atividade e system_penalidades é ligada nos próprios arquivos;
--  system_correlacoes é o próprio registro dos pedidos e não aceita UPDATE):
--   * DELETE, TRUNCATE e RLS em todas as tabelas com prefixo (laço idempotente);
--   * RLS: nenhuma política para anon, authenticated ou service_role. O service_role passa pelo RLS por ser
--     do Supabase (bypassrls). O papel de carga recebe uma política própria, só para ele;
--   * funções: anon e authenticated sem execução; o service_role executa as do app, mas NÃO as de carga
--     (system_iniciar_contexto_sistema, score_ativar_execucao, config_gerar_usuarios, core_repassar_deal);
--   * ninguém apaga: revoke de DELETE e TRUNCATE para o app e para a carga.

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
    -- política só para o papel de carga (cargas do dataset e do score)
    if not exists (select 1 from pg_policies where schemaname = 'public' and tablename = t
                    and policyname = 'system_carga_acesso') then
      execute format('create policy system_carga_acesso on %I to system_carga using (true) with check (true)', t);
    end if;
  end loop;
end $$;

do $$
declare
  r text;
begin
  -- carga: lê, insere e altera; executa tudo; não apaga
  execute 'grant select, insert, update on all tables in schema public to system_carga';
  execute 'grant usage, select on all sequences in schema public to system_carga';
  execute 'grant execute on all functions in schema public to system_carga';
  execute 'revoke delete, truncate on all tables in schema public from system_carga';

  execute 'revoke execute on all functions in schema public from public';
  foreach r in array array['anon', 'authenticated'] loop
    if exists (select 1 from pg_roles where rolname = r) then
      execute format('revoke all on all tables in schema public from %I', r);
      execute format('revoke all on all sequences in schema public from %I', r);
      execute format('revoke execute on all functions in schema public from %I', r);
    end if;
  end loop;
  if exists (select 1 from pg_roles where rolname = 'service_role') then
    execute 'grant select, insert, update on all tables in schema public to service_role';
    execute 'grant usage, select on all sequences in schema public to service_role';
    execute 'grant execute on all functions in schema public to service_role';
    execute 'revoke delete, truncate on all tables in schema public from service_role';
    -- funções só da carga: o app não age como "sistema"
    execute 'revoke execute on function system_iniciar_contexto_sistema(uuid) from service_role';
    execute 'revoke execute on function score_ativar_execucao(uuid, bigint) from service_role';
    execute 'revoke execute on function config_gerar_usuarios(uuid) from service_role';
    execute 'revoke execute on function core_repassar_deal(uuid, text, text, text, bigint, smallint, smallint, smallint, text) from service_role';
  end if;
end $$;

-- Conferência: toda tabela com prefixo tem RLS, os dois gatilhos de bloqueio e nenhuma política fora da carga
do $$
declare
  v_faltando text;
  v_politica text;
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
  select string_agg(tablename || '.' || policyname, ', ') into v_politica
    from pg_policies where schemaname = 'public' and roles <> array['system_carga']::name[];
  if v_politica is not null then
    raise exception 'Política de RLS fora do papel de carga: %', v_politica;
  end if;
end $$;
