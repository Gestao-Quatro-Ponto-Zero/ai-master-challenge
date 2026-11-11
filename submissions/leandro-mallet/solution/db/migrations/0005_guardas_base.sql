-- 0005_guardas_base.sql  [LOTE 1]
-- Guardas que valem desde o início para as tabelas do lote 1:
--   1. relógio do CRM (data do negócio e dia real);
--   2. contexto de quem escreve (usuário, correlation_id, lote, limite de escritas) e o contexto "sistema" das cargas;
--   3. auditoria por gatilho (antes, depois, usuário, papel, correlation_id, lote, data do negócio) — ARQ-04;
--   4. versão de core_deals (atualizado_em/atualizado_por);
--   5. DELETE e TRUNCATE barrados por gatilho e por revoke; auditoria sem UPDATE — BD-04;
--   6. RLS ligado em todas as tabelas, sem política; só a service role lê, grava e executa — BD-03.
-- O laço do item 5/6 é idempotente: o lote 2 roda o mesmo laço para as tabelas novas.
-- Códigos de erro próprios (o servidor traduz em frase simples):
--   GS400 entrada inválida · GS401 sem usuário/correlation · GS403 papel sem permissão · GS404 não encontrado
--   GS405 apagar proibido · GS409 conflito de versão · GS422 regra de negócio · GS429 limite de escritas

-- 1. Relógio do CRM ---------------------------------------------------------------------------------

create or replace function system_data_negocio() returns date
language sql stable set search_path = public as $$
  select case
           when config_booleano('modo_demonstracao') then (config_texto('data_referencia'))::date
           else (now() at time zone coalesce(config_texto('fuso_horario'), 'UTC'))::date
         end
$$;

create or replace function system_dia_real() returns date
language sql stable set search_path = public as $$
  select (now() at time zone coalesce(config_texto('fuso_horario'), 'UTC'))::date
$$;

-- 2. Contexto de quem escreve ------------------------------------------------------------------------

create or replace function system_iniciar_contexto(
  p_usuario_id     bigint,
  p_correlation_id uuid,
  p_contar_limite  boolean default true,
  p_lote_id        bigint default null
) returns config_usuarios
language plpgsql set search_path = public as $$
declare
  v_usuario  config_usuarios;
  v_recentes integer;
begin
  if p_usuario_id is null or p_correlation_id is null then
    raise exception 'Escolha um perfil antes de alterar dados.' using errcode = 'GS401';
  end if;
  select * into v_usuario from config_usuarios where id = p_usuario_id;
  if not found or not v_usuario.ativo then
    raise exception 'Usuário % não encontrado ou inativo.', p_usuario_id using errcode = 'GS401';
  end if;
  perform set_config('app.usuario_id', p_usuario_id::text, true);
  perform set_config('app.correlation_id', p_correlation_id::text, true);
  perform set_config('app.lote_id', coalesce(p_lote_id::text, ''), true);
  if p_contar_limite then
    select count(*) into v_recentes
      from system_auditoria
     where usuario_id = p_usuario_id
       and lote_id is null
       and criado_em > now() - interval '1 minute';
    if v_recentes >= coalesce(config_inteiro('limite_escritas_por_minuto'), 30) then
      raise exception 'Muitas mudanças seguidas. Espere alguns segundos.' using errcode = 'GS429';
    end if;
  end if;
  return v_usuario;
end $$;

-- Contexto do usuário "sistema", para as cargas (seed do dataset, Python e score). Vale até o fim da transação.
create or replace function system_iniciar_contexto_sistema(p_correlation_id uuid) returns config_usuarios
language sql set search_path = public as $$
  select system_iniciar_contexto((select id from config_usuarios where papel = 'sistema' order by id limit 1),
                                 p_correlation_id, false)
$$;

-- 3. Auditoria -------------------------------------------------------------------------------------

create or replace function system_mascarar_contato(p_registro jsonb) returns jsonb
language sql immutable as $$
  select case
           when p_registro is null then null
           else p_registro
                || jsonb_build_object(
                     'email', case when p_registro ->> 'email' is null then null
                                   else regexp_replace(p_registro ->> 'email', '^(.).*(@.*)$', '\1***\2') end,
                     'telefone', case when p_registro ->> 'telefone' is null then null
                                      else '***' || right(p_registro ->> 'telefone', 2) end)
         end
$$;

create or replace function system_auditar() returns trigger
language plpgsql set search_path = public as $$
declare
  v_usuario bigint := nullif(current_setting('app.usuario_id', true), '')::bigint;
  v_corr    uuid   := nullif(current_setting('app.correlation_id', true), '')::uuid;
  v_lote    bigint := nullif(current_setting('app.lote_id', true), '')::bigint;
  v_papel   text;
  v_antes   jsonb;
  v_depois  jsonb := to_jsonb(new);
