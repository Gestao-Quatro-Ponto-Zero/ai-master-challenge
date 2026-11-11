-- 0028_contexto_obrigatorio.sql  [correção de segurança — achado L2-1 da revisão do lote 2]
-- Problema: o papel do app (service_role) conseguia gravar ajustando app.usuario_id e app.correlation_id
-- direto, sem system_iniciar_contexto. A escrita passava pela auditoria, mas o pedido não entrava em
-- system_correlacoes e pulava o limite por usuário, o teto global e a regra de um correlation_id por pedido.
-- Correção:
--   1. Para os papéis do app, toda escrita auditada e todo evento exigem que o correlation_id esteja em
--      system_correlacoes com a transação atual e o mesmo usuário. Senão: GS401.
--   2. O registro em system_correlacoes passa a ser conferido por gatilho: a origem (app ou não), a
--      transação e o horário são preenchidos pelo banco, e os limites (por usuário e global) e a recusa do
--      usuário "sistema" valem mesmo para quem tentar gravar o registro direto na tabela.
-- O papel de carga (system_carga) e o dono continuam com o caminho próprio, sem limites.

-- Pedido registrado nesta transação para este usuário?
create or replace function system_contexto_registrado(p_usuario_id bigint, p_correlation_id uuid) returns boolean
language sql stable set search_path = public as $$
  select exists (select 1 from system_correlacoes
                  where correlation_id = p_correlation_id
                    and usuario_id = p_usuario_id
                    and transacao = txid_current())
$$;

-- 1. Registro do pedido conferido pelo banco --------------------------------------------------------------

create or replace function system_correlacoes_conferir() returns trigger
language plpgsql set search_path = public as $$
declare
  v_janela   interval := make_interval(secs => coalesce(config_inteiro('janela_limite_segundos'), 60));
  v_papel    text;
  v_recentes integer;
  v_global   integer;
begin
  -- mesmo correlation_id já registrado: o "on conflict" decide (mesma transação passa; outra é recusada depois)
  if exists (select 1 from system_correlacoes where correlation_id = new.correlation_id) then
    return new;
  end if;
  new.do_app := system_eh_papel_do_app();       -- origem decidida pelo banco, não por quem grava
  new.transacao := txid_current();
  new.criado_em := now();
  if not new.do_app then
    return new;                                  -- dono e papel de carga: sem limites
  end if;
  select papel into v_papel from config_usuarios where id = new.usuario_id;
  if v_papel = 'sistema' then
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

create trigger system_correlacoes_conferir before insert on system_correlacoes
  for each row execute function system_correlacoes_conferir();

-- 2. Auditoria exige o pedido registrado (substitui a versão de 0022) ----------------------------------------

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
  if system_eh_papel_do_app() then
    if v_papel = 'sistema' then
      raise exception 'O app não pode gravar como o usuário sistema.' using errcode = 'GS403';
    end if;
    if not system_contexto_registrado(v_usuario, v_corr) then
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
  values (tg_table_name, v_depois ->> tg_argv[0], lower(tg_op), v_antes, v_depois, v_usuario, v_papel, v_corr, v_lote,
          system_data_negocio());
  return new;
end $$;

-- 3. Eventos também exigem o pedido registrado, para o app (substitui a versão de 0013) --------------------

create or replace function system_registrar_evento(p_tipo text, p_detalhe jsonb default '{}'::jsonb) returns void
language plpgsql set search_path = public as $$
declare
  v_usuario bigint := nullif(current_setting('app.usuario_id', true), '')::bigint;
  v_corr    uuid   := nullif(current_setting('app.correlation_id', true), '')::uuid;
begin
  if system_eh_papel_do_app() and (v_usuario is null or v_corr is null
                                   or not system_contexto_registrado(v_usuario, v_corr)) then
    raise exception 'Pedido sem registro. Escolha o perfil e tente de novo.' using errcode = 'GS401';
  end if;
  insert into system_eventos (tipo, detalhe, usuario_id, correlation_id)
  values (p_tipo, coalesce(p_detalhe, '{}'::jsonb), v_usuario, v_corr);
end $$;

-- 4. Permissões das funções novas e substituídas ------------------------------------------------------------

do $$
declare
  f text;
begin
  foreach f in array array[
    'system_contexto_registrado(bigint, uuid)',
    'system_correlacoes_conferir()',
    'system_auditar()',
    'system_registrar_evento(text, jsonb)'
  ] loop
    execute format('revoke execute on function %s from public', f);
    if exists (select 1 from pg_roles where rolname = 'anon') then
      execute format('revoke execute on function %s from anon, authenticated', f);
    end if;
    if exists (select 1 from pg_roles where rolname = 'service_role') then
      execute format('grant execute on function %s to service_role', f);
    end if;
    execute format('grant execute on function %s to system_carga', f);
  end loop;
end $$;
