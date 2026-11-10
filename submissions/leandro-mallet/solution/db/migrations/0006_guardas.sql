-- 0006_guardas: o que não pode ser pulado.
--   * contexto obrigatório (usuario_id + correlation_id) e limite de escritas por minuto;
--   * auditoria por gatilho (antes, depois, usuário, papel, correlation_id e lote);
--   * DELETE e TRUNCATE barrados por gatilho e por revoke em todas as tabelas;
--   * RLS ligado em todas as tabelas, sem política (só a service role, no servidor, acessa);
--   * gatilhos de regra: versão do deal, último contato, limite de tags e contato da mesma empresa.
-- Códigos de erro (SQLSTATE) para a API traduzir em frase simples:
--   G4401 sem contexto ou usuário inválido · G4403 papel sem permissão · G4404 não encontrado
--   G4405 remoção proibida · G4409 conflito de versão (HTTP 409) · G4422 dado inválido · G4429 limite de taxa

-- ---------------------------------------------------------------- contexto da escrita
create function system_definir_contexto(p_usuario_id bigint, p_correlation_id uuid, p_lote_id bigint default null)
returns text
language plpgsql
set search_path = public
as $$
declare
  v_papel text;
  v_ativo boolean;
  v_corr_atual text := nullif(current_setting('app.correlation_id', true), '');
  v_limite integer;
  v_recentes integer;
begin
  if p_usuario_id is null or p_correlation_id is null then
    raise exception using errcode = 'G4401', message = 'contexto_obrigatorio';
  end if;
  select papel, ativo into v_papel, v_ativo from config_usuarios where id = p_usuario_id;
  if v_papel is null or not v_ativo then
    raise exception using errcode = 'G4401', message = 'usuario_invalido';
  end if;

  -- limite de abuso (sem senha, qualquer um age como qualquer usuário): pedidos distintos no último minuto
  if v_papel <> 'sistema' and v_corr_atual is distinct from p_correlation_id::text then
    v_limite := config_inteiro('limite_por_minuto', 60);
    select count(distinct correlation_id) into v_recentes
      from system_auditoria
     where usuario_id = p_usuario_id and criado_em > now() - interval '1 minute';
    if v_recentes >= v_limite then
      raise exception using errcode = 'G4429', message = 'limite_de_taxa';
    end if;
  end if;

  perform set_config('app.usuario_id', p_usuario_id::text, true);
  perform set_config('app.correlation_id', p_correlation_id::text, true);
  if p_lote_id is not null then
    perform set_config('app.lote_id', p_lote_id::text, true);
  elsif v_corr_atual is distinct from p_correlation_id::text then
    perform set_config('app.lote_id', '', true);
  end if;
  perform set_config('app.versao', '', true);
  return v_papel;
end;
$$;
comment on function system_definir_contexto(bigint, uuid, bigint) is 'Chamada no início de toda function de escrita. Sem ela, o gatilho de auditoria recusa a escrita.';

create function system_mascarar(p jsonb) returns jsonb
language sql immutable
as $$
  -- e-mail e telefone mascarados na auditoria (ARQ-04: sem dado pessoal desnecessário)
  select case when p is null then null else
    p || jsonb_build_object(
      'email', case when p->>'email' is null then null
                    else left(p->>'email', 1) || '***@' || split_part(p->>'email', '@', 2) end,
      'telefone', case when p->>'telefone' is null then null
                       else '***' || right(regexp_replace(p->>'telefone', '[^0-9]', '', 'g'), 2) end)
  end
$$;

-- ---------------------------------------------------------------- auditoria
create function system_auditar() returns trigger
language plpgsql
set search_path = public
as $$
declare
  v_usuario bigint := nullif(current_setting('app.usuario_id', true), '')::bigint;
  v_corr uuid := nullif(current_setting('app.correlation_id', true), '')::uuid;
  v_lote bigint := nullif(current_setting('app.lote_id', true), '')::bigint;
  v_papel text;
  v_antes jsonb;
  v_depois jsonb := to_jsonb(new);