begin
  if v_usuario is null or v_corr is null then
    raise exception 'Escrita sem usuário ou sem correlation_id em %.', tg_table_name using errcode = 'GS401';
  end if;
  select papel into v_papel from config_usuarios where id = v_usuario;
  if v_papel is null then
    raise exception 'Usuário % não existe.', v_usuario using errcode = 'GS401';
  end if;
  if tg_op = 'UPDATE' then
    v_antes := to_jsonb(old);
    if v_antes = v_depois then
      return new;                                   -- nada mudou: não grava auditoria
    end if;
  end if;
  if tg_table_name = 'core_contatos' then            -- sem dado pessoal desnecessário na auditoria (ARQ-04)
    v_antes := system_mascarar_contato(v_antes);
    v_depois := system_mascarar_contato(v_depois);
  end if;
  insert into system_auditoria (tabela, registro_id, operacao, antes, depois, usuario_id, papel, correlation_id, lote_id, data_negocio)
  values (tg_table_name, v_depois ->> tg_argv[0], lower(tg_op), v_antes, v_depois, v_usuario, v_papel, v_corr, v_lote,
          system_data_negocio());
  return new;
end $$;

-- 4. Bloqueios e versão ------------------------------------------------------------------------------

create or replace function system_bloquear_delete() returns trigger
language plpgsql as $$
begin
  raise exception 'Apagar dados não é permitido (tabela %). Use a remoção lógica.', tg_table_name using errcode = 'GS405';
end $$;

create or replace function system_bloquear_alteracao() returns trigger
language plpgsql as $$
begin
  raise exception 'Registros de % não podem ser alterados.', tg_table_name using errcode = 'GS405';
end $$;

create or replace function core_marcar_atualizacao() returns trigger
language plpgsql set search_path = public as $$
begin
  -- Mudança só no último contato (feita pelo gatilho de ações) não conta como nova versão do deal.
  if tg_table_name = 'core_deals'
     and (to_jsonb(new) - 'ultimo_contato_em' - 'atualizado_em' - 'atualizado_por')
       = (to_jsonb(old) - 'ultimo_contato_em' - 'atualizado_em' - 'atualizado_por') then
    new.atualizado_em := old.atualizado_em;
    new.atualizado_por := old.atualizado_por;
    return new;
  end if;
  new.atualizado_em := now();
  new.atualizado_por := nullif(current_setting('app.usuario_id', true), '')::bigint;
  return new;
end $$;

create trigger core_deals_marcar_atualizacao before update on core_deals
  for each row execute function core_marcar_atualizacao();

-- Auditoria nas tabelas do lote 1 (tabela e coluna da chave)
create trigger core_escritorios_auditar after insert or update on core_escritorios for each row execute function system_auditar('nome');
create trigger core_managers_auditar after insert or update on core_managers for each row execute function system_auditar('nome');
create trigger core_vendedores_auditar after insert or update on core_vendedores for each row execute function system_auditar('nome');
create trigger core_produtos_auditar after insert or update on core_produtos for each row execute function system_auditar('nome');
create trigger core_contas_auditar after insert or update on core_contas for each row execute function system_auditar('nome');
create trigger core_deals_auditar after insert or update on core_deals for each row execute function system_auditar('opportunity_id');
create trigger config_usuarios_auditar after insert or update on config_usuarios for each row execute function system_auditar('id');
create trigger config_parametros_auditar after insert or update on config_parametros for each row execute function system_auditar('chave');

-- A auditoria não muda depois de gravada
create trigger system_auditoria_bloquear_alteracao before update on system_auditoria
  for each row execute function system_bloquear_alteracao();

-- 5 e 6. DELETE, TRUNCATE e RLS em todas as tabelas com prefixo (idempotente) -------------------------

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

-- Permissões: anon e authenticated sem acesso; a service role lê, insere e altera, mas não apaga.
-- Os papéis existem no Supabase; o bloco ignora papel ausente (útil para validar fora do Supabase).
do $$
declare
  r text;
begin
  execute 'revoke execute on all functions in schema public from public';
  execute 'alter default privileges in schema public revoke execute on functions from public';
  foreach r in array array['anon', 'authenticated'] loop
    if exists (select 1 from pg_roles where rolname = r) then
      execute format('revoke all on all tables in schema public from %I', r);
      execute format('revoke all on all sequences in schema public from %I', r);
      execute format('revoke execute on all functions in schema public from %I', r);
      execute format('alter default privileges in schema public revoke all on tables from %I', r);
      execute format('alter default privileges in schema public revoke execute on functions from %I', r);
    end if;
  end loop;
  if exists (select 1 from pg_roles where rolname = 'service_role') then
    execute 'grant select, insert, update on all tables in schema public to service_role';
    execute 'grant usage, select on all sequences in schema public to service_role';
    execute 'grant execute on all functions in schema public to service_role';
    execute 'revoke delete, truncate on all tables in schema public from service_role';
    execute 'alter default privileges in schema public revoke delete, truncate on tables from service_role';
  end if;
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
