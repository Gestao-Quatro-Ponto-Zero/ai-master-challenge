-- 0031_funil_cinco_etapas.sql  [O-31 — funil com 5 etapas, decisão do Leandro]
-- As etapas na tela são Novo lead, Atendimento, Em negociação, Fechado e Perdido. O dado continua o mesmo
-- (Prospecting, Engaging, Won, Lost): "Novo lead" e "Atendimento" são o Prospecting sem e com contato
-- registrado (core_deals.ultimo_contato_em), e quem separa é o app. Esta migration só:
--   1. troca o rótulo de Won de "Ganho" para "Fechado" (core_rotulo_estagio: linha do tempo e mensagens);
--   2. cria a ação "contato" (registro de atendimento com tipo de atividade e comentário obrigatórios),
--      usada quando o deal entra em Atendimento pelo Pipeline. Conta como contato pelo gatilho de 0023
--      (tipo com conta_como_contato), então o lead passa de Novo lead para Atendimento sozinho;
--   3. põe a ação "contato" na linha do tempo e o fechamento como "Fechado: R$ …".
-- Nada é apagado: a troca da regra de acao_registros.acao só acrescenta um valor permitido.
-- Trava de contexto, limites, auditoria e permissões seguem como estão.

-- 1. Rótulo do estágio ---------------------------------------------------------------------------------------

create or replace function core_rotulo_estagio(p_estagio text) returns text
language sql immutable as $$
  select case p_estagio
           when 'Prospecting' then 'Prospecção'
           when 'Engaging' then 'Em negociação'
           when 'Won' then 'Fechado'
           when 'Lost' then 'Perdido'
           else p_estagio
         end
$$;

-- 2. Ação "contato" -------------------------------------------------------------------------------------------

alter table acao_registros drop constraint acao_registros_acao_check;
alter table acao_registros
  add constraint acao_registros_acao_check
    check (acao in ('liguei', 'requalifiquei', 'desisti', 'prioridade_feita', 'prioridade_pulada', 'contato')),
  add constraint acao_registros_contato_completo_chk
    check (acao <> 'contato' or (tipo_atividade is not null and nullif(btrim(nota), '') is not null));

-- Registrar atendimento: tipo de atividade que conta como contato e comentário obrigatórios; deal aberto.
create or replace function acao_registrar_contato(
  p_usuario_id     bigint,
  p_correlation_id uuid,
  p_opportunity_id text,
  p_tipo_atividade text,
  p_comentario     text
) returns acao_registros
language plpgsql set search_path = public as $$
declare
  u        config_usuarios := system_iniciar_contexto(p_usuario_id, p_correlation_id);
  r        acao_registros;
  v_tipo   text := nullif(btrim(p_tipo_atividade), '');
  v_coment text := nullif(btrim(p_comentario), '');
begin
  if v_tipo is null or not exists (select 1 from config_tipos_atividade where codigo = v_tipo and ativo and conta_como_contato) then
    raise exception 'Escolha o tipo de atividade.' using errcode = 'GS400';
  end if;
  if v_coment is null then
    raise exception 'Escreva um comentário sobre o que foi feito.' using errcode = 'GS400';
  end if;
  if char_length(v_coment) > 280 or v_coment ~ '<[a-zA-Z/!]' then
    raise exception 'Comentário de até 280 caracteres, sem HTML.' using errcode = 'GS400';
  end if;
  if not exists (select 1 from core_deals where opportunity_id = p_opportunity_id) then
    raise exception 'Deal não encontrado.' using errcode = 'GS404';
  end if;
  if not exists (select 1 from core_deals where opportunity_id = p_opportunity_id and estagio in ('Prospecting', 'Engaging')) then
    raise exception 'Só é possível registrar atendimento em deal aberto.' using errcode = 'GS422';
  end if;
  insert into acao_registros (opportunity_id, usuario_id, papel, execucao_id, acao, nota, data_negocio, tipo_atividade)
  values (p_opportunity_id, u.id, u.papel, score_execucao_ativa(), 'contato', v_coment, system_data_negocio(), v_tipo)
  returning * into r;
  return r;
end $$;

-- 3. Linha do tempo (a de 0015, com a ação "contato" e o fechamento como "Fechado") ---------------------------