begin
  if v_usuario is null or v_corr is null then
    raise exception using errcode = 'G4401', message = 'auditoria_sem_contexto',
      hint = 'Chame system_definir_contexto antes de escrever em ' || tg_table_name;
  end if;
  select papel into v_papel from config_usuarios where id = v_usuario;
  if v_papel is null then
    raise exception using errcode = 'G4401', message = 'usuario_invalido';
  end if;
  if tg_op = 'UPDATE' then
    v_antes := to_jsonb(old);
    if v_antes = v_depois then
      return null;
    end if;
  end if;
  if coalesce(tg_argv[1], '') = 'mascarar' then
    v_antes := system_mascarar(v_antes);
    v_depois := system_mascarar(v_depois);
  end if;
  insert into system_auditoria (tabela, registro_id, operacao, antes, depois, usuario_id, papel, correlation_id, lote_id)
  values (tg_table_name, v_depois->>tg_argv[0], lower(tg_op), v_antes, v_depois, v_usuario, v_papel, v_corr, v_lote);
  return null;
end;
$$;

create trigger system_auditar after insert or update on core_deals
  for each row execute function system_auditar('opportunity_id');
create trigger system_auditar after insert or update on core_contas
  for each row execute function system_auditar('nome');
create trigger system_auditar after insert or update on core_contatos
  for each row execute function system_auditar('id', 'mascarar');
create trigger system_auditar after insert or update on core_vendedores
  for each row execute function system_auditar('nome');
create trigger system_auditar after insert or update on config_usuarios
  for each row execute function system_auditar('id');
create trigger system_auditar after insert or update on config_parametros
  for each row execute function system_auditar('chave');
create trigger system_auditar after insert or update on config_tags
  for each row execute function system_auditar('id');
create trigger system_auditar after insert or update on config_motivos_perda
  for each row execute function system_auditar('codigo');
create trigger system_auditar after insert or update on acao_registros
  for each row execute function system_auditar('id');
create trigger system_auditar after insert or update on acao_comentarios
  for each row execute function system_auditar('id');
create trigger system_auditar after insert or update on acao_deal_tags
  for each row execute function system_auditar('id');
create trigger system_auditar after insert or update on acao_prioridades
  for each row execute function system_auditar('id');
create trigger system_auditar after insert or update on acao_atribuicoes
  for each row execute function system_auditar('id');
create trigger system_auditar after insert or update on system_lotes
  for each row execute function system_auditar('id');

-- ---------------------------------------------------------------- nada é apagado
create function system_bloquear_delete() returns trigger
language plpgsql
as $$
begin
  raise exception using errcode = 'G4405', message = 'remocao_proibida',
    hint = 'Use a remoção lógica (removido_em, removida_em, inativo_em, ativo = false) ou encerre o deal.';
end;
$$;

create function system_bloquear_truncate() returns trigger
language plpgsql
as $$
begin
  raise exception using errcode = 'G4405', message = 'truncate_proibido';
end;
$$;

-- ---------------------------------------------------------------- regras de dado
create function core_marcar_atualizacao() returns trigger
language plpgsql
set search_path = public
as $$
declare
  v_versao text := nullif(current_setting('app.versao', true), '');
begin
  -- só o último contato mudou (gatilho de acao_registros): não muda a versão do deal
  if (to_jsonb(new) - 'ultimo_contato_em' - 'atualizado_em' - 'atualizado_por')
     = (to_jsonb(old) - 'ultimo_contato_em' - 'atualizado_em' - 'atualizado_por') then
    return new;
  end if;
  if v_versao is not null and old.atualizado_em <> v_versao::timestamptz then
    raise exception using errcode = 'G4409', message = 'conflito_versao',
      detail = jsonb_build_object('opportunity_id', old.opportunity_id,
                                  'atualizado_em', old.atualizado_em,
                                  'atualizado_por', old.atualizado_por)::text;
  end if;
  new.atualizado_em := clock_timestamp();
  new.atualizado_por := nullif(current_setting('app.usuario_id', true), '')::bigint;
  return new;
end;
$$;
create trigger core_marcar_atualizacao before update on core_deals
  for each row execute function core_marcar_atualizacao();

create function core_carimbar_atualizacao() returns trigger
language plpgsql
as $$
begin
  new.atualizado_em := clock_timestamp();
  new.atualizado_por := nullif(current_setting('app.usuario_id', true), '')::bigint;
  return new;
end;
$$;
create trigger core_carimbar_atualizacao before update on core_contas
  for each row execute function core_carimbar_atualizacao();
create trigger core_carimbar_atualizacao before update on core_contatos
  for each row execute function core_carimbar_atualizacao();

