-- 0027_limite_exato.sql  [correção de segurança — ajuste da 0026]
-- A 0026 foi aplicada com as comparações ">" contando também o pedido atual. Este arquivo torna os tetos
-- exatos: as contagens consideram só os pedidos ANTERIORES da janela e usam ">=". Resultado: no máximo
-- 30 pedidos por usuário e 300 no total do app por janela (o seguinte é recusado com GS429).
--
-- IMPORTANTE: o limite por endereço de rede (IP) nas rotas do app é OBRIGATÓRIO e vem antes do banco.
-- O teto global aqui é rede de segurança: protege o banco, mas, se o limite por IP faltar, uma só origem
-- pode esgotá-lo e travar as escritas de todos até a janela passar. O limite por usuário só organiza o uso.
-- O papel de carga (system_carga) continua fora dos dois limites.

create or replace function system_iniciar_contexto(
  p_usuario_id     bigint,
  p_correlation_id uuid,
  p_contar_limite  boolean default true,
  p_lote_id        bigint default null
) returns config_usuarios
language plpgsql set search_path = public as $$
declare
  v_usuario  config_usuarios;
  v_app      boolean := system_eh_papel_do_app();
  v_registro system_correlacoes;
  v_janela   interval := make_interval(secs => coalesce(config_inteiro('janela_limite_segundos'), 60));
  v_recentes integer;
  v_global   integer;
begin
  if p_usuario_id is null or p_correlation_id is null then
    raise exception 'Escolha um perfil antes de alterar dados.' using errcode = 'GS401';
  end if;
  select * into v_usuario from config_usuarios where id = p_usuario_id;
  if not found or not v_usuario.ativo then
    raise exception 'Usuário % não encontrado ou inativo.', p_usuario_id using errcode = 'GS401';
  end if;
  if v_usuario.papel = 'sistema' and v_app then
    raise exception 'O app não pode agir como o usuário sistema.' using errcode = 'GS403';
  end if;

  -- correlation_id: um por transação; reuso em outra transação é recusado
  insert into system_correlacoes (correlation_id, usuario_id, transacao, do_app)
  values (p_correlation_id, p_usuario_id, txid_current(), v_app)
  on conflict (correlation_id) do nothing;
  select * into v_registro from system_correlacoes where correlation_id = p_correlation_id;
  if v_registro.transacao <> txid_current() or v_registro.usuario_id <> p_usuario_id then
    raise exception 'Código do pedido já usado. Gere um novo correlation_id no servidor.' using errcode = 'GS400';
  end if;

  perform set_config('app.usuario_id', p_usuario_id::text, true);
  perform set_config('app.correlation_id', p_correlation_id::text, true);
  perform set_config('app.lote_id', coalesce(p_lote_id::text, ''), true);

  -- limites do app, contados pelo banco: por usuário (organiza) e global (protege). A carga fica fora.
  -- Contam os pedidos ANTERIORES da janela (sem o atual): com ">=", o teto é exato (30 passam, o 31º não).
  if v_app then
    select count(*) into v_recentes
      from system_correlacoes
     where usuario_id = p_usuario_id and criado_em > now() - v_janela
       and correlation_id <> p_correlation_id;
    if v_recentes >= coalesce(config_inteiro('limite_escritas_por_minuto'), 30) then
      raise exception 'Muitas mudanças seguidas. Espere alguns segundos.' using errcode = 'GS429';
    end if;
    select count(*) into v_global
      from system_correlacoes
     where do_app and criado_em > now() - v_janela
       and correlation_id <> p_correlation_id;
    if v_global >= coalesce(config_inteiro('limite_global_escritas'), 300) then
      raise exception 'O sistema está recebendo muitas mudanças agora. Tente de novo em alguns segundos.' using errcode = 'GS429';
    end if;
  end if;
  return v_usuario;
end $$;

-- Permissões da função substituída (create or replace mantém as anteriores; reforço explícito)
do $$
begin
  execute 'revoke execute on function system_iniciar_contexto(bigint, uuid, boolean, bigint) from public';
  if exists (select 1 from pg_roles where rolname = 'anon') then
    execute 'revoke execute on function system_iniciar_contexto(bigint, uuid, boolean, bigint) from anon, authenticated';
  end if;
  if exists (select 1 from pg_roles where rolname = 'service_role') then
    execute 'grant execute on function system_iniciar_contexto(bigint, uuid, boolean, bigint) to service_role';
  end if;
  execute 'grant execute on function system_iniciar_contexto(bigint, uuid, boolean, bigint) to system_carga';
end $$;
