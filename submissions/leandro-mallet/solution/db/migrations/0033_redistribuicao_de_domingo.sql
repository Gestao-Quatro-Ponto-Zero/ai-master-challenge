-- 0033_redistribuicao_de_domingo.sql  [O-39 — redistribuição de domingo só por equilíbrio]
-- Achado da #3 antes de gravar: core_repassar_deal (0024) aceita p_origem = 'redistribuicao', mas aplicava as
-- travas do repasse (fit_minimo 75, no máximo 3 pontos abaixo do dono, top 5 do novo) a QUALQUER origem. Com isso,
-- 224 das 475 trocas do plano seriam recusadas. A regra decidida (decisão 47, cenário B) é só equilíbrio.
-- O que muda:
--   1. core_repassar_deal (mesma assinatura e mesmas permissões: só o papel de carga executa):
--      - as três travas valem só para 'repasse_janela';
--      - para 'redistribuicao' continuam: deal aberto, SEM contato registrado (a checagem de contato passa a valer
--        para as duas origens), vendedor de destino ativo e diferente do dono, limite de repasses por lead (se
--        configurado), registro em acao_reatribuicoes com fit_dono e fit_novo, e auditoria;
--      - o motivo da redistribuição passa a ser "Redistribuição de domingo.";
--      - a redistribuição continua sem penalidade (só o repasse por janela gera, quando configurada).
--   2. core_linha_do_tempo (a da 0031): os repasses automáticos aparecem com o motivo
--      ("Redistribuição de domingo. Anna Snelling → Cecily Lampkin"); a troca de vendedor feita pelo sistema deixa
--      de aparecer também como "Passado para …" (sem duplicar). A reatribuição pelo manager segue igual.
-- Fica para depois (README): a trava do dono pelo manager, que ainda não existe no banco.
-- Nada é apagado. Trava de contexto, limites e auditoria seguem como estão.

-- 1. Repasse e redistribuição ------------------------------------------------------------------------------------

create or replace function core_repassar_deal(
  p_correlation_id uuid,
  p_opportunity_id text,
  p_para_vendedor  text,
  p_origem         text,          -- 'repasse_janela' ou 'redistribuicao'
  p_execucao_id    bigint,
  p_fit_dono       smallint,
  p_fit_novo       smallint,
  p_posicao_top    smallint,
  p_faixa_heat     text default null
) returns acao_reatribuicoes
language plpgsql set search_path = public as $$
declare
  u        config_usuarios := system_iniciar_contexto_sistema(p_correlation_id);   -- recusa o app (GS403)
  d        core_deals;
  r        acao_reatribuicoes;
  v_rep    jsonb := coalesce(config_valor('repasse'), '{}'::jsonb);
  v_pen    jsonb := coalesce(config_valor('penalidade_roteamento'), '{}'::jsonb);
  v_qtd    integer;