create function core_validar_contato() returns trigger
language plpgsql
set search_path = public
as $$
declare
  v_conta text;
  v_inativo timestamptz;
begin
  if new.contato_id is null then
    return new;
  end if;
  select conta_nome, inativo_em into v_conta, v_inativo from core_contatos where id = new.contato_id;
  if v_conta is not null and v_conta is distinct from new.conta_nome then
    raise exception using errcode = 'G4422', message = 'contato_de_outra_empresa';
  end if;
  if v_inativo is not null then
    if tg_op = 'INSERT' then
      raise exception using errcode = 'G4422', message = 'contato_inativo';
    elsif new.contato_id is distinct from old.contato_id then
      raise exception using errcode = 'G4422', message = 'contato_inativo';
    end if;
  end if;
  return new;
end;
$$;
create trigger core_validar_contato before insert or update of contato_id, conta_nome on core_deals
  for each row execute function core_validar_contato();

create function acao_atualizar_ultimo_contato() returns trigger
language plpgsql
set search_path = public
as $$
declare
  v_tipos text[] := array(select jsonb_array_elements_text(
                      coalesce(config_valor('acoes_contato'), '["liguei","requalifiquei"]'::jsonb)));
  v_novo date;
begin
  if not (new.acao = any(v_tipos)) then
    return null;
  end if;
  select greatest(d.ultimo_contato_carga,
                  (select max(r.data_negocio) from acao_registros r
                    where r.opportunity_id = new.opportunity_id
                      and r.desfeita_em is null and r.acao = any(v_tipos)))
    into v_novo
    from core_deals d where d.opportunity_id = new.opportunity_id;
  update core_deals set ultimo_contato_em = v_novo
   where opportunity_id = new.opportunity_id and ultimo_contato_em is distinct from v_novo;
  return null;
end;
$$;
create trigger acao_atualizar_ultimo_contato after insert or update of desfeita_em on acao_registros
  for each row execute function acao_atualizar_ultimo_contato();

create function acao_limitar_tags() returns trigger
language plpgsql
set search_path = public
as $$
declare
  v_ativas integer;
begin
  if new.removida_em is not null then
    return new;
  end if;
  if tg_op = 'UPDATE' then
    if old.removida_em is null then
      return new;
    end if;
  end if;
  select count(*) into v_ativas from acao_deal_tags
   where opportunity_id = new.opportunity_id and removida_em is null and id is distinct from new.id;
  if v_ativas >= config_inteiro('max_tags_por_deal', 10) then
    raise exception using errcode = 'G4422', message = 'limite_de_tags';
  end if;
  return new;
end;
$$;
create trigger acao_limitar_tags before insert or update of removida_em on acao_deal_tags
  for each row execute function acao_limitar_tags();

-- ---------------------------------------------------------------- RLS, gatilhos de bloqueio e revoke em todas as tabelas
do $$
declare
  v_tabela text;
  v_papel text;
begin
  for v_tabela in
    select c.relname
      from pg_class c join pg_namespace n on n.oid = c.relnamespace
     where n.nspname = 'public' and c.relkind = 'r' and c.relname ~ '^(core|config|score|acao|system)_'
  loop
    execute format('alter table %I enable row level security', v_tabela);
    execute format('create trigger system_bloquear_delete before delete on %I for each row execute function system_bloquear_delete()', v_tabela);
    execute format('create trigger system_bloquear_truncate before truncate on %I for each statement execute function system_bloquear_truncate()', v_tabela);
    execute format('revoke delete, truncate on table %I from public', v_tabela);
    foreach v_papel in array array['anon', 'authenticated', 'service_role'] loop
      if exists (select 1 from pg_roles where rolname = v_papel) then
        execute format('revoke delete, truncate on table %I from %I', v_tabela, v_papel);
        if v_papel <> 'service_role' then
          execute format('revoke all on table %I from %I', v_tabela, v_papel);
        end if;
      end if;
    end loop;
  end loop;

  foreach v_papel in array array['anon', 'authenticated'] loop
    if exists (select 1 from pg_roles where rolname = v_papel) then
      execute format('alter default privileges in schema public revoke all on tables from %I', v_papel);
      execute format('alter default privileges in schema public revoke all on functions from %I', v_papel);
    end if;
  end loop;
end;
$$;
