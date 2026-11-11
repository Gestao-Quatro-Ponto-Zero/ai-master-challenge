-- 0015_functions_leitura.sql  [LOTE 2]
-- Cria as funções de leitura das telas:
--   core_atende_etiquetas / core_buscar_deals / core_resumir_colunas — Pipeline e Leads, pelas etiquetas do filtro;
--   core_linha_do_tempo — modal do deal;
--   core_painel_numeros / core_painel_funil — Painel.
-- As etiquetas chegam já validadas pelo servidor (zod). Chaves desconhecidas são ignoradas.

create or replace function core_atende_etiquetas(v core_deals_visao, e jsonb) returns boolean
language sql stable set search_path = public as $$
  select
        (not (e ? 'ids')              or v.opportunity_id = any (array(select jsonb_array_elements_text(e -> 'ids'))))
    and (not (e ? 'estagios')         or v.estagio = any (array(select jsonb_array_elements_text(e -> 'estagios'))))
    and (not (e ? 'nota_min')         or v.score >= (e ->> 'nota_min')::integer)
    and (not (e ? 'nota_max')         or v.score <= (e ->> 'nota_max')::integer)
    and (not coalesce((e ->> 'sem_nota')::boolean, false) or v.score is null)
    and (not (e ? 'icones')           or v.icone = any (array(select jsonb_array_elements_text(e -> 'icones'))))
    and (not (e ? 'abertura_de')      or v.data_abertura >= (e ->> 'abertura_de')::date)
    and (not (e ? 'abertura_ate')     or v.data_abertura <= (e ->> 'abertura_ate')::date)
    and (not coalesce((e ->> 'sem_abertura')::boolean, false) or v.data_abertura is null)
    and (not (e ? 'dias_aberto_min')  or v.dias_desde_abertura > (e ->> 'dias_aberto_min')::integer)
    and (not (e ? 'contato_ha_dias_min')
         or v.ultimo_contato is null
         or system_data_negocio() - v.ultimo_contato >= (e ->> 'contato_ha_dias_min')::integer)
    and (not (e ? 'contato_ha_dias_max')
         or (v.ultimo_contato is not null and system_data_negocio() - v.ultimo_contato <= (e ->> 'contato_ha_dias_max')::integer))
    and (not coalesce((e ->> 'sem_contato')::boolean, false) or v.ultimo_contato is null)
    and (not coalesce((e ->> 'sem_contato_principal')::boolean, false) or v.contato_id is null)
    and (not (e ? 'setores')          or v.setor = any (array(select jsonb_array_elements_text(e -> 'setores'))))
    and (not (e ? 'portes')           or v.porte = any (array(select jsonb_array_elements_text(e -> 'portes'))))
    and (not coalesce((e ->> 'sem_empresa')::boolean, false) or v.conta_nome is null)
    and (not (e ? 'empresas')         or v.conta_nome = any (array(select jsonb_array_elements_text(e -> 'empresas'))))
    and (not (e ? 'produtos')         or v.produto_nome = any (array(select jsonb_array_elements_text(e -> 'produtos'))))
    and (not (e ? 'series')           or v.serie = any (array(select jsonb_array_elements_text(e -> 'series'))))
    and (not (e ? 'vendedores')       or v.vendedor_nome = any (array(select jsonb_array_elements_text(e -> 'vendedores'))))
    and (not (e ? 'managers')         or v.manager_nome = any (array(select jsonb_array_elements_text(e -> 'managers'))))
    and (not (e ? 'regioes')          or v.escritorio_nome = any (array(select jsonb_array_elements_text(e -> 'regioes'))))
    and (not (e ? 'acoes_sugeridas')  or v.acao_sugerida = any (array(select jsonb_array_elements_text(e -> 'acoes_sugeridas'))))
    and (not (e ? 'marcadores')       or v.marcadores && array(select jsonb_array_elements_text(e -> 'marcadores')))
    and (not (e ? 'valor_min')        or coalesce(v.valor_esperado, v.close_value) >= (e ->> 'valor_min')::integer)
    and (not (e ? 'fechamento_de')    or v.close_date >= (e ->> 'fechamento_de')::date)
    and (not (e ? 'fechamento_ate')   or v.close_date <= (e ->> 'fechamento_ate')::date)
    and (not (e ? 'tags')             or v.tags && array(select jsonb_array_elements_text(e -> 'tags')))
    and (not coalesce((e ->> 'sem_tag')::boolean, false) or cardinality(v.tags) = 0)
    and (not coalesce((e ->> 'com_comentario')::boolean, false) or v.qtd_comentarios > 0)
    and (not (e ? 'importacao_id')    or v.importacao_id = (e ->> 'importacao_id')::bigint)
    and (not (e ? 'contem')
         or strpos(lower(concat_ws(' ', v.opportunity_id, v.nome, v.produto_nome, v.conta_nome, v.vendedor_nome,
                                   v.contato_nome, array_to_string(v.tags, ' '))), lower(e ->> 'contem')) > 0
         or exists (select 1 from acao_comentarios cm
                     where cm.opportunity_id = v.opportunity_id and cm.removido_em is null
                       and strpos(lower(cm.texto), lower(e ->> 'contem')) > 0))