begin
  if p_origem not in ('repasse_janela', 'redistribuicao') then
    raise exception 'Origem do repasse inválida.' using errcode = 'GS400';
  end if;
  select * into d from core_deals where opportunity_id = p_opportunity_id for update;
  if not found then
    raise exception 'Deal % não encontrado.', p_opportunity_id using errcode = 'GS404';
  end if;
  if d.estagio not in ('Prospecting', 'Engaging') then
    raise exception 'Só deal aberto é repassado.' using errcode = 'GS422';
  end if;
  if d.vendedor_nome = p_para_vendedor then
    raise exception 'O lead já é deste vendedor.' using errcode = 'GS422';
  end if;
  if not exists (select 1 from core_vendedores v join config_usuarios cu on cu.vendedor_nome = v.nome and cu.ativo
                  where v.nome = p_para_vendedor) then
    raise exception 'Vendedor % não está ativo.', p_para_vendedor using errcode = 'GS422';
  end if;
  -- sem contato registrado: vale para o repasse por janela e para a redistribuição
  if d.ultimo_contato_em is not null then
    raise exception 'Lead com contato registrado não é repassado.' using errcode = 'GS422';
  end if;
  -- travas da decisão 38 (números em config_parametros.repasse): só no repasse por mudança de janela
  if p_origem = 'repasse_janela' then
    if p_fit_novo is null or p_fit_novo < coalesce((v_rep ->> 'fit_minimo')::integer, 75) then
      raise exception 'FIT do novo vendedor abaixo do mínimo para repasse.' using errcode = 'GS422';
    end if;
    if p_fit_dono is not null and p_fit_novo < p_fit_dono - coalesce((v_rep ->> 'max_abaixo_do_dono')::integer, 3) then
      raise exception 'FIT do novo vendedor muito abaixo do dono atual.' using errcode = 'GS422';
    end if;
    if p_posicao_top is null or p_posicao_top > coalesce((v_rep ->> 'top_n')::integer, 5) then
      raise exception 'O lead não entra no top do novo vendedor.' using errcode = 'GS422';
    end if;
  end if;
  if (v_rep ->> 'max_repasses_por_lead') is not null then
    select count(*) into v_qtd from acao_reatribuicoes
     where opportunity_id = p_opportunity_id and origem in ('repasse_janela', 'redistribuicao');
    if v_qtd >= (v_rep ->> 'max_repasses_por_lead')::integer then
      raise exception 'Este lead já atingiu o máximo de repasses.' using errcode = 'GS422';
    end if;
  end if;

  update core_deals set vendedor_nome = p_para_vendedor where opportunity_id = p_opportunity_id;
  insert into acao_reatribuicoes (opportunity_id, de_vendedor, para_vendedor, usuario_id, motivo, origem,
                                  execucao_id, fit_dono, fit_novo, posicao_top, faixa_heat)
  values (p_opportunity_id, d.vendedor_nome, p_para_vendedor, u.id,
          case p_origem when 'repasse_janela' then 'Lead sem contato mudou de faixa.' else 'Redistribuição de domingo.' end,
          p_origem, p_execucao_id, p_fit_dono, p_fit_novo, p_posicao_top, p_faixa_heat)
  returning * into r;

  -- penalidade: só o repasse por janela (a redistribuição é equilíbrio, não punição)
  if p_origem = 'repasse_janela' and (v_pen ->> 'pontos') is not null and (v_pen ->> 'dias') is not null then
    insert into system_penalidades (vendedor_nome, pontos, fim, opportunity_id, reatribuicao_id, correlation_id)
    values (d.vendedor_nome, (v_pen ->> 'pontos')::numeric, now() + make_interval(days => (v_pen ->> 'dias')::integer),
            p_opportunity_id, r.id, p_correlation_id);
  end if;
  return r;
end $$;

-- 2. Linha do tempo (a da 0031, com os repasses automáticos e o motivo) ----------------------------------------------

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
           case when aud.antes ->> 'vendedor_nome' is distinct from aud.depois ->> 'vendedor_nome' and aud.papel <> 'sistema'
                then 'Passado para ' || (aud.depois ->> 'vendedor_nome') end),
         aud.nome_exibicao, false, aud.correlation_id::text
    from aud
   where aud.operacao = 'update'
     and (aud.antes ->> 'nome' is distinct from aud.depois ->> 'nome'
          or aud.antes ->> 'conta_nome' is distinct from aud.depois ->> 'conta_nome'
          or aud.antes ->> 'contato_id' is distinct from aud.depois ->> 'contato_id'
          or (aud.antes ->> 'vendedor_nome' is distinct from aud.depois ->> 'vendedor_nome' and aud.papel <> 'sistema'))
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
  -- repasses automáticos (repasse por mudança de janela e redistribuição de domingo), com o motivo
  select coalesce(
           (select a.data_negocio from aud a
             where a.operacao = 'update' and a.papel = 'sistema'
               and a.antes ->> 'vendedor_nome' = r.de_vendedor and a.depois ->> 'vendedor_nome' = r.para_vendedor
             order by abs(extract(epoch from a.criado_em - r.criado_em)) limit 1),
           system_data_negocio()),
         r.criado_em, 'repasse',
         coalesce(r.motivo, 'Repasse.') || ' ' || r.de_vendedor || ' → ' || r.para_vendedor,
         null::text, false, r.id::text
    from acao_reatribuicoes r
   where r.opportunity_id = p_opportunity_id and r.origem in ('repasse_janela', 'redistribuicao')
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
