-- 0029_reforco_contexto.sql  [correção de segurança — reforço da 0028]
-- 1. Usuário ativo: system_correlacoes_conferir (pedido do app) e system_auditar carregam a linha inteira de
--    config_usuarios e recusam (GS401) usuário inexistente ou inativo, como já faz system_iniciar_contexto.
-- 2. Inserção só pelas funções: service_role, anon, authenticated e o papel de carga perdem o INSERT em
--    system_correlacoes, system_eventos e system_auditoria. As funções que gravam nelas passam a ser
--    SECURITY DEFINER (rodam como o dono das tabelas), com search_path fixo:
--      system_iniciar_contexto, system_iniciar_contexto_sistema, system_auditar, system_registrar_evento,
--      system_correlacoes_conferir e system_contexto_registrado.
--    Como uma função SECURITY DEFINER roda como o dono, current_user deixa de mostrar quem chamou. Por isso
--    system_eh_papel_do_app passa a olhar também o papel ativo da sessão (SET ROLE), que continua sendo o do
--    app (no Supabase, a API entra como authenticator e assume service_role por SET ROLE).
--    Isso fecha o L2-5 da revisão: nem o app nem a carga forjam linhas de auditoria ou eventos.
-- 3. L2-6: o app só lê as notas. service_role perde INSERT e UPDATE nas 6 tabelas score_* (mantém SELECT);
--    quem grava é a carga do score, pelo papel system_carga.

-- 0. Quem chamou: papel efetivo ou papel ativo da sessão --------------------------------------------------

create or replace function system_eh_papel_do_app() returns boolean
language sql stable as $$
  select current_user in ('anon', 'authenticated', 'service_role')
      or coalesce(current_setting('role', true), 'none') in ('anon', 'authenticated', 'service_role')
$$;

-- 1. Usuário ativo no registro do pedido e na auditoria ---------------------------------------------------

create or replace function system_correlacoes_conferir() returns trigger
language plpgsql set search_path = public, pg_temp as $$
declare
  v_janela   interval := make_interval(secs => coalesce(config_inteiro('janela_limite_segundos'), 60));
  v_usuario  config_usuarios;
  v_recentes integer;
  v_global   integer;
begin
  if exists (select 1 from system_correlacoes where correlation_id = new.correlation_id) then
    return new;                                  -- o "on conflict" decide
  end if;
  new.do_app := system_eh_papel_do_app();
  new.transacao := txid_current();
  new.criado_em := now();
  if not new.do_app then
    return new;                                  -- dono e papel de carga: sem limites
  end if;
  select * into v_usuario from config_usuarios where id = new.usuario_id;
  if not found or not v_usuario.ativo then
    raise exception 'Usuário % não encontrado ou inativo.', new.usuario_id using errcode = 'GS401';
  end if;
  if v_usuario.papel = 'sistema' then
    raise exception 'O app não pode agir como o usuário sistema.' using errcode = 'GS403';
  end if;
  select count(*) into v_recentes from system_correlacoes
   where usuario_id = new.usuario_id and criado_em > now() - v_janela;
  if v_recentes >= coalesce(config_inteiro('limite_escritas_por_minuto'), 30) then
    raise exception 'Muitas mudanças seguidas. Espere alguns segundos.' using errcode = 'GS429';
  end if;
  select count(*) into v_global from system_correlacoes
   where do_app and criado_em > now() - v_janela;
  if v_global >= coalesce(config_inteiro('limite_global_escritas'), 300) then
    raise exception 'O sistema está recebendo muitas mudanças agora. Tente de novo em alguns segundos.' using errcode = 'GS429';
  end if;
  return new;
end $$;

create or replace function system_auditar() returns trigger
language plpgsql set search_path = public, pg_temp as $$
declare
  v_usuario_id bigint := nullif(current_setting('app.usuario_id', true), '')::bigint;
  v_corr       uuid   := nullif(current_setting('app.correlation_id', true), '')::uuid;
  v_lote       bigint := nullif(current_setting('app.lote_id', true), '')::bigint;
  v_usuario    config_usuarios;
  v_antes      jsonb;
  v_depois     jsonb := to_jsonb(new);
