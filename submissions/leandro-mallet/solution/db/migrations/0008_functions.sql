-- 0008_functions: leitura das telas e toda a escrita do CRM.
-- Regras comuns às functions de escrita:
--   * recebem p_usuario_id e p_correlation_id e chamam system_definir_contexto (auditoria obrigatória);
--   * não apagam nada; remover, desfazer e arquivar são updates;
--   * não bloqueiam por dono do deal (decisão 16). Só duas regras de papel ficam no banco, por serem
--     regra de dado: reabrir deal encerrado e reatribuir deal (manager e admin);
--   * versão do deal: p_versao = o atualizado_em lido pela tela; se mudou, erro G4409 (HTTP 409).
-- Escopo de leitura (p_escopo jsonb): {"vendedor": nome} | {"manager": nome} | {} (todos),
-- com filtros opcionais "regiao", "manager" e "vendedor" combináveis.

-- ================================================================ apoio
create function core_escopo_vendedores(p_escopo jsonb) returns setof text
language sql stable
set search_path = public
as $$
  select v.nome
    from core_vendedores v
    join core_managers m on m.nome = v.manager_nome
   where (p_escopo ->> 'vendedor' is null or v.nome = p_escopo ->> 'vendedor')
     and (p_escopo ->> 'manager' is null or v.manager_nome = p_escopo ->> 'manager')
     and (p_escopo ->> 'regiao' is null or m.escritorio_nome = p_escopo ->> 'regiao')
$$;

create function core_gerar_opportunity_id() returns text
language plpgsql volatile
set search_path = public
as $$
declare
  v_letras constant text := 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  v_id text;
begin
  loop
    select string_agg(substr(v_letras, 1 + floor(random() * 36)::integer, 1), '')
      into v_id from generate_series(1, 8);
    exit when not exists (select 1 from core_deals where opportunity_id = v_id);
  end loop;
  return v_id;
end;
$$;

create function core_restaurar_deal(p_opportunity_id text, p_antes jsonb) returns void
language plpgsql
set search_path = public
as $$
begin
  -- usado pelos "desfazer": devolve os campos editáveis ao estado do "antes" da auditoria
  update core_deals
     set estagio              = p_antes ->> 'estagio',
         nome                 = p_antes ->> 'nome',
         vendedor_nome        = p_antes ->> 'vendedor_nome',
         conta_nome           = p_antes ->> 'conta_nome',
         contato_id           = (p_antes ->> 'contato_id')::bigint,
         data_abertura        = (p_antes ->> 'data_abertura')::date,
         close_date           = (p_antes ->> 'close_date')::date,
         close_value          = (p_antes ->> 'close_value')::integer,
         motivo_perda         = p_antes ->> 'motivo_perda',
         motivo_perda_detalhe = p_antes ->> 'motivo_perda_detalhe'
   where opportunity_id = p_opportunity_id;
end;
$$;

-- ================================================================ leitura: Pipeline e Leads
create function core_filtrar_deals(p_etiquetas jsonb, p_escopo jsonb) returns setof core_deals_visao
language sql stable
set search_path = public
as $$
  with e as (select coalesce(p_etiquetas, '{}'::jsonb) as j)
  select v.*
    from core_deals_visao v, e
   where v.vendedor_nome in (select core_escopo_vendedores(coalesce(p_escopo, '{}'::jsonb)))
     and (e.j -> 'estagios' is null or v.estagio = any (array(select jsonb_array_elements_text(e.j -> 'estagios'))))
     and (e.j ->> 'nota_min' is null or v.score >= (e.j ->> 'nota_min')::integer)
     and (e.j ->> 'nota_menor_que' is null or v.score < (e.j ->> 'nota_menor_que')::integer)
     and (not coalesce((e.j ->> 'sem_nota')::boolean, false) or v.score is null)
     and (e.j -> 'icones' is null or v.icone = any (array(select jsonb_array_elements_text(e.j -> 'icones'))))
     and (e.j ->> 'abertura_de' is null or v.data_abertura >= (e.j ->> 'abertura_de')::date)
     and (e.j ->> 'abertura_ate' is null or v.data_abertura <= (e.j ->> 'abertura_ate')::date)
     and (not coalesce((e.j ->> 'sem_abertura')::boolean, false) or v.data_abertura is null)
     and (e.j ->> 'dias_abertura_maior_que' is null or v.dias_abertura > (e.j ->> 'dias_abertura_maior_que')::integer)
     and (e.j ->> 'contato_ha_dias_min' is null
          or v.ultimo_contato_em is null or v.dias_sem_contato >= (e.j ->> 'contato_ha_dias_min')::integer)
     and (e.j ->> 'contato_ha_dias_max' is null or v.dias_sem_contato <= (e.j ->> 'contato_ha_dias_max')::integer)
     and (not coalesce((e.j ->> 'sem_contato')::boolean, false) or v.ultimo_contato_em is null)
     and (not coalesce((e.j ->> 'sem_contato_principal')::boolean, false) or v.contato_id is null)
     and (e.j -> 'setores' is null or v.setor = any (array(select jsonb_array_elements_text(e.j -> 'setores'))))
     and (e.j -> 'portes' is null or v.porte = any (array(select jsonb_array_elements_text(e.j -> 'portes'))))
     and (not coalesce((e.j ->> 'sem_empresa')::boolean, false) or v.conta_nome is null)
     and (e.j -> 'empresas' is null or v.conta_nome = any (array(select jsonb_array_elements_text(e.j -> 'empresas'))))
     and (e.j -> 'produtos' is null or v.produto_nome = any (array(select jsonb_array_elements_text(e.j -> 'produtos'))))
     and (e.j -> 'series' is null or v.serie = any (array(select jsonb_array_elements_text(e.j -> 'series'))))
     and (e.j -> 'vendedores' is null or v.vendedor_nome = any (array(select jsonb_array_elements_text(e.j -> 'vendedores'))))
     and (e.j -> 'managers' is null or v.manager_nome = any (array(select jsonb_array_elements_text(e.j -> 'managers'))))
     and (e.j -> 'regioes' is null or v.regiao = any (array(select jsonb_array_elements_text(e.j -> 'regioes'))))
     and (e.j -> 'acoes' is null or v.acao_sugerida = any (array(select jsonb_array_elements_text(e.j -> 'acoes'))))
     and (e.j ->> 'fechamento_de' is null or v.close_date >= (e.j ->> 'fechamento_de')::date)
     and (e.j ->> 'fechamento_ate' is null or v.close_date <= (e.j ->> 'fechamento_ate')::date)
     and (e.j ->> 'valor_min' is null or coalesce(v.valor_esperado, v.close_value) >= (e.j ->> 'valor_min')::integer)
     and (e.j -> 'tags' is null or exists (
            select 1 from acao_deal_tags dt
             where dt.opportunity_id = v.opportunity_id and dt.removida_em is null
               and dt.tag_id = any (array(select (jsonb_array_elements_text(e.j -> 'tags'))::bigint))))
     and (not coalesce((e.j ->> 'sem_tag')::boolean, false) or jsonb_array_length(v.tags) = 0)
     and (not coalesce((e.j ->> 'com_comentario')::boolean, false) or v.comentarios > 0)
     and (e.j ->> 'contem' is null or (
            v.nome ilike '%' || (e.j ->> 'contem') || '%'
            or v.produto_nome ilike '%' || (e.j ->> 'contem') || '%'
            or v.conta_nome ilike '%' || (e.j ->> 'contem') || '%'
            or v.vendedor_nome ilike '%' || (e.j ->> 'contem') || '%'
            or v.opportunity_id ilike '%' || (e.j ->> 'contem') || '%'
            or v.tags::text ilike '%' || (e.j ->> 'contem') || '%'
            or exists (select 1 from acao_comentarios co
                        where co.opportunity_id = v.opportunity_id and co.removido_em is null
                          and co.texto ilike '%' || (e.j ->> 'contem') || '%')))
$$;
comment on function core_filtrar_deals(jsonb, jsonb) is 'Etiquetas do interpretador -> filtro. Chaves aceitas listadas no README da pasta db.';

create function core_buscar_deals(p_etiquetas jsonb, p_escopo jsonb, p_ordem text default 'nota',
                                  p_limite integer default 50, p_cursor text default null)
returns jsonb
language plpgsql stable
set search_path = public
as $$
declare
  v_ordem text := coalesce(p_ordem, 'nota');
  v_limite integer := least(greatest(coalesce(p_limite, 50), 1), 200);
  v_offset integer := coalesce(nullif(p_cursor, '')::integer, 0);
  v_total integer;
  v_linhas jsonb;