create or replace function core_linha_do_tempo(p_opportunity_id text)
returns table (data_negocio date, momento timestamptz, tipo text, descricao text, autor text, desfeito boolean, referencia text)
language sql stable set search_path = public as $$
  with d as (select * from core_deals where opportunity_id = p_opportunity_id),
  aud as (
    select a.*, u.nome_exibicao
      from system_auditoria a
      join config_usuarios u on u.id = a.usuario_id
     where a.tabela = 'core_deals' and a.registro_id = p_opportunity_id
  )
  -- abertura vinda do dataset ou da importação (sem mudança de estágio registrada no CRM)
  select d.data_abertura, null::timestamptz, 'aberto', 'Aberto (entrou em negociação)', null::text, false, null::text
    from d
   where d.data_abertura is not null
     and not exists (select 1 from aud where aud.operacao = 'update'
                       and aud.antes ->> 'estagio' = 'Prospecting' and aud.depois ->> 'estagio' = 'Engaging')
  union all
  -- fechamento vindo do dataset ou da importação
  select d.close_date, null, 'fechado',
         case when d.estagio = 'Won' then 'Fechado: R$ ' || d.close_value else 'Perdido' end, null, false, null
    from d
   where d.estagio in ('Won', 'Lost')
     and not exists (select 1 from aud where aud.operacao = 'update'
                       and aud.depois ->> 'estagio' = d.estagio and aud.antes ->> 'estagio' is distinct from d.estagio)
  union all
  -- criado ou importado no CRM (as cargas do usuário "sistema" não aparecem)
  select aud.data_negocio, aud.criado_em,
         case when aud.depois ->> 'importacao_id' is not null then 'importado' else 'criado' end,
         case when aud.depois ->> 'importacao_id' is not null then 'Importado de planilha' else 'Cadastrado no CRM' end,
         aud.nome_exibicao, false, aud.correlation_id::text
    from aud
   where aud.operacao = 'insert' and aud.papel <> 'sistema'
  union all
  -- mudanças de estágio
  select aud.data_negocio, aud.criado_em, 'estagio',
         'Estágio: ' || core_rotulo_estagio(aud.antes ->> 'estagio') || ' → ' || core_rotulo_estagio(aud.depois ->> 'estagio')
           || case when aud.depois ->> 'estagio' = 'Won' then ' (R$ ' || (aud.depois ->> 'close_value') || ')' else '' end,
         aud.nome_exibicao, false, aud.correlation_id::text
    from aud
   where aud.operacao = 'update' and aud.antes ->> 'estagio' is distinct from aud.depois ->> 'estagio'
  union all
  -- nome, empresa, contato e vendedor
  select aud.data_negocio, aud.criado_em, 'dados',
         concat_ws('; ',
           case when aud.antes ->> 'nome' is distinct from aud.depois ->> 'nome' then 'Nome alterado' end,
           case when aud.antes ->> 'conta_nome' is distinct from aud.depois ->> 'conta_nome' then 'Empresa: ' || coalesce(aud.depois ->> 'conta_nome', '—') end,
           case when aud.antes ->> 'contato_id' is distinct from aud.depois ->> 'contato_id' then 'Contato principal alterado' end,
           case when aud.antes ->> 'vendedor_nome' is distinct from aud.depois ->> 'vendedor_nome' then 'Passado para ' || (aud.depois ->> 'vendedor_nome') end),
         aud.nome_exibicao, false, aud.correlation_id::text
    from aud
   where aud.operacao = 'update'
     and (aud.antes ->> 'nome' is distinct from aud.depois ->> 'nome'
          or aud.antes ->> 'conta_nome' is distinct from aud.depois ->> 'conta_nome'
          or aud.antes ->> 'contato_id' is distinct from aud.depois ->> 'contato_id'
          or aud.antes ->> 'vendedor_nome' is distinct from aud.depois ->> 'vendedor_nome')
  union all
  -- ações (as desfeitas aparecem riscadas na tela)
  select r.data_negocio, r.criado_em, 'acao',
         case r.acao
           when 'liguei' then 'Liguei'
           when 'requalifiquei' then 'Requalifiquei'
           when 'desisti' then 'Desisti'
           when 'prioridade_feita' then 'Feito na prioridade do dia'
           when 'prioridade_pulada' then 'Pulado na prioridade do dia'
           when 'contato' then 'Atendimento: ' || coalesce(t.rotulo, r.tipo_atividade)
           else r.acao
         end || coalesce(' — "' || r.nota || '"', ''),
         u.nome_exibicao, r.desfeita_em is not null, r.id::text
    from acao_registros r
    join config_usuarios u on u.id = r.usuario_id
    left join config_tipos_atividade t on t.codigo = r.tipo_atividade
   where r.opportunity_id = p_opportunity_id
  union all
  -- comentários não apagados
  select cm.data_negocio, cm.criado_em, 'comentario', left(cm.texto, 280) || case when cm.editado_em is not null then ' (editado)' else '' end,
         u.nome_exibicao, false, cm.id::text
    from acao_comentarios cm
    join config_usuarios u on u.id = cm.usuario_id
   where cm.opportunity_id = p_opportunity_id and cm.removido_em is null
  union all
  -- tags aplicadas e removidas
  select a.data_negocio, a.criado_em, 'tag',
         case when a.operacao = 'insert' then 'Tag #' else 'Tag removida: #' end || tg.nome,
         u.nome_exibicao, false, a.registro_id
    from system_auditoria a
    join config_usuarios u on u.id = a.usuario_id
    join config_tags tg on tg.id = (a.depois ->> 'tag_id')::bigint
   where a.tabela = 'acao_deal_tags'
     and a.depois ->> 'opportunity_id' = p_opportunity_id
     and (a.operacao = 'insert' or (a.antes ->> 'removida_em' is null and a.depois ->> 'removida_em' is not null))
  order by 1 nulls first, 2 nulls first
$$;

-- 4. Permissões da função nova, como as demais: app e carga executam; public, anon e authenticated não ---------

do $$
declare
  r text;
begin
  execute 'revoke execute on function acao_registrar_contato(bigint, uuid, text, text, text) from public';
  foreach r in array array['anon', 'authenticated'] loop
    if exists (select 1 from pg_roles where rolname = r) then
      execute format('revoke execute on function acao_registrar_contato(bigint, uuid, text, text, text) from %I', r);
    end if;
  end loop;
  foreach r in array array['service_role', 'system_carga'] loop
    if exists (select 1 from pg_roles where rolname = r) then
      execute format('grant execute on function acao_registrar_contato(bigint, uuid, text, text, text) to %I', r);
    end if;
  end loop;
end $$;
