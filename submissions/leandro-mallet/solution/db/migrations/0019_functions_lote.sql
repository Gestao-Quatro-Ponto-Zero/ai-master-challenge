-- 0019_functions_lote.sql  [LOTE 2]
-- Cria as ações em lote da tela Leads (ESPEC-TELAS 6.1) e o "Desfazer este lote":
--   system_executar_lote — aplica uma ação em até limite_lote deals, numa transação só; os que não se
--                          aplicam são pulados e contados; cada escrita leva o lote_id na auditoria;
--   system_desfazer_lote — em até horas_desfazer_lote, devolve cada deal ao "antes" da auditoria,
--                          pulando o que mudou depois.

create or replace function system_executar_lote(
  p_usuario_id     bigint,
  p_correlation_id uuid,
  p_tipo           text,
  p_parametros     jsonb,
  p_ids            text[],
  p_etiquetas      jsonb default '{}'::jsonb
) returns jsonb
language plpgsql set search_path = public as $$
declare
  u        config_usuarios;
  v_ids    text[];
  v_id     text;
  v_lote   bigint;
  v_tag    bigint;
  v_texto  text;
  v_motivo text;
  v_hoje   date := system_data_negocio();
  v_ap     integer := 0;
  v_pu     integer := 0;
  v_ativas integer;
begin
  u := system_iniciar_contexto(p_usuario_id, p_correlation_id);
  perform system_exigir_papel(u, config_lista('papeis_lote'));
  v_ids := array(select distinct x from unnest(coalesce(p_ids, '{}'::text[])) x where x is not null);
  if cardinality(v_ids) = 0 then
    raise exception 'Selecione pelo menos um lead.' using errcode = 'GS400';
  end if;
  if cardinality(v_ids) > coalesce(config_inteiro('limite_lote'), 500) then
    raise exception 'Selecione até % por vez; refine o filtro.', coalesce(config_inteiro('limite_lote'), 500)
      using errcode = 'GS400';
  end if;
  if p_tipo not in ('aplicar_tag', 'remover_tag', 'comentar', 'avancar_estagio', 'encerrar_perdido') then
    raise exception 'Ação em lote desconhecida.' using errcode = 'GS400';
  end if;
  if p_tipo in ('aplicar_tag', 'remover_tag') then
    v_tag := (p_parametros ->> 'tag_id')::bigint;
    if not exists (select 1 from config_tags where id = v_tag and (ativa or p_tipo = 'remover_tag')) then
      raise exception 'Tag não encontrada ou arquivada.' using errcode = 'GS404';
    end if;
  end if;
  if p_tipo = 'comentar' then
    v_texto := btrim(p_parametros ->> 'texto');
    if v_texto is null or char_length(v_texto) not between 1 and 1000 or v_texto ~ '<[a-zA-Z/!]' then
      raise exception 'Escreva um comentário de 1 a 1.000 caracteres, sem HTML.' using errcode = 'GS400';
    end if;
  end if;
  if p_tipo = 'encerrar_perdido' then
    v_motivo := p_parametros ->> 'motivo';
    if v_motivo is null and config_booleano('motivo_perda_obrigatorio') then
      raise exception 'Escolha o motivo da perda.' using errcode = 'GS400';
    end if;
  end if;

  insert into system_lotes (usuario_id, tipo, parametros, etiquetas, quantidade, correlation_id)
  values (u.id, p_tipo, coalesce(p_parametros, '{}'::jsonb), coalesce(p_etiquetas, '{}'::jsonb), cardinality(v_ids), p_correlation_id)
  returning id into v_lote;
  perform set_config('app.lote_id', v_lote::text, true);

  foreach v_id in array v_ids loop
    if not exists (select 1 from core_deals where opportunity_id = v_id) then
      v_pu := v_pu + 1;
      continue;
    end if;

    if p_tipo = 'aplicar_tag' then
      select count(*) into v_ativas from acao_deal_tags where opportunity_id = v_id and removida_em is null;
      if exists (select 1 from acao_deal_tags where opportunity_id = v_id and tag_id = v_tag and removida_em is null)
         or v_ativas >= coalesce(config_inteiro('max_tags_por_deal'), 10) then
        v_pu := v_pu + 1;
      else
        insert into acao_deal_tags (opportunity_id, tag_id, usuario_id) values (v_id, v_tag, u.id);
        v_ap := v_ap + 1;
      end if;

    elsif p_tipo = 'remover_tag' then
      update acao_deal_tags set removida_em = now(), removida_por = u.id
       where opportunity_id = v_id and tag_id = v_tag and removida_em is null;
      if found then v_ap := v_ap + 1; else v_pu := v_pu + 1; end if;

    elsif p_tipo = 'comentar' then
      insert into acao_comentarios (opportunity_id, usuario_id, texto, data_negocio) values (v_id, u.id, v_texto, v_hoje);
      v_ap := v_ap + 1;

    elsif p_tipo = 'avancar_estagio' then
      update core_deals set estagio = 'Engaging', data_abertura = coalesce(data_abertura, v_hoje)
       where opportunity_id = v_id and estagio = 'Prospecting';
      if found then v_ap := v_ap + 1; else v_pu := v_pu + 1; end if;

    elsif p_tipo = 'encerrar_perdido' then
      update core_deals
         set estagio = 'Lost', close_date = v_hoje, close_value = 0, motivo_perda = v_motivo,
             motivo_perda_detalhe = nullif(btrim(p_parametros ->> 'motivo_detalhe'), '')
       where opportunity_id = v_id and estagio in ('Prospecting', 'Engaging')
         and (data_abertura is null or data_abertura <= v_hoje);
      if found then v_ap := v_ap + 1; else v_pu := v_pu + 1; end if;
    end if;
  end loop;

  update system_lotes set aplicados = v_ap, pulados = v_pu where id = v_lote;
  perform system_registrar_evento('lote_aplicado', jsonb_build_object('lote_id', v_lote, 'tipo', p_tipo,
                                  'aplicados', v_ap, 'pulados', v_pu));
  return jsonb_build_object('lote_id', v_lote, 'aplicados', v_ap, 'pulados', v_pu);
