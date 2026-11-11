-- 0022_seguranca.sql  [LOTE 2 — correção de segurança]
-- Corrige o achado da revisão: sem login, o app poderia variar ou repetir o correlation_id para fugir do
-- limite de escritas e poderia agir como o usuário "sistema".
--   1. Papel de banco system_carga, separado do papel do app (service_role). Só ele age como "sistema"
--      (cargas do dataset e do score). O app não executa system_iniciar_contexto_sistema e não pode
--      escolher o usuário "sistema"; a auditoria também recusa "sistema" vindo dos papéis do app.
--   2. Todo correlation_id fica registrado em system_correlacoes com a transação em que foi usado.
--      Reaproveitar um correlation_id em outra transação é recusado (GS400). O servidor gera o id
--      (crypto.randomUUID na rota) e nunca aceita o do cliente.
--   3. Limite de escritas contado pelo banco: pedidos (transações) por usuário na janela, lidos de
--      system_correlacoes. Vale sempre para os papéis do app; só papéis confiáveis (dono e carga) ficam fora.
-- Limitação que continua (documentada no README): sem login, qualquer pessoa pode escolher qualquer
-- usuário da tela, inclusive o admin. A auditoria mostra qual usuário foi escolhido em cada escrita.

-- 1. Papel de carga ----------------------------------------------------------------------------------

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'system_carga') then
    create role system_carga nologin noinherit;
  end if;
  -- quem roda as migrations (o dono do schema) pode assumir o papel de carga: set role system_carga
  execute format('grant system_carga to %I', current_user);
end $$;

grant usage on schema public to system_carga;

-- 2. Registro dos correlation_id --------------------------------------------------------------------

create table system_correlacoes (
  correlation_id uuid primary key,
  usuario_id     bigint not null references config_usuarios (id) on delete restrict,
  transacao      bigint not null,                      -- txid_current() da transação que usou o id
  criado_em      timestamptz not null default now()
);
create index system_correlacoes_usuario_criado_idx on system_correlacoes (usuario_id, criado_em desc);

create trigger system_correlacoes_bloquear_alteracao before update on system_correlacoes
  for each row execute function system_bloquear_alteracao();

-- 3. Contexto de quem escreve (substitui a versão de 0005) --------------------------------------------

create or replace function system_eh_papel_do_app() returns boolean
language sql stable as $$
  select current_user in ('anon', 'authenticated', 'service_role')
$$;

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
  v_recentes integer;
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
  insert into system_correlacoes (correlation_id, usuario_id, transacao)
  values (p_correlation_id, p_usuario_id, txid_current())
  on conflict (correlation_id) do nothing;
  select * into v_registro from system_correlacoes where correlation_id = p_correlation_id;
  if v_registro.transacao <> txid_current() or v_registro.usuario_id <> p_usuario_id then
    raise exception 'Código do pedido já usado. Gere um novo correlation_id no servidor.' using errcode = 'GS400';
  end if;

  perform set_config('app.usuario_id', p_usuario_id::text, true);
  perform set_config('app.correlation_id', p_correlation_id::text, true);
  perform set_config('app.lote_id', coalesce(p_lote_id::text, ''), true);

  -- limite: pedidos do usuário na janela, contados pelo banco. O app não pode desligar a contagem.
  if v_app or p_contar_limite then
    select count(*) into v_recentes
      from system_correlacoes
     where usuario_id = p_usuario_id
       and criado_em > now() - make_interval(secs => coalesce(config_inteiro('janela_limite_segundos'), 60));
    if v_app and v_recentes > coalesce(config_inteiro('limite_escritas_por_minuto'), 30) then
      raise exception 'Muitas mudanças seguidas. Espere alguns segundos.' using errcode = 'GS429';
    end if;
  end if;
  return v_usuario;
end $$;

-- Contexto "sistema": só o papel de carga (e o dono, nas migrations)
create or replace function system_iniciar_contexto_sistema(p_correlation_id uuid) returns config_usuarios
language plpgsql set search_path = public as $$
begin
  if system_eh_papel_do_app() then
    raise exception 'Só o papel de carga age como sistema.' using errcode = 'GS403';
  end if;
  return system_iniciar_contexto((select id from config_usuarios where papel = 'sistema' order by id limit 1),
                                 p_correlation_id, false);
end $$;

-- 4. Auditoria: recusa "sistema" vindo dos papéis do app (substitui a versão de 0005) -------------------

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
  if v_papel = 'sistema' and system_eh_papel_do_app() then
    raise exception 'O app não pode gravar como o usuário sistema.' using errcode = 'GS403';
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

-- 5. Parâmetro da janela do limite -------------------------------------------------------------------

select set_config('app.usuario_id', '1', true), set_config('app.correlation_id', '00000000-0000-4000-8000-000000000022', true);
insert into config_parametros (chave, valor, descricao) values
  ('janela_limite_segundos', '60'::jsonb, 'Janela do limite de escritas por usuário (pedidos contados em system_correlacoes).')
on conflict do nothing;
select set_config('app.usuario_id', '', true), set_config('app.correlation_id', '', true);