begin
  if v_usuario_id is null or v_corr is null then
    raise exception 'Escrita sem usuário ou sem correlation_id em %.', tg_table_name using errcode = 'GS401';
  end if;
  select * into v_usuario from config_usuarios where id = v_usuario_id;
  if not found or not v_usuario.ativo then
    raise exception 'Usuário % não encontrado ou inativo.', v_usuario_id using errcode = 'GS401';
  end if;
  if system_eh_papel_do_app() then
    if v_usuario.papel = 'sistema' then
      raise exception 'O app não pode gravar como o usuário sistema.' using errcode = 'GS403';
    end if;
    if not system_contexto_registrado(v_usuario_id, v_corr) then
      raise exception 'Pedido sem registro. Escolha o perfil e tente de novo.' using errcode = 'GS401',
        hint = 'Toda escrita do app começa com system_iniciar_contexto.';
    end if;
  end if;
  if tg_op = 'UPDATE' then
    v_antes := to_jsonb(old);
    if v_antes = v_depois then
      return new;
    end if;
  end if;
  if tg_table_name = 'core_contatos' then
    v_antes := system_mascarar_contato(v_antes);
    v_depois := system_mascarar_contato(v_depois);
  end if;
  insert into system_auditoria (tabela, registro_id, operacao, antes, depois, usuario_id, papel, correlation_id, lote_id, data_negocio)
  values (tg_table_name, v_depois ->> tg_argv[0], lower(tg_op), v_antes, v_depois, v_usuario_id, v_usuario.papel, v_corr, v_lote,
          system_data_negocio());
  return new;
end $$;

-- 2. Funções que gravam nas três tabelas: SECURITY DEFINER com search_path fixo ---------------------------

alter function system_iniciar_contexto(bigint, uuid, boolean, bigint) security definer set search_path = public, pg_temp;
alter function system_iniciar_contexto_sistema(uuid)                  security definer set search_path = public, pg_temp;
alter function system_auditar()                                        security definer set search_path = public, pg_temp;
alter function system_registrar_evento(text, jsonb)                    security definer set search_path = public, pg_temp;
alter function system_correlacoes_conferir()                           security definer set search_path = public, pg_temp;
alter function system_contexto_registrado(bigint, uuid)                security definer set search_path = public, pg_temp;

-- 3. Ninguém além do dono insere direto nas três tabelas -------------------------------------------------

do $$
declare
  r text;
begin
  foreach r in array array['service_role', 'anon', 'authenticated', 'system_carga'] loop
    if exists (select 1 from pg_roles where rolname = r) then
      execute format('revoke insert, update on table system_correlacoes, system_eventos, system_auditoria from %I', r);
    end if;
  end loop;
  execute 'revoke insert, update on table system_correlacoes, system_eventos, system_auditoria from public';

  -- L2-6: o app só LÊ as notas; quem grava score_* é a carga do score (system_carga)
  if exists (select 1 from pg_roles where rolname = 'service_role') then
    execute 'revoke insert, update on table score_execucoes, score_deals, score_componentes, score_motivos,
             score_fit_vendedores, score_padroes_conta from service_role';
    execute 'grant select on table score_execucoes, score_deals, score_componentes, score_motivos,
             score_fit_vendedores, score_padroes_conta to service_role';
  end if;
  execute 'grant select, insert, update on table score_execucoes, score_deals, score_componentes, score_motivos,
           score_fit_vendedores, score_padroes_conta to system_carga';
end $$;

-- 4. Execução: SECURITY DEFINER não pode ficar aberta ao public ------------------------------------------

do $$
declare
  f text;
begin
  foreach f in array array[
    'system_eh_papel_do_app()',
    'system_iniciar_contexto(bigint, uuid, boolean, bigint)',
    'system_auditar()',
    'system_registrar_evento(text, jsonb)',
    'system_correlacoes_conferir()',
    'system_contexto_registrado(bigint, uuid)',
    'system_iniciar_contexto_sistema(uuid)'
  ] loop
    execute format('revoke execute on function %s from public', f);
    if exists (select 1 from pg_roles where rolname = 'anon') then
      execute format('revoke execute on function %s from anon, authenticated', f);
    end if;
    execute format('grant execute on function %s to system_carga', f);
  end loop;
  if exists (select 1 from pg_roles where rolname = 'service_role') then
    -- o app executa tudo, menos o contexto "sistema" (só a carga)
    execute 'grant execute on function system_eh_papel_do_app() to service_role';
    execute 'grant execute on function system_iniciar_contexto(bigint, uuid, boolean, bigint) to service_role';
    execute 'grant execute on function system_auditar() to service_role';
    execute 'grant execute on function system_registrar_evento(text, jsonb) to service_role';
    execute 'grant execute on function system_correlacoes_conferir() to service_role';
    execute 'grant execute on function system_contexto_registrado(bigint, uuid) to service_role';
    execute 'revoke execute on function system_iniciar_contexto_sistema(uuid) from service_role';
  end if;
end $$;