end $$;

create or replace function system_desfazer_lote(p_usuario_id bigint, p_correlation_id uuid, p_lote_id bigint) returns jsonb
language plpgsql set search_path = public as $$
declare
  u   config_usuarios := system_iniciar_contexto(p_usuario_id, p_correlation_id, false);
  l   system_lotes;
  a   record;
  v_r integer := 0;
  v_p integer := 0;
begin
  select * into l from system_lotes where id = p_lote_id for update;
  if not found then
    raise exception 'Lote não encontrado.' using errcode = 'GS404';
  end if;
  if l.desfeito_em is not null then
    raise exception 'Este lote já foi desfeito.' using errcode = 'GS422';
  end if;
  if l.usuario_id <> u.id and u.papel not in ('manager', 'admin') then
    raise exception 'Só quem aplicou o lote, o manager ou o admin podem desfazer.' using errcode = 'GS403';
  end if;
  if l.criado_em < now() - make_interval(hours => coalesce(config_inteiro('horas_desfazer_lote'), 24)) then
    raise exception 'O prazo para desfazer este lote passou.' using errcode = 'GS422';
  end if;

  for a in
    select * from system_auditoria
     where lote_id = p_lote_id and tabela in ('core_deals', 'acao_deal_tags', 'acao_comentarios')
     order by id desc
  loop
    if a.tabela = 'core_deals' and a.operacao = 'update' then
      update core_deals
         set estagio              = a.antes ->> 'estagio',
             data_abertura        = (a.antes ->> 'data_abertura')::date,
             close_date           = (a.antes ->> 'close_date')::date,
             close_value          = (a.antes ->> 'close_value')::integer,
             motivo_perda         = a.antes ->> 'motivo_perda',
             motivo_perda_detalhe = a.antes ->> 'motivo_perda_detalhe'
       where opportunity_id = a.registro_id
         and atualizado_em = (a.depois ->> 'atualizado_em')::timestamptz;
    elsif a.tabela = 'acao_deal_tags' and a.operacao = 'insert' then
      update acao_deal_tags set removida_em = now(), removida_por = u.id
       where id = a.registro_id::bigint and removida_em is null;
    elsif a.tabela = 'acao_deal_tags' and a.operacao = 'update' then
      update acao_deal_tags set removida_em = null, removida_por = null
       where id = a.registro_id::bigint
         and removida_em = (a.depois ->> 'removida_em')::timestamptz
         and not exists (select 1 from acao_deal_tags o
                          where o.opportunity_id = a.depois ->> 'opportunity_id'
                            and o.tag_id = (a.depois ->> 'tag_id')::bigint and o.removida_em is null);
    elsif a.tabela = 'acao_comentarios' and a.operacao = 'insert' then
      update acao_comentarios set removido_em = now(), removido_por = u.id
       where id = a.registro_id::bigint and removido_em is null;
    else
      continue;
    end if;
    if found then v_r := v_r + 1; else v_p := v_p + 1; end if;
  end loop;

  update system_lotes set desfeito_em = now(), desfeito_por = u.id where id = p_lote_id;
  perform system_registrar_evento('lote_desfeito', jsonb_build_object('lote_id', p_lote_id, 'restaurados', v_r, 'pulados', v_p));
  return jsonb_build_object('lote_id', p_lote_id, 'restaurados', v_r, 'pulados', v_p);
end $$;