begin
  if v_ordem not in ('nota', 'valor', 'dias_sem_contato', 'dias_abertura', 'data_abertura',
                     'ultimo_contato', 'fechamento', 'vendedor', 'lead', 'padrao_leads') then
    raise exception using errcode = 'G4422', message = 'ordem_invalida';
  end if;

  select count(*) into v_total from core_filtrar_deals(p_etiquetas, p_escopo);

  select coalesce(jsonb_agg(to_jsonb(x) - 'ordem_linha' order by x.ordem_linha), '[]'::jsonb)
    into v_linhas
    from (
      select f.*,
             row_number() over (order by
               case when v_ordem = 'padrao_leads' then (not f.aberto)::integer end asc nulls last,
               case when v_ordem in ('nota', 'padrao_leads') then f.score end desc nulls last,
               case when v_ordem = 'padrao_leads' then f.close_date end desc nulls last,
               case when v_ordem = 'valor' then coalesce(f.valor_esperado, f.close_value) end desc nulls last,
               case when v_ordem = 'dias_sem_contato' then f.dias_sem_contato end desc nulls first,
               case when v_ordem = 'dias_abertura' then f.dias_abertura end desc nulls last,
               case when v_ordem = 'data_abertura' then f.data_abertura end desc nulls last,
               case when v_ordem = 'ultimo_contato' then f.ultimo_contato_em end desc nulls last,
               case when v_ordem = 'fechamento' then f.close_date end desc nulls last,
               case when v_ordem = 'vendedor' then f.vendedor_nome end asc,
               case when v_ordem = 'lead' then f.nome end asc,
               f.opportunity_id) as ordem_linha
        from core_filtrar_deals(p_etiquetas, p_escopo) f
    ) x
   where x.ordem_linha > v_offset and x.ordem_linha <= v_offset + v_limite;

  return jsonb_build_object(
    'linhas', v_linhas,
    'total', v_total,
    'proximo_cursor', case when v_offset + v_limite < v_total then (v_offset + v_limite)::text end);
end;
$$;

create function core_resumir_colunas(p_etiquetas jsonb, p_escopo jsonb) returns jsonb
language sql stable
set search_path = public
as $$
  select jsonb_agg(jsonb_build_object('estagio', c.estagio,
                                      'quantidade', coalesce(r.quantidade, 0),
                                      'valor_esperado', coalesce(r.valor, 0)) order by c.ordem)
    from (values ('Prospecting', 1), ('Engaging', 2)) as c (estagio, ordem)
    left join (
      select f.estagio, count(*) as quantidade, sum(f.valor_esperado) as valor
        from core_filtrar_deals(p_etiquetas, p_escopo) f
       group by f.estagio
    ) r on r.estagio = c.estagio
$$;

-- ================================================================ leitura: Painel
create function core_painel_numeros(p_escopo jsonb) returns jsonb
language sql stable
set search_path = public
as $$
  with s as (
    select coalesce(sum(leads_novos_hoje), 0) as leads_novos_hoje,
           coalesce(sum(leads_novos_30d), 0) as leads_novos_30d,
           coalesce(sum(leads_novos_30d_antes), 0) as leads_novos_30d_antes,
           coalesce(sum(em_negociacao_qtd), 0) as em_negociacao_qtd,
           coalesce(sum(em_negociacao_valor), 0) as em_negociacao_valor,
           coalesce(sum(ganhos_hoje_qtd), 0) as ganhos_hoje_qtd,
           coalesce(sum(ganhos_hoje_valor), 0) as ganhos_hoje_valor,
           coalesce(sum(ganhos_30d_qtd), 0) as ganhos_30d_qtd,
           coalesce(sum(ganhos_30d_valor), 0) as ganhos_30d_valor,
           coalesce(sum(ganhos_30d_antes_qtd), 0) as ganhos_30d_antes_qtd,
           coalesce(sum(ganhos_30d_antes_valor), 0) as ganhos_30d_antes_valor,
           coalesce(sum(perdidos_30d_qtd), 0) as perdidos_30d_qtd,
           coalesce(sum(perdidos_30d_antes_qtd), 0) as perdidos_30d_antes_qtd,
           coalesce(sum(pipeline_aberto_valor), 0) as pipeline_aberto_valor,
           coalesce(bool_or(pipeline_pelo_preco_tabela), true) as pipeline_pelo_preco_tabela,
           coalesce(sum(total_leads), 0) as total_leads,
           coalesce(sum(em_risco_qtd), 0) as em_risco_qtd,
           coalesce(sum(esfriou_qtd), 0) as esfriou_qtd
      from core_painel_janelas
     where vendedor_nome in (select core_escopo_vendedores(coalesce(p_escopo, '{}'::jsonb)))
  )
  select to_jsonb(s) || jsonb_build_object(
           'data_referencia', config_data_negocio(),
           'leads_novos_variacao_pct', case when s.leads_novos_30d_antes > 0
                then round((s.leads_novos_30d - s.leads_novos_30d_antes) * 100.0 / s.leads_novos_30d_antes, 1) end,
           'ganhos_variacao_pct', case when s.ganhos_30d_antes_qtd > 0
                then round((s.ganhos_30d_qtd - s.ganhos_30d_antes_qtd) * 100.0 / s.ganhos_30d_antes_qtd, 1) end,
           'receita_variacao_pct', case when s.ganhos_30d_antes_valor > 0
                then round((s.ganhos_30d_valor - s.ganhos_30d_antes_valor) * 100.0 / s.ganhos_30d_antes_valor, 1) end,
           'conversao_30d_pct', case when s.ganhos_30d_qtd + s.perdidos_30d_qtd > 0
                then round(s.ganhos_30d_qtd * 100.0 / (s.ganhos_30d_qtd + s.perdidos_30d_qtd), 1) end,
           'conversao_30d_antes_pct', case when s.ganhos_30d_antes_qtd + s.perdidos_30d_antes_qtd > 0
                then round(s.ganhos_30d_antes_qtd * 100.0 / (s.ganhos_30d_antes_qtd + s.perdidos_30d_antes_qtd), 1) end)
    from s
$$;

create function core_painel_funil(p_escopo jsonb) returns jsonb
language sql stable
set search_path = public
as $$
  select jsonb_agg(jsonb_build_object('estagio', c.estagio,
                                      'quantidade', coalesce(r.quantidade, 0),
                                      'valor', coalesce(r.valor, 0)) order by c.ordem)
    from (values ('Prospecting', 1), ('Engaging', 2), ('Won', 3), ('Lost', 4)) as c (estagio, ordem)
    left join (
      select v.estagio,
             count(*) as quantidade,
             sum(case when v.estagio = 'Won' then v.close_value
                      when v.estagio = 'Lost' then v.preco_tabela
                      else v.valor_esperado end) as valor
        from core_deals_visao v
       where v.vendedor_nome in (select core_escopo_vendedores(coalesce(p_escopo, '{}'::jsonb)))
       group by v.estagio
    ) r on r.estagio = c.estagio
$$;

-- ================================================================ leitura: linha do tempo do modal
create function core_linha_do_tempo(p_opportunity_id text)
returns table (data_negocio date, momento timestamptz, tipo text, detalhe jsonb,
               usuario_id bigint, usuario_nome text, desfeito boolean, referencia text)
language sql stable
set search_path = public
as $$
  with d as (select * from core_deals where opportunity_id = p_opportunity_id),
  mudancas as (
    select a.*,
           (select jsonb_object_agg(k, jsonb_build_object('de', a.antes -> k, 'para', a.depois -> k))
              from jsonb_object_keys(a.depois) k
             where a.antes -> k is distinct from a.depois -> k
               and k not in ('atualizado_em', 'atualizado_por', 'ultimo_contato_em')) as campos
      from system_auditoria a
     where a.tabela = 'core_deals' and a.registro_id = p_opportunity_id and a.operacao = 'update'
  )
  -- dataset: abertura e encerramento que não vieram do CRM
  select d.engage_date, null::timestamptz, 'aberto', jsonb_build_object('origem', 'dataset'),
         null::bigint, null::text, false, null::text
    from d where d.engage_date is not null and d.criado_em is null
  union all
  select d.close_date, null, case when d.estagio = 'Won' then 'ganho' else 'perdido' end,
         jsonb_build_object('origem', 'dataset', 'close_value', d.close_value), null, null, false, null
    from d
   where d.close_date is not null and d.criado_em is null
     and not exists (select 1 from mudancas m where m.campos ? 'estagio')
  -- criado no CRM ou importado
  union all
  select a.data_negocio, d.criado_em, case when d.importacao_id is null then 'criado' else 'importado' end,
         jsonb_build_object('importacao_id', d.importacao_id), d.criado_por, u.nome_exibicao, false, null
    from d
    left join system_auditoria a on a.tabela = 'core_deals' and a.registro_id = d.opportunity_id and a.operacao = 'insert'
    left join config_usuarios u on u.id = d.criado_por
   where d.criado_em is not null
  -- mudanças no deal (estágio, encerramento, reabertura, nome, empresa, contato, vendedor)
  union all
  select m.data_negocio, m.criado_em,
         case when m.campos ? 'estagio' then 'estagio' else 'alteracao' end,
         m.campos, m.usuario_id, u.nome_exibicao, false, m.id::text
    from mudancas m
    left join config_usuarios u on u.id = m.usuario_id
   where m.campos is not null
  -- tags aplicadas e removidas
  union all
  select a.data_negocio, a.criado_em,
         case when a.operacao = 'insert' then 'tag_aplicada' else 'tag_removida' end,
         jsonb_build_object('tag_id', a.depois -> 'tag_id', 'nome', t.nome),
         a.usuario_id, u.nome_exibicao, false, a.id::text
    from system_auditoria a
    left join config_tags t on t.id = (a.depois ->> 'tag_id')::bigint
    left join config_usuarios u on u.id = a.usuario_id
   where a.tabela = 'acao_deal_tags' and a.depois ->> 'opportunity_id' = p_opportunity_id
     and (a.operacao = 'insert' or (a.antes ->> 'removida_em' is null and a.depois ->> 'removida_em' is not null))
  -- ações (Liguei, Requalifiquei, Desisti, prioridades) — as desfeitas aparecem riscadas
  union all
  select r.data_negocio, r.criado_em, r.acao, jsonb_build_object('nota', r.nota),
         r.usuario_id, u.nome_exibicao, r.desfeita_em is not null, r.id::text
    from acao_registros r
    left join config_usuarios u on u.id = r.usuario_id
   where r.opportunity_id = p_opportunity_id
  -- comentários não apagados
  union all
  select c.data_negocio, c.criado_em, 'comentario',
         jsonb_build_object('texto', c.texto, 'editado', c.editado_em is not null),
         c.usuario_id, u.nome_exibicao, false, c.id::text
    from acao_comentarios c
    left join config_usuarios u on u.id = c.usuario_id
   where c.opportunity_id = p_opportunity_id and c.removido_em is null
  -- atribuições (roteamento e reatribuição)
  union all
  select t.data_negocio, t.criado_em, t.origem,
         jsonb_build_object('de', t.vendedor_de, 'para', t.vendedor_para, 'motivo', t.motivo),
         t.usuario_id, u.nome_exibicao, false, t.id::text
    from acao_atribuicoes t
    left join config_usuarios u on u.id = t.usuario_id
   where t.opportunity_id = p_opportunity_id
   order by 1 nulls last, 2 nulls first