$$;

-- Ordens: nota (padrão), padrao_leads, valor, dias_sem_contato, dias_aberto, abertura, fechamento, vendedor, lead.
-- Devolve {"total": n, "linhas": [...]}; no máximo 200 linhas por chamada.
create or replace function core_buscar_deals(
  p_escopo    jsonb,
  p_etiquetas jsonb default '{}'::jsonb,
  p_ordem     text default 'nota',
  p_limite    integer default 50,
  p_offset    integer default 0
) returns jsonb
language sql stable set search_path = public as $$
  with f as (
    select v.*
      from core_deals_visao v
     where core_no_escopo(p_escopo, v.vendedor_nome, v.manager_nome, v.escritorio_nome)
       and core_atende_etiquetas(v, coalesce(p_etiquetas, '{}'::jsonb))
  ), o as (
    select f.*,
           row_number() over (order by
             case when p_ordem = 'padrao_leads' then (f.estagio in ('Won', 'Lost'))::integer end asc,
             case when p_ordem in ('nota', 'padrao_leads') then f.score end desc nulls last,
             case when p_ordem = 'padrao_leads' then f.close_date end desc nulls last,
             case when p_ordem = 'valor' then coalesce(f.valor_esperado, f.close_value) end desc nulls last,
             case when p_ordem = 'dias_sem_contato' then f.ultimo_contato end asc nulls first,
             case when p_ordem = 'dias_aberto' then f.data_abertura end asc nulls last,
             case when p_ordem = 'abertura' then f.data_abertura end desc nulls last,
             case when p_ordem = 'fechamento' then f.close_date end desc nulls last,
             case when p_ordem = 'vendedor' then f.vendedor_nome end asc,
             case when p_ordem = 'lead' then f.nome end asc,
             f.preco desc,
             f.opportunity_id) as posicao
      from f
  )
  select jsonb_build_object(
           'total', (select count(*) from f),
           'linhas', coalesce((select jsonb_agg(to_jsonb(x) - 'posicao' order by x.posicao)
                                 from (select * from o order by o.posicao
                                        limit least(greatest(coalesce(p_limite, 50), 1), 200)
                                       offset greatest(coalesce(p_offset, 0), 0)) x), '[]'::jsonb))
$$;

-- Cabeçalho das colunas do Pipeline: quantidade e soma do valor por estágio
create or replace function core_resumir_colunas(p_escopo jsonb, p_etiquetas jsonb default '{}'::jsonb)
returns table (estagio text, quantidade bigint, valor bigint)
language sql stable set search_path = public as $$
  select v.estagio, count(*), coalesce(sum(v.valor_esperado), 0)::bigint
    from core_deals_visao v
   where v.estagio in ('Prospecting', 'Engaging')
     and core_no_escopo(p_escopo, v.vendedor_nome, v.manager_nome, v.escritorio_nome)
     and core_atende_etiquetas(v, coalesce(p_etiquetas, '{}'::jsonb))
   group by v.estagio
