-- 0020_functions_cargas.sql  [LOTE 2]
-- Cria as funções usadas pelas cargas (Python e dados iniciais), sempre assinadas pelo usuário "sistema":
--   config_gerar_usuarios — cria em config_usuarios um usuário para cada vendedor e manager do time (idempotente);
--   score_ativar_execucao — aponta a execução de score ativa e registra a carga em system_eventos.
-- As notas (score_*) são inseridas pelo Python e não passam pela auditoria linha a linha: a carga
-- é registrada como um evento, com a execução e as contagens.

create or replace function config_gerar_usuarios(p_correlation_id uuid) returns integer
language plpgsql set search_path = public as $$
declare
  v_vendedores integer;
  v_managers   integer;
begin
  perform system_iniciar_contexto_sistema(p_correlation_id);
  insert into config_usuarios (papel, nome_exibicao, vendedor_nome)
  select 'vendedor', v.nome, v.nome
    from core_vendedores v
   where not exists (select 1 from config_usuarios u where u.vendedor_nome = v.nome)
   order by v.nome;
  get diagnostics v_vendedores = row_count;
  insert into config_usuarios (papel, nome_exibicao, manager_nome)
  select 'manager', m.nome, m.nome
    from core_managers m
   where not exists (select 1 from config_usuarios u where u.manager_nome = m.nome)
   order by m.nome;
  get diagnostics v_managers = row_count;
  perform system_registrar_evento('usuarios_gerados', jsonb_build_object('vendedores', v_vendedores, 'managers', v_managers));
  return v_vendedores + v_managers;
end $$;

create or replace function score_ativar_execucao(p_correlation_id uuid, p_execucao_id bigint) returns void
language plpgsql set search_path = public as $$
declare
  v_deals integer;
begin
  perform system_iniciar_contexto_sistema(p_correlation_id);
  if not exists (select 1 from score_execucoes where id = p_execucao_id) then
    raise exception 'Execução de score % não existe.', p_execucao_id using errcode = 'GS404';
  end if;
  select count(*) into v_deals from score_deals where execucao_id = p_execucao_id;
  update config_parametros set valor = to_jsonb(p_execucao_id), atualizado_em = now() where chave = 'execucao_ativa';
  perform system_registrar_evento('carga_score', jsonb_build_object('execucao_id', p_execucao_id, 'deals', v_deals));
end $$;