$$;

-- ================================================================ roteamento de lead novo
create function core_rotear_lead(p_produto_nome text, p_conta_nome text default null) returns jsonb
language plpgsql stable
set search_path = public
as $$
declare
  v_exec bigint := config_execucao_ativa();
  v_min integer := config_inteiro('roteamento_min_casos', 10);
  v_teto integer := config_inteiro('roteamento_teto_abertos', 200);
  v_atributos jsonb;
  r record;
begin
  -- atributos do lead que podem casar com um cohort do vendedor (mesmas dimensões de score_vendedor_cohorts)
  select jsonb_build_object('produto', pr.nome, 'serie', pr.serie) into v_atributos
    from core_produtos pr where pr.nome = p_produto_nome;
  if v_atributos is null then
    raise exception using errcode = 'G4422', message = 'produto_inexistente';
  end if;
  if p_conta_nome is not null then
    select v_atributos || jsonb_strip_nulls(jsonb_build_object(
             'setor', c.setor, 'porte', c.porte, 'empresa', c.nome,
             'sede', case when c.pais = 'United States' then 'EUA' when c.pais is not null then 'fora dos EUA' end))
      into v_atributos
      from core_contas c where c.nome = p_conta_nome;
  end if;

  -- 1) vendedor de maior FIT no cohort do lead, com mínimo de casos e abaixo do teto de abertos
  if v_exec is not null then
    select c.vendedor_nome, c.dimensao, c.valor, c.n, c.taxa_encolhida, ab.abertos
      into r
      from score_vendedor_cohorts c
      join core_vendedores v on v.nome = c.vendedor_nome and v.ativo
      cross join lateral (
        select count(*) as abertos from core_deals d
         where d.vendedor_nome = c.vendedor_nome and d.estagio in ('Prospecting', 'Engaging')) ab
     where c.execucao_id = v_exec
       and c.n >= v_min
       and c.taxa_encolhida is not null
       and v_atributos ->> c.dimensao = c.valor
       and ab.abertos < v_teto
     order by c.taxa_encolhida desc, ab.abertos asc, c.vendedor_nome
     limit 1;
    if found then
      return jsonb_build_object(
        'vendedor_nome', r.vendedor_nome, 'origem', 'roteamento', 'execucao_id', v_exec, 'fit', r.taxa_encolhida,
        'criterio', jsonb_build_object('dimensao', r.dimensao, 'valor', r.valor, 'n', r.n,
                                       'abertos', r.abertos, 'min_casos', v_min, 'teto_abertos', v_teto));
    end if;
  end if;

  -- 2) reserva: sem nota ou sem candidato, vai para o vendedor ativo com menos deals abertos
  select v.nome, count(d.opportunity_id) as abertos into r
    from core_vendedores v
    left join core_deals d on d.vendedor_nome = v.nome and d.estagio in ('Prospecting', 'Engaging')
   where v.ativo
   group by v.nome
   order by count(d.opportunity_id) asc, v.nome
   limit 1;
  if not found then
    raise exception using errcode = 'G4422', message = 'sem_vendedor_ativo';
  end if;
  return jsonb_build_object(
    'vendedor_nome', r.nome, 'origem', 'roteamento_reserva', 'execucao_id', v_exec, 'fit', null,
    'criterio', jsonb_build_object('motivo', case when v_exec is null then 'sem_execucao_ativa' else 'sem_candidato' end,
                                   'abertos', r.abertos, 'min_casos', v_min, 'teto_abertos', v_teto));
end;
$$;

-- ================================================================ escrita: deals
create function core_criar_deal(p_usuario_id bigint, p_correlation_id uuid, p_produto_nome text,
                                p_vendedor_nome text default null, p_conta_nome text default null,
                                p_nome text default null, p_estagio text default 'Prospecting',
                                p_data_abertura date default null, p_contato_id bigint default null)
returns jsonb
language plpgsql
set search_path = public
as $$
declare
  v_papel text := system_definir_contexto(p_usuario_id, p_correlation_id);
  v_hoje date := config_data_negocio();
  v_id text := core_gerar_opportunity_id();
  v_rota jsonb;
  v_vendedor text := p_vendedor_nome;
begin
  if p_estagio not in ('Prospecting', 'Engaging') then
    raise exception using errcode = 'G4422', message = 'estagio_inicial_invalido';
  end if;
  if not exists (select 1 from core_produtos where nome = p_produto_nome) then
    raise exception using errcode = 'G4422', message = 'produto_inexistente';
  end if;
  if p_conta_nome is not null and not exists (select 1 from core_contas where nome = p_conta_nome) then
    raise exception using errcode = 'G4422', message = 'empresa_inexistente';
  end if;
  if v_vendedor is null then
    v_rota := core_rotear_lead(p_produto_nome, p_conta_nome);
    v_vendedor := v_rota ->> 'vendedor_nome';
  elsif not exists (select 1 from core_vendedores where nome = v_vendedor) then
    raise exception using errcode = 'G4422', message = 'vendedor_inexistente';
  end if;

  insert into core_deals (opportunity_id, nome, vendedor_nome, produto_nome, conta_nome, contato_id, estagio,
                          data_abertura, criado_em, criado_por)
  values (v_id,
          coalesce(nullif(trim(p_nome), ''), coalesce(p_conta_nome, 'Sem empresa') || ' · ' || p_produto_nome),
          v_vendedor, p_produto_nome, p_conta_nome, p_contato_id, p_estagio,
          case when p_estagio = 'Engaging' then coalesce(p_data_abertura, v_hoje) end,
          now(), p_usuario_id);

  if v_rota is not null then
    insert into acao_atribuicoes (opportunity_id, vendedor_de, vendedor_para, origem, usuario_id, execucao_id,
                                  fit, criterio, data_negocio, correlation_id)
    values (v_id, null, v_vendedor, v_rota ->> 'origem', p_usuario_id, (v_rota ->> 'execucao_id')::bigint,
            (v_rota ->> 'fit')::numeric, v_rota -> 'criterio', v_hoje, p_correlation_id);
    if v_rota ->> 'origem' = 'roteamento_reserva' then
      insert into system_eventos (tipo, detalhe, usuario_id, correlation_id)
      values ('roteamento_reserva', jsonb_build_object('opportunity_id', v_id) || (v_rota -> 'criterio'),
              p_usuario_id, p_correlation_id);
    end if;
  end if;

  return jsonb_build_object('opportunity_id', v_id, 'vendedor_nome', v_vendedor, 'atribuicao', v_rota,
                            'atualizado_em', (select atualizado_em from core_deals where opportunity_id = v_id));
end;
$$;

create function core_importar_deals(p_usuario_id bigint, p_correlation_id uuid, p_arquivo_nome text,
                                    p_arquivo_sha256 text, p_linhas jsonb, p_somente_conferir boolean default true)
returns jsonb
language plpgsql
set search_path = public
as $$
declare
  v_max integer := config_inteiro('importacao_max_linhas', 10000);
  v_grafias jsonb := coalesce(config_valor('importacao_grafias'), '{}'::jsonb);
  v_item record;
  v_linha integer;
  v_id text; v_vendedor text; v_produto text; v_conta text; v_estagio text;
  v_engage date; v_close date; v_valor integer;
  v_motivo text;
  v_vistos text[] := '{}';
  v_prontas jsonb := '[]'::jsonb;
  v_recusas jsonb := '[]'::jsonb;
  v_ja_existiam integer := 0;
  v_total integer;
  v_importacao bigint;
  v_inseridos integer := 0;
  v_n integer;