$$;

-- Linha do tempo do modal: dataset + auditoria + ações + comentários (os apagados não aparecem)
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
         case when d.estagio = 'Won' then 'Ganho: US$ ' || d.close_value else 'Perdido' end, null, false, null
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
           || case when aud.depois ->> 'estagio' = 'Won' then ' (US$ ' || (aud.depois ->> 'close_value') || ')' else '' end,
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
         end || coalesce(' — "' || r.nota || '"', ''),
         u.nome_exibicao, r.desfeita_em is not null, r.id::text
    from acao_registros r
    join config_usuarios u on u.id = r.usuario_id
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

-- Painel: os 8 cartões, com as janelas de hoje, 30 dias e 30 dias antes (ESPEC-TELAS 4.3)
create or replace function core_painel_numeros(p_escopo jsonb) returns jsonb
language sql stable set search_path = public as $$
  with b as (
    select * from core_painel_janelas
     where core_no_escopo(p_escopo, vendedor_nome, manager_nome, escritorio_nome)
  ), n as (
    select
      count(*) filter (where abriu_hoje)                                       as leads_hoje,
      count(*) filter (where abriu_janela)                                     as leads_janela,
      count(*) filter (where abriu_janela_anterior)                            as leads_janela_anterior,
      count(*) filter (where estagio = 'Engaging')                             as em_negociacao,
      coalesce(sum(valor_esperado) filter (where estagio = 'Engaging'), 0)     as em_negociacao_valor,
      count(*) filter (where estagio = 'Won' and fechou_hoje)                  as fechamentos_hoje,
      coalesce(sum(close_value) filter (where estagio = 'Won' and fechou_hoje), 0) as fechamentos_hoje_valor,
      count(*) filter (where estagio = 'Won' and fechou_janela)                as fechamentos_janela,
      coalesce(sum(close_value) filter (where estagio = 'Won' and fechou_janela), 0) as receita_janela,
      count(*) filter (where estagio = 'Won' and fechou_janela_anterior)       as fechamentos_janela_anterior,
      coalesce(sum(close_value) filter (where estagio = 'Won' and fechou_janela_anterior), 0) as receita_janela_anterior,
      count(*) filter (where estagio = 'Lost' and fechou_janela)               as perdidos_janela,
      count(*) filter (where estagio = 'Lost' and fechou_janela_anterior)      as perdidos_janela_anterior,
      coalesce(sum(valor_esperado) filter (where estagio in ('Prospecting', 'Engaging')), 0) as pipeline_aberto_valor,
      coalesce(bool_or(valor_pelo_preco_de_tabela), false)                     as pipeline_pelo_preco_de_tabela,
      count(*)                                                                 as total_leads,
      count(*) filter (where icone = 'em_risco')                               as em_risco,
      count(*) filter (where icone = 'esfriou')                                as esfriou
    from b
  )
  select to_jsonb(n)
         || jsonb_build_object(
              'data', system_data_negocio(),
              'janela_dias', coalesce(config_inteiro('janela_painel_dias'), 30),
              'conversao_janela', round(n.fechamentos_janela::numeric / nullif(n.fechamentos_janela + n.perdidos_janela, 0), 4),
              'conversao_janela_anterior', round(n.fechamentos_janela_anterior::numeric
                                                 / nullif(n.fechamentos_janela_anterior + n.perdidos_janela_anterior, 0), 4),
              'fim_de_trimestre', extract(month from system_data_negocio())::integer in (3, 6, 9, 12))
    from n
$$;

create or replace function core_painel_funil(p_escopo jsonb)
returns table (estagio text, quantidade bigint, valor bigint)
language sql stable set search_path = public as $$
  select v.estagio,
         count(*),
         coalesce(sum(case when v.estagio = 'Won' then v.close_value
                           when v.estagio = 'Lost' then v.preco
                           else v.valor_esperado end), 0)::bigint
    from core_deals_visao v
   where core_no_escopo(p_escopo, v.vendedor_nome, v.manager_nome, v.escritorio_nome)
   group by v.estagio
$$;