begin
  if jsonb_typeof(p_linhas) is distinct from 'array' then
    raise exception using errcode = 'G4422', message = 'linhas_invalidas';
  end if;
  v_total := jsonb_array_length(p_linhas);
  if v_total > v_max then
    raise exception using errcode = 'G4422', message = 'arquivo_acima_do_limite', detail = v_max::text;
  end if;

  for v_item in select value as l, ordinality as ord from jsonb_array_elements(p_linhas) with ordinality loop
    v_linha := coalesce((v_item.l ->> 'linha')::integer, v_item.ord::integer + 1);  -- +1: o cabeçalho é a linha 1
    v_motivo := null;
    v_id := upper(trim(v_item.l ->> 'opportunity_id'));
    v_estagio := trim(v_item.l ->> 'deal_stage');
    v_valor := null;

    -- normalização igual à da limpeza: espaços, maiúsculas e grafias conhecidas
    select nome into v_vendedor from core_vendedores where lower(nome) = lower(trim(v_item.l ->> 'sales_agent'));
    v_produto := trim(v_item.l ->> 'product');
    v_produto := coalesce(v_grafias ->> v_produto, v_produto);
    select nome into v_produto from core_produtos where lower(nome) = lower(v_produto);
    v_conta := nullif(trim(v_item.l ->> 'account'), '');
    if v_conta is not null then
      select nome into v_conta from core_contas where lower(nome) = lower(trim(v_item.l ->> 'account'));
    end if;

    begin
      v_engage := nullif(trim(v_item.l ->> 'engage_date'), '')::date;
      v_close := nullif(trim(v_item.l ->> 'close_date'), '')::date;
      v_valor := round(nullif(trim(v_item.l ->> 'close_value'), '')::numeric)::integer;
    exception when others then
      v_motivo := 'data ou valor em formato inválido (use AAAA-MM-DD e número)';
    end;

    if v_motivo is null then
      v_motivo := case
        when v_id is null or v_id !~ '^[A-Z0-9]{8}$' then 'opportunity_id ausente ou fora do formato (8 letras ou números)'
        when v_id = any (v_vistos) then 'opportunity_id repetido no arquivo'
        when v_vendedor is null then format('o vendedor "%s" não está no time', v_item.l ->> 'sales_agent')
        when v_produto is null then format('o produto "%s" não está no catálogo', v_item.l ->> 'product')
        when nullif(trim(v_item.l ->> 'account'), '') is not null and v_conta is null
          then format('a empresa "%s" não está cadastrada. Cadastre a empresa ou deixe a coluna vazia', v_item.l ->> 'account')
        when v_estagio is null or v_estagio not in ('Prospecting', 'Engaging', 'Won', 'Lost') then 'deal_stage inválido'
        when v_estagio <> 'Prospecting' and v_estagio <> 'Lost' and v_engage is null then 'engage_date obrigatória fora de Prospecting'
        when v_estagio in ('Won', 'Lost') and v_close is null then 'deal encerrado sem close_date'
        when v_estagio in ('Prospecting', 'Engaging') and (v_close is not null or v_valor is not null) then 'deal aberto com dados de fechamento'
        when v_close is not null and v_engage is not null and v_close < v_engage then 'close_date anterior a engage_date'
        when v_estagio = 'Won' and coalesce(v_valor, 0) <= 0 then 'deal ganho sem valor de fechamento'
        when v_estagio = 'Lost' and coalesce(v_valor, 0) <> 0 then 'deal perdido com valor de fechamento'
      end;
    end if;

    if v_id is not null then
      v_vistos := v_vistos || v_id;
    end if;
    if v_motivo is not null then
      v_recusas := v_recusas || jsonb_build_object('linha', v_linha, 'motivo', v_motivo);
    elsif exists (select 1 from core_deals where opportunity_id = v_id) then
      v_ja_existiam := v_ja_existiam + 1;
    else
      v_prontas := v_prontas || jsonb_build_object(
        'opportunity_id', v_id, 'vendedor_nome', v_vendedor, 'produto_nome', v_produto, 'conta_nome', v_conta,
        'estagio', v_estagio, 'engage_date', v_engage, 'close_date', v_close,
        'close_value', case when v_estagio = 'Won' then v_valor when v_estagio = 'Lost' then 0 end);
    end if;
  end loop;

  if p_somente_conferir then
    return jsonb_build_object('etapa', 'conferir', 'linhas_total', v_total, 'prontas', jsonb_array_length(v_prontas),
                              'ja_existiam', v_ja_existiam, 'recusadas', jsonb_array_length(v_recusas),
                              'recusas', v_recusas);
  end if;

  perform system_definir_contexto(p_usuario_id, p_correlation_id);
  insert into system_importacoes (usuario_id, arquivo_nome, arquivo_sha256, linhas_total, recusadas, recusas, correlation_id)
  values (p_usuario_id, p_arquivo_nome, p_arquivo_sha256, v_total, jsonb_array_length(v_recusas), v_recusas, p_correlation_id)
  returning id into v_importacao;

  for v_item in select value as l from jsonb_array_elements(v_prontas) loop
    insert into core_deals (opportunity_id, nome, vendedor_nome, produto_nome, conta_nome, estagio, engage_date,
                            data_abertura, close_date, close_value, criado_em, criado_por, importacao_id)
    values (v_item.l ->> 'opportunity_id',
            coalesce(v_item.l ->> 'conta_nome', 'Sem empresa') || ' · ' || (v_item.l ->> 'produto_nome'),
            v_item.l ->> 'vendedor_nome', v_item.l ->> 'produto_nome', v_item.l ->> 'conta_nome', v_item.l ->> 'estagio',
            (v_item.l ->> 'engage_date')::date, (v_item.l ->> 'engage_date')::date,
            (v_item.l ->> 'close_date')::date, (v_item.l ->> 'close_value')::integer,
            now(), p_usuario_id, v_importacao)
    on conflict (opportunity_id) do nothing;
    get diagnostics v_n = row_count;
    v_inseridos := v_inseridos + v_n;
  end loop;

  update system_importacoes
     set aceitas = v_inseridos,
         ja_existiam = v_ja_existiam + (jsonb_array_length(v_prontas) - v_inseridos)
   where id = v_importacao;

  return jsonb_build_object('etapa', 'importar', 'importacao_id', v_importacao, 'linhas_total', v_total,
                            'aceitas', v_inseridos,
                            'ja_existiam', v_ja_existiam + (jsonb_array_length(v_prontas) - v_inseridos),
                            'recusadas', jsonb_array_length(v_recusas), 'recusas', v_recusas);
end;
$$;

create function core_encerrar_deal(p_usuario_id bigint, p_correlation_id uuid, p_opportunity_id text,
                                   p_versao timestamptz, p_resultado text, p_valor integer default null,
                                   p_motivo text default null, p_motivo_detalhe text default null)
returns jsonb
language plpgsql
set search_path = public
as $$
declare
  v_papel text := system_definir_contexto(p_usuario_id, p_correlation_id);
  v_deal core_deals%rowtype;
  v_motivo config_motivos_perda%rowtype;
begin
  select * into v_deal from core_deals where opportunity_id = p_opportunity_id for update;
  if not found then
    raise exception using errcode = 'G4404', message = 'deal_nao_encontrado';
  end if;
  if v_deal.estagio not in ('Prospecting', 'Engaging') then
    raise exception using errcode = 'G4422', message = 'deal_ja_encerrado';
  end if;

  if p_resultado = 'Won' then
    if v_deal.estagio <> 'Engaging' then
      raise exception using errcode = 'G4422', message = 'ganho_exige_negociacao';
    end if;
    if p_valor is null or p_valor <= 0 then
      raise exception using errcode = 'G4422', message = 'valor_de_fechamento_obrigatorio';
    end if;
  elsif p_resultado = 'Lost' then
    if p_motivo is null and coalesce((config_valor('motivo_perda_obrigatorio') #>> '{}')::boolean, true) then
      raise exception using errcode = 'G4422', message = 'motivo_de_perda_obrigatorio';
    end if;
    if p_motivo is not null then
      select * into v_motivo from config_motivos_perda where codigo = p_motivo and ativo;
      if not found then
        raise exception using errcode = 'G4422', message = 'motivo_de_perda_invalido';
      end if;
      if v_motivo.exige_detalhe and nullif(trim(p_motivo_detalhe), '') is null then
        raise exception using errcode = 'G4422', message = 'detalhe_do_motivo_obrigatorio';
      end if;
    end if;
  else
    raise exception using errcode = 'G4422', message = 'resultado_invalido';
  end if;

  if p_versao is not null then
    perform set_config('app.versao', p_versao::text, true);
  end if;
  update core_deals
     set estagio = p_resultado,
         close_date = config_data_negocio(),
         close_value = case when p_resultado = 'Won' then p_valor else 0 end,
         motivo_perda = case when p_resultado = 'Lost' then p_motivo end,
         motivo_perda_detalhe = case when p_resultado = 'Lost' then nullif(trim(p_motivo_detalhe), '') end
   where opportunity_id = p_opportunity_id;
  perform set_config('app.versao', '', true);

  return jsonb_build_object('opportunity_id', p_opportunity_id, 'estagio', p_resultado,
    'atualizado_em', (select atualizado_em from core_deals where opportunity_id = p_opportunity_id),
    'auditoria_id', (select max(id) from system_auditoria
                      where tabela = 'core_deals' and registro_id = p_opportunity_id and correlation_id = p_correlation_id));
end;
$$;

create function core_reabrir_deal(p_usuario_id bigint, p_correlation_id uuid, p_opportunity_id text,
                                  p_versao timestamptz)
returns jsonb
language plpgsql
set search_path = public
as $$
declare
  v_papel text := system_definir_contexto(p_usuario_id, p_correlation_id);
  v_deal core_deals%rowtype;
begin
  if v_papel not in ('manager', 'admin') then
    raise exception using errcode = 'G4403', message = 'reabrir_so_manager_ou_admin';
  end if;
  select * into v_deal from core_deals where opportunity_id = p_opportunity_id for update;
  if not found then
    raise exception using errcode = 'G4404', message = 'deal_nao_encontrado';
  end if;
  if v_deal.estagio not in ('Won', 'Lost') then
    raise exception using errcode = 'G4422', message = 'deal_nao_esta_encerrado';
  end if;

  if p_versao is not null then
    perform set_config('app.versao', p_versao::text, true);
  end if;
  update core_deals
     set estagio = 'Engaging',
         data_abertura = coalesce(data_abertura, config_data_negocio()),
         close_date = null,
         close_value = null,
         motivo_perda = null,
         motivo_perda_detalhe = null
   where opportunity_id = p_opportunity_id;
  perform set_config('app.versao', '', true);

  return jsonb_build_object('opportunity_id', p_opportunity_id, 'estagio', 'Engaging',
    'atualizado_em', (select atualizado_em from core_deals where opportunity_id = p_opportunity_id),
    'auditoria_id', (select max(id) from system_auditoria
                      where tabela = 'core_deals' and registro_id = p_opportunity_id and correlation_id = p_correlation_id));
end;
$$;

create function core_mudar_estagio(p_usuario_id bigint, p_correlation_id uuid, p_opportunity_id text,
                                   p_versao timestamptz, p_para text, p_valor integer default null,
                                   p_motivo text default null, p_motivo_detalhe text default null,
                                   p_data_abertura date default null)
returns jsonb
language plpgsql
set search_path = public
as $$
declare
  v_papel text := system_definir_contexto(p_usuario_id, p_correlation_id);
  v_de text;
begin
  select estagio into v_de from core_deals where opportunity_id = p_opportunity_id for update;
  if v_de is null then
    raise exception using errcode = 'G4404', message = 'deal_nao_encontrado';
  end if;
  if v_de = p_para then
    raise exception using errcode = 'G4422', message = 'mesmo_estagio';
  end if;

  -- tabela 2.6 da ESPEC-TELAS
  if v_de = 'Prospecting' and p_para = 'Engaging' then
    if p_versao is not null then
      perform set_config('app.versao', p_versao::text, true);
    end if;
    update core_deals
       set estagio = 'Engaging', data_abertura = coalesce(p_data_abertura, config_data_negocio())
     where opportunity_id = p_opportunity_id;
    perform set_config('app.versao', '', true);
    return jsonb_build_object('opportunity_id', p_opportunity_id, 'estagio', 'Engaging',
      'atualizado_em', (select atualizado_em from core_deals where opportunity_id = p_opportunity_id),
      'auditoria_id', (select max(id) from system_auditoria
                        where tabela = 'core_deals' and registro_id = p_opportunity_id and correlation_id = p_correlation_id));
  elsif (v_de = 'Engaging' and p_para in ('Won', 'Lost')) or (v_de = 'Prospecting' and p_para = 'Lost') then
    return core_encerrar_deal(p_usuario_id, p_correlation_id, p_opportunity_id, p_versao, p_para,
                              p_valor, p_motivo, p_motivo_detalhe);
  elsif v_de in ('Won', 'Lost') and p_para = 'Engaging' then
    return core_reabrir_deal(p_usuario_id, p_correlation_id, p_opportunity_id, p_versao);
  end if;
  raise exception using errcode = 'G4422', message = 'transicao_invalida',
    detail = jsonb_build_object('de', v_de, 'para', p_para)::text;
end;
$$;

create function core_desfazer_mudanca(p_usuario_id bigint, p_correlation_id uuid, p_auditoria_id bigint)
returns jsonb
language plpgsql
set search_path = public
as $$
declare
  v_papel text := system_definir_contexto(p_usuario_id, p_correlation_id);
  v_aud system_auditoria%rowtype;
  v_atual timestamptz;
begin
  select * into v_aud from system_auditoria where id = p_auditoria_id;
  if not found or v_aud.tabela <> 'core_deals' or v_aud.operacao <> 'update' then
    raise exception using errcode = 'G4404', message = 'mudanca_nao_encontrada';
  end if;
  if v_aud.usuario_id <> p_usuario_id then
    raise exception using errcode = 'G4403', message = 'so_o_autor_desfaz';
  end if;
  if v_aud.criado_em < now() - make_interval(secs => config_inteiro('desfazer_segundos', 10)) then
    raise exception using errcode = 'G4422', message = 'prazo_para_desfazer_encerrado';
  end if;
  select atualizado_em into v_atual from core_deals where opportunity_id = v_aud.registro_id for update;
  if v_atual is distinct from (v_aud.depois ->> 'atualizado_em')::timestamptz then
    raise exception using errcode = 'G4409', message = 'conflito_versao';
  end if;
  perform core_restaurar_deal(v_aud.registro_id, v_aud.antes);
  return jsonb_build_object('opportunity_id', v_aud.registro_id, 'estagio', v_aud.antes ->> 'estagio',
    'atualizado_em', (select atualizado_em from core_deals where opportunity_id = v_aud.registro_id));
end;
$$;

create function core_atualizar_deal(p_usuario_id bigint, p_correlation_id uuid, p_opportunity_id text,
                                    p_versao timestamptz, p_campos jsonb)
returns jsonb
language plpgsql
set search_path = public
as $$
declare
  v_papel text := system_definir_contexto(p_usuario_id, p_correlation_id);
  v_chave text;
begin
  for v_chave in select jsonb_object_keys(coalesce(p_campos, '{}'::jsonb)) loop
    if v_chave not in ('nome', 'conta_nome', 'contato_id') then
      raise exception using errcode = 'G4422', message = 'campo_nao_editavel', detail = v_chave;
    end if;
  end loop;
  if p_campos ? 'nome' and char_length(trim(coalesce(p_campos ->> 'nome', ''))) not between 1 and 120 then
    raise exception using errcode = 'G4422', message = 'nome_invalido';
  end if;
  if p_campos ->> 'conta_nome' is not null
     and not exists (select 1 from core_contas where nome = p_campos ->> 'conta_nome') then
    raise exception using errcode = 'G4422', message = 'empresa_inexistente';
  end if;
  if not exists (select 1 from core_deals where opportunity_id = p_opportunity_id) then
    raise exception using errcode = 'G4404', message = 'deal_nao_encontrado';
  end if;

  if p_versao is not null then
    perform set_config('app.versao', p_versao::text, true);
  end if;
  update core_deals
     set nome       = case when p_campos ? 'nome' then trim(p_campos ->> 'nome') else nome end,
         conta_nome = case when p_campos ? 'conta_nome' then p_campos ->> 'conta_nome' else conta_nome end,
         contato_id = case when p_campos ? 'contato_id' then (p_campos ->> 'contato_id')::bigint else contato_id end
   where opportunity_id = p_opportunity_id;
  perform set_config('app.versao', '', true);

  return jsonb_build_object('opportunity_id', p_opportunity_id,
    'atualizado_em', (select atualizado_em from core_deals where opportunity_id = p_opportunity_id),
    'auditoria_id', (select max(id) from system_auditoria
                      where tabela = 'core_deals' and registro_id = p_opportunity_id and correlation_id = p_correlation_id));
end;
$$;

create function core_salvar_contato(p_usuario_id bigint, p_correlation_id uuid, p_contato_id bigint,
                                    p_dados jsonb, p_opportunity_id text default null,
                                    p_versao timestamptz default null)
returns jsonb
language plpgsql
set search_path = public
as $$
declare
  v_papel text := system_definir_contexto(p_usuario_id, p_correlation_id);
  v_id bigint := p_contato_id;
  v_conta text;
begin
  if p_opportunity_id is not null then
    select conta_nome into v_conta from core_deals where opportunity_id = p_opportunity_id;
    if not found then
      raise exception using errcode = 'G4404', message = 'deal_nao_encontrado';
    end if;
  end if;

  if (v_id is null or p_dados ? 'nome') and char_length(trim(coalesce(p_dados ->> 'nome', ''))) not between 1 and 120 then
    raise exception using errcode = 'G4422', message = 'contato_nome_invalido';
  end if;
  if nullif(trim(p_dados ->> 'email'), '') is not null
     and trim(p_dados ->> 'email') !~* '^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$' then
    raise exception using errcode = 'G4422', message = 'contato_email_invalido';
  end if;

  if v_id is null then
    insert into core_contatos (conta_nome, nome, cargo, email, telefone, criado_por)
    values (coalesce(p_dados ->> 'conta_nome', v_conta), trim(p_dados ->> 'nome'),
            nullif(trim(p_dados ->> 'cargo'), ''), nullif(trim(p_dados ->> 'email'), ''),
            nullif(trim(p_dados ->> 'telefone'), ''), p_usuario_id)
    returning id into v_id;
  else
    update core_contatos
       set nome       = case when p_dados ? 'nome' then trim(p_dados ->> 'nome') else nome end,
           cargo      = case when p_dados ? 'cargo' then nullif(trim(p_dados ->> 'cargo'), '') else cargo end,
           email      = case when p_dados ? 'email' then nullif(trim(p_dados ->> 'email'), '') else email end,
           telefone   = case when p_dados ? 'telefone' then nullif(trim(p_dados ->> 'telefone'), '') else telefone end,
           conta_nome = case when p_dados ? 'conta_nome' then p_dados ->> 'conta_nome' else conta_nome end,
           inativo_em = case when p_dados ? 'inativo'
                             then case when (p_dados ->> 'inativo')::boolean then coalesce(inativo_em, now()) end
                             else inativo_em end
     where id = v_id;
    if not found then
      raise exception using errcode = 'G4404', message = 'contato_nao_encontrado';
    end if;
  end if;

  if p_opportunity_id is not null then
    if p_versao is not null then
      perform set_config('app.versao', p_versao::text, true);
    end if;
    update core_deals set contato_id = v_id
     where opportunity_id = p_opportunity_id and contato_id is distinct from v_id;
    perform set_config('app.versao', '', true);
  end if;

  return jsonb_build_object('contato_id', v_id, 'opportunity_id', p_opportunity_id,
    'atualizado_em', (select atualizado_em from core_deals where opportunity_id = p_opportunity_id));
end;
$$;

create function core_reatribuir_deal(p_usuario_id bigint, p_correlation_id uuid, p_opportunity_id text,
                                     p_versao timestamptz, p_vendedor_para text, p_motivo text default null)
returns jsonb
language plpgsql
set search_path = public
as $$
declare
  v_papel text := system_definir_contexto(p_usuario_id, p_correlation_id);
  v_de text;
begin
  if v_papel not in ('manager', 'admin') then
    raise exception using errcode = 'G4403', message = 'reatribuir_so_manager_ou_admin';
  end if;
  select vendedor_nome into v_de from core_deals where opportunity_id = p_opportunity_id for update;
  if v_de is null then
    raise exception using errcode = 'G4404', message = 'deal_nao_encontrado';
  end if;
  if not exists (select 1 from core_vendedores where nome = p_vendedor_para) then
    raise exception using errcode = 'G4422', message = 'vendedor_inexistente';
  end if;
  if v_de = p_vendedor_para then
    raise exception using errcode = 'G4422', message = 'mesmo_vendedor';
  end if;

  if p_versao is not null then
    perform set_config('app.versao', p_versao::text, true);
  end if;
  update core_deals set vendedor_nome = p_vendedor_para where opportunity_id = p_opportunity_id;
  perform set_config('app.versao', '', true);

  insert into acao_atribuicoes (opportunity_id, vendedor_de, vendedor_para, origem, usuario_id,
                                execucao_id, motivo, data_negocio, correlation_id)
  values (p_opportunity_id, v_de, p_vendedor_para, 'reatribuicao', p_usuario_id,
          config_execucao_ativa(), nullif(trim(p_motivo), ''), config_data_negocio(), p_correlation_id);

  return jsonb_build_object('opportunity_id', p_opportunity_id, 'de', v_de, 'para', p_vendedor_para,
    'atualizado_em', (select atualizado_em from core_deals where opportunity_id = p_opportunity_id));
end;
$$;

-- ================================================================ escrita: ações
create function acao_registrar(p_usuario_id bigint, p_correlation_id uuid, p_opportunity_id text,
                               p_acao text, p_nota text default null)
returns jsonb
language plpgsql
set search_path = public
as $$
declare
  v_papel text := system_definir_contexto(p_usuario_id, p_correlation_id);
  v_estagio text;
  v_id bigint;
begin
  if p_acao not in ('liguei', 'requalifiquei', 'desisti', 'resposta_recebida') then
    raise exception using errcode = 'G4422', message = 'acao_invalida';
  end if;
  if char_length(p_nota) > 280 then
    raise exception using errcode = 'G4422', message = 'nota_acima_de_280';
  end if;
  select estagio into v_estagio from core_deals where opportunity_id = p_opportunity_id;
  if v_estagio is null then
    raise exception using errcode = 'G4404', message = 'deal_nao_encontrado';
  end if;
  if v_estagio not in ('Prospecting', 'Engaging') then
    raise exception using errcode = 'G4422', message = 'deal_ja_encerrado';
  end if;
  insert into acao_registros (opportunity_id, usuario_id, papel, execucao_id, acao, nota, data_negocio, correlation_id)
  values (p_opportunity_id, p_usuario_id, v_papel, config_execucao_ativa(), p_acao,
          nullif(trim(p_nota), ''), config_data_negocio(), p_correlation_id)
  returning id into v_id;
  return jsonb_build_object('registro_id', v_id);
end;
$$;

create function acao_desfazer(p_usuario_id bigint, p_correlation_id uuid, p_registro_id bigint)
returns jsonb
language plpgsql
set search_path = public
as $$
declare
  v_papel text := system_definir_contexto(p_usuario_id, p_correlation_id);
  v_desfeita timestamptz;
begin
  select desfeita_em into v_desfeita from acao_registros where id = p_registro_id for update;
  if not found then
    raise exception using errcode = 'G4404', message = 'registro_nao_encontrado';
  end if;
  if v_desfeita is not null then
    raise exception using errcode = 'G4422', message = 'registro_ja_desfeito';
  end if;
  update acao_registros set desfeita_em = now(), desfeita_por = p_usuario_id where id = p_registro_id;
  return jsonb_build_object('registro_id', p_registro_id, 'desfeito', true);
end;
$$;

create function acao_prioridades_do_dia(p_usuario_id bigint, p_correlation_id uuid) returns jsonb
language plpgsql
set search_path = public
as $$
declare
  v_papel text := system_definir_contexto(p_usuario_id, p_correlation_id);
  v_hoje date := config_data_negocio();
  v_usuario config_usuarios%rowtype;
  v_fila_max integer := config_inteiro('prioridades_fila_max', 50);
  v_dias_alerta integer := config_inteiro('dias_pulado_alerta', 3);
  v_tipos_contato text[] := array(select jsonb_array_elements_text(
                              coalesce(config_valor('acoes_contato'), '["liguei","requalifiquei"]'::jsonb)));
  v_itens jsonb;
  v_feitas integer;
  v_puladas integer;
begin
  select * into v_usuario from config_usuarios where id = p_usuario_id;
  if v_papel = 'sistema' then
    raise exception using errcode = 'G4403', message = 'usuario_sistema_sem_prioridades';
  end if;

  -- monta a fila na primeira abertura do dia; depois ela fica estável (ESPEC 4.5)
  if not exists (select 1 from acao_prioridades where usuario_id = p_usuario_id and data_negocio = v_hoje) then
    -- vendedor: maior nota; sem nota, super hot > em risco > maior preço de tabela.
    -- manager e admin (P17): deals em risco ou super hot do escopo, por valor.
    insert into acao_prioridades (usuario_id, data_negocio, posicao, opportunity_id)
    select p_usuario_id, v_hoje,
           row_number() over (order by c.chave1 desc nulls last, c.chave2 desc nulls last, c.opportunity_id),
           c.opportunity_id
      from (
        select v.opportunity_id,
               case when v_papel = 'vendedor' then v.score else v.valor_esperado end as chave1,
               case when v_papel = 'vendedor'
                    then (case v.icone when 'super_hot' then 3 when 'em_risco' then 2 else 1 end) * 1000000 + v.preco_tabela
                    else v.score end as chave2
          from core_deals_visao v
         where v.aberto
           and (   (v_papel = 'vendedor' and v.vendedor_nome = v_usuario.vendedor_nome)
                or (v_papel = 'manager' and v.manager_nome = v_usuario.manager_nome and v.icone in ('super_hot', 'em_risco'))
                or (v_papel = 'admin' and v.icone in ('super_hot', 'em_risco')))
         order by chave1 desc nulls last, chave2 desc nulls last, v.opportunity_id
         limit v_fila_max
      ) c;
  end if;

  select coalesce(jsonb_agg(jsonb_build_object(
           'posicao', p.posicao, 'opportunity_id', v.opportunity_id, 'nome', v.nome,
           'vendedor_nome', v.vendedor_nome, 'score', v.score, 'faixa_nota', v.faixa_nota,
           'icone', v.icone, 'valor_esperado', v.valor_esperado,
           'pulado_varios_dias', (select count(distinct r.data_negocio) from acao_registros r
                                   where r.opportunity_id = p.opportunity_id and r.usuario_id = p_usuario_id
                                     and r.acao = 'prioridade_pulada' and r.desfeita_em is null
                                     and r.data_negocio between v_hoje - v_dias_alerta and v_hoje - 1) >= v_dias_alerta)
           order by p.posicao), '[]'::jsonb)
    into v_itens
    from acao_prioridades p
    join core_deals_visao v on v.opportunity_id = p.opportunity_id
   where p.usuario_id = p_usuario_id and p.data_negocio = v_hoje and v.aberto
     and not exists (
       select 1 from acao_registros r
        where r.opportunity_id = p.opportunity_id and r.data_negocio = v_hoje and r.desfeita_em is null
          and ((r.usuario_id = p_usuario_id and r.acao in ('prioridade_feita', 'prioridade_pulada'))
               or r.acao = any (v_tipos_contato)));

  select count(*) filter (where acao = 'prioridade_feita'), count(*) filter (where acao = 'prioridade_pulada')
    into v_feitas, v_puladas
    from acao_registros
   where usuario_id = p_usuario_id and data_negocio = v_hoje and desfeita_em is null
     and acao in ('prioridade_feita', 'prioridade_pulada');

  return jsonb_build_object('data_negocio', v_hoje, 'itens', v_itens,
                            'feitas', v_feitas, 'puladas', v_puladas,
                            'meta', config_inteiro('meta_prioridades_dia', 10),
                            'visiveis', config_inteiro('prioridades_visiveis', 5));
end;
$$;

create function acao_marcar_prioridade(p_usuario_id bigint, p_correlation_id uuid, p_opportunity_id text,
                                       p_resultado text, p_nota text default null)
returns jsonb
language plpgsql
set search_path = public
as $$
declare
  v_papel text := system_definir_contexto(p_usuario_id, p_correlation_id);
  v_estagio text;
  v_id bigint;
begin
  if p_resultado not in ('feita', 'pulada') then
    raise exception using errcode = 'G4422', message = 'resultado_invalido';
  end if;
  if char_length(p_nota) > 280 then
    raise exception using errcode = 'G4422', message = 'nota_acima_de_280';
  end if;
  select estagio into v_estagio from core_deals where opportunity_id = p_opportunity_id;
  if v_estagio is null then
    raise exception using errcode = 'G4404', message = 'deal_nao_encontrado';
  end if;
  if v_estagio not in ('Prospecting', 'Engaging') then
    raise exception using errcode = 'G4422', message = 'deal_ja_encerrado';
  end if;
  insert into acao_registros (opportunity_id, usuario_id, papel, execucao_id, acao, nota, data_negocio, correlation_id)
  values (p_opportunity_id, p_usuario_id, v_papel, config_execucao_ativa(), 'prioridade_' || p_resultado,
          nullif(trim(p_nota), ''), config_data_negocio(), p_correlation_id)
  returning id into v_id;
  return jsonb_build_object('registro_id', v_id, 'fila', acao_prioridades_do_dia(p_usuario_id, p_correlation_id));
end;
$$;

-- ================================================================ escrita: comentários (remoção lógica)
create function acao_comentar(p_usuario_id bigint, p_correlation_id uuid, p_opportunity_id text, p_texto text)
returns jsonb
language plpgsql
set search_path = public
as $$
declare
  v_papel text := system_definir_contexto(p_usuario_id, p_correlation_id);
  v_texto text := trim(p_texto);
  v_id bigint;
begin
  if char_length(coalesce(v_texto, '')) not between 1 and 1000 then
    raise exception using errcode = 'G4422', message = 'comentario_tamanho_invalido';
  end if;
  if v_texto ~ '<[a-zA-Z!/]' then
    raise exception using errcode = 'G4422', message = 'comentario_sem_html';
  end if;
  if not exists (select 1 from core_deals where opportunity_id = p_opportunity_id) then
    raise exception using errcode = 'G4404', message = 'deal_nao_encontrado';
  end if;
  insert into acao_comentarios (opportunity_id, usuario_id, texto, data_negocio)
  values (p_opportunity_id, p_usuario_id, v_texto, config_data_negocio())
  returning id into v_id;
  return jsonb_build_object('comentario_id', v_id);
end;
$$;

create function acao_editar_comentario(p_usuario_id bigint, p_correlation_id uuid, p_comentario_id bigint, p_texto text)
returns jsonb
language plpgsql
set search_path = public
as $$
declare
  v_papel text := system_definir_contexto(p_usuario_id, p_correlation_id);
  v_texto text := trim(p_texto);
begin
  if char_length(coalesce(v_texto, '')) not between 1 and 1000 then
    raise exception using errcode = 'G4422', message = 'comentario_tamanho_invalido';
  end if;
  if v_texto ~ '<[a-zA-Z!/]' then
    raise exception using errcode = 'G4422', message = 'comentario_sem_html';
  end if;
  update acao_comentarios set texto = v_texto, editado_em = now()
   where id = p_comentario_id and removido_em is null;
  if not found then
    raise exception using errcode = 'G4404', message = 'comentario_nao_encontrado';
  end if;
  return jsonb_build_object('comentario_id', p_comentario_id, 'editado', true);
end;
$$;

create function acao_remover_comentario(p_usuario_id bigint, p_correlation_id uuid, p_comentario_id bigint)
returns jsonb
language plpgsql
set search_path = public
as $$
declare
  v_papel text := system_definir_contexto(p_usuario_id, p_correlation_id);
begin
  update acao_comentarios set removido_em = now(), removido_por = p_usuario_id
   where id = p_comentario_id and removido_em is null;
  if not found then
    raise exception using errcode = 'G4404', message = 'comentario_nao_encontrado';
  end if;
  return jsonb_build_object('comentario_id', p_comentario_id, 'removido', true);
end;
$$;

create function acao_restaurar_comentario(p_usuario_id bigint, p_correlation_id uuid, p_comentario_id bigint)
returns jsonb
language plpgsql
set search_path = public
as $$
declare
  v_papel text := system_definir_contexto(p_usuario_id, p_correlation_id);
begin
  update acao_comentarios set removido_em = null, removido_por = null
   where id = p_comentario_id and removido_em is not null;
  if not found then
    raise exception using errcode = 'G4404', message = 'comentario_nao_encontrado';
  end if;
  return jsonb_build_object('comentario_id', p_comentario_id, 'removido', false);
end;
$$;

-- ================================================================ escrita: tags
create function config_criar_tag(p_usuario_id bigint, p_correlation_id uuid, p_nome text, p_cor_token text)
returns jsonb
language plpgsql
set search_path = public
as $$
declare
  v_papel text := system_definir_contexto(p_usuario_id, p_correlation_id);
  v_nome text := trim(p_nome);
  v_id bigint;
begin
  if char_length(coalesce(v_nome, '')) not between 1 and 30 then
    raise exception using errcode = 'G4422', message = 'tag_nome_invalido';
  end if;
  if not (coalesce(config_valor('tag_cores'), '[]'::jsonb) ? p_cor_token) then
    raise exception using errcode = 'G4422', message = 'tag_cor_invalida';
  end if;
  if exists (select 1 from config_tags where lower(nome) = lower(v_nome)) then
    raise exception using errcode = 'G4422', message = 'tag_ja_existe';
  end if;
  insert into config_tags (nome, cor_token, criada_por) values (v_nome, p_cor_token, p_usuario_id)
  returning id into v_id;
  return jsonb_build_object('tag_id', v_id);
end;
$$;

create function config_arquivar_tag(p_usuario_id bigint, p_correlation_id uuid, p_tag_id bigint)
returns jsonb
language plpgsql
set search_path = public
as $$
declare
  v_papel text := system_definir_contexto(p_usuario_id, p_correlation_id);
begin
  update config_tags set ativa = false, arquivada_em = now(), arquivada_por = p_usuario_id
   where id = p_tag_id and ativa;
  if not found then
    raise exception using errcode = 'G4404', message = 'tag_nao_encontrada';
  end if;
  return jsonb_build_object('tag_id', p_tag_id, 'ativa', false);
end;
$$;

create function acao_aplicar_tag(p_usuario_id bigint, p_correlation_id uuid, p_opportunity_id text, p_tag_id bigint)
returns jsonb
language plpgsql
set search_path = public
as $$
declare
  v_papel text := system_definir_contexto(p_usuario_id, p_correlation_id);
  v_id bigint;
begin
  if not exists (select 1 from config_tags where id = p_tag_id and ativa) then
    raise exception using errcode = 'G4422', message = 'tag_inativa_ou_inexistente';
  end if;
  if not exists (select 1 from core_deals where opportunity_id = p_opportunity_id) then
    raise exception using errcode = 'G4404', message = 'deal_nao_encontrado';
  end if;
  select id into v_id from acao_deal_tags
   where opportunity_id = p_opportunity_id and tag_id = p_tag_id and removida_em is null;
  if found then
    return jsonb_build_object('deal_tag_id', v_id, 'ja_aplicada', true);
  end if;
  insert into acao_deal_tags (opportunity_id, tag_id, usuario_id) values (p_opportunity_id, p_tag_id, p_usuario_id)
  returning id into v_id;
  return jsonb_build_object('deal_tag_id', v_id, 'ja_aplicada', false);
end;
$$;

create function acao_remover_tag(p_usuario_id bigint, p_correlation_id uuid, p_opportunity_id text, p_tag_id bigint)
returns jsonb
language plpgsql
set search_path = public
as $$
declare
  v_papel text := system_definir_contexto(p_usuario_id, p_correlation_id);
  v_id bigint;
begin
  update acao_deal_tags set removida_em = now(), removida_por = p_usuario_id
   where opportunity_id = p_opportunity_id and tag_id = p_tag_id and removida_em is null
  returning id into v_id;
  if v_id is null then
    raise exception using errcode = 'G4422', message = 'tag_nao_aplicada';
  end if;
  return jsonb_build_object('deal_tag_id', v_id, 'removida', true);
end;
$$;

-- ================================================================ escrita: lote e desfazer lote
create function system_executar_lote(p_usuario_id bigint, p_correlation_id uuid, p_tipo text,
                                     p_parametros jsonb, p_ids text[], p_etiquetas jsonb default null)
returns jsonb
language plpgsql
set search_path = public
as $$
declare
  v_papel text := system_definir_contexto(p_usuario_id, p_correlation_id);
  v_ids text[] := array(select distinct x from unnest(p_ids) x where x is not null order by 1);
  v_lote bigint;
  v_id text;
  v_res jsonb;
  v_estagio text;
  v_aplicados integer := 0;
  v_pulados jsonb := '[]'::jsonb;
begin
  if p_tipo not in ('tag', 'remover_tag', 'comentario', 'avancar_estagio', 'encerrar_perdido') then
    raise exception using errcode = 'G4422', message = 'tipo_de_lote_invalido';
  end if;
  if coalesce(array_length(v_ids, 1), 0) = 0 then
    raise exception using errcode = 'G4422', message = 'lote_vazio';
  end if;
  if array_length(v_ids, 1) > config_inteiro('limite_lote', 500) then
    raise exception using errcode = 'G4422', message = 'lote_acima_do_limite',
      detail = config_inteiro('limite_lote', 500)::text;
  end if;

  insert into system_lotes (usuario_id, tipo, parametros, etiquetas, quantidade, correlation_id)
  values (p_usuario_id, p_tipo, coalesce(p_parametros, '{}'::jsonb), p_etiquetas, array_length(v_ids, 1), p_correlation_id)
  returning id into v_lote;
  perform system_definir_contexto(p_usuario_id, p_correlation_id, v_lote);

  foreach v_id in array v_ids loop
    begin
      if p_tipo = 'tag' then
        v_res := acao_aplicar_tag(p_usuario_id, p_correlation_id, v_id, (p_parametros ->> 'tag_id')::bigint);
        if (v_res ->> 'ja_aplicada')::boolean then
          raise exception using errcode = 'G4422', message = 'tag_ja_aplicada';
        end if;
      elsif p_tipo = 'remover_tag' then
        perform acao_remover_tag(p_usuario_id, p_correlation_id, v_id, (p_parametros ->> 'tag_id')::bigint);
      elsif p_tipo = 'comentario' then
        perform acao_comentar(p_usuario_id, p_correlation_id, v_id, p_parametros ->> 'texto');
      elsif p_tipo = 'avancar_estagio' then
        select estagio into v_estagio from core_deals where opportunity_id = v_id;
        if v_estagio is distinct from 'Prospecting' then
          raise exception using errcode = 'G4422', message = 'nao_esta_em_prospeccao';
        end if;
        perform core_mudar_estagio(p_usuario_id, p_correlation_id, v_id, null, 'Engaging');
      elsif p_tipo = 'encerrar_perdido' then
        perform core_encerrar_deal(p_usuario_id, p_correlation_id, v_id, null, 'Lost', null,
                                   p_parametros ->> 'motivo', p_parametros ->> 'motivo_detalhe');
      end if;
      v_aplicados := v_aplicados + 1;
    exception when sqlstate 'G4422' or sqlstate 'G4404' or sqlstate 'G4409' then
      v_pulados := v_pulados || jsonb_build_object('opportunity_id', v_id, 'motivo', sqlerrm);
    end;
  end loop;

  update system_lotes
     set aplicados = v_aplicados,
         pulados = jsonb_array_length(v_pulados),
         detalhe = jsonb_build_object('pulados', v_pulados)
   where id = v_lote;
  insert into system_eventos (tipo, detalhe, usuario_id, correlation_id)
  values ('lote_aplicado', jsonb_build_object('lote_id', v_lote, 'tipo', p_tipo, 'aplicados', v_aplicados,
                                              'pulados', jsonb_array_length(v_pulados)),
          p_usuario_id, p_correlation_id);

  return jsonb_build_object('lote_id', v_lote, 'quantidade', array_length(v_ids, 1),
                            'aplicados', v_aplicados, 'pulados', v_pulados);
end;
$$;

create function system_desfazer_lote(p_usuario_id bigint, p_correlation_id uuid, p_lote_id bigint)
returns jsonb
language plpgsql
set search_path = public
as $$
declare
  v_papel text := system_definir_contexto(p_usuario_id, p_correlation_id);
  v_lote system_lotes%rowtype;
  v_aud system_auditoria%rowtype;
  v_revertidos integer := 0;
  v_pulados jsonb := '[]'::jsonb;
  v_atual timestamptz;
  v_n integer;
begin
  select * into v_lote from system_lotes where id = p_lote_id for update;
  if not found then
    raise exception using errcode = 'G4404', message = 'lote_nao_encontrado';
  end if;
  if v_lote.desfeito_em is not null then
    raise exception using errcode = 'G4422', message = 'lote_ja_desfeito';
  end if;
  if v_lote.criado_em < now() - make_interval(hours => config_inteiro('lote_desfazer_horas', 24)) then
    raise exception using errcode = 'G4422', message = 'prazo_para_desfazer_encerrado';
  end if;
  if v_lote.usuario_id <> p_usuario_id and v_papel not in ('manager', 'admin') then
    raise exception using errcode = 'G4403', message = 'desfazer_lote_autor_manager_ou_admin';
  end if;

  for v_aud in
    select * from system_auditoria
     where lote_id = p_lote_id and tabela in ('core_deals', 'acao_deal_tags', 'acao_comentarios')
     order by id desc
  loop
    begin
      v_n := 0;
      if v_aud.tabela = 'core_deals' and v_aud.operacao = 'update' then
        select atualizado_em into v_atual from core_deals where opportunity_id = v_aud.registro_id for update;
        if v_atual = (v_aud.depois ->> 'atualizado_em')::timestamptz then
          perform core_restaurar_deal(v_aud.registro_id, v_aud.antes);
          v_n := 1;
        end if;
      elsif v_aud.tabela = 'acao_deal_tags' and v_aud.operacao = 'insert' then
        update acao_deal_tags set removida_em = now(), removida_por = p_usuario_id
         where id = v_aud.registro_id::bigint and removida_em is null;
        get diagnostics v_n = row_count;
      elsif v_aud.tabela = 'acao_deal_tags' and v_aud.operacao = 'update' then
        update acao_deal_tags set removida_em = null, removida_por = null
         where id = v_aud.registro_id::bigint and removida_em = (v_aud.depois ->> 'removida_em')::timestamptz;
        get diagnostics v_n = row_count;
      elsif v_aud.tabela = 'acao_comentarios' and v_aud.operacao = 'insert' then
        update acao_comentarios set removido_em = now(), removido_por = p_usuario_id
         where id = v_aud.registro_id::bigint and removido_em is null;
        get diagnostics v_n = row_count;
      end if;
      if v_n > 0 then
        v_revertidos := v_revertidos + 1;
      else
        v_pulados := v_pulados || jsonb_build_object('tabela', v_aud.tabela, 'registro_id', v_aud.registro_id,
                                                     'motivo', 'mudou_depois_do_lote');
      end if;
    exception when sqlstate 'G4422' or sqlstate 'G4409' then
      v_pulados := v_pulados || jsonb_build_object('tabela', v_aud.tabela, 'registro_id', v_aud.registro_id,
                                                   'motivo', sqlerrm);
    end;
  end loop;

  update system_lotes set desfeito_em = now(), desfeito_por = p_usuario_id where id = p_lote_id;
  insert into system_eventos (tipo, detalhe, usuario_id, correlation_id)
  values ('lote_desfeito', jsonb_build_object('lote_id', p_lote_id, 'revertidos', v_revertidos,
                                              'pulados', jsonb_array_length(v_pulados)),
          p_usuario_id, p_correlation_id);

  return jsonb_build_object('lote_id', p_lote_id, 'revertidos', v_revertidos, 'pulados', v_pulados);
end;
$$;

-- ================================================================ permissões: só a service role executa
do $$
declare
  v_papel text;
begin
  execute 'revoke execute on all functions in schema public from public';
  foreach v_papel in array array['anon', 'authenticated'] loop
    if exists (select 1 from pg_roles where rolname = v_papel) then
      execute format('revoke execute on all functions in schema public from %I', v_papel);
    end if;
  end loop;
  if exists (select 1 from pg_roles where rolname = 'service_role') then
    execute 'grant execute on all functions in schema public to service_role';
  end if;
end;
$$;
